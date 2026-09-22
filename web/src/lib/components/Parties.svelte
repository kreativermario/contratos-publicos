<script lang="ts">
	/**
	 * The firms on a contract row, linked where the record gave us a NIF.
	 *
	 * A name without a NIF cannot be resolved to one company (the record spells
	 * the same firm several ways), so it renders as plain text rather than as a
	 * link that would land on the wrong page or on nothing.
	 */
	import { L, t } from '$lib/messages';

	let { parties = [], names = [], buyer = null }: {
		parties?: { name: string; nif: string | null }[];
		/** fallback for rows fetched before the API carried NIFs */
		names?: string[];
		/** the câmara, so a firm with no NIF can still open its contracts there */
		buyer?: string | null;
	} = $props();

	const hrefFor = (p: { name: string; nif: string | null }) =>
		p.nif
			? L(`/empresa/${p.nif}`)
			: buyer
				? L(`/municipio/${buyer}?tab=contratos&supplier=${encodeURIComponent(p.name)}`)
				: null;

	const list = $derived(
		parties.length ? parties : names.map((name) => ({ name, nif: null }))
	);
</script>

{#if !list.length}
	{t('common.na')}
{:else}
	{#each list as p, i (p.name)}{i ? ', ' : ''}{@const href = hrefFor(p)}{#if href}<a {href}>{p.name}</a>{:else}{p.name}{/if}{/each}
{/if}
