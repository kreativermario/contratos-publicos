import { api, type Config } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch: _f }) => {
	// The ceilings come from the API, not from this page. They are statutory,
	// they get amended, and an explainer quoting a different number from the one
	// the index actually used would be worse than no explainer at all.
	const cfg = await api<Config>('/config');
	return { limits: cfg.limits };
};
