import { api, type Company, type ContractRow, type SupplierDetail } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch: _f }) => {
	const nif = params.nif;

	// Two independent sides of the same firm: what it won here, and what the
	// commercial register says about it. The register is often silent, and that
	// must not take the contracts down with it.
	const [supplier, contracts, company] = await Promise.all([
		api<SupplierDetail>(`/suppliers/${nif}`),
		api<ContractRow[]>(`/suppliers/${nif}/contracts`, { limit: 50 }),
		api<Company>(`/companies/${nif}`).catch(() => null)
	]);

	return { nif, supplier, contracts, company };
};
