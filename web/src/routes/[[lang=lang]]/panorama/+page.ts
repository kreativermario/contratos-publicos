import { api, type DistrictRow, type MandateMapRow, type PartyRow } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch: _f }) => {
	// Both sides of the comparison, fetched together: the page is the comparison,
	// so a half-loaded version of it would say something the data does not.
	const [parties, districts, mapRows, years] = await Promise.all([
		api<PartyRow[]>('/rankings/parties'),
		api<DistrictRow[]>('/rankings/districts'),
		// All 308, unlike everything else here, which is limited to the
		// municipalities whose contracts are loaded.
		api<MandateMapRow[]>('/rankings/map'),
		api<number[]>('/rankings/elections')
	]);
	return { parties, districts, mapRows, years };
};
