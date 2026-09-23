import { version } from '$app/environment';
import { env } from '$env/dynamic/public';
import { maybe, t } from '$lib/messages';

// Single place that knows where the API lives. Dynamic (not static) env so one
// image works behind any hostname without a rebuild.
const BASE = env.PUBLIC_API_BASE || '/api/v1';

export async function api<T>(path: string, params: Record<string, unknown> = {}): Promise<T> {
	const qs = new URLSearchParams(
		Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '') as [string, string][]
	);
	// Responses are cached for an hour by Cache-Control, which is right for data
	// that moves nightly and wrong the moment a deploy changes the JSON shape.
	// Stamping the build in means a new bundle never reads an old bundle's cache.
	qs.set('v', version);
	const url = `${BASE}${path}?${qs}`;
	const res = await fetch(url);
	if (!res.ok) throw new Error(`${res.status} ${res.statusText} on ${path}`);
	return res.json();
}

// `unit` says what `n` counts, in the plural: contratos, empresas or anos.
// It is not always contracts, and for repeat_winners `n` is a fractional
// number of years.
export type Flag = {
	pct: number | null;
	n?: number | null;
	unit?: string | null;
	disclosed?: number | null;
};

export type SatiricalIndex = {
	score: number | null;
	/** clean | fishy | blatant. The API ships no prose; `verdict()` words it. */
	band: string;
	/** ok | warn | critical, so the words and the colour agree */
	tone: 'ok' | 'warn' | 'critical';
	units: { bifanas: number; salarios_minimos_anuais: number };
};

/** The verdict and its quip, in the page's language, from the API's band key. */
export const verdict = (band: string) => ({
	name: t(`verdict.${band}`),
	quip: t(`verdict.${band}.quip`)
});

export type Score = {
	nif: string;
	name: string | null;
	period: { from: number | null; to: number | null };
	totals: { contracts: number; value: number; suppliers: number };
	risk_index: number | null;
	/** which keys of `flags` feed the index, and which sit beside it */
	scored_flags: string[];
	context_flags: string[];
	satirical_index: SatiricalIndex;
	flags: Record<string, Flag>;
	/** disclaimer keys; the wording lives in messages.ts, in both languages */
	caveats: string[];
};

export type Supplier = {
	name: string; nif: string | null; contracts: number; total: number;
	first_win: string | null; last_win: string | null; ad_pct: number | null;
	country: string | null;
	/** dominant CPV division, in Portuguese */
	sector: string;
	/** first appearance anywhere in the record; the only proxy for company age */
	first_seen: string | null;
	debut_days: number | null;
	/** null where the loaded record starts too late to tell, never a false "old" */
	newcomer: boolean | null;
	/** read off the firm name, which by law carries the suffix */
	legal_form: string | null;
};

export type Limits = {
	ajuste_direto_servicos: number;
	ajuste_direto_obras: number;
	consulta_previa: number;
	banda_limite: number;
	dias_estreante: number;
};

export type Config = {
	default: Municipality | null;
	cache_seconds: number;
	limits: Limits | null;
	/** the legal forms a firm name can be read as; the only values the filter matches */
	legal_forms: string[];
};

export type SupplierDetail = {
	nif: string; name: string | null; contracts: number; total: number | null;
	first_win: string | null; last_win: string | null; ad_pct: number | null;
	buyers: number; sector: string;
	by_year: { label: number; contracts: number; total: number; ad_pct: number | null }[];
	by_buyer: {
		nif: string | null; name: string | null; contracts: number; total: number | null;
		/** territory, where the buyer name resolves to one unambiguously */
		dico: string | null; concelho: string | null; district: string | null;
	}[];
};

export type ContractDetail = {
	id: number; object: string | null; procedure: string | null;
	contract_types: string[];
	value: number | null; base_price: number | null;
	signed_date: string | null; pub_date: string | null; exec_days: number | null;
	cpv: string | null; cpv_desc: string | null; sector: string;
	n_bidders: number | null; framework: string | null;
	justification: string | null; ad_justification: string | null;
	centralized: boolean | null; green: boolean | null; criterion: string | null;
	buyer_nif: string | null; buyer_name: string | null;
	suppliers: { name: string; nif: string | null }[];
	bidders: { name: string; nif: string | null }[];
	locations: string[];
	link_pieces: string | null; link_announcement: string | null;
	near_limit: number | null;
};

export type StatRow = { label: string | number | null; contracts: number; total: number | null; mean?: number | null };

