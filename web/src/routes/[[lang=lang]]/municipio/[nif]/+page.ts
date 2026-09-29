import {
	api, type Config, type ContractRow, type Mandate, type MapCell, type Municipality,
	type Rival, type Score, type Stats, type Supplier
} from '$lib/api';
import type { PageLoad } from './$types';

/** Longest window the year picker offers. Five years of one municipality is
 *  already a wide read, and the UI has to stop somewhere it can label. */
export const _MAX_SPAN = 5;

const year = (v: string | null): number | undefined => {
	const n = Number(v);
	return Number.isInteger(n) && n > 1900 ? n : undefined;
};

export const load: PageLoad = async ({ url, params, fetch: _f }) => {
	// The nif is the path, not a query parameter. It is also the only stable
	// identifier: concelho names repeat (there are two Lagoas), so a slug would
	// need disambiguating and would still break the moment a name is respelled.
	const nif = params.nif;
	// Started first: neither depends on the window or on the NIF, and asking
	// for them in sequence cost two round trips before the page's own data.
	const municipalitiesP = api<Municipality[]>('/municipalities');
	// The legal forms the filter can offer. Served rather than listed here, so
	// the dropdown can only ever contain values the query actually matches.
	const legalFormsP = api<Config>('/config')
		.then((c) => c.legal_forms ?? [])
		.catch(() => [] as string[]);

	// One window for the whole page. Every panel reads the same years, so the
	// index, the graph, the map and the tables can never disagree about which
	// period they are describing. Empty means whatever is loaded.
	let yearFrom = year(url.searchParams.get('from'));
	let yearTo = year(url.searchParams.get('to'));
	if (yearFrom && yearTo && yearFrom > yearTo) [yearFrom, yearTo] = [yearTo, yearFrom];
	if (yearFrom && yearTo && yearTo - yearFrom + 1 > _MAX_SPAN) yearFrom = yearTo - _MAX_SPAN + 1;

	// A mandate is not a run of years: it starts on election day, in late
	// September or October, so filtering a term by year dragged in the previous
	// administration's autumn. When the URL carries exact dates they win.
	const dateFrom = url.searchParams.get('de') ?? undefined;
	const dateTo = url.searchParams.get('ate') ?? undefined;

	const win = dateFrom || dateTo
		? { date_from: dateFrom, date_to: dateTo }
		: { year_from: yearFrom, year_to: yearTo };

	// Nothing is awaited. SvelteKit blocks the navigation on everything a load
	// awaits, and on a cache miss these took up to half a minute between them,
	// all of it spent looking at the previous page. Returned as one promise,
	// the page paints its skeleton at once and fills in when the data lands.
	const rest = fetchAll(nif, win, municipalitiesP, legalFormsP);
	// Attached here so a reader who navigates away before it settles does not
	// leave an unhandled rejection behind; the page reads the error itself.
	rest.catch(() => {});

	return { nif, rest, yearFrom, yearTo, dateFrom, dateTo };
};

function fetchAll(nif: string, win: Record<string, unknown>,
                  municipalitiesP: Promise<Municipality[]>, legalFormsP: Promise<string[]>) {
	return Promise.all([
		municipalitiesP,
		legalFormsP,
		api<Score>(`/municipalities/${nif}/score`, win),
		api<Supplier[]>(`/municipalities/${nif}/suppliers`, { limit: 120, ...win }),
		api<Rival[]>(`/municipalities/${nif}/rivals`, { limit: 40, ...win }),
		api<ContractRow[]>(`/municipalities/${nif}/contracts`, { limit: 40, ...win }),
		api<MapCell[]>(`/municipalities/${nif}/map`, win),
		api<Stats>(`/municipalities/${nif}/stats`, win),
		// Not year-filtered on purpose: the timeline is the whole run of terms.
		// A miss is survivable, the rest of the page does not depend on it.
		api<Mandate[]>(`/municipalities/${nif}/mandates`).catch(() => [] as Mandate[])
	]).then(([municipalities, legalForms,
	          score, suppliers, rivals, contracts, cells, stats, mandates]) => ({
		current: municipalities.find((m) => m.nif === nif) ?? null,
		municipalities, score, suppliers, rivals, contracts, cells, stats, mandates, legalForms
	}));
}

/** What `Municipio.svelte` renders: the window plus everything `rest` resolved to. */
export type Loaded = Awaited<ReturnType<typeof fetchAll>> & {
	nif: string; yearFrom?: number; yearTo?: number; dateFrom?: string; dateTo?: string;
};
