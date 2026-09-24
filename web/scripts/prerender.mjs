/**
 * Give every município page a real HTML file, so a crawler gets a real page.
 *
 * The site is `ssr: false` behind adapter-static, which means nginx returns the
 * same `index.html` for every URL: one title, one description, an empty body.
 * The per-route head tags are written by client JavaScript after hydration.
 * Google runs that JavaScript on a second pass; Bing, DuckDuckGo and every link
 * unfurler do not. Handing a crawler 308 URLs that all answer with the same
 * title is how a site teaches an index that it is duplicate thin content, so
 * the sitemap below and these files ship together or not at all.
 *
 * What this does NOT do is prerender content. The body stays the SPA shell and
 * the numbers still arrive from the API on hydration. Only the head is written
 * here, and only from facts that do not move between deploys: the name, the
 * canonical pair, the structured data. Never a euro total, which would be a day
 * stale before anybody read it.
 *
 * nginx needs no change for any of this. `location /` already ends
 * `try_files $uri $uri/ /index.html`, so `/municipio/506811570` resolves
 * `$uri/` to this directory's index.html when it exists and falls through to
 * the SPA shell when it does not.
 *
 * Runs from `npm run build`, after `vite build`.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { seoUrls, shortMunicipality } from '../src/lib/seo.ts';

const BUILD = 'build';
const SITE = (process.env.PUBLIC_SITE_URL ?? 'https://ondevaiparar.pt').replace(/\/$/, '');
// Nothing is hardcoded, but a bare `npm run build` has to produce a usable site,
// so the default is the live API. A build that cannot reach it degrades to the
// static-only sitemap rather than failing: a data source being down must never
// block a deploy.
const API = (process.env.PRERENDER_API ?? `${SITE}/api/v1`).replace(/\/$/, '');
// The .com is a redirect domain and the .pt stays canonical everywhere. This is
// not a second home for the site, it is the one Search Console property that can
// be verified while the .pt is still pending: a property only accepts a sitemap
// listing its own host, so the alternate needs its own file with its own URLs.
// Google follows the 301s back to the .pt, which is how a move is signalled.
// Empty writes no file, which is the state to return to once the .pt verifies.
const ALT_SITE = (process.env.PRERENDER_ALT_SITE ?? '').replace(/\/$/, '');

const STATIC_PATHS = ['/', '/panorama', '/faqs', '/termos'];
const LANGS = /** @type {const} */ (['pt', 'en']);

/* ---- messages -------------------------------------------------------------
 * Read as text, not imported: messages.ts imports `$app/state`, which does not
 * exist under plain node. scripts/check-messages.mjs reads it the same way and
 * for the same reason, and it is that script which guarantees the keys below
 * exist in both bundles.
 */
const messagesSrc = readFileSync('src/lib/messages.ts', 'utf8');

function bundle(name) {
	const start = messagesSrc.indexOf(`const ${name}: Record<string, string> = {`);
	if (start < 0) throw new Error(`no ${name} bundle in messages.ts`);
	const body = messagesSrc.slice(start, messagesSrc.indexOf('\n};', start));
	const out = {};
	// Single-quoted values, optionally wrapped onto the next line, which is how
	// the longer strings in that file are written.
	for (const m of body.matchAll(/^\t'([^']+)':\s*\n?\s*'((?:[^'\\]|\\.)*)'/gm)) {
		out[m[1]] = m[2].replace(/\\'/g, "'").replace(/\\\\/g, '\\');
	}
	return out;
}

const MESSAGES = { pt: bundle('PT'), en: bundle('EN') };

/** One string, in one language, with `{name}` filled. Mirrors `t()` exactly,
 *  Portuguese fallback included, so a key missing from `en` renders the same
 *  here as it does in the browser. */
function msg(lang, key, vars) {
	const raw = MESSAGES[lang][key] ?? MESSAGES.pt[key] ?? key;
	return vars ? raw.replace(/\{(\w+)\}/g, (w, k) => (k in vars ? String(vars[k]) : w)) : raw;
}

/* ---- html ---------------------------------------------------------------- */

/** Anything going into an attribute or a text node. Council names come from
 *  IMPIC verbatim and are not ours to trust with angle brackets. */
const esc = (s) =>
	String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;').replace(/'/g, '&#39;');

/** Replace the shell's head tags rather than appending: a second <title> or a
 *  second canonical is worse than the generic one it was meant to fix. */
function rewriteHead(shell, { title, description, canonical, alternates, jsonLd }) {
	let html = shell
		.replace(/<title>[\s\S]*?<\/title>/, `<title>${esc(title)}</title>`)
		.replace(/<meta name="description" content="[^"]*" \/>/,
			`<meta name="description" content="${esc(description)}" />`)
		.replace(/<meta property="og:url" content="[^"]*" \/>/,
			`<meta property="og:url" content="${esc(canonical)}" />`)
		.replace(/<meta property="og:title" content="[^"]*" \/>/,
			`<meta property="og:title" content="${esc(title)}" />`)
		.replace(/<meta property="og:description" content="[^"]*" \/>/,
			`<meta property="og:description" content="${esc(description)}" />`)
		.replace(/<meta name="twitter:title" content="[^"]*" \/>/,
			`<meta name="twitter:title" content="${esc(title)}" />`)
		.replace(/<meta name="twitter:description" content="[^"]*" \/>/,
			`<meta name="twitter:description" content="${esc(description)}" />`);

	const links = [
		`<link rel="canonical" href="${esc(canonical)}" />`,
		...alternates.map(([hreflang, href]) =>
			`<link rel="alternate" hreflang="${hreflang}" href="${esc(href)}" />`),
		`<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>`
	].join('\n\t\t');

	return html.replace('</head>', `\t${links}\n\t</head>`);
}

