<script lang="ts">
	import { untrack } from 'svelte';
	import { goto } from '$app/navigation';
	import { reveal } from '$lib/reveal';
	import { narrow } from '$lib/narrow.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { eurShort, num, pct } from '$lib/format';
	import { L, t } from '$lib/messages';
	import { partyColour, partyHead, partyLabel } from '$lib/parties';
	import { api, type MandateMapRow } from '$lib/api';
	import Chart from '$lib/Chart.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import { mapKey, politicalMapOption, type GeoFeature, type PoliticalCell } from '$lib/charts';
	import echarts from '$lib/echarts';

	let { data } = $props();

	const VIEWS = [
		{ id: 'mapa', label: t('pan.view.map') },
		{ id: 'partido', label: t('pan.view.party') }
	] as const;
	type ViewId = (typeof VIEWS)[number]['id'];
	let view = $state<ViewId>('mapa');

	/* ---- the political map -------------------------------------------- */
	let features = $state<GeoFeature[]>([]);
	let bboxes = $state<Record<string, Box>>({});
	let geoError = $state(false);
	let geoBusy = $state(false);
	let year = $state<number | null>(null);
	// The loader's first election; the year buttons take it from here.
	let rows = $state<MandateMapRow[]>(untrack(() => data.mapRows));
	let mapBusy = $state(false);
	/** null = the whole country by district; a name = drilled into that district */
	let drill = $state<string | null>(null);

	type Box = [[number, number], [number, number]];

	const grow = (b: Box, lng: number, lat: number): void => {
		b[0][0] = Math.min(b[0][0], lng); b[0][1] = Math.min(b[0][1], lat);
		b[1][0] = Math.max(b[1][0], lng); b[1][1] = Math.max(b[1][1], lat);
	};

	/** Coordinates nest to an unknown depth (Polygon vs MultiPolygon). */
	function walk(node: any, box: Box): void {
		if (!Array.isArray(node)) return;
		if (typeof node[0] === 'number' && typeof node[1] === 'number') {
			grow(box, node[0], node[1]);
			return;
		}
		for (const child of node) walk(child, box);
	}

	// Two geometries, because they are two maps. Painting all 308 concelhos with
	// their district's colour looked like a district map right up until two
	// neighbouring districts landed on the same party, at which point the border
	// between them vanished. pt-distritos.geojson is the concelhos dissolved.
	$effect(() => {
		if (view !== 'mapa' || features.length || geoBusy || geoError) return;
		geoBusy = true;
		Promise.all([
			fetch('/pt-distritos.geojson').then((r) => r.json()),
			fetch('/pt-municipios.geojson').then((r) => r.json())
		])
			.then(([distritos, municipios]) => {
				echarts.registerMap('pt-distritos', distritos);
				echarts.registerMap('portugal', municipios);

				const boxes: Record<string, Box> = {};
				for (const f of distritos.features) {
					const box: Box = [[180, 90], [-180, -90]];
					walk(f.geometry?.coordinates, box);
					boxes[f.properties.name] = box;
				}
				bboxes = boxes;

				features = municipios.features
					.map((f: any) => ({
						name: f.properties.name,
						key: f.properties.key ?? '',
						dkey: f.properties.dkey ?? '',
						district: f.properties.district ?? ''
					}))
					.filter((f: GeoFeature) => f.name);
			})
			.catch(() => (geoError = true))
			.finally(() => (geoBusy = false));
	});

	let yearFailed = $state(false);

	async function pickYear(y: number) {
		if (y === (year ?? data.years[0]) || mapBusy) return;
		mapBusy = true;
		yearFailed = false;
		try {
			rows = await api<MandateMapRow[]>('/rankings/map', { year: y });
			year = y;
		} catch {
			// Leaving this uncaught left the old election on screen with the new
			// year highlighted, which is worse than saying nothing happened.
			yearFailed = true;
		} finally {
			mapBusy = false;
		}
	}

	/** Each concelho's row, keyed by the geometry name ECharts matches on. */
	const byGeoName = $derived.by(() => {
		const byKey = new Map(features.map((f) => [f.key, f]));
		const out = new Map<string, MandateMapRow>();
		for (const r of rows) {
			const f = byKey.get(mapKey(r.concelho));
			if (f) out.set(f.name, r);
		}
		return out;
	});

	/** A district's câmaras, its leading party, and what the loaded ones spent. */
	type District = {
		name: string; rows: MandateMapRow[]; party: string;
		held: number; total: number; value: number; contracts: number;
		loaded: number; adValue: number;
	};

	const districts = $derived.by(() => {
		const groups = new Map<string, MandateMapRow[]>();
		for (const r of rows) {
			if (!r.district) continue;
			(groups.get(r.district) ?? groups.set(r.district, []).get(r.district)!).push(r);
		}
		const out: District[] = [];
		for (const [name, list] of groups) {
			const counts = new Map<string, number>();
			for (const r of list) {
				const h = partyHead(r.party);
				counts.set(h, (counts.get(h) ?? 0) + 1);
			}
			const [party, held] = [...counts].sort((a, b) => b[1] - a[1])[0] ?? ['', 0];
			const loadedRows = list.filter((r) => r.value !== null);
			out.push({
				name, rows: list, party, held, total: list.length,
				loaded: loadedRows.length,
				value: loadedRows.reduce((a, r) => a + (r.value ?? 0), 0),
				contracts: loadedRows.reduce((a, r) => a + (r.contracts ?? 0), 0),
				adValue: loadedRows.reduce((a, r) => a + ((r.value ?? 0) * (r.ad_pct ?? 0)) / 100, 0)
			});
		}
		return out.sort((a, b) => b.total - a.total);
	});

	/** A term shorter than a year reads as months. "0,9 anos" is not a duration
	 *  anyone says out loud, and the current mandate is short by definition. */
	function termLength(years: number | null): string {
		if (years === null) return t('common.na');
		if (years < 1) {
			const months = Math.max(1, Math.round(years * 12));
			return months === 1 ? t('pan.month', { n: months }) : t('pan.months', { n: months });
		}
		return t('muni.nYears', { n: num(years, 1) });
	}

	/** What one câmara's row says, as tooltip rows. */
	function concelhoLines(r: MandateMapRow): [string, string][] {
		const lines: [string, string][] = [
			[t('pan.tip.list'), partyLabel(r.party)],
			[t('pan.tip.president'), r.president ?? t('common.na')],
			[t('pan.tip.term'), termLength(r.years)]
		];
		if (r.value === null) {
			lines.push([t('pan.tip.contracts'), t('pan.tip.notLoaded')]);
		} else {
			lines.push([t('pan.tip.spentInTerm'), eurShort(r.value)]);
			lines.push([t('pan.tip.contracts'), num(r.contracts ?? 0)]);
			lines.push([t('pan.tip.noTender'), pct(r.ad_pct)]);
		}
		return lines;
	}

	/** Filter the map to one party, counted the way the colour counts it. */
	let partyFilter = $state<string | null>(null);
	const matchesFilter = (party: string) => !partyFilter || partyHead(party) === partyFilter;

	const cells = $derived.by((): PoliticalCell[] => {
		if (!features.length || !rows.length) return [];

		if (!drill) {
			// One shape per district, from the dissolved geometry.
			return districts.map((d) => {
				const lines: [string, string][] = [
					[t('pan.tip.leadingParty'),
						t('pan.tip.ofTotal', { label: partyLabel(d.party), held: d.held, total: d.total })]
				];
				if (d.loaded) {
					lines.push([t('pan.tip.spentInTerm'), eurShort(d.value)]);
					lines.push([t('pan.tip.contracts'), num(d.contracts)]);
					lines.push([t('pan.tip.noTender'), pct(d.value ? (100 * d.adValue) / d.value : null)]);
					lines.push([
						t('pan.tip.withData'),
						d.total === 1
							? t('pan.tip.camaraWithData', { loaded: d.loaded, total: d.total })
							: t('pan.tip.camarasWithData', { loaded: d.loaded, total: d.total })
					]);
				} else {
					lines.push([t('pan.tip.contracts'), t('pan.tip.noneLoaded')]);
				}
				return {
					name: d.name,
					colour: partyColour(d.party),
					muted: !matchesFilter(d.party),
					title: d.name,
					lines
				};
			});
		}

		// Inside a district: its câmaras take their own colours, the rest fade.
		return features.map((f) => {
			const r = byGeoName.get(f.name);
			if (f.district !== drill || !r) {
				return {
					name: f.name, colour: 'rgba(156,128,120,.2)', muted: true,
					title: f.name, lines: []
				};
			}
			return {
				name: f.name,
				colour: partyColour(r.party),
				muted: !matchesFilter(r.party),
				title: r.concelho,
				lines: concelhoLines(r)
			};
		});
	});

	/** The câmaras in the open district whose pages actually exist. */
	const openable = $derived(
		drill ? rows.filter((r) => r.district === drill && r.nif) : []
	);

	const mapOption = $derived(
		cells.length
			? politicalMapOption(drill ? 'portugal' : 'pt-distritos', cells,
				drill ? bboxes[drill] : undefined, $narrow)
			: null
	);

	/**
	 * One click, two meanings, decided by where you already are.
	 *
	 * From the country view a click opens the district. Once inside it, a click
	 * on a câmara we hold the contracts for goes to that câmara's page, which is
	 * the whole point of drilling in. A câmara with nothing loaded stays put:
	 * sending someone to an empty page is worse than not moving.
	 */
	function onMapPick(datum: any) {
		if (!datum?.name) return;

		if (!drill) {
			// The country map's areas are districts, so the name is the district.
			drill = datum.name;
			return;
		}
		const row = byGeoName.get(datum.name);
		if (row?.nif) goto(L(`/municipio/${row.nif}`));
	}

	/**
	 * The legend, which is also the filter, so it can only ever list what the
	 * map is actually painting.
	 *
	 * On the country view that is the party leading each district, not every
	 * party that won a câmara somewhere: offering "INOV25" as a filter on a map
	 * with no INOV25 district greys the whole country and explains nothing.
	 */
	const legend = $derived.by(() => {
		const parties = drill
			? rows.filter((r) => r.district === drill).map((r) => r)
			: districts.map((d) => ({ party: d.party, coalition: false }));
		const counts = new Map<string, { n: number; coalitions: number }>();
		for (const r of parties) {
			const head = partyHead(r.party);
			const cur = counts.get(head) ?? { n: 0, coalitions: 0 };
			cur.n += 1;
			if (r.coalition) cur.coalitions += 1;
			counts.set(head, cur);
		}
		return [...counts].sort((a, b) => b[1].n - a[1].n);
	});

	// Three is what a reader compares without counting. The rest stay one tap
	// away rather than filling a line and a half with parties holding one câmara.
	const LEGEND_TOP = 3;
	let legendAll = $state(false);
	const legendShown = $derived(legendAll ? legend : legend.slice(0, LEGEND_TOP));
	const legendRest = $derived(Math.max(0, legend.length - LEGEND_TOP));

	// The country view is never filtered: its colours are district majorities,
	// and a filter there would fade districts whose leading party simply differs.
	$effect(() => {
		if (!drill) partyFilter = null;
	});

	const ERAS = [
		{ id: 'antes', label: t('pan.era.before'), note: t('pan.era.beforeNote') },
		{ id: 'depois', label: t('pan.era.after'), note: t('pan.era.afterNote') }
	] as const;

	// Both sides flattened to one shape. The alternative is branching the whole
	// list markup on the view, which duplicates it and makes the two drift.
	type Row = {
		key: string; label: string; kind: string | null;
		ad_pct: number | null; ad_low: number | null; ad_high: number | null;
		spread_n: number; value: number; contracts: number; scope: string; colour: string;
	};

	function rowsFor(era: string): Row[] {
		return data.parties.filter((p) => p.era === era).map((p) => ({
			key: p.party, label: partyLabel(p.party), colour: partyColour(p.party),
			kind: p.coalition ? t('mandate.coalition') : p.citizens_group ? t('mandate.citizens') : null,
			ad_pct: p.ad_pct, ad_low: p.ad_low, ad_high: p.ad_high, spread_n: p.spread_n,
			value: p.value, contracts: p.contracts,
			scope: t('pan.mandatesIn', {
				mandates: p.mandates === 1
					? t('pan.mandateOne', { n: num(p.mandates) })
					: t('pan.mandateMany', { n: num(p.mandates) }),
				municipalities: p.municipalities === 1
					? t('pan.municipalityOne', { n: num(p.municipalities) })
					: t('pan.municipalityMany', { n: num(p.municipalities) })
			})
		}));
	}

	// One scale per era, so bars are read against their own law, never across it.
	//
	// It has to cover the spread markers too, not just the averages. Scaling to
	// the highest average alone sent every range whose top exceeded it straight
	// off the end of the track: PCP-PEV averages 49% but reaches 78%.
	const scale = (era: string) => {
		const rows = rowsFor(era);
		return Math.max(10, ...rows.flatMap((r) => [r.ad_pct ?? 0, r.ad_high ?? 0]));
	};

	/** Never let rounding push a bar past its own track. */
	const clampPct = (n: number) => Math.max(0, Math.min(100, n));
