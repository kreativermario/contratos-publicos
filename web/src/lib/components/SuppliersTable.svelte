<script lang="ts">
	import { untrack } from 'svelte';
	import { api, type Supplier } from '$lib/api';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import { dateShort, eur, num, pct } from '$lib/format';
	import { L, t } from '$lib/messages';

	let { nif, initial = [], yearFrom, yearTo, forms = [] }: {
		nif: string | null;
		initial?: Supplier[];
		yearFrom?: number;
		yearTo?: number;
		/** legal forms the API will match, served from /config */
		forms?: string[];
	} = $props();

	const PAGE = 50;

	// Only columns the API is willing to sort on. Anything else would sort the
	// page the reader happens to be holding, which looks the same and lies.
	const COLS = [
		{ key: 'total', label: t('tbl.totalReceived'), align: 'r' },
		{ key: 'contracts', label: t('tbl.contracts'), align: 'r' },
		{ key: 'ad_pct', label: t('tbl.noTender'), align: 'r' },
		{ key: 'last_win', label: t('tbl.lastContract'), align: 'r' }
	] as const;

	let query = $state('');
	let formPick = $state('');
	let sort = $state<string>('total');
	let desc = $state(true);

	let rows = $state<Supplier[]>(untrack(() => initial));
	let offset = $state(untrack(() => initial.length));
	let done = $state(untrack(() => initial.length < PAGE));
	let busy = $state(false);
	let failed = $state(false);

	// The loader hands a fresh first page whenever the município or the year
	// window changes; without this the table keeps paging the previous one.
	$effect(() => {
		const next = initial;
		rows = next;
		offset = next.length;
		done = next.length < PAGE;
		sort = 'total';
		desc = true;
	});

	const filtered = $derived(Boolean(query.trim() || formPick));

	function params(from: number) {
		return {
			q: query.trim() || undefined, form: formPick || undefined, sort, desc,
			year_from: yearFrom, year_to: yearTo,
			limit: PAGE, offset: from
		};
	}

	async function fetchPage(from: number, replace: boolean) {
		if (!nif || busy) return;
		busy = true;
		failed = false;
		try {
			const page = await api<Supplier[]>(`/municipalities/${nif}/suppliers`, params(from));
			if (replace) {
				rows = page;
			} else {
				const seen = new Set(rows.map((r) => r.nif ?? r.name));
				rows = [...rows, ...page.filter((r) => !seen.has(r.nif ?? r.name))];
			}
			offset = from + page.length;
			done = page.length < PAGE;
		} catch {
			failed = true;
			done = true;
		} finally {
			busy = false;
		}
	}

	function sortBy(key: string) {
		if (sort === key) desc = !desc;
		else {
			sort = key;
			// Money and counts start big; a date starts recent. Both are the
			// interesting end of their own column.
			desc = true;
		}
	}

	// Refetch from the top on any change, debounced so typing is not a request
	// per keystroke.
	let timer: ReturnType<typeof setTimeout> | undefined;
	let first = true;
	$effect(() => {
		const key = [query.trim(), formPick, sort, String(desc)].join(' ');
		if (first) {
			first = false;
			return;
		}
		clearTimeout(timer);
		timer = setTimeout(() => {
			done = false;
			fetchPage(0, true);
		}, 250);
		return () => clearTimeout(timer);
	});

	const arrow = (key: string) => (sort !== key ? '' : desc ? '▾' : '▴');
</script>