/** Structured data only, for the one file that must stay route-agnostic. */
function addJsonLd(shell, jsonLd) {
	return shell.replace('</head>',
		`\t<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>\n\t</head>`);
}

/* ---- structured data ------------------------------------------------------
 * This is the "associate the site with contratos públicos and base.gov.pt"
 * half, in the only form a search engine can act on. `sameAs` is the specific
 * mechanism that ties an entity to others, and `isBasedOn` names the register
 * the numbers come from.
 *
 * Nothing here may assert more than the site asserts on screen. No rating, no
 * claim of officialness: the disclaimer rules in scoring.py apply to markup.
 */
const SAME_AS = [
	'https://www.base.gov.pt',
	'https://dados.gov.pt',
	'https://www.impic.pt',
	'https://github.com/kreativermario/contratos-publicos'
];

const publisher = {
	'@type': 'Organization',
	name: 'Onde Vai Parar',
	url: `${SITE}/`,
	sameAs: SAME_AS
};

function municipioJsonLd({ name, canonical, description, lang }) {
	return {
		'@context': 'https://schema.org',
		'@graph': [
			{
				'@type': 'Dataset',
				name,
				description,
				url: canonical,
				inLanguage: lang === 'en' ? 'en' : 'pt-PT',
				license: 'https://creativecommons.org/licenses/by/4.0/',
				creator: publisher,
				isBasedOn: 'https://dados.gov.pt',
				spatialCoverage: { '@type': 'Place', name },
				isAccessibleForFree: true
			},
			{
				'@type': 'BreadcrumbList',
				itemListElement: [
					{ '@type': 'ListItem', position: 1, name: 'Onde Vai Parar',
					  item: lang === 'en' ? `${SITE}/en` : `${SITE}/` },
					{ '@type': 'ListItem', position: 2, name }
				]
			}
		]
	};
}

function homeJsonLd(lang) {
	return {
		'@context': 'https://schema.org',
		'@graph': [
			publisher,
			{
				'@type': 'WebSite',
				name: 'Onde Vai Parar',
				url: lang === 'en' ? `${SITE}/en` : `${SITE}/`,
				inLanguage: lang === 'en' ? 'en' : 'pt-PT',
				publisher
			}
		]
	};
}

/* ---- prerendered body ------------------------------------------------------
 * A head alone is not a page. The app is ssr:false, so every crawler that does
 * not run JavaScript, which is all of them except Google, was handed 616 URLs
 * carrying a distinct title over an identical empty body: the exact shape an
 * index reads as thin duplicate content. This writes the part of the page that
 * does not move between deploys, which is the only part that may be written
 * here at all. The name, what the page holds, where the numbers come from, and
 * the one sentence that has to travel with them. No figure, no euro total, no
 * count: these files are regenerated on deploy and nothing else touches them.
 *
 * It is removed on mount by src/routes/+layout.svelte. SvelteKit mounts into
 * the `display: contents` div below it, appending rather than replacing, so
 * without that the static copy would sit above the real page for good.
 */
function municipioBody(lang, { name, description }) {
	const home = lang === 'en' ? '/en' : '/';
	const panorama = lang === 'en' ? '/en/panorama' : '/panorama';
	return `<div id="prerendered" class="wrap">
	<p class="eyebrow">${esc(msg(lang, 'muni.eyebrow'))}</p>
	<h1>${esc(name)}</h1>
	<p>${esc(description)}</p>
	<p>${esc(msg(lang, 'muni.prerenderSections', { name }))}</p>
	<p>${esc(msg(lang, 'disclaimer.source'))}</p>
	<p>${esc(msg(lang, 'disclaimer.legal'))}</p>
	<p><a href="${esc(home)}">${esc(msg(lang, 'common.site'))}</a>
	 | <a href="${esc(panorama)}">${esc(msg(lang, 'nav.panorama'))}</a></p>
</div>
`;
}

/** Put it in the body, before the div SvelteKit mounts into. */
const withBody = (html, body) =>
	html.replace(/(<div style="display: contents">)/, `${body}\t\t$1`);

/* ---- sitemap -------------------------------------------------------------- */

