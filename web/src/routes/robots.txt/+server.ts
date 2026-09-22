import { PUBLIC_SITE_URL } from '$env/static/public';
import type { RequestHandler } from './$types';

export const prerender = true;

export const GET: RequestHandler = async () =>
	new Response(
		`# allow crawling everything by default
User-agent: *
Disallow:

Sitemap: ${PUBLIC_SITE_URL}/sitemap.xml
`,
		{ headers: { 'content-type': 'text/plain' } }
	);