<div class="filters">
	<label class="grow">
		<span class="eyebrow">{t('tbl.searchCompany')}</span>
		<input type="search" bind:value={query} placeholder={t('tbl.searchCompanyPlaceholder')} />
	</label>
	{#if forms.length}
		<label>
			<span class="eyebrow">{t('tbl.companyType')}</span>
			<select bind:value={formPick}>
				<option value="">{t('common.all')}</option>
				{#each forms as f (f)}<option value={f}>{f}</option>{/each}
			</select>
		</label>
	{/if}
	{#if filtered}
		<button class="clear lift" onclick={() => { query = ''; formPick = ''; }}>{t('common.clear')}</button>
	{/if}
</div>

<div class="msort">
	<label>
		<span class="eyebrow">{t('common.sortBy')}</span>
		<select bind:value={sort}>
			{#each COLS as c (c.key)}<option value={c.key}>{c.label}</option>{/each}
		</select>
	</label>
	<button type="button" onclick={() => (desc = !desc)}
		aria-label={desc ? t('common.sortDesc') : t('common.sortAsc')}>
		{desc ? '▾' : '▴'}
	</button>
</div>

<p class="hint" aria-live="polite">
	{#if failed}{t('tbl.searchFailed')}
	{:else if !rows.length && !busy}{t('tbl.noCompanies')}
	{:else}
		<span class="num">{num(rows.length)}</span>
		{rows.length === 1 ? t('common.company') : t('common.companies')}{done ? '' : ` ${t('tbl.companiesSoFar')}`}.
		{t('tbl.companiesHint')}
	{/if}
</p>

<div class="card table-wrap" aria-busy={busy}>
	<table class="stack">
		<thead>
			<tr>
				<th>{t('tbl.company')}</th>
				<th>{t('tbl.sector')}</th>
				<th>{t('tbl.type')}</th>
				{#each COLS as c (c.key)}
					<th class={c.align} aria-sort={sort === c.key ? (desc ? 'descending' : 'ascending') : 'none'}>
						<button type="button" onclick={() => sortBy(c.key)}>
							{c.label}<span class="arrow" aria-hidden="true">{arrow(c.key)}</span>
						</button>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each rows as s (s.nif ?? s.name)}
				<tr>
					<td class="firm" data-label={t('tbl.company')}>
						{#if s.nif}
							<a href={L(`/empresa/${s.nif}`)}>{s.name}</a>
						{:else}
							<!-- No NIF means no company page: the record does not publish one
							     for a natural person, and a name alone cannot be resolved to
							     one firm. Its contracts here are still reachable. -->
							<a href={L(`/municipio/${nif}?tab=contratos&supplier=${encodeURIComponent(s.name)}`)}
								title={t('tbl.noNifTitle')}>{s.name}</a>
							<span class="nonif">{t('tbl.noNif')}</span>
						{/if}
						{#if s.newcomer}<span class="tag">{t('tbl.newCompany')}</span>{/if}
					</td>
					<td class="sector" data-label={t('tbl.sector')}>{s.sector}</td>
					<td class="sector" data-label={t('tbl.type')}>{s.legal_form ?? t('common.na')}</td>
					<td class="r num money" data-label={t('tbl.totalReceived')}>{eur(s.total)}</td>
					<td class="r num" data-label={t('tbl.contracts')}>{num(s.contracts)}</td>
					<td class="r num" data-label={t('tbl.noTender')}>{pct(s.ad_pct)}</td>
					<td class="r num date" data-label={t('tbl.lastContract')}>{dateShort(s.last_win)}</td>
				</tr>
			{/each}
			{#if busy}
				{#each [0, 1, 2, 3, 4] as i (i)}
					<tr class="ghost" aria-hidden="true">
						<td><Skeleton w="24ch" h=".85rem" /></td>
						<td><Skeleton w="12ch" h=".85rem" /></td>
						<td><Skeleton w="10ch" h=".85rem" /></td>
						<td class="r"><span class="right"><Skeleton w="5rem" h=".85rem" /></span></td>
						<td class="r"><span class="right"><Skeleton w="2.2rem" h=".85rem" /></span></td>
						<td class="r"><span class="right"><Skeleton w="3rem" h=".85rem" /></span></td>
						<td class="r"><span class="right"><Skeleton w="5.5rem" h=".85rem" /></span></td>
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>

<div class="more">
	{#if !done}
		<button class="lift" onclick={() => fetchPage(offset, false)} disabled={busy}>
			{busy ? t('common.loading') : t('common.loadMore')}
		</button>
	{:else if rows.length}
		<p class="hint">{t('common.endOfList')}</p>
	{/if}
</div>

<style>
	.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: .75rem; margin-bottom: .75rem; }
	.filters label { display: flex; flex-direction: column; gap: .2rem; }
	.filters .grow { flex: 1 1 18rem; }
	.filters input, .filters select {
		/* 1rem, not .9: below 16px iOS Safari zooms the page on focus. */
		font: inherit; font-size: 1rem; font-weight: 600; color: var(--ink);
		background: var(--paper-2); border: 2px solid var(--ink); border-radius: var(--radius);
		padding: .38rem .7rem; max-width: 100%;
		/* one height for both: a select is sized by its own box model and an
		   input by its font, so left alone they never line up */
		height: 2.6rem;
	}
	.filters input { width: 100%; }
	@media (max-width: 560px) {
		.filters label { flex: 1 1 100%; min-width: 0; }
		.filters select { width: 100%; }
	}
	.clear { border: 2px solid var(--ink); border-radius: var(--radius); background: var(--ink);
		color: var(--paper); font-weight: 700; font-size: .85rem; padding: .45rem .9rem; cursor: pointer; }
	.clear:hover { background: var(--sangria); }

	.hint { margin: 0 0 .6rem; font-size: .8rem; color: var(--ink-faint); }

	/* Below the stacking breakpoint the whole thead is hidden, and the sort
	   controls live inside it. Server-side sorting would otherwise be locked to
	   its default on every phone, which is what the copy promised was not true. */
	.msort { display: none; }
	@media (max-width: 820px) {
		.msort { display: flex; align-items: flex-end; gap: .5rem; margin-bottom: .75rem; }
		.msort label { display: flex; flex-direction: column; gap: .2rem; flex: 1 1 auto; min-width: 0; }
		/* a raw OS select at 13px among poster-styled controls read as a bug, and
		   under 16px iOS zooms the page on focus, which is what this round was
		   supposed to stop */
		.msort select {
			width: 100%; font: inherit; font-size: 1rem; font-weight: 600;
			color: var(--ink); background: var(--paper-2);
			border: 2px solid var(--ink); border-radius: var(--radius);
			padding: .38rem .7rem; min-height: 2.75rem;
		}
		.msort button {
			flex: none; cursor: pointer; font-weight: 800; font-size: 1rem;
			min-width: 3rem; min-height: 2.75rem; padding: 0 .75rem;
			color: var(--ink); background: var(--paper-2);
			border: 2px solid var(--ink); border-radius: var(--radius);
		}
	}


	.table-wrap { overflow-x: auto; }
	/* A sticky thead inside `overflow-x: auto` sticks to the scroll container,
	   not to the viewport, and lands in the middle of its own table. Dropping the
	   container's overflow lets it stick properly, but only where the table
	   actually fits: at 821px it does not, and the rows spilled past the card and
	   scrolled the whole document sideways. Measured, these tables need ~1065px,
	   so 1140 is the first width where the card can stop scrolling.

	   The offset clears the nav *and* the tab bar; at the nav's 71px alone the
	   header stuck underneath the bar and was never visible. */
	@media (min-width: 1140px) {
		.table-wrap { overflow: visible; }
		thead th {
			position: sticky; top: calc(4rem + 7px + 3.5rem);
			background: var(--paper-2); z-index: 11;
		}
	}
	table { width: 100%; border-collapse: collapse; font-size: .87rem; }
	thead th { text-align: left; font-size: .7rem; text-transform: uppercase; letter-spacing: .1em;
		color: var(--ink-faint); padding: .8rem .9rem; border-bottom: 2px solid var(--ink); white-space: nowrap; }
	thead th.r { text-align: right; }
	/* the whole header cell is the sort control, so the target matches the label */
	thead th button {
		font: inherit; color: inherit; background: none; border: 0; padding: 0; cursor: pointer;
		text-transform: inherit; letter-spacing: inherit;
	}
	thead th button:hover { color: var(--sangria); }
	.arrow { display: inline-block; width: .9em; text-align: left; color: var(--sangria); }
	td { padding: .75rem .9rem; border-bottom: 1px solid var(--rule); vertical-align: top; }
	tbody tr:last-child td { border-bottom: 0; }
	tbody tr:hover { background: #fffdf3; }
	.r { text-align: right; }
	.money { font-weight: 700; }
	.firm { font-weight: 700; overflow-wrap: anywhere; }
	.firm a { color: var(--ink); text-decoration-color: var(--azulejo); text-underline-offset: 2px; }
	.firm a:hover { color: var(--sangria); }
	.sector, .date { color: var(--ink-soft); }
	.nonif {
		display: inline-block; margin-left: .4rem; font-size: .64rem; font-weight: 700;
		letter-spacing: .04em; text-transform: uppercase; color: var(--ink-faint);
	}
	.tag {
		display: inline-block; margin-left: .4rem; font-size: .66rem; font-weight: 800;
		text-transform: uppercase; letter-spacing: .06em; padding: .08rem .4rem;
		border: 1.5px solid var(--sev-warn, #a06a00); border-radius: 99px; color: var(--sev-warn, #a06a00);
	}
	@media (min-width: 821px) { .money, .date, .sector { white-space: nowrap; } }

	.ghost td { vertical-align: middle; }
	.right { display: flex; justify-content: flex-end; }

	.more { display: flex; flex-direction: column; align-items: center; gap: .4rem; padding: 1.25rem 0 .25rem; }
	.more button {
		font: inherit; font-weight: 700; font-size: .88rem; cursor: pointer;
		color: var(--ink); background: var(--paper-2); border: 2px solid var(--ink);
		border-radius: var(--radius); box-shadow: var(--shadow-hard); padding: .5rem 1.1rem;
	}
	.more button:hover:not(:disabled) { background: var(--amarelo); }
	.more button:disabled { opacity: .6; cursor: default; box-shadow: none; }
	.more .hint { margin: 0; }
</style>
