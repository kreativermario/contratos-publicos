import { api, type ContractDetail } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch: _f }) => {
	const contract = await api<ContractDetail>(`/contracts/${params.id}`);
	return { contract };
};
