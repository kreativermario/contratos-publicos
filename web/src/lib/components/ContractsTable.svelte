<script lang="ts">
	import { untrack } from 'svelte';
	import { api, type ContractRow } from '$lib/api';
	import Flags from '$lib/components/Flags.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import { dateShort, eur, num } from '$lib/format';
	import { L, t } from '$lib/messages';

	let { nif, initial = [], years = [], procedures = [], sectors = [], forms = [],
		preset = {} }: {
		nif: string | null;
		initial?: ContractRow[];
		years?: number[];
		procedures?: string[];
		sectors?: string[];
		/** legal forms the API will match, served from /config */
		forms?: string[];
		/** filters arriving from elsewhere, e.g. a click on an overview bar */
		preset?: { sector?: string; procedure?: string; supplier?: string };
	} = $props();

	// Only columns the API is willing to order on. Sorting the page the reader
	// happens to be holding would look identical and be wrong.
	const SORTABLE: Record<string, string> = {
		object: t('tbl.object'),
		procedure: t('tbl.procedure'),
		n_bidders: t('tbl.bidders'),
		value: t('tbl.value'),
		signed_date: t('tbl.date')
	};

	const PAGE = 40;
	// Auto-loading forever puts the footer permanently out of reach, so after
	// this many automatic pages the reader has to ask for the next one.
	const AUTO_PAGES = 5;

	// A supplier arriving from elsewhere goes into the search box, which is what
	// the API filters on anyway, so the reader can see and clear it.
	let query = $state(untrack(() => preset.supplier ?? ''));
	let yearPick = $state('');
	let procPick = $state(untrack(() => preset.procedure ?? ''));
	let sectorPick = $state(untrack(() => preset.sector ?? ''));
	let formPick = $state('');
	let sort = $state('value');
	let desc = $state(true);

	// `initial` is the loader's first page. Captured on purpose (untrack says so
	// rather than leaving a warning), then re-synced below.
	let rows = $state<ContractRow[]>(untrack(() => initial));
	let offset = $state(untrack(() => initial.length));
	let done = $state(untrack(() => initial.length < PAGE));
	let busy = $state(false);
	let failed = $state(false);
	let autoPages = $state(0);

	// The loader hands over a different first page whenever the municipality or
	// the year window changes. Without this the table kept paging from the old
	// one, showing contracts from a period the rest of the page had left behind.
	$effect(() => {
		const next = initial;
		rows = next;
		offset = next.length;
		done = next.length < PAGE;
		autoPages = 0;
	});

	const filtered = $derived(Boolean(query.trim() || yearPick || procPick || sectorPick || formPick));

	// A procedure arriving from a bar click is spelled as the grouping spelled
	// it, which is not always one of the facets; without this the select renders
	// blank and the reader cannot see or clear the filter that is applied.
	const procedureOptions = $derived(
		procPick && !procedures.includes(procPick) ? [procPick, ...procedures] : procedures
	);
	const sectorOptions = $derived(
		sectorPick && !sectors.includes(sectorPick) ? [sectorPick, ...sectors] : sectors
	);
	const canAuto = $derived(autoPages < AUTO_PAGES);

	function params(from: number) {
		return {
			q: query.trim() || undefined,
			year: yearPick || undefined,
			procedure: procPick || undefined,
			sector: sectorPick || undefined,
			form: formPick || undefined,
			sort,
			desc,
			limit: PAGE,
			offset: from
		};
	}

	async function fetchPage(from: number, replace: boolean) {
		if (!nif || busy) return;
		busy = true;
		failed = false;
		try {
			const page = await api<ContractRow[]>(`/municipalities/${nif}/contracts`, params(from));
			if (replace) {
				rows = page;
			} else {
				// offset paging can repeat a row when values tie; key on id
				const seen = new Set(rows.map((r) => r.id));
				rows = [...rows, ...page.filter((r) => !seen.has(r.id))];
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

	function loadMore() {
		if (done || busy) return;
		autoPages += 1;
		fetchPage(offset, false);
	}

	function clearFilters() {
		query = '';
		yearPick = '';
		procPick = '';
		sectorPick = '';
		formPick = '';
	}

	function sortBy(key: string) {
		if (sort === key) desc = !desc;
		else {
			sort = key;
			// Money, counts and dates all start at the interesting end.
			desc = true;
		}
	}

	const arrow = (key: string) => (sort !== key ? '' : desc ? '▾' : '▴');

	// Refetch from the top whenever a filter changes, debounced so typing does
	// not fire a request per keystroke.
	let timer: ReturnType<typeof setTimeout> | undefined;
	// The guard exists to suppress the fetch on mount, because the loader already
	// supplied the first page. But when a filter arrives in the URL, that loader
	// page is the *unfiltered* one, so skipping the first run left the controls
	// showing a filter the rows did not have. Arriving with a preset means the
	// first run is the one that matters.
	let first = untrack(() => !(preset.supplier || preset.procedure || preset.sector));
	$effect(() => {
		const key = [query.trim(), yearPick, procPick, sectorPick, formPick, sort, String(desc)].join(' ');
		if (first) {
			first = false;
			return;
		}
		clearTimeout(timer);
		timer = setTimeout(() => {
			autoPages = 0;
			done = false;
			fetchPage(0, true);
		}, 250);
		return () => clearTimeout(timer);
	});

	// Seamless scrolling: a sentinel below the table pulls the next page in.
	let sentinel = $state<HTMLDivElement | undefined>();
	$effect(() => {
		const el = sentinel;
		if (!el || done) return;
		const io = new IntersectionObserver(
			(entries) => {
				if (entries.some((e) => e.isIntersecting) && canAuto) loadMore();
			},
			{ rootMargin: '600px 0px' }
		);
		io.observe(el);
		return () => io.disconnect();
	});
</script>

<div class="filters">
	<label class="grow">
		<span class="eyebrow">{t('tbl.searchObject')}</span>
		<input type="search" bind:value={query} placeholder={t('tbl.searchObjectPlaceholder')} />
	</label>
	<label>
		<span class="eyebrow">{t('tbl.year')}</span>
		<select bind:value={yearPick}>
			<option value="">{t('common.all')}</option>
			{#each years as y (y)}<option value={String(y)}>{y}</option>{/each}
		</select>
	</label>
	<label>
		<span class="eyebrow">{t('tbl.procedure')}</span>
		<select bind:value={procPick}>
			<option value="">{t('common.all')}</option>
			{#each procedures as p (p)}<option value={p}>{p}</option>{/each}
		</select>
	</label>
	{#if sectors.length}
		<label>
			<span class="eyebrow">{t('tbl.sector')}</span>
			<select bind:value={sectorPick}>
				<option value="">{t('common.all')}</option>
				{#each sectors as s (s)}<option value={s}>{s}</option>{/each}
			</select>
		</label>
	{/if}
	{#if forms.length}
		<label>
			<span class="eyebrow">{t('tbl.companyType')}</span>
			<select bind:value={formPick}>
				<option value="">{t('common.all')}</option>
				{#each forms as f (f)}<option value={f}>{f}</option>{/each}
			</select>
		</label>
	{/if}
	{#if filtered}<button class="clear lift" onclick={clearFilters}>{t('common.clear')}</button>{/if}
</div>

<div class="msort">
	<label>
		<span class="eyebrow">{t('common.sortBy')}</span>
		<select bind:value={sort}>
			{#each Object.entries(SORTABLE) as [key, label] (key)}
				<option value={key}>{label}</option>
			{/each}
		</select>
	</label>
	<button type="button" onclick={() => (desc = !desc)}
		aria-label={desc ? t('common.sortDesc') : t('common.sortAsc')}>
		{desc ? '▾' : '▴'}
	</button>
</div>

<p class="hint" aria-live="polite">
	{#if failed}{t('tbl.searchFailed')}
	{:else if !rows.length && !busy}{t('tbl.noContracts')}
	{:else}
		<span class="num">{num(rows.length)}</span>
		{rows.length === 1 ? t('common.contract') : t('common.contracts')}{done ? '' : ` ${t('tbl.companiesSoFar')}`}{t('tbl.contractsSuffix')}
	{/if}
</p>

<div class="card table-wrap" aria-busy={busy}>
	<table class="stack">
		<thead>
			<tr>
				{#each [['object', ''], ['procedure', ''], ['n_bidders', 'r'], ['value', 'r']] as [key, align], i (key)}
					{#if i === 1}<th>{t('tbl.supplier')}</th>{/if}
					<th class={align} aria-sort={sort === key ? (desc ? 'descending' : 'ascending') : 'none'}>
						<button type="button" onclick={() => sortBy(key)}>
							{SORTABLE[key]}<span class="arrow" aria-hidden="true">{arrow(key)}</span>
						</button>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each rows as c (c.id)}
				<tr>
					<td class="obj wide" data-label={t('tbl.object')}
						><a href={L(`/contrato/${c.id}`)}>{c.object ?? t('common.noDescription')}</a><span
							class="date num">{dateShort(c.signed_date)}</span><Flags flags={c.flags} /></td>
					<td data-label={t('tbl.supplier')}>{c.suppliers.join(', ') || t('common.na')}</td>
					<td data-label={t('tbl.procedure')}>
						<span class="proc" class:ad={/ajuste direto/i.test(c.procedure ?? '')}
							>{c.procedure ?? t('common.na')}</span>
					</td>
					<td class="r num" data-label={t('tbl.bidders')}>{c.n_bidders ?? t('common.na')}</td>
					<td class="r num money" data-label={t('tbl.value')}>{eur(c.value)}</td>
				</tr>
			{/each}
			{#if busy}
				{#each [0, 1, 2, 3, 4] as i (i)}
					<tr class="ghost" aria-hidden="true">
						<td class="obj wide">
							<!-- widths in ch, so the columns keep the geometry they will have -->
							<Skeleton w="32ch" h=".85rem" lines={2} gap=".3rem" last="23ch" />
							<span class="pad"><Skeleton w="9ch" h=".6rem" /></span>
						</td>
						<td><Skeleton w="20ch" h=".85rem" /></td>
						<td><Skeleton w="14ch" h="1.1rem" /></td>
						<td class="r"><span class="right"><Skeleton w="2.2rem" h=".85rem" /></span></td>
						<td class="r"><span class="right"><Skeleton w="4.5rem" h=".85rem" /></span></td>
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>

<div bind:this={sentinel} class="more">
	{#if !done}
		<button class="lift" onclick={loadMore} disabled={busy}>
			{busy ? t('common.loading') : t('common.loadMore')}
		</button>
		{#if !canAuto}
			<p class="hint">{t('tbl.loadedSoFar', { n: num(rows.length) })}</p>
		{/if}
	{:else if rows.length}
		<p class="hint">{t('common.endOfList')}</p>
	{/if}
</div>

<style>

	.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: .75rem; margin-bottom: .75rem; }
	.filters label { display: flex; flex-direction: column; gap: .2rem; }
	.filters .grow { flex: 1 1 16rem; }
	.filters input, .filters select {
		/* 1rem, not .9: below 16px iOS Safari zooms the page on focus and leaves
		   it zoomed, which turns a filter into a horizontal-scroll trap. */
		font: inherit; font-size: 1rem; font-weight: 600; color: var(--ink);
		background: var(--paper-2); border: 2px solid var(--ink); border-radius: var(--radius);
		padding: .38rem .7rem; max-width: 100%;
		/* one height for both: a select is sized by its own box model and an
		   input by its font, so left alone they never line up */
		height: 2.6rem;
	}
	.filters input { width: 100%; }
	/* A select is as wide as its widest option, and IMPIC procedure names run to
	   forty characters. max-width:100% cannot save it: the percentage resolves
	   against a label whose own width the select is deciding. */
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
		/* Stacked, the same description ran to twenty-five lines and made one row
		   most of a phone screen. The full text is one tap away on the contract
		   page. `display` has to be set here too: the desktop clamp lives behind
		   its own min-width query, so on a phone the anchor was plain inline and
		   -webkit-line-clamp had nothing to clamp. */
		.obj a {
			display: -webkit-box; -webkit-line-clamp: 4; line-clamp: 4;
			-webkit-box-orient: vertical; overflow: hidden;
		}
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
	/* the header stays put: a 7000px table whose labels scroll away after one
	   screen is a table you read eight screens of from memory */
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
	th { text-align: left; font-size: .7rem; text-transform: uppercase; letter-spacing: .1em;
		color: var(--ink-faint); padding: .8rem .9rem; border-bottom: 2px solid var(--ink); white-space: nowrap; }
	/* the whole header cell is the control, so the target matches the label */
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
	.obj a { color: var(--ink); font-weight: 600; text-decoration-color: var(--azulejo);
		text-underline-offset: 2px; }
	.obj a:hover { color: var(--sangria); }
	.date { display: block; font-size: .72rem; color: var(--ink-faint); margin-top: .2rem; }
	.money { font-weight: 700; }
	.proc { font-size: .78rem; border: 1.5px solid var(--rule); border-radius: 99px; padding: .12rem .5rem; }
	.proc.ad { border-color: var(--sev-critical); color: var(--sev-critical); font-weight: 700; }
	@media (min-width: 821px) {
		/* The object holds the longest text on the row and had the narrowest
		   column, so one GERTAL description wrapped to 25 lines and made the row
		   taller than the window. Widest column, and clamped. */
		.obj { max-width: 48ch; }
		.obj a {
			display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3;
			-webkit-box-orient: vertical; overflow: hidden;
		}
		.money, .proc { white-space: nowrap; }
	}

	/* rows keep arriving in place instead of the table snapping taller */
	.ghost td { vertical-align: middle; }
	.pad { display: block; margin-top: .3rem; }
	.right { display: flex; justify-content: flex-end; }

	.more { display: flex; flex-direction: column; align-items: center; gap: .4rem;
		padding: 1.25rem 0 .25rem; }
	.more button {
		font: inherit; font-weight: 700; font-size: .88rem; cursor: pointer;
		color: var(--ink); background: var(--paper-2); border: 2px solid var(--ink);
		border-radius: var(--radius); box-shadow: var(--shadow-hard); padding: .5rem 1.1rem;
	}
	.more button:hover:not(:disabled) { background: var(--amarelo); }
	.more button:disabled { opacity: .6; cursor: default; box-shadow: none; }
	.more .hint { margin: 0; }
</style>
