import { redirect } from '@sveltejs/kit';
import { api, type Municipality } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url, params, fetch: _f }) => {
	// `/?nif=X` was the old address for a município. Keep it working: links to it
	// are already out there, and a dead link is a worse outcome than a redirect.
	const legacy = url.searchParams.get('nif');
	if (legacy) {
		const rest = new URLSearchParams(url.searchParams);
		rest.delete('nif');
		const qs = rest.toString();
		// `page` is not available inside a load, so the language comes off the
		// route parameter directly. Without it, /en/?nif=X redirected out of English.
		const base = params.lang ? `/${params.lang}` : '';
		redirect(308, `${base}/municipio/${encodeURIComponent(legacy)}${qs ? `?${qs}` : ''}`);
	}

	// The landing only needs the list. Everything heavy belongs to a município.
	return { municipalities: await api<Municipality[]>('/municipalities') };
};
