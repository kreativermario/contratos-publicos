<script lang="ts">
	import { goto, replaceState } from '$app/navigation';
	import { keepInView } from '$lib/keepInView';
	import { page } from '$app/state';
	import { api, signal, unmeasurable, verdict, type Company, type ContractRow } from '$lib/api';
	import Chart from '$lib/Chart.svelte';
	import CompanyProfile from '$lib/components/CompanyProfile.svelte';
	import ContractsTable from '$lib/components/ContractsTable.svelte';
	import Parties from '$lib/components/Parties.svelte';
	import SuppliersTable from '$lib/components/SuppliersTable.svelte';
	import { categoryNameOf, graphOption, mapOption, sectorCategories, statBarOption, topSuppliersOption } from '$lib/charts';
	import BigIndex from '$lib/components/BigIndex.svelte';
	import Flags from '$lib/components/Flags.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import MandateTimeline from '$lib/components/MandateTimeline.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import SignalCard from '$lib/components/SignalCard.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import SkeletonTable from '$lib/components/SkeletonTable.svelte';
	import StatTable from '$lib/components/StatTable.svelte';
	import echarts from '$lib/echarts';
	import { dateShort, eur, eurShort, eurShortParts, nearLimitLabel, novaSentence, num, pct, shortMunicipality } from '$lib/format';
	import { L, locale, t } from '$lib/messages';

	import { narrow } from '$lib/narrow.svelte';
	import { reveal } from '$lib/reveal';

	import { MAX_SPAN } from './+page';

	let { data } = $props();

	const TABS = [
		{ id: 'geral',        label: t('muni.tab.overview') },
		{ id: 'mapa',         label: t('muni.tab.map') },
		{ id: 'rede',         label: t('muni.tab.network') },
		{ id: 'empresas',     label: t('muni.tab.companies') },
		{ id: 'estatisticas', label: t('muni.tab.stats') },
		{ id: 'contratos',    label: t('muni.tab.contracts') }
	] as const;
	type TabId = (typeof TABS)[number]['id'];
	const isTab = (v: string | null): v is TabId => TABS.some((t) => t.id === v);

	// The tab a real navigation asks for: a deep link, or a chart click that
	// sends the reader to the contracts table with a filter already applied.
	const urlTab = $derived<TabId>(isTab(page.url.searchParams.get('tab'))
		? (page.url.searchParams.get('tab') as TabId) : 'geral');

	// And the tab the reader chose since then, which the URL cannot tell us.
	//
	// `replaceState` writes the address bar and sets `page.state`; it does NOT
	// update `page.url` (see client.js: it clones the page object and assigns
	// state, nothing else). Deriving the tab from `page.url` alone therefore
	// left every click updating the address bar while the panel never moved,
	// which looked exactly like a tab that would not load. So the reader's
	// choice lives here, and the URL stays in step only so it can be shared.
	let chosenTab = $state<TabId | null>(null);
	// A real navigation outranks it: `urlTab` only ever changes when one has
	// happened, since a shallow update leaves `page.url` alone.
	$effect(() => {
		urlTab;
		chosenTab = null;
	});
	const tab = $derived<TabId>(chosenTab ?? urlTab);

	let tabsEl = $state<HTMLElement | undefined>();

	function setTab(id: TabId) {
		const url = new URL(page.url);
		id === 'geral' ? url.searchParams.delete('tab') : url.searchParams.set('tab', id);
		// SHALLOW, not goto. `load` reads url.searchParams for the year window, so
		// SvelteKit treats the whole URL as a dependency and re-runs it on any
		// search param change: every tab switch refetched score, 120 suppliers,
		// rivals, contracts, map cells, stats, mandates, the municipality list
		// and the config, and blocked the navigation until all nine returned.
		// The tab chooses which of that already-loaded data to show; it is not an
		// input to any of it. replaceState updates page.url, `tab` derives from
		// it, and a deep link still reads the param on a real navigation.
		chosenTab = id;
		// The address bar only, so the tab can still be copied and shared. The
		// panel is already switching off `chosenTab` above.
		replaceState(url, page.state);
		// After the swap, never before it. The panels are wildly different
		// heights, so the old panel's geometry says nothing about where the tab
		// bar will be once the new one has rendered, and a tall panel replaced
		// by a short one leaves the browser clamping the reader into the middle
		// of something they did not open.
		keepInView(tabsEl);
	}

	// how many suppliers the graph draws, the single biggest lever on clutter
	let graphSize = $state(40);

	// ---- period ----------------------------------------------------------
	// 1 is deliberately absent: the single-year chips below already say it, and
	// better, by naming the year instead of counting back from the latest one.
	const YEAR_PRESETS = [2, 3, 5] as const;
	// How many individual years stay on the row. Two, not six: the row also has
	// to hold Tudo, 2 anos and Intervalo…, and with six years those wrapped to a
	// second line where the reader stopped seeing them.
	const YEAR_CHIPS = 2;
	let custom = $state(false);

	// The span offered comes from the municipality row, which is fetched without
	// a year filter. Deriving it from the filtered data instead would shrink the
	// list to the years already selected, stranding the picker.
	const availableYears = $derived.by(() => {
		const lo = data.current?.since ? new Date(data.current.since).getFullYear() : null;
		const hi = data.current?.latest ? new Date(data.current.latest).getFullYear() : null;
		if (!lo || !hi || hi < lo) return [];
		return Array.from({ length: hi - lo + 1 }, (_, i) => hi - i); // newest first
	});

	// Two out, the rest behind a toggle. Fifteen year chips filled the row and
	// pushed "Tudo" and "Intervalo…" onto a second line, where nobody looked.
	const recentYears = $derived(availableYears.slice(0, YEAR_CHIPS));
	const olderYears = $derived(availableYears.slice(YEAR_CHIPS));
	let showOlder = $state(false);

	/** The exact-date window a mandate sets. Clearing it is part of every other
	 *  window change, or a year chip would silently keep a term's dates. */
	function setDates(from?: string, to?: string) {
		const url = new URL(page.url);
		url.searchParams.delete('from');
		url.searchParams.delete('to');
		from ? url.searchParams.set('de', from) : url.searchParams.delete('de');
		to ? url.searchParams.set('ate', to) : url.searchParams.delete('ate');
		goto(`?${url.searchParams}`, { keepFocus: true, noScroll: true });
	}

	function setWindow(from?: number, to?: number) {
		const url = new URL(page.url);
		url.searchParams.delete('de');
		url.searchParams.delete('ate');
		from ? url.searchParams.set('from', String(from)) : url.searchParams.delete('from');
		to ? url.searchParams.set('to', String(to)) : url.searchParams.delete('to');
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}

	function preset(n: number) {
		const hi = availableYears[0];
		const lo = availableYears[availableYears.length - 1];
		if (hi === undefined) return;
		setWindow(Math.max(hi - n + 1, lo), hi);
	}
	const isPreset = (n: number) =>
		data.yearTo === availableYears[0] &&
		data.yearFrom === Math.max(availableYears[0] - n + 1, availableYears[availableYears.length - 1]);

	// Picking one end alone is normal, so the other end defaults to itself: a
	// half-open window would silently widen to everything.
	const setFrom = (v: string) =>
		setWindow(v ? Number(v) : undefined, data.yearTo ?? (v ? Number(v) : undefined));
	const setTo = (v: string) =>
		setWindow(data.yearFrom ?? (v ? Number(v) : undefined), v ? Number(v) : undefined);

	// The loader clamps anything wider than MAX_SPAN; say so rather than silently
	// returning a different period from the one the URL asked for.
	const spanTrimmed = $derived.by(() => {
		const f = Number(page.url.searchParams.get('from'));
		const t = Number(page.url.searchParams.get('to'));
		return Boolean(f && t && Math.abs(t - f) + 1 > MAX_SPAN);
	});

	// Who held the câmara during the period on screen. A narrowed period usually
	// sits inside one mandate, and naming it there saves scrolling to the
	// timeline to find out who was in charge of the numbers being read.
	const rulingTerms = $derived.by(() => {
		const terms = data.mandates ?? [];
		if (!terms.length) return [];
		// The window is years; mandates are dates. Compare on the year boundaries,
		// erring towards including a term that overlaps at all.
		const from = data.yearFrom ?? -Infinity;
		const to = data.yearTo ?? Infinity;
		return terms.filter((t) => {
			const start = Number(t.term_start.slice(0, 4));
			const end = t.term_end ? Number(t.term_end.slice(0, 4)) : Infinity;
			return start <= to && end >= from;
		});
	});
	// Only worth naming when the period actually narrows to one administration.
	const rulingOne = $derived(rulingTerms.length === 1 ? rulingTerms[0] : null);

	const score = $derived(data.score);
	// The verdict arrives as a band key; the words are ours, in both languages.
	const said = $derived(verdict(data.score?.satirical_index.band ?? 'clean'));
	const buyer = $derived(data.current?.name ?? score?.name ?? t('muni.fallbackName'));
	const shortName = $derived(shortMunicipality(buyer));

	// A fixed clamp() sizes every name the same and so renders them at wildly
	// different widths: MAFRA swims in the line while VILA FRANCA DE XIRA runs
	// off it. Scale by length instead, so each municipality fills roughly the
	// same measure.
	//
	// Computed here rather than in CSS because it has to be an inline style, and
	// an inline style beats `.hero.compact .title`. Getting that wrong left the
	// title full size on every tab, which is what made the header lurch when you
	// moved off the overview.
	const titleSize = $derived.by(() => {
		const overview = tab === 'geral';
		const budget = overview ? 88 : 34;          // vw to spend on the whole name
		const cap = overview ? 11 : 4.4;            // vw ceiling for a short name
		const vw = Math.min(cap, budget / Math.max(shortName.length, 5));
		return overview
			? `clamp(2rem, ${vw.toFixed(2)}vw, 7rem)`
			: `clamp(1.5rem, ${vw.toFixed(2)}vw, 2.9rem)`;
	});

	// period is the *requested* window; with no filter it is null, and the honest
	// label is then the span actually loaded, not "todos os anos disponíveis".
	const periodLabel = $derived.by(() => {
		const { from, to } = score?.period ?? { from: null, to: null };
		if (from && to) return from === to ? `${from}` : t('muni.periodFromTo', { from, to });
		if (from) return t('muni.periodSince', { from });
		if (to) return t('muni.periodUntil', { to });
		const years = (data.stats?.by_year ?? [])
			.map((r) => Number(r.label))
			.filter((y) => Number.isFinite(y));
		if (!years.length) return t('muni.periodUnknown');
		const lo = Math.min(...years), hi = Math.max(...years);
		return lo === hi ? `${lo}` : t('muni.periodFromTo', { from: lo, to: hi });
	});

	const gastos = $derived(eurShortParts(data.score?.totals.value ?? 0));
	// how many signals actually fed the index here, which is not always all of them
	const scoredKeys = $derived(data.score?.scored_flags?.length
		? data.score.scored_flags
		: Object.keys(data.score?.flags ?? {}));
	const contextKeys = $derived(data.score?.context_flags ?? []);
	// One grid. The ones outside the index keep their own tag on the card, which
	// is a quieter way of saying it than a second heading and a paragraph.
	const allKeys = $derived([...scoredKeys, ...contextKeys.filter((k) => !scoredKeys.includes(k))]);
	const counted = $derived((data.score?.scored_flags ?? [])
		.filter((k) => data.score?.flags[k]?.pct !== null && data.score?.flags[k]?.pct !== undefined).length);
	const shown = $derived(data.suppliers.slice(0, graphSize));
	// Categories come from the UNFILTERED set on purpose: derive them after
	// filtering and a sector you just switched off disappears from the legend,
	// leaving no way to switch it back on.
	const categories = $derived(sectorCategories(shown));

	// Clicking a legend entry hides that sector. The old canvas legend did this
	// for free; the HTML one has to filter the data itself.
	let hiddenSectors = $state<string[]>([]);
	function toggleSector(name: string) {
		hiddenSectors = hiddenSectors.includes(name)
			? hiddenSectors.filter((s) => s !== name)
			: [...hiddenSectors, name];
	}
	// A different municipality has different sectors, so old hides would silently
	// filter the new one.
	$effect(() => {
		data.nif;
		hiddenSectors = [];
	});

	const graphSuppliers = $derived(
		shown.filter((s) => !hiddenSectors.includes(categoryNameOf(s.sector, categories)))
	);
	const graph = $derived(score ? graphOption(buyer, graphSuppliers, categories, $narrow ? 4 : 6, $narrow) : null);

	// Firms whose debut in the whole public record is recent. Null means the
	// loaded years start too late to tell, which is not the same as "established".
	const newcomers = $derived(data.suppliers.filter((s) => s.newcomer === true));

	/**
	 * A bar is a destination for money, so clicking one goes to that destination.
	 *
	 * A supplier bar opens the firm's own page; a sector or procedure bar hands
	 * the contracts table the same filter it would have applied itself, which is
	 * the only honest "more detail" for a grouping that is not one entity.
	 */
	function pickBar(datum: any) {
		if (grouping === 'fornecedor') {
			if (datum?.nif) goto(L(`/empresa/${datum.nif}`));
			return;
		}
		const value = datum?.name;
		if (!value) return;
		const params = new URLSearchParams(page.url.searchParams);
		params.set('tab', 'contratos');
		params.set(grouping === 'sector' ? 'sector' : 'procedure', value);
		goto(`?${params}`, { noScroll: false, keepFocus: false });
	}
	const newcomerKnown = $derived(data.suppliers.some((s) => s.newcomer !== null));

	// Clicking a node opens that supplier's contracts, fetched on demand.
	let picked = $state<{ name: string; sector?: string; newcomer?: boolean | null;
		firstSeen?: string | null; debutDays?: number | null; contracts?: number;
		nif?: string | null } | null>(null);
	let pickedRows = $state<ContractRow[]>([]);
	// Newest first: someone opening a supplier wants to know what it won lately,
	// not what it won biggest. The API orders by value, so sort here; 50 rows is
	// nothing, and doing it client-side makes every column sortable for free.
	type PickKey = 'date' | 'object' | 'procedure' | 'bidders' | 'value';
	let pickedKey = $state<PickKey>('date');
	let pickedDesc = $state(true);
	function sortPicked(key: PickKey) {
		if (pickedKey === key) pickedDesc = !pickedDesc;
		else { pickedKey = key; pickedDesc = true; }
	}
	const pickedSorted = $derived.by(() => {
		const dir = pickedDesc ? -1 : 1;
		// Sorted in Portuguese whatever the page language: these are the register's
		// own strings, and pt-PT collation is what orders them correctly.
		const txt = (v: string | null | undefined) => (v ?? '').toLocaleLowerCase('pt-PT');
		return [...pickedRows].sort((a, b) => {
			switch (pickedKey) {
				case 'object': return dir * txt(a.object).localeCompare(txt(b.object), 'pt-PT');
				case 'procedure': return dir * txt(a.procedure).localeCompare(txt(b.procedure), 'pt-PT');
				case 'bidders': return dir * ((a.n_bidders ?? -1) - (b.n_bidders ?? -1));
				case 'value': return dir * ((a.value ?? 0) - (b.value ?? 0));
				default: return dir * txt(a.signed_date).localeCompare(txt(b.signed_date));
			}
		});
	});
	// The newcomers table was the only one on the page with dead headers.
	type NovaKey = 'name' | 'sector' | 'seen' | 'total';
	let novaKey = $state<NovaKey>('total');
	let novaDesc = $state(true);
	function sortNova(key: NovaKey) {
		if (novaKey === key) novaDesc = !novaDesc;
		else { novaKey = key; novaDesc = true; }
	}
	const novaSorted = $derived.by(() => {
		const dir = novaDesc ? -1 : 1;
		const txt = (v: string | null | undefined) => (v ?? '').toLocaleLowerCase('pt-PT');
		return [...newcomers].sort((a, b) => {
			switch (novaKey) {
				case 'name': return dir * txt(a.name).localeCompare(txt(b.name), 'pt-PT');
				case 'sector': return dir * txt(a.sector).localeCompare(txt(b.sector), 'pt-PT');
				case 'seen': return dir * txt(a.first_seen).localeCompare(txt(b.first_seen));
				default: return dir * ((a.total ?? 0) - (b.total ?? 0));
			}
		});
	});
	const novaAria = (key: NovaKey) =>
		novaKey !== key ? 'none' : novaDesc ? 'descending' : 'ascending';
	const novaCaret = (key: NovaKey) => (novaKey === key ? (novaDesc ? '▾' : '▴') : '');

	const pickedAria = (key: PickKey) =>
		pickedKey !== key ? 'none' : pickedDesc ? 'descending' : 'ascending';
	const caret = (key: PickKey) => (pickedKey === key ? (pickedDesc ? '▾' : '▴') : '');
	let pickedBusy = $state(false);
	let pickedError = $state(false);
	// registry profile, fetched beside the contracts; a miss is normal and silent
	let pickedCompany = $state<Company | null>(null);
	// tracked apart from pickedBusy: the two land independently, and each half of
	// the panel must swap its own skeleton for its own data
	let companyBusy = $state(false);

	async function pickSupplier(d: any) {
		if (!d?.name || d.isBuyer || !data.nif) return;
		picked = { name: d.name, sector: d.sector, newcomer: d.newcomer,
			firstSeen: d.firstSeen, debutDays: d.debutDays, contracts: d.contracts, nif: d.nif };
		pickedRows = [];
		pickedError = false;
		pickedCompany = null;
		pickedBusy = true;
		companyBusy = Boolean(d.nif);
		// the registry can be slow or down; it must never hold up the contracts
		if (d.nif) {
			api<Company>(`/companies/${d.nif}`)
				.then((c) => { if (picked?.name === d.name) pickedCompany = c; })
				.catch(() => { /* no registry entry for this NIF, nothing to show */ })
				.finally(() => { if (picked?.name === d.name) companyBusy = false; });
		}
		try {
			pickedRows = await api<ContractRow[]>(`/municipalities/${data.nif}/contracts`, {
				supplier: d.name, limit: 50
			});
		} catch {
			pickedRows = [];
			pickedError = true;
		} finally {
			pickedBusy = false;
		}
	}
	// "Quem recebeu mais" cut three ways: the firm, what it sold, how it was bought.
	const GROUPINGS = [
		{ id: 'fornecedor',   label: t('muni.group.supplier') },
		{ id: 'sector',       label: t('muni.group.sector') },
		{ id: 'procedimento', label: t('muni.group.procedure') }
	] as const;
	let grouping = $state<(typeof GROUPINGS)[number]['id']>('fornecedor');

	const bars = $derived.by(() => {
		if (!score) return null;
		if (grouping === 'sector') return statBarOption(data.stats?.by_sector ?? []);
		if (grouping === 'procedimento') return statBarOption(data.stats?.by_procedure ?? []);
		return topSuppliersOption(data.suppliers, 10);
	});

	// The map needs its geometry registered with ECharts before the option is set.
	let mapNames = $state<{ name: string; key: string; dkey: string }[]>([]);
	let mapError = $state<string | null>(null);
	$effect(() => {
		if (tab !== 'mapa' || mapNames.length || mapError) return;
		fetch('/pt-municipios.geojson')
			.then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
			.then((geo) => {
				echarts.registerMap('portugal', geo);
				mapNames = geo.features
					.map((f: any) => ({
						name: f.properties.name,
						key: f.properties.key ?? '',
						dkey: f.properties.dkey ?? ''
					}))
					.filter((f: any) => f.name);
			})
			.catch((e) => (mapError = String(e)));
	});
	const map = $derived(mapNames.length ? mapOption(data.cells, 'portugal', mapNames, $narrow) : null);

	const mapTotal = $derived(data.cells.reduce((s, c) => s + (c.total ?? 0), 0));

	// Clicking a concelho opens the contracts executed there, fetched on demand.
	let area = $state<{ name: string; district: string | null; total: number | null;
		contracts: number } | null>(null);
	let areaRows = $state<ContractRow[]>([]);
	let areaBusy = $state(false);
	let areaError = $state(false);

	async function pickArea(d: any) {
		const cell = d?.cell;
		if (!cell?.municipality || !data.nif) return;
		area = { name: cell.municipality, district: cell.district,
			total: cell.total, contracts: cell.contracts };
		areaBusy = true;
		areaError = false;
		try {
			areaRows = await api<ContractRow[]>(`/municipalities/${data.nif}/contracts`, {
				municipality: cell.municipality, limit: 50
			});
		} catch {
			areaRows = [];
			areaError = true;
		} finally {
			areaBusy = false;
		}
	}

	// The contracts tab owns its own filters and paging; the page only supplies
	// the option lists, which come from the distributions it already has.
	const years = $derived((data.stats?.by_year ?? [])
		.map((r) => Number(r.label)).filter((y) => Number.isFinite(y)).sort((a, b) => b - a));
	const procedures = $derived((data.stats?.by_procedure ?? [])
		.map((r) => String(r.label ?? '')).filter(Boolean));
	const sectorNames = $derived((data.stats?.by_sector ?? [])
		.map((r) => String(r.label ?? '')).filter(Boolean));

	function pick(nif: string) {
		goto(L(`/municipio/${nif}`), { invalidateAll: true });
	}
