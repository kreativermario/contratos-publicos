<script lang="ts">
	import { keepInView } from '$lib/keepInView';
	import { untrack } from 'svelte';
	import Parties from '$lib/components/Parties.svelte';
	import { api, type ContractRow, type StatRow } from '$lib/api';
	import { eur, num, pct } from '$lib/format';
	import { L, t } from '$lib/messages';

	// A distribution table: label, count, money, share of the total.
	// Sortable on every column, and each row opens the contracts behind it.
	let { rows, title, unitLabel = '', nif = null, filter = null,
		yearFrom, yearTo }: {
		rows: StatRow[];
		title: string;
		unitLabel?: string;
		/** needed to fetch a row's contracts; without it rows are not expandable */
		nif?: string | null;
		/** which contracts query a row label drives */
		filter?: 'procedure' | 'sector' | 'year' | null;
		/** the page's year window; the expansion has to read the same period as
		 *  the totals above it, or the two disagree on screen */
		yearFrom?: number;
		yearTo?: number;
	} = $props();

	// Quota is total divided by a constant, so it sorts identically to total.
	// It still gets its own key: a sortable column that silently does nothing
	// when clicked is worse than one that is not sortable at all.
	type Key = 'label' | 'contracts' | 'total' | 'share';
	// A year table sorted by value is not a year table: it read 2025, 2024,
	// 2023, 2020, 2026, 2017… and destroyed the only ordering that matters.
	// untrack: the prop is fixed per instance, and this is only the default the
	// reader then changes by clicking a header
	let sortKey = $state<Key>(untrack(() => (filter === 'year' ? 'label' : 'total')));
	let sortDesc = $state(true);

	const total = $derived(rows.reduce((s, r) => s + (r.total ?? 0), 0));
	const expandable = $derived(Boolean(nif && filter));

	const sorted = $derived([...rows].sort((a, b) => {
		const dir = sortDesc ? -1 : 1;
		if (sortKey === 'label') {
			return dir * String(a.label ?? '').localeCompare(String(b.label ?? ''), 'pt-PT');
		}
		const key = sortKey === 'share' ? 'total' : sortKey;
		return dir * ((a[key] ?? 0) - (b[key] ?? 0));
	}));

	function sortBy(key: Key) {
		// a fresh column starts descending, because the interesting end is the top
		if (sortKey === key) sortDesc = !sortDesc;
		else { sortKey = key; sortDesc = true; }
	}

	const ariaSort = (key: Key) =>
		sortKey !== key ? 'none' : sortDesc ? 'descending' : 'ascending';

	// How many contracts a row loads at once. A row can claim 569 contratos, so
	// this has to be visible rather than a silent truncation.
	const PAGE = 25;

	let open = $state<string | null>(null);
	let openRows = $state<ContractRow[]>([]);
	let openBusy = $state(false);
	// Tracked apart from "no rows": a failed request was rendering as "Sem
	// contratos para mostrar aqui", which reads as a fact about the data when it
	// is really a fact about the network. A rate-limited 429 looked identical to
	// an empty row.
	let openError = $state(false);
	let openTotal = $state(0);
	const openDone = $derived(openRows.length >= openTotal);

	// Changing the year window replaces `rows`, and an expansion opened under the
	// old window kept showing its old contracts with no sign anything had moved.
	// Closing it is the honest reset: the totals above have changed too.
	let seen = untrack(() => rows);
	$effect(() => {
		if (rows === seen) return;
		seen = rows;
		open = null;
		openRows = [];
		openError = false;
	});

	async function toggle(label: string | number | null, btn?: HTMLElement) {
		if (!expandable) return;
		const key = String(label ?? '');
		if (open === key) {
			open = null;
			// Collapsing removes rows from under the reader. Harmless here, since
			// they are all below this button, but the reader may have scrolled
			// into them, and then this button is off the top of the window.
			keepInView(btn);
			return;
		}
		// Only one row is open at a time, so opening this one closes the other.
		// If that one was ABOVE this button, its rows vanish and everything below
		// slides up: the row just clicked can end up above the top of the window,
		// which reads as the page having jumped somewhere at random.
		open = key;
		openRows = [];
		openError = false;
		openTotal = rows.find((r) => String(r.label ?? '') === key)?.contracts ?? 0;
		await keepInView(btn);
		await loadMore(key);
	}

	async function loadMore(key: string) {
		openBusy = true;
		try {
			const next = await api<ContractRow[]>(`/municipalities/${nif}/contracts`, {
				[filter as string]: key,
				year_from: yearFrom, year_to: yearTo,
				limit: PAGE, offset: openRows.length
			});
			openRows = [...openRows, ...next];
			openError = false;
		} catch {
			openError = true;
		} finally {
			openBusy = false;
			// Nothing scrolls here on purpose. The new rows are appended ABOVE this
			// button, so they appear exactly where the reader was already looking
			// and the browser holds the offset by itself. Following the button
			// instead pulled the page down past every row it had just added, which
			// landed the reader at the bottom of a list they had not read yet and
			// made an expand look like a navigation. On a phone, where the stacked
			// rows are tall, that was most of a screen per click.
		}
	}
