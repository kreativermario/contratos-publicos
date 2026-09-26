import { PUBLIC_SITE_URL } from '$env/static/public';
import type { RequestHandler } from './$types';

// RFC 9116. The route name encodes the two literal dots: SvelteKit skips any
// directory starting with one, so `.well-known` has to be spelled `[x+2e]`.
// nginx would also swallow this path, hence the ^~ exception in
// default.conf.template that has to outrank the dotfile 404.
export const prerender = true;

const REPO = 'https://github.com/kreativermario/contratos-publicos';

// Expires is mandatory and a stale one makes the file non-compliant, so it is
// computed at build time rather than typed in and forgotten. A year is the
// longest the RFC recommends; any deploy renews it.
const expires = new Date(Date.now() + 365 * 864e5).toISOString().replace(/\.\d{3}Z$/, 'Z');

export const GET: RequestHandler = async () =>
	new Response(
		`Contact: ${REPO}/security/advisories/new
Policy: ${REPO}/blob/main/SECURITY.md
Canonical: ${PUBLIC_SITE_URL}/.well-known/security.txt
Preferred-Languages: pt, en
Expires: ${expires}
`,
		{ headers: { 'content-type': 'text/plain' } }
	);
