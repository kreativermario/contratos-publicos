/**
 * The two languages must carry the same keys, and every key the source asks for
 * must exist.
 *
 * A missing key is not a crash: `t()` falls back to Portuguese and then to the
 * key itself, so the failure mode is English prose with a stray `muni.spent`
 * in the middle of it. Nothing else catches that: svelte-check reads types, not
 * strings. Run with `node scripts/check-messages.mjs`.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const src = readFileSync('src/lib/messages.ts', 'utf8');

/** The key lists of the two bundles, read off the literal declarations. */
function keysOf(name) {
	const start = src.indexOf(`const ${name}: Record<string, string> = {`);
	if (start < 0) throw new Error(`no ${name} bundle in messages.ts`);
	const body = src.slice(start, src.indexOf('\n};', start));
	return new Set([...body.matchAll(/^\t'([^']+)':/gm)].map((m) => m[1]));
}

const pt = keysOf('PT');
const en = keysOf('EN');
const problems = [];

for (const k of pt) if (!en.has(k)) problems.push(`missing from en: ${k}`);
for (const k of en) if (!pt.has(k)) problems.push(`missing from pt: ${k}`);

/** Every literal `t('x')` / `tl('pt', 'x')` / `maybe('x')` in the app. */
function* files(dir) {
	for (const name of readdirSync(dir)) {
		const path = join(dir, name);
		if (statSync(path).isDirectory()) yield* files(path);
		else if (/\.(svelte|ts)$/.test(path) && !path.endsWith('messages.ts')) yield path;
	}
}

for (const path of files('src')) {
	const text = readFileSync(path, 'utf8');
	for (const m of text.matchAll(/\b(?:t|maybe)\(\s*'([a-zA-Z0-9_.]+)'/g)) {
		if (!pt.has(m[1])) problems.push(`${path}: unknown key ${m[1]}`);
	}
	for (const m of text.matchAll(/\btl\(\s*'(?:pt|en)'\s*,\s*'([a-zA-Z0-9_.]+)'/g)) {
		if (!pt.has(m[1])) problems.push(`${path}: unknown key ${m[1]}`);
	}
}

// The API's own keys, which no literal in the source spells out: they arrive in
// the JSON and are looked up through a template string.
const fromApi = [
	...['source', 'publication_lag', 'bidders', 'map_overlap', 'legal'].map((k) => `disclaimer.${k}`),
	...['clean', 'fishy', 'blatant'].flatMap((k) => [`verdict.${k}`, `verdict.${k}.quip`]),
	...['ok', 'warn', 'serious', 'critical'].map((k) => `sev.${k}`),
	...['limite', 'pessoa', 'sozinho'].flatMap((k) => [`flag.${k}`, `flag.${k}.why`]),
	...['ajuste_direto', 'concentracao', 'single_bidder', 'threshold_surf', 'newcomer_value',
		'ad_contracts', 'undisclosed_bidders', 'top_supplier', 'top3_suppliers', 'repeat_winners']
		.flatMap((k) => [`signal.${k}`, `signal.${k}.blurb`])
];
for (const k of fromApi) if (!pt.has(k)) problems.push(`no message for API key ${k}`);

if (problems.length) {
	console.error(problems.join('\n'));
	process.exit(1);
}
console.log(`ok: ${pt.size} keys, both languages`);
