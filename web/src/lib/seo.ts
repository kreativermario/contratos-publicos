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