</script>

<div class="wrapper card">
	<table class="stack">
		<caption class="eyebrow">{title}</caption>
		<thead>
			<tr>
				<th scope="col" aria-sort={ariaSort('label')}>
					<button class:on={sortKey === 'label'}
						onclick={() => sortBy('label')}>{unitLabel}<span class="caret">{sortKey === 'label' ? (sortDesc ? '▾' : '▴') : ''}</span></button>
				</th>
				<th scope="col" class="r" aria-sort={ariaSort('contracts')}>
					<button class:on={sortKey === 'contracts'}
						onclick={() => sortBy('contracts')}>{t('tbl.count')}<span class="caret">{sortKey === 'contracts' ? (sortDesc ? '▾' : '▴') : ''}</span></button>
				</th>
				<th scope="col" class="r" aria-sort={ariaSort('total')}>
					<button class:on={sortKey === 'total'}
						onclick={() => sortBy('total')}>{t('tbl.value')}<span class="caret">{sortKey === 'total' ? (sortDesc ? '▾' : '▴') : ''}</span></button>
				</th>
				<th scope="col" class="r" aria-sort={ariaSort('share')}>
					<button class:on={sortKey === 'share'}
						onclick={() => sortBy('share')}>{t('tbl.share')}<span class="caret">{sortKey === 'share' ? (sortDesc ? '▾' : '▴') : ''}</span></button>
				</th>
			</tr>
		</thead>
		<tbody>
			{#each sorted as r (String(r.label))}
				{@const share = total ? (100 * (r.total ?? 0)) / total : 0}
				{@const key = String(r.label ?? '')}
				<tr class:expandable class:open={open === key}>
					<th scope="row" data-label={unitLabel}>
						{#if expandable}
							<button class="row-open" aria-expanded={open === key} onclick={(e) => toggle(r.label, e.currentTarget)}>
								<span class="twist" aria-hidden="true">{open === key ? '▾' : '▸'}</span>
								{r.label ?? t('common.na')}
							</button>
						{:else}{r.label ?? t('common.na')}{/if}
					</th>
					<td class="r num" data-label={t('tbl.countLabel')}>{num(r.contracts)}</td>
					<td class="r num money" data-label={t('tbl.value')}>{eur(r.total)}</td>
					<td class="r share" data-label={t('tbl.share')}>
						<span class="bar" style:width="{share}%"></span>
						<span class="num">{pct(share)}</span>
					</td>
				</tr>
				{#if open === key}
					<tr class="detail">
						<td colspan="4" class="wide" data-label={t('tbl.contracts')}>
							{#if openBusy}
								<ul class="ghost" aria-hidden="true">
									{#each [0, 1, 2, 3] as i (i)}<li><span class="g wide"></span><span class="g short"></span></li>{/each}
								</ul>
								<p class="sr">{t('tbl.loadingContracts')}</p>
							{:else if openRows.length}
								<ul class="mini">
									{#each openRows as c (c.id)}
										<li>
											<a class="obj" href={L(`/contrato/${c.id}`)}>{c.object ?? t('common.noDescription')}</a>
											<span class="who"><Parties parties={c.parties} names={c.suppliers} /></span>
											<span class="val num">{eur(c.value)}</span>
										</li>
									{/each}
								</ul>
								<p class="more">
									<span>{t('tbl.showingOf', { shown: num(openRows.length), total: num(openTotal) })}</span>
									{#if !openDone}
										<button type="button" onclick={() => loadMore(key)}>{t('tbl.showMoreN', { n: num(Math.min(PAGE, openTotal - openRows.length)) })}</button>
									{/if}
								</p>
							{:else if openError}
								<p class="none">
									{t('tbl.loadFailed')}
									<button type="button" onclick={() => loadMore(key)}>{t('common.retry')}</button>
								</p>
							{:else}
								<p class="none">{t('tbl.nothingHere')}</p>
							{/if}
						</td>
					</tr>
				{/if}
			{/each}
		</tbody>
	</table>
</div>

<style>
	.more { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem .8rem;
		margin: .6rem 0 0; font-size: .82rem; color: var(--ink-soft); font-weight: 600; }
	.more button, .none button {
		font: inherit; font-size: .8rem; font-weight: 700; cursor: pointer;
		padding: .25rem .65rem; border: 2px solid var(--ink); border-radius: 999px;
		background: var(--paper); color: var(--ink);
	}
	.more button:hover, .none button:hover { background: var(--amarelo); }

	.wrapper { overflow-x: auto; }
	table { width: 100%; border-collapse: collapse; font-size: .87rem; }
	caption { text-align: left; padding: 1.1rem .9rem .7rem; }
	th, td { padding: .6rem .9rem; border-bottom: 1px solid var(--rule); }
	thead th { text-align: left; font-size: .7rem; text-transform: uppercase; letter-spacing: .1em;
		color: var(--ink-faint); border-bottom: 2px solid var(--ink); white-space: nowrap; padding: 0; }
	thead th button {
		width: 100%; background: none; border: 0; cursor: pointer; font: inherit;
		color: inherit; text-transform: inherit; letter-spacing: inherit;
		padding: 1rem .9rem .8rem; text-align: inherit; display: flex; gap: .35rem;
		align-items: baseline; line-height: 1.25;
	}
	thead th.r button { justify-content: flex-end; }
	thead th button:hover { color: var(--ink); background: var(--paper-3); }
	thead th button.on { color: var(--ink); }
	.caret { font-size: .8em; min-width: .6em; }
	tbody th { text-align: left; font-weight: 600; }
	tbody tr:last-child th, tbody tr:last-child td { border-bottom: 0; }
	tbody tr:hover { background: #fffdf3; }
	.r { text-align: right; }
	.money { font-weight: 600; }
	.share { position: relative; min-width: 8rem; white-space: nowrap; }
	.bar { position: absolute; left: .4rem; top: 50%; transform: translateY(-50%);
		height: 9px; background: var(--azulejo); opacity: .22; border-radius: 99px; }
	.share .num { position: relative; }

	.row-open { min-height: 2.75rem; background: none; border: 0; padding: 0; font: inherit; color: inherit;
		font-weight: 600; cursor: pointer; display: flex; align-items: baseline; gap: .45rem;
		text-align: left; }
	.row-open:hover { color: var(--sangria); }
	.twist { color: var(--ink-faint); font-size: .8em; }
	tr.open { background: var(--paper-3); }
	tr.detail td { background: #fffdf6; padding: .4rem .9rem .8rem 2rem; }
	.mini { list-style: none; margin: 0; padding: 0; display: grid; gap: .3rem; }
	.mini li { display: grid; grid-template-columns: 1fr auto auto; gap: .9rem;
		align-items: baseline; font-size: .82rem; padding: .25rem 0;
		border-bottom: 1px dotted var(--rule); }
	.mini li:last-child { border-bottom: 0; }
	.obj { color: var(--ink); }
	.mini .obj { font-weight: 600; }
	.who { color: var(--ink-soft); white-space: nowrap; max-width: 22ch;
		overflow: hidden; text-overflow: ellipsis; }
	.val { font-weight: 700; white-space: nowrap; }
	.none { margin: .3rem 0; font-size: .82rem; color: var(--ink-faint); }

	/* a skeleton, so an expanding row does not snap open empty then reflow */
	.ghost { list-style: none; margin: 0; padding: 0; display: grid; gap: .55rem; }
	.ghost li { display: grid; grid-template-columns: 1fr 8rem; gap: .9rem; }
	.g { display: block; height: .82rem; border-radius: 99px; background: var(--paper-3);
		background-image: linear-gradient(90deg, transparent 0%, rgba(255,255,255,.75) 50%, transparent 100%);
		background-size: 200% 100%; animation: sweep 1.4s linear infinite; }
	.g.short { justify-self: end; width: 100%; }
	@keyframes sweep { from { background-position: 200% 0; } to { background-position: -200% 0; } }
	@media (prefers-reduced-motion: reduce) { .g { animation: none; } }

	.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }

	@media (max-width: 820px) {
		/* absolutely positioned, so in a stacked row it sat under the label the
		   ::before draws and "QUOTA" read as a selected pill */
		.bar { display: none; }
		.mini li { grid-template-columns: 1fr; gap: .1rem; }
		.who, .val { white-space: normal; max-width: none; }
		tr.detail td { padding-left: .9rem; }
	}
</style>
