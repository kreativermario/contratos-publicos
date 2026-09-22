// Node 24 strips the types, so the real module is tested rather than a copy.
import assert from 'node:assert/strict';
import { seoUrls } from '../src/lib/seo.ts';

const S = 'https://exemplo.pt';
const cases = [
	['/',                 'https://exemplo.pt/',            'https://exemplo.pt/en'],
	['/en',               'https://exemplo.pt/',            'https://exemplo.pt/en'],
	['/en/',              'https://exemplo.pt/',            'https://exemplo.pt/en'],
	['/panorama',         'https://exemplo.pt/panorama',    'https://exemplo.pt/en/panorama'],
	['/panorama/',        'https://exemplo.pt/panorama',    'https://exemplo.pt/en/panorama'],
	['/en/panorama',      'https://exemplo.pt/panorama',    'https://exemplo.pt/en/panorama'],
	// "empresa" begins with "en" and must not be eaten by the prefix strip
	['/empresa/500123456','https://exemplo.pt/empresa/500123456', 'https://exemplo.pt/en/empresa/500123456']
];

for (const [path, pt, en] of cases) {
	assert.deepEqual(seoUrls(S, path), { pt, en }, path);
}
console.log(`ok: ${cases.length} canonical pairs`);