</script>

<svelte:head>
	<title>{t('pan.title')} · {t('common.site')}</title>
	<meta name="description" content={t('pan.lede')} />
</svelte:head>

<Nav municipalities={[]} current={null} />

<main>
	<section class="head" use:reveal>
		<div class="wrap">
			<p class="eyebrow" data-in style="--i:0">{t('pan.eyebrow')}</p>
			<h1 class="poster" data-in style="--i:1"><span>{t('pan.title')}</span></h1>
			<p class="lede" data-in style="--i:2">{t('pan.lede')}</p>

			<div class="vtabs" role="tablist" data-in style="--i:3" aria-label={t('pan.howToCompare')}>
				{#each VIEWS as v (v.id)}
					<button type="button" role="tab" aria-selected={view === v.id}
						onclick={() => (view = v.id)}>{v.label}</button>
				{/each}
			</div>
		</div>
	</section>

	<div class="wrap">
		<!-- keyed on the view, so switching crossfades instead of cutting. The two
		     views are very different heights, so the outgoing one leaves the flow
		     immediately and only the incoming one is animated: a fade-out that
		     holds its space makes the page jump twice instead of once. -->
		{#key view}
		<div class="viewswap">
		{#if view === 'mapa'}
			<section class="era">
				<div class="maphead">
					<div>
						<nav class="crumbs" aria-label={t('common.whereAmI')}>
							<button type="button" class:on={!drill} onclick={() => (drill = null)}>
								{t('common.portugal')}
							</button>
							{#if drill}
								<span aria-hidden="true">›</span>
								<button type="button" class="on" aria-current="page">{drill}</button>
							{/if}
						</nav>
						<h2 class="sectag">{drill ?? t('pan.whoWon')}</h2>
						<p class="note">
							{#if drill}
								{t('pan.drilledNote', { n: num(rows.filter((r) => r.district === drill).length) })}
							{:else}
								{t('pan.countryNote')}
							{/if}
						</p>
					</div>
				</div>

				<div class="years" role="group" aria-label={t('pan.election')}>
					{#each data.years as y (y)}
						<button type="button" class:on={(year ?? data.years[0]) === y}
							disabled={mapBusy} onclick={() => pickYear(y)}>{y}</button>
					{/each}
				</div>

				{#if yearFailed}
					<p class="err">{t('pan.yearFailed')}</p>
				{/if}
				{#if geoError}
					<p class="none">{t('pan.mapError')}</p>
				{:else if mapOption}
					<div class="mapgrid">
					<div class="card mapcard mapframe" aria-busy={mapBusy}>
						<Chart option={mapOption} height={$narrow ? '400px' : '640px'} onpick={onMapPick}
							ariaLabel={drill
								? t('pan.mapAriaDistrict', { district: drill })
								: t('pan.mapAriaCountry')} />
					</div>
					<div class="aside">
					<div class="undermap">
						{#if drill}
							<button type="button" class="back" onclick={() => (drill = null)}>
								<span aria-hidden="true">←</span> {t('pan.seeCountry')}
							</button>
						{/if}
						<ul class="legend">
							{#each legendShown as [party, c] (party)}
								<li>
									<button type="button" class:off={partyFilter && partyFilter !== party}
										class:static={!drill}
										aria-pressed={drill ? partyFilter === party : undefined}
										disabled={!drill}
										onclick={() => (partyFilter = partyFilter === party ? null : party)}>
										<i style:background={partyColour(party)}></i>
										{partyLabel(party)}<span class="n">{num(c.n)}</span>
										{#if c.coalitions}<span class="co">{t('pan.inCoalition', { n: num(c.coalitions) })}</span>{/if}
									</button>
								</li>
							{/each}
							{#if legendRest && !legendAll}
								<li>
									<button type="button" class="clearf" onclick={() => (legendAll = true)}>
										{t('pan.showMore', { n: num(legendRest) })}
									</button>
								</li>
							{:else if legendAll && legendRest}
								<li>
									<button type="button" class="clearf" onclick={() => (legendAll = false)}>
										{t('pan.showLess')}
									</button>
								</li>
							{/if}
							{#if partyFilter}
								<li>
									<button type="button" class="clearf" onclick={() => (partyFilter = null)}>
										{t('pan.clearFilter')}
									</button>
								</li>
							{/if}
						</ul>
					</div>
					<p class="note">
						{t('pan.hoverNote', { verb: $narrow ? t('pan.hoverNarrow') : t('pan.hoverWide') })}
					</p>
					{#if drill && openable.length}
						<p class="note">
							{t('pan.withData')}
							{#each openable as o, i (o.dico)}<!--
							-->{i ? ', ' : ' '}<a href={L(`/municipio/${o.nif}`)}>{o.concelho}</a><!--
							-->{/each}.
						</p>
					{/if}
					</div>
					</div>
				{:else if geoBusy || !rows.length}
					<div class="card mapcard mapframe"><Skeleton h={$narrow ? '400px' : '640px'} /></div>
				{:else}
					<p class="none">{t('pan.noElection')}</p>
				{/if}
			</section>
		{:else}
		{#each ERAS as era (era.id)}
			{@const rows = rowsFor(era.id)}
			<section class="era">
				<h2 class="sectag">{era.label}</h2>
				<p class="note">{era.note}</p>

				{#if rows.length}
					<ul class="bars">
						{#each rows as r (r.key)}
							<li>
								<div class="row">
									<span class="name">
										<i class="dot" style:background={r.colour} aria-hidden="true"></i>{r.label}
										{#if r.kind}<i class="kind">{r.kind}</i>{/if}
									</span>
									<span class="val num">{pct(r.ad_pct)}</span>
								</div>
								<div class="track">
									<span class="fill" style:width="{clampPct((100 * (r.ad_pct ?? 0)) / scale(era.id))}%"
										style:background={r.colour}></span>
									{#if r.ad_low !== null && r.ad_high !== null && r.spread_n > 1}
										<!-- the range across mandates, drawn on the same axis -->
										<span class="range"
											style:left="{clampPct((100 * r.ad_low) / scale(era.id))}%"
											style:width="{clampPct((100 * (r.ad_high - r.ad_low)) / scale(era.id))}%"></span>
									{/if}
								</div>
								<p class="meta">
									{r.scope}
									· {eurShort(r.value)} · {num(r.contracts)} {t('common.contracts')}
									{#if r.spread_n > 1}
										· {t('pan.spread', { low: pct(r.ad_low), high: pct(r.ad_high) })}
									{:else}
										· <b>{t('pan.singleCase')}</b>{t('pan.singleCaseTail')}
									{/if}
								</p>
							</li>
						{/each}
					</ul>
				{:else}
					<p class="none">{t('pan.noEraData')}</p>
				{/if}
			</section>
		{/each}
		{/if}
		</div>
		{/key}

		<section class="warn">
			<h2>{t('pan.howToRead')}</h2>
			<p>{t('pan.read1')}</p>
			<p>{t('pan.read2')}</p>
			<p>{t('pan.read3')}</p>
		</section>
	</div>
</main>

<Footer />

<style>
	.head { padding: 2.4rem 0 1.6rem; border-bottom: 2px solid var(--ink); }
	.head h1 {
		font-size: clamp(1.9rem, 5vw, 3.2rem); margin-top: .9rem; text-wrap: balance; max-width: 20ch;
	}
	.lede { margin-top: .9rem; max-width: 62ch; font-weight: 600; color: var(--ink-soft); }

	.vtabs { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: 1.3rem; }
	.vtabs button {
		transition: background var(--t-hover) var(--ease-out), color var(--t-hover) var(--ease-out),
			transform var(--t-hover) var(--ease-out);
		font: inherit; font-size: .86rem; font-weight: 700; cursor: pointer;
		padding: .45rem .9rem; border: 2px solid var(--ink); border-radius: 999px;
		background: var(--paper); color: var(--ink-soft);
	}
	.vtabs button[aria-selected='true'] { background: var(--ink); color: var(--paper); }

	.viewswap { animation: viewin .42s cubic-bezier(.16, 1, .3, 1) both; }
	@keyframes viewin {
		from { opacity: 0; transform: translateY(10px); }
		to { opacity: 1; transform: none; }
	}
	@media (prefers-reduced-motion: reduce) { .viewswap { animation: none; } }

	.era { padding: 2rem 0 0; }

	/* the political map */
	.mapcard { padding: .4rem; margin-top: 1rem; }
	/* On a wide screen the map keeps its own width and everything that explains
	   it moves alongside, instead of the map floating in a half-empty row. */
	.mapgrid { display: grid; gap: 1.4rem; align-items: start; }
	@media (min-width: 1000px) {
		.mapgrid { grid-template-columns: minmax(0, 46rem) minmax(16rem, 1fr); }
		.aside { padding-top: 1rem; }
		.aside .undermap { margin-top: 0; }
		.aside .legend { flex-direction: column; align-items: stretch; }
	}
	.maphead { display: flex; align-items: flex-start; justify-content: space-between;
		gap: 1rem; flex-wrap: wrap; }
	.crumbs { display: flex; align-items: center; gap: .4rem; font-size: .78rem;
		font-weight: 700; color: var(--ink-faint); margin-bottom: .35rem; }
	.crumbs button {
		font: inherit; font-weight: 700; cursor: pointer;
		/* a 19px-tall target was the only way back out of a drilled district */
		padding: .5rem .2rem; margin: -.5rem -.2rem;
		background: none; border: 0; color: var(--ink-soft);
		text-decoration: underline; text-decoration-color: var(--rule);
		text-decoration-thickness: 2px; text-underline-offset: 3px;
	}
	.crumbs button:hover { color: var(--sangria); text-decoration-color: var(--sangria); }
	.crumbs button.on { color: var(--ink); text-decoration: none; cursor: default; }
	.err { margin: .6rem 0 0; font-size: .85rem; font-weight: 700; color: var(--sev-serious); }
	.undermap { display: flex; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-top: .9rem; }
	.back {
		font: inherit; font-size: .82rem; font-weight: 800; cursor: pointer; flex: none;
		padding: .45rem .9rem; border: 2px solid var(--ink); border-radius: var(--radius);
		background: var(--paper-2); box-shadow: var(--shadow-hard);
		transition: transform var(--t-hover) var(--ease-out),
			box-shadow var(--t-hover) var(--ease-out), background var(--t-hover) var(--ease-out);
	}
	.back:hover {
		background: var(--amarelo);
		transform: translate(calc(var(--lift) * -1), calc(var(--lift) * -1));
		box-shadow: var(--shadow-lift);
	}
	.back:active { transform: translate(2px, 2px); box-shadow: 0 0 0 var(--ink); transition-duration: .08s; }
	.years { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: 1.1rem; }
	.years button {
		font: inherit; font-size: .82rem; font-weight: 700; cursor: pointer;
		padding: .55rem .9rem; min-height: 2.75rem; border: 2px solid var(--ink); border-radius: 999px;
		background: var(--paper); color: var(--ink-soft);
	}
	.years button.on { background: var(--ink); color: var(--paper); }
	.years button { transition: background var(--t-hover) var(--ease-out), color var(--t-hover) var(--ease-out); }
	.years button:not(.on):hover { background: var(--amarelo); color: var(--ink); }
	.years button:disabled { opacity: .55; cursor: default; }
	/* the legend is the filter: the only way to say "just this party" that does
	   not need a second control saying the same thing twice */
	.legend { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: .4rem; }
	.legend button {
		display: flex; align-items: center; gap: .4rem; cursor: pointer;
		font: inherit; font-size: .8rem; font-weight: 700; color: var(--ink-soft);
		background: var(--paper-2); border: 2px solid var(--rule);
		border-radius: 99px; padding: .5rem .8rem .5rem .6rem; min-height: 2.75rem;
		transition: border-color var(--t-hover) var(--ease-out), opacity var(--t-hover) var(--ease-out),
			color var(--t-hover) var(--ease-out);
	}
	.legend button:hover { border-color: var(--ink); color: var(--ink); }
	.legend button[aria-pressed='true'] { border-color: var(--ink); color: var(--ink); background: var(--paper-3); }
	.legend button.off { opacity: .45; text-decoration: line-through; }
	/* on the country view the legend is a key, not a control */
	.legend button.static { cursor: default; }
	.legend button.static:hover { border-color: var(--rule); color: var(--ink-soft); }
	.legend i { width: 13px; height: 13px; border-radius: 3px; border: 1.5px solid var(--ink); flex: none; }
	.legend .n { font-variant-numeric: tabular-nums; font-weight: 800; color: var(--ink); }
	.legend .co { font-weight: 500; font-size: .72rem; color: var(--ink-faint); }
	.legend .clearf { padding: .25rem .8rem; border-style: dashed; }
	.note { margin: .3rem 0 0; font-size: .85rem; font-weight: 600; color: var(--ink-soft); }
	.none { margin-top: 1rem; color: var(--ink-faint); font-weight: 600; }

	.bars { list-style: none; margin: 1.1rem 0 0; padding: 0; display: grid; gap: 1rem; }
	.row { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; }
	.name { font-weight: 800; overflow-wrap: anywhere; }
	.kind {
		margin-left: .4rem; font-size: .62rem; font-style: normal; font-weight: 700;
		letter-spacing: .05em; text-transform: uppercase; color: var(--ink-faint);
	}
	.val { font-family: 'Bowlby One', Impact, sans-serif; font-size: 1.1rem; }

	.track {
		position: relative; height: 14px; margin-top: .3rem; overflow: hidden;
		background: rgba(156,128,120,.18); border-radius: 99px;
	}
	.fill { position: absolute; inset: 0 auto 0 0; background: var(--ink); border-radius: 99px; }
	/* the colour is the party's own, as any election-night graphic uses it */
	.dot {
		display: inline-block; width: .7rem; height: .7rem; margin-right: .45rem;
		border-radius: 50%; border: 1.5px solid var(--ink); vertical-align: baseline;
	}
	/* the range sits over the bar, so the eye reads "this is the spread" */
	.range {
		position: absolute; top: 3px; bottom: 3px;
		border-left: 2px solid var(--sangria); border-right: 2px solid var(--sangria);
		background: rgba(223,34,37,.16);
	}
	.meta { margin: .35rem 0 0; font-size: .78rem; font-weight: 600; color: var(--ink-soft); }

	.warn {
		margin: 2.6rem 0 3rem; padding: 1.2rem 1.3rem;
		border: 3px dashed var(--azulejo); border-radius: var(--radius); background: var(--paper-2);
	}
	.warn h2 { font-size: 1.1rem; color: var(--azulejo); }
	.warn p { margin-top: .7rem; max-width: 70ch; font-weight: 600; color: var(--ink-soft); }
</style>