function sitemap(paths, base) {
	const entries = paths.map((path) => {
		const { pt, en } = seoUrls(base, path);
		return [pt, en].map((loc) => `  <url>
    <loc>${esc(loc)}</loc>
    <xhtml:link rel="alternate" hreflang="pt-PT" href="${esc(pt)}" />
    <xhtml:link rel="alternate" hreflang="en" href="${esc(en)}" />
    <xhtml:link rel="alternate" hreflang="x-default" href="${esc(pt)}" />
    <changefreq>daily</changefreq>
    <priority>${path === '/' ? '1.0' : '0.7'}</priority>
  </url>`).join('\n');
	}).join('\n');

	return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${entries}
</urlset>
`;
}

/* ---- run ------------------------------------------------------------------ */

// Comments are for whoever reads this repository, not for whoever loads the
// page. app.html is the only source of them that survives the build (the Svelte
// compiler drops component comments already), and every file written below is a
// copy of it, so stripping once here strips them everywhere. There is no
// `%sveltekit.body%` content to protect: the app is ssr:false, so the shell
// carries no hydration markers of the `<!--[-->` kind.
const shell = readFileSync(join(BUILD, 'index.html'), 'utf8').replace(/\n?\s*<!--[\s\S]*?-->/g, '');

/** The shell path for a route in a language tree: '' for pt, '/en' for en. */
const fileFor = (lang, path) =>
	join(BUILD, lang === 'en' ? 'en' : '.', path, 'index.html');

function write(lang, path, html) {
	const file = fileFor(lang, path);
	mkdirSync(dirname(file), { recursive: true });
	writeFileSync(file, html);
	return file;
}

let municipalities = [];
try {
	const res = await fetch(`${API}/municipalities`, { signal: AbortSignal.timeout(30_000) });
	if (!res.ok) throw new Error(`HTTP ${res.status}`);
	municipalities = await res.json();
} catch (err) {
	// Loud, but not fatal. A deploy must not be blocked because a data source is
	// down, and a smaller sitemap must never ship silently.
	console.warn(`prerender: could not reach ${API}/municipalities (${err.message})`);
	console.warn('prerender: writing the static-only sitemap, no município pages');
}

const written = [];

// `build/index.html` is the SPA fallback for EVERY route nginx cannot resolve
// to a file: /empresa/500123456, /contrato/99, /panorama, all of them. So it
// must NOT carry a canonical, a route title or a route description. A canonical
// written here would tell the index that every one of those URLs is the
// homepage, which is the exact failure app.html already carries a comment
// about. It gets the site-wide Organization and WebSite graph and nothing else:
// those are true on any page of the site, which is the test for belonging here.
written.push(write('pt', '/', addJsonLd(shell, homeJsonLd('pt'))));

// `/en` is different. nginx resolves it to build/en/index.html via `$uri/`, and
// falls back to the root shell for /en/faqs and everything deeper, so this file
// is only ever served for the English homepage and can safely be specific.
{
	const { pt, en } = seoUrls(SITE, '/');
	written.push(write('en', '/', rewriteHead(shell, {
		title: msg('en', 'common.siteTitle'),
		description: msg('en', 'common.description'),
		canonical: en,
		alternates: [['pt-PT', pt], ['en', en], ['x-default', pt]],
		jsonLd: homeJsonLd('en')
	})));
}

for (const m of municipalities) {
	if (!m?.nif) continue;
	const name = shortMunicipality(m.name ?? '') || m.nif;
	const path = `/municipio/${encodeURIComponent(m.nif)}`;
	const { pt, en } = seoUrls(SITE, path);
	for (const lang of LANGS) {
		const description = msg(lang, 'muni.metaDescription', { name });
		const canonical = lang === 'en' ? en : pt;
		written.push(write(lang, path, withBody(rewriteHead(shell, {
			title: msg(lang, 'muni.metaTitle', { name }),
			description,
			canonical,
			alternates: [['pt-PT', pt], ['en', en], ['x-default', pt]],
			jsonLd: municipioJsonLd({ name, canonical, description, lang })
		}), municipioBody(lang, { name, description }))));
	}
}

const paths = [
	...STATIC_PATHS,
	...municipalities.filter((m) => m?.nif).map((m) => `/municipio/${encodeURIComponent(m.nif)}`)
];
writeFileSync(join(BUILD, 'sitemap.xml'), sitemap(paths, SITE));
if (ALT_SITE) writeFileSync(join(BUILD, 'sitemap-alt.xml'), sitemap(paths, ALT_SITE));

// The failure that would otherwise reach production in silence: a sitemap
// promising a URL that resolves to the generic shell.
for (const path of paths) {
	if (STATIC_PATHS.includes(path)) continue;
	for (const lang of LANGS) {
		const file = fileFor(lang, path);
		if (!existsSync(file)) throw new Error(`sitemap lists ${path} but ${file} was not written`);
	}
}

console.log(
	`ok: ${written.length} prerendered pages, ${paths.length * 2} sitemap URLs` +
	(ALT_SITE ? ` (+ sitemap-alt.xml for ${ALT_SITE})` : '') +
	(municipalities.length ? '' : ' (no API, static paths only)')
);
