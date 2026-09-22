import { locale, t } from '$lib/messages';

// Both languages format money the European way (EUR, comma decimals in pt-PT,
// point decimals in en-GB). The locale follows the page, not the browser: a
// reader on /en gets one consistent set of figures.

export const eur = (n: number | null | undefined, digits = 0) =>
	new Intl.NumberFormat(locale(), {
		style: 'currency', currency: 'EUR',
		minimumFractionDigits: digits, maximumFractionDigits: digits
	}).format(n ?? 0);

/**
 * 30 949 329 € is unreadable in a tile; 30,9 M € is not.
 *
 * Returned split because Bowlby One carries no € glyph: set as one string the
 * symbol drops to the fallback face and lands beside the number looking pasted
 * on. The tile sets the amount in the display face and the unit in Archivo.
 */
export function eurShortParts(n: number | null | undefined): [string, string] {
	const v = n ?? 0;
	const a = Math.abs(v);
	const f = (x: number, d: number) => x.toLocaleString(locale(), { maximumFractionDigits: d });
	if (a >= 1e9) return [f(v / 1e9, 1), t('unit.bn')];
	if (a >= 1e6) return [f(v / 1e6, 1), t('unit.m')];
	if (a >= 1e3) return [f(v / 1e3, 0), t('unit.k')];
	return [f(v, 0), t('unit.eur')];
}

export function eurShort(n: number | null | undefined): string {
	return eurShortParts(n).join(' ');
}

export const num = (n: number | null | undefined, digits = 0) =>
	(n ?? 0).toLocaleString(locale(), { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const pct = (n: number | null | undefined) =>
	n === null || n === undefined ? 'N/A' : `${n.toLocaleString(locale(), { maximumFractionDigits: 1 })}%`;

/**
 * The "empresa nova" sentence.
 *
 * "Estreante" was jargon nobody asked for, and the old wording ("ganhou aqui no
 * mesmo dia") described the mechanism instead of the point. What matters to a
 * reader is that the firm had no public-contract history before this, and that
 * the contract came without competition.
 */
export function novaSentence(
	firstSeen: string | null | undefined,
	days: number | null | undefined
): string {
	const date = firstSeen ?? 'N/A';
	if (days === null || days === undefined) return t('fmt.nova.unknown', { date });
	if (days <= 0) return t('fmt.nova.first', { date });
	if (days <= 31) return t('fmt.nova.weeks', { date });
	return t('fmt.nova.days', { date, days: num(days) });
}

/**
 * Strip the "Município de/da/do" prefix for display. The particle varies
 * ("Município da Amadora", "Município de Odivelas"), and a pattern that missed
 * "da" left the hero rendering the whole legal name at display size.
 */
/**
 * "a 6 € do limite de 75 000 €".
 *
 * Says how close a contract came to needing a more demanding procedure. The gap
 * is the point: 6 euros reads very differently from 3 000, and a percentage
 * would flatten exactly that difference.
 */
export function nearLimitLabel(value: number | null | undefined, limit: number): string {
	const gap = Math.max(0, limit - (value ?? 0));
	return t('fmt.nearLimit', { gap: eur(gap), limit: eur(limit) });
}

export const shortMunicipality = (name: string): string =>
	name.replace(/^(?:Munic[ií]pio|C[âa]mara\s+Municipal)\s+d[aeo]\s*/i, '').trim();

/** A date the way a Portuguese reader writes one. The record hands over ISO,
 *  which is right for sorting and wrong for reading. */
export const dateShort = (iso: string | null | undefined): string =>
	iso ? new Date(iso + 'T00:00:00').toLocaleDateString(locale()) : 'N/A';

export type Severity = 'ok' | 'warn' | 'serious' | 'critical';

/** Severity is always rendered with its written label too, never colour alone. */
export function severity(value: number | null | undefined): Severity {
	if (value === null || value === undefined) return 'ok';
	if (value >= 70) return 'critical';
	if (value >= 45) return 'serious';
	if (value >= 20) return 'warn';
	return 'ok';
}

/** The written level that always ships beside the colour. */
export const severityLabel = (sev: Severity): string => t(`sev.${sev}`);