export type Stats = {
	headline: {
		contracts: number; total: number | null; mean: number | null; median: number | null;
		p90: number | null; largest: number | null; smallest: number | null;
		mean_exec_days: number | null; median_exec_days: number | null;
		base_total: number | null; with_base: number;
		median_discount_pct: number | null; no_discount: number;
		suppliers_to_half: number | null;
		cpv_codes: number; framework_contracts: number; zero_value: number;
	};
	by_procedure: StatRow[];
	by_year: StatRow[];
	by_sector: StatRow[];
};

export type Cae = { code: string; description: string | null; type: string | null };

/** What the registries say. No capital social or incorporation date exists in
 *  any free source, so those are deliberately absent rather than guessed. */
export type Company = {
	nif: string;
	name: string | null;
	sicae_name: string | null;
	legal_type: string | null;
	address: string | null;
	cae: Cae[];
	// year of the first act in the commercial register, which only begins in 2006
	founded_year: number | null;
	// false means the year is a bound, not a date: the firm predates the register
	founded_exact: boolean;
	legal_form: string | null;
	source: string | null;
};

/** One municipal term, with what was contracted during it. */
export type Mandate = {
	election_date: string;
	term_start: string;
	term_end: string | null;
	party: string;
	coalition: boolean;
	citizens_group: boolean;
	president: string | null;
	contracts: number;
	value: number;
	ad_pct: number | null;
};

/** One party or district, in one of the two legal eras. */
export type PartyRow = {
	party: string;
	era: 'antes' | 'depois';
	coalition: boolean;
	citizens_group: boolean;
	mandates: number;
	municipalities: number;
	contracts: number;
	value: number;
	ad_pct: number | null;
	ad_low: number | null;
	ad_median: number | null;
	ad_high: number | null;
	spread_n: number;
};

export type DistrictRow = {
	district: string;
	era: 'antes' | 'depois';
	municipalities: number;
	contracts: number;
	value: number;
	ad_pct: number | null;
	ad_low: number | null;
	ad_high: number | null;
	spread_n: number;
};

export type MandateMapRow = {
	dico: string; concelho: string; district: string | null;
	election_date: string; party: string;
	coalition: boolean; citizens_group: boolean; president: string | null;
	term_start: string | null; term_end: string | null;
	/** how long the term ran; the current one counts up to today */
	years: number | null;
	/** the buyer NIF, set only where this câmara's contracts are loaded */
	nif: string | null;
	/** null, never zero, where this câmara's contracts are not loaded */
	contracts: number | null; value: number | null; ad_pct: number | null;
};

export type Rival = {
	firm_a: string; firm_b: string;
	nif_a: string | null; nif_b: string | null;
	tenders: number;
};

/** One flag on a contract: the key names the sentence, the data fills it in. */
export type ContractFlag = { key: string; data?: Record<string, number | string> };

export type ContractRow = {
	id: number; object: string | null; procedure: string | null; value: number | null;
	signed_date: string | null; year: number | null; cpv_desc: string | null;
	n_bidders: number | null; ad_justification: string | null; suppliers: string[];
	/** the same firms with their NIFs, so a row can link to a company page */
	parties?: { name: string; nif: string | null }[];
	/**
	 * Patterns worth a second look; every one of them is legal.
	 *
	 * `key` picks the sentence out of the message bundle and `data` fills its
	 * `{placeholders}`, so the API still ships no prose while the chip can say
	 * "3 contratos, todos abaixo de 20 000 €" instead of naming a category.
	 */
	flags?: ContractFlag[];
	/** statutory ceiling this contract sits just under, if any */
	near_limit?: number | null;
	/** only set when read from a supplier's side, where the counterparty is the câmara */
	buyer_nif?: string | null;
	buyer_name?: string | null;
};

export type MapCell = {
	municipality: string; district: string | null; contracts: number; total: number | null;
};

export type Municipality = {
	nif: string; name: string | null; contracts: number; total: number | null;
	since?: string | null; latest?: string | null;
};

/**
 * Every scored signal is a share of the money, so they can be averaged. The
 * context ones are counts or ratios of a different kind and are shown beside
 * the index rather than inside it.
 *
 * The wording lives in messages.ts under `signal.<key>` and
 * `signal.<key>.blurb`, because it exists in two languages. No statistical term
 * appears in either: the reader is a resident, not an economist.
 */
export const signal = (key: string) => ({
	label: t(`signal.${key}`),
	blurb: t(`signal.${key}.blurb`)
});

/**
 * Why a signal has no value. Shown in place of the explanation, because a card
 * reading "N/A" needs the reason far more than it needs the definition. Empty
 * for a signal that is always measurable.
 */
export const unmeasurable = (key: string): string => maybe(`unmeasurable.${key}`);
