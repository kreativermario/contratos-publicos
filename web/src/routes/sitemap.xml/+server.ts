import { PUBLIC_SITE_URL } from '$env/static/public';
import type { RequestHandler } from './$types';

// Prerendered into a real file at build time, so nginx serves it from disk and
// the SPA fallback never has to answer for it. `prerender` overrides the root
// layout, which turns it off for every page.
export const prerender = true;

/** Both language trees. Query-parameter views are the same URL to a crawler. */
const PATHS = ['/', '/panorama', '/faqs', '/termos'];

export const GET: RequestHandler = async () => {
	const site = PUBLIC_SITE_URL;
	const url = (path: string, lang: '' | '/en') =>
		`${site}${lang}${lang && path === '/' ? '' : path}`;

	const entries = PATHS.flatMap((path) =>
		(['', '/en'] as const).map(
			(lang) => `  <url>
    <loc>${url(path, lang)}</loc>
    <xhtml:link rel="alternate" hreflang="pt-PT" href="${url(path, '')}" />
    <xhtml:link rel="alternate" hreflang="en" href="${url(path, '/en')}" />
    <xhtml:link rel="alternate" hreflang="x-default" href="${url(path, '')}" />
    <changefreq>daily</changefreq>
    <priority>${path === '/' ? '1.0' : '0.7'}</priority>
  </url>`
		)
	).join('\n');

	return new Response(
		`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${entries}
</urlset>
`,
		{ headers: { 'content-type': 'application/xml' } }
	);
};
