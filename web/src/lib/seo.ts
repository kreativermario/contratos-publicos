/** The canonical pair for a route, in both language trees.
 *
 *  One static shell serves every route, so these cannot be baked into
 *  app.html: a canonical written there points every page at the root and folds
 *  the whole site into one URL in the index. `+layout.svelte` renders them per
 *  route instead. The query string is dropped on purpose, so ?tab= and the
 *  period pickers all canonicalise to the page itself.
 */
export function seoUrls(site: string, pathname: string): { pt: string; en: string } {
	const path = pathname.replace(/^\/en(?=\/|$)/, '').replace(/\/$/, '');
	return { pt: `${site}${path || '/'}`, en: `${site}/en${path}` };
}

/** "Município de Odivelas" as a reader says it: "Odivelas".
 *
 *  Here rather than in format.ts because format.ts reaches messages.ts, which
 *  imports `$app/state`, which does not exist under plain node. This module is
 *  the one the build scripts can import, and the short name is now part of a
 *  page's identity: it is the title, the description and the JSON-LD name.
 *  Re-exported from format.ts so callers there are unchanged.
 */
export const shortMunicipality = (name: string): string =>
	name.replace(/^(?:Munic[ií]pio|C[\u00e2a]mara\s+Municipal)\s+d[aeo]\s*/i, '').trim();
