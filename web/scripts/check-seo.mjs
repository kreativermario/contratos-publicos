// Node 24 strips the types, so the real module is tested rather than a copy.
import assert from 'node:assert/strict';
import { seoUrls, shortMunicipality } from '../src/lib/seo.ts';

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
// The short name is a page's identity now: the title, the description and the
// JSON-LD all carry it, in the static file a crawler reads. Both spellings of
// the prefix appear in the register, and a council whose name simply lacks one
// must come back whole rather than empty.
const names = [
	['Município de Odivelas',        'Odivelas'],
	['Municipio de Odivelas',        'Odivelas'],
	['Câmara Municipal de Loures',   'Loures'],
	['Camara Municipal do Porto',    'Porto'],
	['Município da Lourinhã',        'Lourinhã'],
	['Freguesia de Caneças',         'Freguesia de Caneças']
];
for (const [full, short] of names) {
	assert.equal(shortMunicipality(full), short, full);
}

console.log(`ok: ${cases.length} canonical pairs, ${names.length} short names`);
