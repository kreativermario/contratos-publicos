/**
 * Party colours, as Portuguese polling graphics use them.
 *
 * These are conventions, not a designed palette: a reader who follows an
 * election night already knows PS is rose and PSD is orange, and inventing
 * different hues would cost more in recognition than it could ever gain in
 * harmony. They are deliberately exempt from the project's chart palette, which
 * exists for data series that carry no prior meaning.
 *
 * Each is darkened enough to hold up on the cream ground; the pale originals
 * (CDS sky blue in particular) fail badly on #fff5d8.
 */
const COLOURS: Record<string, string> = {
	PS: '#e5177f',
	'PPD/PSD': '#c25f00',   // darkened from the poll-graphic orange: the original is 2.98:1 on cream
	'CDS-PP': '#0079c2',
	PCP: '#c8102e',
	'PCP-PEV': '#c8102e',
	CDU: '#c8102e',
	PEV: '#2e7d32',
	BE: '#8c0d2b',
	IL: '#00849e',
	CH: '#1b2a6b',
	PAN: '#0b6b5e',
	L: '#0f8f7e',
	MPT: '#3f7d20',
	PPM: '#6b4a9c',
	/** Independent candidacies and citizens' groups: no party, no party colour. */
	I: '#6b4a44'
};

const OTHER = '#8a7a6d';

/**
 * A coalition is drawn in the colour of the party that leads it.
 *
 * The acronyms join with a dot: "PPD/PSD.CDS-PP.IL" is PSD-led. Splitting on
 * the dot and taking the head is how the results themselves are ordered, so
 * this follows the source rather than imposing a ranking of our own.
 */
export const partyHead = (acronym: string): string =>
	(acronym ?? '').split('.')[0].trim().toUpperCase();

export function partyColour(acronym: string): string {
	if (!acronym) return OTHER;
	return COLOURS[partyHead(acronym)] ?? COLOURS[acronym.trim().toUpperCase()] ?? OTHER;
}

/** Independent lists get their name spelled out; a bare "I" means nothing. */
export const partyLabel = (acronym: string): string =>
	acronym === 'I' ? 'Independente' : acronym;
