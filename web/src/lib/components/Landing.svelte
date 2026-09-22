<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Municipality } from '$lib/api';
	import Chart from '$lib/Chart.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import { mapKey, pickerMapOption, type GeoFeature, type PickTarget } from '$lib/charts';
	import { narrow } from '$lib/narrow.svelte';
	import { reveal } from '$lib/reveal';
	import echarts from '$lib/echarts';
	import { eurShortParts, num, shortMunicipality } from '$lib/format';
	import { L, t } from '$lib/messages';

	let { municipalities = [] }: { municipalities?: Municipality[] } = $props();

	// Three ways in, because they answer different questions: "onde fica",
	// "de que distrito é" and "como se chama". None is the right one for
	// everybody, so none of them is the only one.
	const TABS = [
		{ id: 'nome', label: t('landing.tab.name') },
		{ id: 'distrito', label: t('landing.tab.district') },
		{ id: 'mapa', label: t('landing.tab.map') }
	] as const;
	type TabId = (typeof TABS)[number]['id'];
	let tab = $state<TabId>('nome');

	const short = (m: Municipality) => shortMunicipality(m.name ?? '') || m.nif;

	// Totals for the hero, summed from the municipality rows so the page states
	// only what it can actually count. No supplier total: the same firm works for
	// several câmaras, so adding the per-município counts would overstate it.
	const totalValue = $derived(municipalities.reduce((s, m) => s + (m.total ?? 0), 0));
	const totalContracts = $derived(municipalities.reduce((s, m) => s + m.contracts, 0));
	const gastos = $derived(eurShortParts(totalValue));
	const period = $derived.by(() => {
		const years = municipalities
			.flatMap((m) => [m.since, m.latest])
			.filter(Boolean)
			.map((d) => new Date(d as string).getFullYear())
			.filter((y) => Number.isFinite(y));
		if (!years.length) return null;
		const lo = Math.min(...years), hi = Math.max(...years);
		return { lo, hi };
	});

	// One message with a {link} hole, so a translator can put the link wherever
	// the sentence needs it. `{@const}` is only legal as a block's direct child,
	// hence a derived rather than an inline split in the markup.
	const crossTo = $derived(t('landing.crossTo').split('{link}'));

	function open(nif: string) {
		goto(L(`/municipio/${encodeURIComponent(nif)}`));
	}

	/* ---- pelo nome ---------------------------------------------------- */
	let q = $state('');
	const fold = (s: string) =>
		s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
	const found = $derived.by(() => {
		const term = fold(q.trim());
		const rows = term
			? municipalities.filter((m) => fold(short(m)).includes(term))
			: municipalities;
		return [...rows].sort((a, b) => (b.total ?? 0) - (a.total ?? 0));
	});

	/* ---- geometry: only the two tabs that need it pay for it ----------- */
	let features = $state<GeoFeature[]>([]);
	let geoError = $state(false);
	let geoBusy = $state(false);
	$effect(() => {
		if ((tab !== 'mapa' && tab !== 'distrito') || features.length || geoBusy || geoError) return;
		geoBusy = true;
		// Both geometries: the map opens on the districts and drills into the
		// concelhos, the same way the panorama and the company maps do. 308 shapes
		// at country scale is a wall nobody can aim at.
		Promise.all([
			fetch('/pt-distritos.geojson').then((r) => r.json()),
			fetch('/pt-municipios.geojson').then((r) => r.json())
		])
			.then(([distritos, municipios]) => {
				echarts.registerMap('pt-distritos', distritos);
				echarts.registerMap('portugal', municipios);
				const out: Record<string, [[number, number], [number, number]]> = {};
				for (const f of distritos.features) {
					const box: [[number, number], [number, number]] = [[180, 90], [-180, -90]];
					walkCoords(f.geometry?.coordinates, box);
					out[f.properties.name] = box;
				}
				boxes = out;
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

	// The geometry carries the district for all 308 concelhos; the contract data
	// carries none. This join is the only place the two meet.
	const targets = $derived<PickTarget[]>(
		municipalities.map((m) => ({
			key: mapKey(short(m)), nif: m.nif, name: short(m), contracts: m.contracts
		}))
	);
	const districtOf = $derived.by(() => {
		const byKey = new Map(features.map((f: any) => [f.key, f.district as string]));
		return (m: Municipality) => byKey.get(mapKey(short(m))) ?? null;
	});

	/* ---- por distrito --------------------------------------------------- */
	let district = $state('');
	const districts = $derived.by(() => {
		const names = new Set<string>();
		for (const m of municipalities) {
			const d = districtOf(m);
			if (d) names.add(d);
		}
		return [...names].sort((a, b) => a.localeCompare(b, 'pt-PT'));
	});
	const inDistrict = $derived(
		municipalities.filter((m) => districtOf(m) === district)
	);

	/* ---- no mapa -------------------------------------------------------- */
	let boxes = $state<Record<string, [[number, number], [number, number]]>>({});
	/** null = the country by district; a name = drilled into that district */
	let mapDrill = $state<string | null>(null);

	function walkCoords(node: any, box: [[number, number], [number, number]]): void {
		if (!Array.isArray(node)) return;
		if (typeof node[0] === 'number' && typeof node[1] === 'number') {
			box[0][0] = Math.min(box[0][0], node[0]); box[0][1] = Math.min(box[0][1], node[1]);
			box[1][0] = Math.max(box[1][0], node[0]); box[1][1] = Math.max(box[1][1], node[1]);
			return;
		}
		for (const child of node) walkCoords(child, box);
	}

	/** How many loaded municípios each district holds, for the country view. */
	const districtTargets = $derived<PickTarget[]>(
		districts.map((d) => {
			const inside = municipalities.filter((m) => districtOf(m) === d);
			return {
				key: mapKey(d), nif: '', name: d,
				contracts: inside.reduce((a, m) => a + (m.contracts ?? 0), 0)
			};
		})
	);

	const districtFeatures = $derived<GeoFeature[]>(
		[...new Set(features.map((f) => f.district))]
			.filter(Boolean)
			.map((d) => ({ name: d as string, key: mapKey(d as string), dkey: '', district: d as string }))
	);

	const map = $derived(
		!features.length
			? null
			: mapDrill
				? pickerMapOption('portugal', features.filter((f) => f.district === mapDrill),
					targets, $narrow, boxes[mapDrill])
				: pickerMapOption('pt-distritos', districtFeatures, districtTargets, $narrow)
	);

	function pickRegion(d: any) {
		if (!mapDrill) {
			// the country view's areas are districts; only open one that has
			// something loaded in it
			if (d?.name && districts.includes(d.name)) mapDrill = d.name;
			return;
		}
		if (d?.nif) open(d.nif);
	}
</script>

<section class="hero" use:reveal>
	<div class="wrap">
		<p class="eyebrow" data-in style="--i:0">{t('landing.eyebrow')}</p>
		<h1 class="poster" data-in style="--i:1"><span>{t('landing.title')}</span></h1>
		<p class="sub" data-in style="--i:2">{t('landing.sub')}</p>
		<!-- English only: the register's own words stay Portuguese, and a reader
		     who does not know that reads a half-translated page as a bug. -->
		{#if t('common.verbatim')}
			<p class="verbatim" data-in style="--i:2">{t('common.verbatim')}</p>
		{/if}

		{#if municipalities.length}
			<div class="plates stats" data-in style="--i:3">
				<div class="plate plate-red lift">
					<b class="num">{gastos[0]}<i class="unit">{gastos[1]}</i></b><span>{t('landing.awarded')}</span>
				</div>
				<div class="plate plate-blue lift">
					<b class="num">{num(totalContracts)}</b><span>{t('landing.contracts')}</span>
				</div>
				<div class="plate plate-yellow lift">
					<b class="num">{num(municipalities.length)}</b><span>{t('landing.municipalities')}</span>
				</div>
				{#if period}
					<div class="plate plate-green lift">
						<b class="num">{period.lo}</b><span>{t('landing.to', { year: period.hi })}</span>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</section>

<section class="wrap">
	<p class="crossto">
		{crossTo[0]}<a href={L('/panorama')}>{t('landing.crossToLink')}</a>{crossTo[1] ?? ''}
	</p>

	<div class="picker card">
		<header>
			<h2 class="sectag">{t('landing.pickTitle')}</h2>
			<p>{t('landing.pickSub')}</p>
		</header>

		<div class="ptabs" role="tablist" aria-label={t('landing.howToPick')}>
			{#each TABS as t (t.id)}
				<button type="button" role="tab" id="pt-{t.id}" aria-controls="pp-{t.id}"
					aria-selected={tab === t.id} onclick={() => (tab = t.id)}>{t.label}</button>
			{/each}
		</div>

		{#if tab === 'nome'}
			<div class="ppanel" role="tabpanel" id="pp-nome" aria-labelledby="pt-nome">
				<label class="find">
					<span class="sr">{t('landing.search')}</span>
					<input type="search" bind:value={q} placeholder={t('landing.searchPlaceholder')} autocomplete="off" />
				</label>
				{#if found.length}
					<ul class="grid">
						{#each found as m (m.nif)}
							<li><button type="button" class="mcard lift" onclick={() => open(m.nif)}>
								<b>{short(m)}</b>
								<span>{num(m.contracts)} {t('common.contracts')}</span>
							</button></li>
						{/each}
					</ul>
				{:else}
					<p class="none">{t('landing.noMatch')}</p>
				{/if}
			</div>
		{:else if tab === 'distrito'}
			<div class="ppanel" role="tabpanel" id="pp-distrito" aria-labelledby="pt-distrito">
				{#if geoBusy}
					<Skeleton h="3rem" />
				{:else if geoError}
					<p class="none">{t('landing.noDistricts')}</p>
				{:else}
					<div class="fields">
						<label>
							<span class="lbl">{t('landing.district')}</span>
							<select bind:value={district}>
								<option value="">{t('landing.choose')}</option>
								{#each districts as d (d)}<option value={d}>{d}</option>{/each}
							</select>
						</label>
					</div>
					{#if district}
						<ul class="grid">
							{#each inDistrict as m (m.nif)}
								<li><button type="button" class="mcard lift" onclick={() => open(m.nif)}>
									<b>{short(m)}</b>
									<span>{num(m.contracts)} {t('common.contracts')}</span>
								</button></li>
							{/each}
						</ul>
					{:else}
						<p class="none">{t('landing.pickDistrict')}</p>
					{/if}
				{/if}
			</div>
		{:else}
			<div class="ppanel" role="tabpanel" id="pp-mapa" aria-labelledby="pt-mapa">
				<p class="hint">
					{mapDrill ? t('landing.hintDrilled') : t('landing.hintCountry')}
				</p>
				{#if mapDrill}
					<nav class="crumbs" aria-label={t('common.whereAmI')}>
						<button type="button" onclick={() => (mapDrill = null)}>{t('common.portugal')}</button>
						<span aria-hidden="true">›</span>
						<b>{mapDrill}</b>
					</nav>
				{/if}
				{#if geoError}
					<p class="none">{t('landing.noMap')}</p>
				{:else if map}
					<Chart option={map} height={$narrow ? '380px' : '560px'} onpick={pickRegion}
						ariaLabel={mapDrill
							? t('landing.mapAriaDistrict', { district: mapDrill })
							: t('landing.mapAriaCountry')} />
				{:else}
					<Skeleton h={$narrow ? '380px' : '560px'} />
				{/if}
			</div>
		{/if}
	</div>
</section>

<style>
	.sr {
		position: absolute; width: 1px; height: 1px;
		overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
	}
	.crumbs { display: flex; align-items: center; gap: .4rem; font-size: .8rem;
		font-weight: 700; color: var(--ink-faint); margin: 0 0 .7rem; }
	.crumbs button {
		font: inherit; font-weight: 700; cursor: pointer; padding: .4rem .2rem;
		margin: -.4rem -.2rem; background: none; border: 0; color: var(--ink-soft);
		text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: .22em;
	}
	.crumbs button:hover { color: var(--sangria); }
	.crumbs b { color: var(--ink); }

	.hero { padding: 3rem 0 2.2rem; border-bottom: 2px solid var(--ink); }
	.hero h1 {
		font-size: clamp(1.8rem, 5.6vw, 3.6rem);
		margin-top: 1.1rem; max-width: 18ch;
	}
	.sub {
		margin-top: 1.1rem; max-width: 56ch;
		font-size: clamp(1.02rem, 2.2vw, 1.3rem); font-weight: 600; color: var(--ink-soft);
	}
	.stats {
		display: flex; flex-wrap: wrap; gap: 1.4rem 2.4rem;
		margin-top: 1.9rem; padding-top: 1.3rem; border-top: 2px solid var(--ink);
	}

	/* No colour here. The plate decides it: on the red, blue and green fills the
	   label has to be cream, and a scoped rule saying ink-soft outranks the
	   shared one and painted it dark-on-red. */
	.stats div > span {
		font-size: .74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
	}
	.stats .unit {
		/* inherit, not ink-soft: on the red plate that measured 1.63:1, and the
		   plate already knows what colour its own text has to be */
		color: inherit;
		font-family: 'Archivo', sans-serif; font-weight: 800; font-size: .55em;
		margin-left: .5em; font-style: normal;
	}

	.crossto { margin: 1.4rem 0 0; font-weight: 600; color: var(--ink-soft); }
	.verbatim { margin-top: .9rem; max-width: 58ch; font-size: .85rem; color: var(--ink-faint); }
	.picker { margin: 1rem 0 3rem; padding: 0; overflow: visible; }
	.picker > header {
		display: flex; flex-wrap: wrap; gap: .4rem 1rem;
		align-items: baseline; justify-content: space-between;
		padding: .95rem 1.1rem; background: var(--ink); color: var(--paper);
		border-radius: calc(var(--radius) - 2px) calc(var(--radius) - 2px) 0 0;
	}
	/* no colour: the header's ink ground used to pass cream into the yellow
	   .sectag, which read at 1.40:1 */
	.picker > header h2 { font-size: 1.1rem; }
	.picker > header p {
		margin: 0; font-size: .74rem; font-weight: 700; letter-spacing: .06em;
		text-transform: uppercase; color: var(--amarelo);
	}

	.ptabs { display: flex; flex-wrap: wrap; gap: .3rem; padding: .7rem 1.1rem 0; border-bottom: 2px solid var(--ink); }
	.ptabs button {
		font: inherit; font-size: .86rem; font-weight: 700; cursor: pointer;
		padding: .45rem .9rem; position: relative; top: 2px;
		border: 2px solid var(--ink); border-bottom: 0;
		border-radius: var(--radius) var(--radius) 0 0;
		background: var(--paper); color: var(--ink-soft);
	}
	.ptabs button[aria-selected='true'] { background: var(--ink); color: var(--paper); }

	.ppanel { padding: 1.2rem 1.1rem 1.4rem; }
	.hint { margin: 0 0 .9rem; font-size: .85rem; font-weight: 600; color: var(--ink-soft); }
	.none { margin: .9rem 0 0; font-weight: 600; color: var(--ink-faint); }

	.find input::placeholder { color: var(--ink-soft); opacity: 1; }
	.find input, .fields select {
		font: inherit; font-size: 1rem; font-weight: 600; padding: .5rem .65rem;
		/* not a vw floor: the box sits inside a bordered, padded panel inside
		   .wrap, so 82vw is wider than the space it actually has */
		min-width: 0; width: 100%; max-width: 24rem;
		border: 2px solid var(--ink); border-radius: var(--radius);
		background: var(--paper); color: var(--ink);
	}
	.fields label { display: flex; flex-direction: column; gap: .3rem; }
	.lbl { font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-soft); }

	.grid {
		list-style: none; margin: 1rem 0 0; padding: 0; display: grid;
		grid-template-columns: repeat(auto-fill, minmax(215px, 1fr));
		/* equal rows plus a stretching button, so a two-line name does not make
		   its card taller than its neighbours */
		grid-auto-rows: 1fr; gap: .5rem;
	}
	.grid li { margin: 0; display: flex; }
	.mcard {
		flex: 1; display: flex; flex-direction: column; justify-content: center; gap: .1rem;
		text-align: left; font: inherit; cursor: pointer; padding: .6rem .75rem;
		border: 2px solid var(--ink); border-radius: var(--radius);
		background: var(--paper); color: var(--ink);
	}
	.mcard:hover { background: var(--amarelo); }
	.mcard b { font-family: 'Bowlby One', 'Archivo Black', Impact, sans-serif; font-weight: 400; font-size: 1.02rem; text-transform: uppercase; }
	.mcard span { font-size: .76rem; font-weight: 600; color: var(--ink-soft); }

	@media (max-width: 640px) {
		.hero { padding: 2rem 0 1.6rem; }
		.stats { gap: 1rem 1.6rem; }
	}
</style>