</script>

<svelte:head>
	<title>{t('muni.metaTitle', { name: shortName })}</title>
	<meta name="description" content={t('muni.metaDescription', { name: shortName })} />
</svelte:head>


<Nav municipalities={data.municipalities} current={data.current} onpick={pick} />

{#if !score}
	<main class="wrap empty">
		<h1>{t('muni.noData')}</h1>
		<p>{t('muni.noDataBody')}</p>
	</main>
{:else}
	<main>
		<!-- ── hero ───────────────────────────────────────────────── -->
		<section class="hero" use:reveal class:compact={tab !== 'geral'}>
			<div class="wrap">
				<!-- The period control belongs on the line that states the period, not
				     wedged between the title and the totals where it competed with
				     both. Quiet chips, because this is a filter, not the main action. -->
				<div class="eyerow">
					<p class="eyebrow">
						{t('muni.eyebrow')} · {periodLabel}
						{#if rulingOne}
							· <span class="ruler">{rulingOne.party}{#if rulingOne.president}, {rulingOne.president}{/if}</span>
						{:else if rulingTerms.length > 1}
							· <span class="ruler">{t('muni.mandates', { n: rulingTerms.length })}</span>
						{/if}
					</p>

					{#if availableYears.length > 1}
						<div class="years" role="group" aria-label={t('muni.period')}>
							<button type="button"
								class:on={!data.yearFrom && !data.yearTo && !data.dateFrom}
								onclick={() => setWindow()}>{t('muni.everything')}</button>
							<!-- Single years first: picking "2025" is the common case, and it
							     was the thing the old row of presets could not express. Only
							     the two most recent stay out; fifteen chips of years pushed
							     everything else off the row and read as a wall. -->
							{#each recentYears as y (y)}
								<button type="button" class:on={data.yearFrom === y && data.yearTo === y}
									onclick={() => setWindow(y, y)}>{y}</button>
							{/each}
							{#if olderYears.length}
								<button type="button" class="yr-more" aria-expanded={showOlder}
									class:on={showOlder || olderYears.some((y) => data.yearFrom === y && data.yearTo === y)}
									onclick={() => (showOlder = !showOlder)}>
									{showOlder ? t('muni.fewerYears') : t('muni.moreYears', { n: num(olderYears.length) })}
								</button>
							{/if}
							<!-- Only the two-year span stays out here. Three and five live in
							     the interval panel: as chips they made a long row of things that
							     all say roughly the same thing. -->
							{#if availableYears.length > 2}
								<button type="button" class:on={isPreset(2)} onclick={() => preset(2)}>{t('muni.nYears', { n: 2 })}</button>
							{/if}
							<button type="button" class="yr-more" aria-expanded={custom}
								class:on={custom || isPreset(3) || isPreset(5)}
								onclick={() => (custom = !custom)}>{t('muni.range')}</button>
						</div>
						{#if showOlder && olderYears.length}
							<!-- a scroller rather than another wrapped row: the older years are
							     a long tail nobody reads top to bottom -->
							<div class="years older" role="group" aria-label={t('muni.olderYears')}>
								{#each olderYears as y (y)}
									<button type="button" class:on={data.yearFrom === y && data.yearTo === y}
										onclick={() => setWindow(y, y)}>{y}</button>
								{/each}
							</div>
						{/if}
					{/if}
				</div>

				{#if custom}
					<div class="yr-custom">
						{#each [3, 5] as n (n)}
							{#if availableYears.length > n}
								<button type="button" class="yr-span" class:on={isPreset(n)}
									onclick={() => preset(n)}>{t('muni.lastNYears', { n })}</button>
							{/if}
						{/each}
						<label>{t('muni.from')}
							<select value={data.yearFrom ?? ''} onchange={(e) => setFrom(e.currentTarget.value)}>
								<option value="">{t('muni.allYears')}</option>
								{#each availableYears as y (y)}<option value={y}>{y}</option>{/each}
							</select>
						</label>
						<label>{t('muni.until')}
							<select value={data.yearTo ?? ''} onchange={(e) => setTo(e.currentTarget.value)}>
								<option value="">{t('muni.allYears')}</option>
								{#each availableYears as y (y)}<option value={y}>{y}</option>{/each}
							</select>
						</label>
						<span class="yr-max">{t('muni.maxSpan', { n: MAX_SPAN })}</span>
					</div>
				{/if}
				{#if spanTrimmed}
					<p class="yr-note">{t('muni.spanTrimmed', { n: MAX_SPAN })}</p>
				{/if}

				<h1 class="title" class:poster={tab === 'geral'} style:font-size={titleSize}
					data-in style="--i:1"><span>{shortName}</span></h1>

				<div class="plates totals" data-in style="--i:2">
					<div class="plate plate-red lift">
						<b class="num">{gastos[0]}<i class="unit">{gastos[1]}</i></b><span>{t('muni.spent')}</span>
					</div>
					<div class="plate plate-blue lift">
						<b class="num">{num(score.totals.contracts)}</b><span>{t('muni.contracts')}</span>
					</div>
					<div class="plate plate-yellow lift">
						<b class="num">{num(score.totals.suppliers)}</b><span>{t('muni.suppliers')}</span>
					</div>
				</div>

				{#if tab === 'geral'}
				<div class="indices" data-in style="--i:3">
					<BigIndex value={score.risk_index} label={t('muni.riskIndex')}
						caption={t('muni.riskCaption', { n: num(counted) })} />

					<div class="satire-pair">
						<BigIndex value={score.satirical_index.score} label={t('muni.satireIndex')} tone="brand"
							caption={t('muni.satireCaption')} />
						<div class="verdict" data-tone={score.satirical_index.tone ?? 'warn'}>
							<p class="verdict-name">{said.name}</p>
							<p class="quip">“{said.quip}”</p>
							<p class="units">
								{t('muni.units', {
									bifanas: num(score.satirical_index.units.bifanas),
									salarios: num(score.satirical_index.units.salarios_minimos_anuais, 1)
								})}
							</p>
						</div>
					</div>
				</div>
				{:else}
					<!-- other tabs keep the two scores visible as chips, not as a wall -->
					<div class="chips">
						<span class="chip lift risco"><b class="num">{score.risk_index === null ? t('common.na') : num(score.risk_index, 1)}</b><i class="of">/100</i><span>{t('muni.chipRisk')}</span></span>
						<span class="chip lift chip-satire"><b class="num">{score.satirical_index.score === null ? t('common.na') : num(score.satirical_index.score, 1)}</b><i class="of">/100</i><span>{t('muni.chipSatire')}</span></span>
						<span class="chip lift chip-verdict" data-tone={score.satirical_index.tone ?? 'warn'}>{said.name}</span>
					</div>
				{/if}
			</div>
		</section>

		<!-- ── tabs ───────────────────────────────────────────────── -->
		<div class="tabbar">
			<div class="wrap">
				<div role="tablist" aria-label={t('muni.sections')} bind:this={tabsEl}>
					{#each TABS as t}
						<button role="tab" id="tab-{t.id}" aria-controls="panel-{t.id}"
							aria-selected={tab === t.id} class:active={tab === t.id}
							onclick={() => setTab(t.id)}>{t.label}</button>
					{/each}
				</div>
			</div>
		</div>

		<div class="panels">
			<!-- keyed on the tab, so switching crossfades instead of cutting. Only
			     the incoming panel animates: the panels are wildly different
			     heights and fading the outgoing one out would make the page jump
			     twice instead of once. -->
			{#key tab}
			<div class="panelswap">
			{#if tab === 'geral'}
				<div role="tabpanel" id="panel-geral" aria-labelledby="tab-geral" use:reveal>
					<div class="wrap">
					<MandateTimeline mandates={data.mandates} onpick={setDates}
						activeFrom={data.dateFrom ?? null} activeTo={data.dateTo ?? null} />
					</div>

					<!-- the one dark band on this page: it is what the page is for -->
					<section class="band band-ink bandpad">
						<div class="wrap">
					<h2 class="sectag">{t('muni.indicators')}</h2>
					<div class="signals" data-in style="--i:1">
						{#each allKeys as key (key)}
							{#if score.flags[key]}
								{@const sig = signal(key)}
								<SignalCard label={sig.label} blurb={sig.blurb}
									reason={unmeasurable(key)}
									flag={score.flags[key]} counted={scoredKeys.includes(key)} />
							{/if}
						{/each}
					</div>
						</div>
					</section>

					<div class="wrap">
					<div class="sec-head" data-in style="--i:0">
						<h2 class="sectag">{t('muni.whoGotMost')}</h2>
						<div class="segmented" role="group" aria-label={t('muni.groupBy')}>
							{#each GROUPINGS as g}
								<button class:on={grouping === g.id} aria-pressed={grouping === g.id}
									onclick={() => (grouping = g.id)}>{g.label}</button>
							{/each}
						</div>
					</div>
					{#if bars}
						<div class="card panel" data-in style="--i:2">
							<Chart option={bars} height="420px" onpick={pickBar}
								ariaLabel={t('muni.barsAria', { grouping: GROUPINGS.find((g) => g.id === grouping)?.label ?? '' })} />
							<p class="note small">
								{grouping === 'fornecedor' ? t('muni.barsNoteSupplier') : t('muni.barsNoteOther')}
							</p>
							{#if grouping === 'fornecedor'}
								<p class="legend">
									<span class="sw" style:background="var(--sev-ok)"></span> {t('muni.legendNoAd')}
									<span class="sw" style:background="var(--sev-warn)"></span> {t('muni.legendSome')}
									<span class="sw" style:background="var(--sev-serious)"></span> {t('muni.legendMost')}
									<span class="sw" style:background="var(--sev-critical)"></span> {t('muni.legendAlmostAll')}
								</p>
							{:else}
								<p class="legend">{t('muni.legendCategory')}</p>
							{/if}
						</div>
					{:else}
						<p class="note">{t('muni.noGrouping')}</p>
					{/if}
				</div>

					</div>
			{:else if tab === 'mapa'}
				<div role="tabpanel" id="panel-mapa" aria-labelledby="tab-mapa" use:reveal>
					<div class="wrap">
					<h2 class="sectag">{t('muni.mapTitle')}</h2>
					<p class="note">
						{t('muni.mapNote', {
							sum: eurShort(mapTotal),
							tail: mapTotal > (score.totals.value ?? 0)
								? t('muni.mapExceeds', { total: eurShort(score.totals.value) })
								: t('muni.mapMayExceed')
						})}
					</p>
					<div class="card panel" aria-busy={!map && !mapError}>
						{#if mapError}
							<p class="err">{t('muni.mapError')}</p>
						{:else if map}
							<Chart option={map} height={$narrow ? '380px' : '560px'} onpick={pickArea}
								ariaLabel={t('muni.mapAria')} />
						{:else}
							<Skeleton h={$narrow ? '380px' : '560px'} />
						{/if}
					</div>
					{#if area}
						<div class="card picked pop">
							<header class="picked-head">
								<div>
									<p class="eyebrow">{area.district && area.district !== area.name
										? area.district : t('muni.concelho')}</p>
									<h3>{area.name}</h3>
									<p class="badge neutral">{t('muni.areaBadge', { money: eurShort(area.total), n: num(area.contracts) })}</p>
								</div>
								<button class="close" onclick={() => (area = null)} aria-label={t('common.close')}>✕</button>
							</header>
							<div class="table-wrap" aria-busy={areaBusy}>
							{#if areaBusy}
								<SkeletonTable rows={Math.min(area.contracts || 3, 8)}
									cols={['44%', '28%', '14%']} />
							{:else if areaError}
								<p class="err">{t('muni.areaError')}</p>
							{:else if areaRows.length}
									<table class="stack">
										<thead>
											<tr><th>{t('tbl.object')}</th><th>{t('tbl.supplier')}</th>
												<th class="r">{t('tbl.value')}</th></tr>
										</thead>
										<tbody>
											{#each areaRows as c (c.id)}
												<tr>
													<td class="obj wide" data-label={t('tbl.object')}
														><a href={L(`/contrato/${c.id}`)}>{c.object ?? t('common.noDescription')}</a><span
															class="date num">{dateShort(c.signed_date)}</span><Flags flags={c.flags} /></td>
													<td data-label={t('tbl.supplier')}><Parties parties={c.parties} names={c.suppliers} /></td>
													<td class="r num money" data-label={t('tbl.value')}>{eur(c.value)}</td>
												</tr>
											{/each}
										</tbody>
									</table>
							{:else}
								<p class="nothing">{t('muni.areaEmpty')}</p>
							{/if}
							</div>
						</div>
					{:else}
						<p class="note small">{t('muni.areaHint')}</p>
					{/if}

					<p class="note small">{t('muni.islandsNote')}</p>
				</div>

					</div>
			{:else if tab === 'rede'}
				<div role="tabpanel" id="panel-rede" aria-labelledby="tab-rede" use:reveal>
					<div class="wrap">
					<h2 class="sectag">{t('muni.webTitle')}</h2>
					<div class="controls">
						<label>
							{t('muni.graphSize')}
							<input type="range" min="10" max={Math.min(120, data.suppliers.length)} step="5"
								bind:value={graphSize} />
							<span class="num">{graphSize}</span>
						</label>
						<p class="hint">
							{$narrow ? t('muni.graphHintNarrow') : t('muni.graphHintWide')}
						</p>
					</div>
					<div class="card panel" aria-busy={!graph}>
						{#if graph}
							<Chart option={graph} height={$narrow ? '420px' : '620px'} onpick={pickSupplier}
								ariaLabel={t('muni.graphAria')} />
						{:else}
							<Skeleton h={$narrow ? '420px' : '620px'} />
						{/if}
					</div>

					<!-- Legend in HTML, not on the canvas: it has to explain the shapes
					     too, and a confined tooltip kept landing on the canvas one. -->
					<div class="glegend">
						<ul class="gl-list">
							{#each categories as c (c.name)}
								{@const off = hiddenSectors.includes(c.name)}
								<li>
									<button type="button" class="gl-toggle" class:gl-off={off}
										aria-pressed={!off} onclick={() => toggleSector(c.name)}>
										<span class="gl-sw" style:background={c.colour}></span>{c.name}
									</button>
								</li>
							{/each}
						</ul>
						{#if hiddenSectors.length}
							<p class="gl-filtered">
								{hiddenSectors.length === 1
									? t('muni.hidingSector')
									: t('muni.hidingSectors', { n: hiddenSectors.length })}
								<button type="button" class="gl-clear" onclick={() => (hiddenSectors = [])}>{t('muni.showAll')}</button>
							</p>
						{/if}
						<ul class="gl-list gl-syms">
							<li><span class="gl-sym gl-diamond"></span>{t('muni.symDiamond')}</li>
							<li><span class="gl-sym gl-circle"></span>{t('muni.symCircle')}</li>
							<li><span class="gl-sym gl-big"></span>{t('muni.symSize')}</li>
						</ul>
						<p class="gl-note">{t('muni.graphNote')}</p>
					</div>

					{#if picked}
						<div class="card picked pop">
							<header class="picked-head">
								<div>
									<p class="eyebrow">{picked.sector ?? t('muni.supplier')}</p>
									<h3>{picked.name}</h3>
									{#if picked.newcomer}
										<p class="badge">{t('muni.newHere', { sentence: novaSentence(picked.firstSeen, picked.debutDays) })}</p>
									{/if}
								</div>
								<div class="picked-acts">
									{#if picked.nif}
										<a class="seemore lift" href={L(`/empresa/${picked.nif}`)}>{t('muni.seeCompany')}</a>
									{/if}
									<button class="close" onclick={() => (picked = null)} aria-label={t('common.close')}>✕</button>
								</div>
							</header>

							{#if picked.nif || companyBusy}
								<CompanyProfile company={pickedCompany} busy={companyBusy}
									name={picked.name} />
							{/if}

							<div class="table-wrap" aria-busy={pickedBusy}>
							{#if pickedBusy}
								<SkeletonTable rows={Math.min(picked.contracts || 3, 8)}
									cols={['36%', '24%', '13%', '13%']} />
							{:else if pickedError}
								<p class="err">{t('muni.pickedError')}</p>
							{:else if pickedRows.length}
									<table class="stack sortable">
										<thead>
											<tr>
												<th scope="col" aria-sort={pickedAria('object')}>
													<button onclick={() => sortPicked('object')}>{t('tbl.object')}<span class="caret">{caret('object')}</span></button></th>
												<th scope="col" aria-sort={pickedAria('date')}>
													<button onclick={() => sortPicked('date')}>{t('tbl.date')}<span class="caret">{caret('date')}</span></button></th>
												<th scope="col" aria-sort={pickedAria('procedure')}>
													<button onclick={() => sortPicked('procedure')}>{t('tbl.procedure')}<span class="caret">{caret('procedure')}</span></button></th>
												<th scope="col" class="r" aria-sort={pickedAria('bidders')}>
													<button onclick={() => sortPicked('bidders')}>{t('tbl.bidders')}<span class="caret">{caret('bidders')}</span></button></th>
												<th scope="col" class="r" aria-sort={pickedAria('value')}>
													<button onclick={() => sortPicked('value')}>{t('tbl.value')}<span class="caret">{caret('value')}</span></button></th>
											</tr>
										</thead>
										<tbody>
											{#each pickedSorted as c (c.id)}
												<tr>
													<td class="obj wide" data-label={t('tbl.object')}
														><a href={L(`/contrato/${c.id}`)}>{c.object ?? t('common.noDescription')}</a><Flags
															flags={c.flags} /></td>
													<td class="num" data-label={t('tbl.date')}>{dateShort(c.signed_date)}</td>
													<td data-label={t('tbl.procedure')}><span class="proc" class:ad={/ajuste direto/i.test(c.procedure ?? '')}>{c.procedure ?? t('common.na')}</span></td>
													<td class="r num" data-label={t('tbl.bidders')}>{c.n_bidders ?? t('common.na')}</td>
													<td class="r num money" data-label={t('tbl.value')}>{eur(c.value)}</td>
												</tr>
											{/each}
										</tbody>
									</table>
							{:else}
								<p class="nothing">{t('muni.pickedEmpty')}</p>
							{/if}
							</div>
						</div>
					{/if}

					<h2 class="sectag">{t('muni.newcomersTitle')}</h2>
					{#if !newcomerKnown}
						<p class="note">{t('muni.newcomersUnknown', { period: periodLabel })}</p>
					{:else if newcomers.length}
						<p class="note">{t('muni.newcomersNote')}</p>
						<div class="card table-wrap" data-in style="--i:2">
							<table class="stack sortable">
								<thead>
									<tr>
										<th scope="col" aria-sort={novaAria('name')}>
											<button onclick={() => sortNova('name')}>{t('muni.col.company')}<span class="caret">{novaCaret('name')}</span></button></th>
										<th scope="col" aria-sort={novaAria('sector')}>
											<button onclick={() => sortNova('sector')}>{t('muni.col.sector')}<span class="caret">{novaCaret('sector')}</span></button></th>
										<th scope="col" class="r" aria-sort={novaAria('seen')}>
											<button onclick={() => sortNova('seen')}>{t('muni.col.firstPublic')}<span class="caret">{novaCaret('seen')}</span></button></th>
										<th scope="col" class="r" aria-sort={novaAria('total')}>
											<button onclick={() => sortNova('total')}>{t('tbl.value')}<span class="caret">{novaCaret('total')}</span></button></th>
									</tr>
								</thead>
								<tbody>
									{#each novaSorted.slice(0, 15) as s (s.name)}
										<tr>
											<th scope="row" data-label={t('muni.col.company')}>
												{#if s.nif}<a href={L(`/empresa/${s.nif}`)}>{s.name}</a>{:else}{s.name}{/if}
											</th>
											<td data-label={t('muni.col.sector')}>{s.sector}</td>
											<td class="r num" data-label={t('muni.col.firstPublic')}>{dateShort(s.first_seen)}</td>
											<td class="r num money" data-label={t('tbl.value')}>{eur(s.total)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="note">{t('muni.newcomersNone')}</p>
					{/if}

					<h2 class="sectag">{t('muni.rivalsTitle')}</h2>
					{#if data.rivals.length}
						<p class="note">{t('muni.rivalsNote')}</p>
						<div class="card table-wrap" data-in style="--i:2">
							<table class="stack">
								<thead><tr><th>{t('muni.col.company')}</th><th>{t('muni.rivalsAlso')}</th><th class="r">{t('muni.rivalsTenders')}</th></tr></thead>
								<tbody>
									{#each data.rivals.slice(0, 15) as r (r.firm_a + r.firm_b)}
										<tr>
											<td data-label={t('muni.col.company')}>
												{#if r.nif_a}<a href={L(`/empresa/${r.nif_a}`)}>{r.firm_a}</a>{:else}{r.firm_a}{/if}
											</td>
											<td data-label={t('muni.rivalsAlso')}>
												{#if r.nif_b}<a href={L(`/empresa/${r.nif_b}`)}>{r.firm_b}</a>{:else}{r.firm_b}{/if}
											</td>
											<td class="r num" data-label={t('muni.rivalsTenders')}>{r.tenders}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="note">{t('muni.rivalsNone')}</p>
					{/if}
				</div>

					</div>
			{:else if tab === 'estatisticas'}
				<div role="tabpanel" id="panel-estatisticas" aria-labelledby="tab-estatisticas" use:reveal>
					<div class="wrap">
					{#if data.stats}
						{@const h = data.stats.headline}
						{@const maiorPct = 100 * (h.largest ?? 0) / (h.total || 1)}
						{@const med = eurShortParts(h.median)}
						{@const avg = eurShortParts(h.mean)}
						{@const p9 = eurShortParts(h.p90)}
						{@const big = eurShortParts(h.largest)}

						<h2 class="sectag">{t('muni.statsTitle')}</h2>
						<p class="note">{t('muni.statsNote')}</p>
						<div class="kpis" data-in style="--i:1">
							<div class="kpi"><span class="eyebrow">{t('muni.kpi.typical')}</span>
								<b class="num">{med[0]}<i class="unit">{med[1]}</i></b>
								<small>{t('muni.kpi.typicalNote', { n: num(h.contracts) })}</small></div>

							<div class="kpi"><span class="eyebrow">{t('muni.kpi.mean')}</span>
								<b class="num">{avg[0]}<i class="unit">{avg[1]}</i></b>
								<small>{(h.mean ?? 0) > (h.median ?? 0) * 2
									? t('muni.kpi.meanSkewed')
									: t('muni.kpi.meanFlat')}</small></div>

							<div class="kpi"><span class="eyebrow">{t('muni.kpi.priciest')}</span>
								<b class="num">{p9[0]}<i class="unit">{p9[1]}</i></b>
								<small>{t('muni.kpi.priciestNote')}</small></div>

							<div class="kpi" class:bad={(h.suppliers_to_half ?? 99) <= 3}>
								<span class="eyebrow">{t('muni.kpi.half')}</span>
								<b class="num">{h.suppliers_to_half === null ? t('common.na') : num(h.suppliers_to_half)}</b>
								<small>{h.suppliers_to_half === 1
									? t('muni.kpi.halfOne')
									: t('muni.kpi.halfMany')}</small></div>

							<div class="kpi" class:bad={maiorPct >= 25}><span class="eyebrow">{t('muni.kpi.largest')}</span>
								<b class="num">{big[0]}<i class="unit">{big[1]}</i></b>
								<small>{t('muni.kpi.largestNote', { pct: pct(maiorPct) })}</small></div>

							<div class="kpi"><span class="eyebrow">{t('muni.kpi.kinds')}</span>
								<b class="num">{num(h.cpv_codes)}</b>
								<small>{t('muni.kpi.kindsNote')}</small></div>
						</div>
						<p class="note small">
							{#if h.zero_value}
								{h.zero_value === 1
									? t('muni.zeroOne')
									: t('muni.zeroMany', { n: num(h.zero_value) })}
							{/if}
							{t('muni.noOverruns')}
						</p>

						<h2 class="sectag">{t('muni.distributions')}</h2>
						<div class="tables" data-in style="--i:1">
							<StatTable rows={data.stats.by_procedure} title={t('muni.byProcedure')}
								unitLabel={t('muni.unit.procedure')} nif={data.nif} filter="procedure"
								yearFrom={data.yearFrom} yearTo={data.yearTo} />
							<StatTable rows={data.stats.by_sector} title={t('muni.bySector')}
								unitLabel={t('muni.unit.sector')} nif={data.nif} filter="sector"
								yearFrom={data.yearFrom} yearTo={data.yearTo} />
							{#if data.stats.by_year.length > 1}
								<StatTable rows={data.stats.by_year} title={t('muni.byYear')} unitLabel={t('muni.unit.year')}
									nif={data.nif} filter="year"
									yearFrom={data.yearFrom} yearTo={data.yearTo} />
							{/if}
						</div>
					{/if}
				</div>

					</div>
			{:else if tab === 'empresas'}
				<div role="tabpanel" id="panel-empresas" aria-labelledby="tab-empresas" use:reveal>
					<div class="wrap">
					<h2 class="sectag" data-in style="--i:0">{t('muni.companiesTitle')}</h2>
					<p class="note">{t('muni.companiesNote')}</p>
					<div data-in style="--i:1">
						<SuppliersTable nif={data.nif} initial={data.suppliers} forms={data.legalForms}
							yearFrom={data.yearFrom} yearTo={data.yearTo} />
					</div>
				</div>

					</div>
			{:else}
				<div role="tabpanel" id="panel-contratos" aria-labelledby="tab-contratos" use:reveal>
					<div class="wrap">
					<h2 class="sectag" data-in style="--i:0">{t('muni.contractsTitle')}</h2>
					<div data-in style="--i:1">
					<ContractsTable nif={data.nif} initial={data.contracts} forms={data.legalForms}
						preset={{ sector: page.url.searchParams.get('sector') ?? undefined,
							procedure: page.url.searchParams.get('procedure') ?? undefined,
							supplier: page.url.searchParams.get('supplier') ?? undefined }}
						{years} {procedures} sectors={sectorNames} />
					</div>
				</div>
					</div>
			{/if}
			</div>
			{/key}
		</div>
	</main>
{/if}

<Footer caveats={score?.caveats ?? []} latest={data.current?.latest ?? null} />

<style>
	/* content sits above the decorative layer, which is fixed at z-index 0 */
	main { padding-bottom: 1rem; position: relative; z-index: 1; }
	.empty { padding: 5rem 0; }

	/* The hero shrinks when you leave the overview, and a hard cut moved the tab
	   bar and everything under it. Ease the properties that change size. */
	.hero {
		padding: 2.75rem 0 2rem; border-bottom: 2px solid var(--ink);
		transition: padding .22s ease;
	}
	.title {
		font-size: clamp(2.8rem, 11vw, 7rem);
		/* .3em, not a flat .8rem: the block paints .1em of padding and a .1em drop
		   below its own line box, and at 112px that is 22px the plates row was
		   sitting inside. The clearance has to grow with the font. */
		margin: .55rem 0 max(.8rem, .3em); transition: font-size .22s ease, margin .22s ease; }
	.totals { transition: gap .22s ease, margin .22s ease; }
	@media (prefers-reduced-motion: reduce) {
		.hero, .title, .totals { transition: none; }
	}

	/* Outside the overview the hero is a header, not the content. */
	.hero.compact { padding: 1.25rem 0 1rem; }
	.hero.compact .title { font-size: clamp(1.8rem, 5vw, 2.9rem); margin: 0 0 .5rem; }
	.hero.compact .totals { gap: .45rem; margin-bottom: .85rem; }
	.hero.compact .plate { padding: .35rem .7rem .3rem; min-width: 0; box-shadow: 3px 3px 0 var(--ink); }
	.hero.compact .plate b { font-size: 1.1rem; }
	.hero.compact .plate span { font-size: .56rem; margin-top: .1rem; }

	/* center, not stretch: a wrapped row must not inflate the pills on the row
	   above it, and no pill may shrink below the width of its own text */
	.chips { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; }
	/* one height for all three: the verdict pill is display type, the other two
	   are not, and mixing them free-form made the row look mis-scaled */
	/* every part is its own flex item with flex:none, or an anonymous text run
	   breaks onto a second line and the pill grows past its neighbours */
	.chip { display: inline-flex; flex-wrap: nowrap; align-items: center; gap: .3rem;
		min-height: 2.1rem; font-size: .8rem; font-weight: 600; line-height: 1;
		white-space: nowrap; border: 2px solid var(--ink); border-radius: 99px;
		padding: 0 .85rem; background: var(--paper-2); }
	.chip { flex: none; }
	.chip > * { flex: none; }
	.chip b { font-family: 'Bowlby One', Impact, sans-serif; font-size: 1rem; }
	.chip .of { font-style: normal; font-size: .7rem; color: var(--ink-faint); margin-right: .15rem; }
	.chip.risco b { color: var(--sev-warn); }
	.chip.chip-satire b { color: var(--azulejo); }
	.chip.chip-verdict { background: var(--sev-warn); color: #fff5d8; border-color: var(--ink);
		font-family: 'Bowlby One', Impact, sans-serif; font-size: .82rem;
		text-transform: uppercase; letter-spacing: .01em; }
	.chip.chip-verdict[data-tone='ok']       { background: var(--sev-ok); }
	.chip.chip-verdict[data-tone='critical'] { background: var(--sev-critical); }

	.totals { margin-bottom: 2rem; }
	.totals .num { display: inline-flex; align-items: baseline; }

	/* stretch, not start: the two index cards and the verdict share one baseline
	   row, and a card with a caption must not make its neighbour look stunted */
	.indices { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.6fr);
		gap: 1.25rem; align-items: stretch; }
	/* minmax, not auto: the verdict needs a floor or the display type wraps to
	   three lines the moment the score card grows a caption */
	.satire-pair { display: grid; grid-template-columns: minmax(0, 1fr) minmax(15rem, .9fr);
		gap: 1.25rem; align-items: stretch; }
	.verdict { --tone: var(--sev-warn); display: flex; flex-direction: column; justify-content: center;
		border: 2px dashed var(--rule); border-radius: var(--radius); padding: 1rem 1.2rem; background: #fffdf6; }
	.verdict[data-tone='ok']       { --tone: var(--sev-ok); }
	.verdict[data-tone='critical'] { --tone: var(--sev-critical); }
	.verdict-name { font-family: 'Bowlby One', Impact, sans-serif; font-size: clamp(1.1rem, 2.4vw, 1.7rem);
		text-transform: uppercase; color: var(--tone); margin: 0 0 .35rem; line-height: 1; }
	.quip { margin: 0 0 .7rem; font-style: italic; color: var(--ink-soft); }
	.units { margin: 0; font-size: .85rem; color: var(--ink-soft); }

	/* On a phone these wrap to two rows, and with the sticky header above that is
	   about 150px of chrome permanently stuck to a 780px screen. The tabs sit
	   near the top anyway, so stickiness is the thing to give up. */
	@media (max-width: 720px) {
		.tabbar { position: static; }
		/* one row that scrolls, not two that stack: wrapped, the bar was 85px of
		   a 844px screen and left the active underline on the row above the
		   active tab */
		.tabbar [role='tablist'] {
			flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none;
		}
		.tabbar [role='tablist']::-webkit-scrollbar { display: none; }
		.tabbar [role='tab'] { flex: none; }
	}
	.tabbar { position: sticky; top: calc(4rem + 7px); z-index: 10; background: var(--paper-3); border-bottom: 2px solid var(--ink); }
	/* Wraps rather than scrolls: a hidden sideways scroll is a tab nobody finds. */
	[role='tablist'] { display: flex; flex-wrap: wrap; gap: .4rem; }
	[role='tab'] {
		border: 0; background: none; cursor: pointer; padding: .85rem 1.1rem;
		font-weight: 700; color: var(--ink-soft); white-space: nowrap;
		border-bottom: 4px solid transparent; margin-bottom: -2px;
	}
	[role='tab']:hover { color: var(--ink); }
	[role='tab'].active { color: var(--ink); border-bottom-color: var(--sangria); }
	@media (max-width: 720px) {
		[role='tablist'] { gap: .15rem; }
		[role='tab'] { padding: .7rem .55rem; font-size: .84rem; }
	}
	@media (max-width: 400px) {
		[role='tab'] { padding: .6rem .45rem; font-size: .78rem; }
	}

	/* section heading with a control parked on its right */
	.sec-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
		gap: .75rem 1rem; margin: 2rem 0 1rem; }
	.sec-head:first-child { margin-top: 0; }
	.sec-head .sectag { margin: 0; }
	.segmented { display: inline-flex; border: 2px solid var(--ink); border-radius: var(--radius);
		overflow: hidden; background: var(--paper-2); }
	.segmented button {
		border: 0; background: none; cursor: pointer; padding: .7rem .9rem; min-height: 2.75rem;
		font-size: .82rem; font-weight: 700; color: var(--ink-soft); white-space: nowrap;
	}
	.segmented button + button { border-left: 2px solid var(--ink); }
	.segmented button:hover { background: var(--paper-3); color: var(--ink); }
	.segmented button.on { background: var(--ink); color: var(--paper); }

	.badge { display: inline-block; margin: .35rem 0 0; font-size: .78rem; line-height: 1.4;
		color: var(--sev-critical); font-weight: 600; }
	.badge.neutral { color: var(--ink-soft); font-weight: 500; }

	.panels { padding-top: 2rem; }
	.panelswap { animation: panelin .42s cubic-bezier(.16, 1, .3, 1) both; }
	@keyframes panelin {
		from { opacity: 0; transform: translateY(10px); }
		to { opacity: 1; transform: none; }
	}
	@media (prefers-reduced-motion: reduce) { .panelswap { animation: none; } }
	.sectag { margin: 2rem 0 1rem; }
	.sectag:first-child { margin-top: 0; }
	/* six signals: 3x2 rather than 5+1 orphan */
	.signals { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
	@media (max-width: 900px) { .signals { grid-template-columns: repeat(2, 1fr); } }
	@media (max-width: 560px) { .signals { grid-template-columns: 1fr; } }
	.panel { padding: .75rem; }
	.note.small { font-size: .82rem; margin-top: .9rem; }
	.nothing, .err { padding: 3rem; text-align: center; color: var(--ink-faint); }

	.legend { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem 1rem; margin: .4rem .5rem .2rem;
		font-size: .76rem; color: var(--ink-soft); }
	.sw { width: 12px; height: 12px; border-radius: 3px; border: 1.5px solid var(--ink); display: inline-block; margin-right: .1rem; }

	.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; margin-bottom: 1rem; }
	.controls label { display: flex; align-items: center; gap: .6rem; font-weight: 600; font-size: .88rem; }
	.hint { margin: 0; font-size: .8rem; color: var(--ink-faint); }

	/* period picker: sits on the eyebrow line, quiet by default. It is a filter,
	   not a call to action, so it must not out-shout the title or the totals. */
	.eyerow {
		display: flex; flex-wrap: wrap; align-items: baseline;
		justify-content: space-between; gap: .5rem 1rem;
	}
	.years { display: flex; flex-wrap: wrap; gap: .15rem; }
	.years button {
		font: inherit; font-size: .72rem; font-weight: 700; cursor: pointer;
		letter-spacing: .04em; text-transform: uppercase;
		padding: .22rem .5rem; border: 1px solid transparent; border-radius: 999px;
		background: none; color: var(--ink-faint);
	}
	.years button:hover { color: var(--ink); border-color: var(--ink-faint); }
	.years button.on { background: var(--ink); color: var(--paper); border-color: var(--ink); }
	.yr-more { text-transform: none !important; letter-spacing: 0 !important; }
	.years button:focus-visible,
	.yr-custom select:focus-visible { outline: 2px solid var(--azulejo); outline-offset: 2px; }

	.yr-custom {
		display: flex; flex-wrap: wrap; align-items: center; gap: .5rem .9rem;
		margin: .6rem 0 .2rem; padding: .6rem .75rem; font-size: .82rem; font-weight: 600;
		border: 2px dashed var(--ink-faint); border-radius: var(--radius);
	}
	.yr-span {
		font: inherit; font-size: .8rem; font-weight: 700; cursor: pointer;
		padding: .25rem .65rem; border: 2px solid var(--ink); border-radius: 999px;
		background: var(--paper-2, #fffcef); color: var(--ink);
	}
	.yr-span:hover { background: var(--amarelo); }
	.yr-span.on { background: var(--ink); color: var(--paper); }
	.yr-custom label { display: flex; align-items: center; gap: .4rem; }
	.yr-custom select {
		font: inherit; cursor: pointer; padding: .25rem .45rem;
		border: 2px solid var(--ink); border-radius: var(--radius);
		background: var(--paper-2, #fffcef); color: var(--ink);
	}
	.yr-max { color: var(--ink-faint); font-weight: 500; }
	.yr-note { margin: .4rem 0 0; font-size: .78rem; color: var(--ink-soft); }
	/* who was in charge of the numbers on screen, stated where the period is */
	.ruler { color: var(--ink); font-weight: 800; }

	/* Graph legend. Prefixed because Svelte scopes CSS but not class names, and
	   bare names like .list or .note collide with the wrappers above. */
	.glegend { margin-top: .75rem; }
	.gl-list {
		list-style: none; margin: 0 0 .4rem; padding: 0;
		display: flex; flex-wrap: wrap; gap: .35rem 1.1rem;
		font-size: .8rem; color: var(--ink-soft);
	}
	.gl-list li { display: flex; align-items: center; gap: .4rem; }
	.gl-sw { width: 12px; height: 12px; border: 1.5px solid var(--ink); border-radius: 3px; flex: none; }
	.gl-sym { flex: none; background: var(--ink-soft); border: 1.5px solid var(--ink); }
	.gl-circle { width: 12px; height: 12px; border-radius: 50%; }
	.gl-diamond { width: 11px; height: 11px; transform: rotate(45deg); }
	.gl-big { width: 17px; height: 17px; border-radius: 50%; }
	.gl-toggle {
		display: flex; align-items: center; gap: .4rem;
		background: none; border: 0; padding: 0; cursor: pointer;
		font: inherit; color: inherit;
	}
	.gl-toggle:hover { color: var(--ink); }
	.gl-toggle:focus-visible { outline: 2px solid var(--azulejo); outline-offset: 2px; }
	/* switched off reads as off without relying on colour alone: the swatch
	   empties and the label is struck through */
	.gl-off { opacity: .55; text-decoration: line-through; }
	.gl-off .gl-sw { background: transparent !important; }
	.gl-filtered { margin: 0 0 .4rem; font-size: .78rem; color: var(--ink-soft); }
	.gl-clear {
		background: none; border: 0; padding: 0; font: inherit; cursor: pointer;
		color: var(--azulejo); text-decoration: underline;
	}
	.gl-syms { color: var(--ink); }
	.gl-note { margin: 0; font-size: .78rem; color: var(--ink-faint); max-width: 68ch; }



	.table-wrap { overflow-x: auto; }
	table { width: 100%; border-collapse: collapse; font-size: .87rem; }
	/* thead only. A bare `th` rule also hit every <th scope="row">, so the company
	   names in the newcomers table rendered as tiny faint small-caps with a heavy
	   2px rule under them, while the identical table below looked normal. */
	thead th { text-align: left; font-size: .7rem; text-transform: uppercase; letter-spacing: .1em;
		color: var(--ink-faint); padding: .8rem .9rem; border-bottom: 2px solid var(--ink); white-space: nowrap; }
	tbody th { text-align: left; font-weight: 600; }
	td, tbody th { padding: .75rem .9rem; border-bottom: 1px solid var(--rule); vertical-align: top; }
	tbody tr:last-child td, tbody tr:last-child th { border-bottom: 0; }
	tbody tr:hover { background: #fffdf3; }
	.r { text-align: right; }
	@media (min-width: 821px) { .obj { max-width: 34ch; } }
	.date { display: block; font-size: .72rem; color: var(--ink-faint); margin-top: .2rem; }
	.money { font-weight: 700; }
	.proc { font-size: .78rem; border: 1.5px solid var(--rule); border-radius: 99px; padding: .12rem .5rem; }
	/* nowrap only where the columns exist; stacked rows must be free to wrap */
	@media (min-width: 821px) { .money, .proc { white-space: nowrap; } }
	.proc.ad { border-color: var(--sev-critical); color: var(--sev-critical); font-weight: 700; }

	/* eight KPIs: 4x2, stepping down rather than ever leaving an orphan row */
	.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
	@media (max-width: 1100px) { .kpis { grid-template-columns: repeat(3, 1fr); } }
	@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, 1fr); } }
	@media (max-width: 560px) { .kpis { grid-template-columns: 1fr; } }
	.kpi { background: var(--paper-2); border: 2px solid var(--ink); border-radius: var(--radius);
		box-shadow: var(--shadow-hard); padding: .9rem 1rem; display: flex; flex-direction: column; }
	.kpi b { font-family: 'Bowlby One', Impact, sans-serif; font-size: 1.75rem; line-height: 1.05; margin-top: .25rem; }
	.kpi small { color: var(--ink-soft); font-size: .74rem; margin-top: .2rem; line-height: 1.35; }
	.kpi.bad b { color: var(--sev-critical); }
	/* Panels swap instantly, which read as a page reload. A short fade says the
	   chrome around them did not move. */
	[role='tabpanel'] { animation: panel-in .16s ease-out both; }
	@keyframes panel-in { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: none; } }
	@media (prefers-reduced-motion: reduce) { [role='tabpanel'] { animation: none; } }

	/* Same sortable header as StatTable, so the two tables read as one thing. */
	table.sortable th button {
		font: inherit; font-weight: 700; font-size: .72rem; letter-spacing: .09em;
		text-transform: uppercase; color: var(--ink-faint);
		background: none; border: 0; padding: 0; cursor: pointer;
		display: inline-flex; align-items: center; gap: .25rem;
	}
	table.sortable th button:hover { color: var(--ink); }
	table.sortable th button:focus-visible { outline: 2px solid var(--azulejo); outline-offset: 2px; }
	table.sortable .caret { font-size: .8em; }

	.tables { display: grid; gap: 1.25rem; }

	.picked { margin-top: 1rem; }
	.picked-acts { display: flex; align-items: center; gap: .5rem; flex: none; }
	.seemore {
		font-size: .78rem; font-weight: 800; text-decoration: none; white-space: nowrap;
		color: var(--ink); background: var(--amarelo);
		border: 2px solid var(--ink); border-radius: var(--radius);
		box-shadow: var(--shadow-hard); padding: .45rem .8rem;
	}
	.picked-head { display: flex; align-items: flex-start; justify-content: space-between;
		gap: 1rem; padding: .9rem 1rem .4rem; }
	.picked-head h3 { font-size: 1.05rem; margin-top: .15rem; }
	.close { min-width: 2.75rem; min-height: 2.75rem; background: none; border: 2px solid var(--ink); border-radius: 99px; width: 1.9rem; height: 1.9rem;
		cursor: pointer; line-height: 1; flex: none; }
	.close:hover { background: var(--sangria); color: var(--paper); }

	@media (max-width: 900px) {
		.indices { grid-template-columns: 1fr; }
		.satire-pair { grid-template-columns: 1fr; }
	}
</style>
