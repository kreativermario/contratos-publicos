<script lang="ts">
	import CompanyProfile from '$lib/components/CompanyProfile.svelte';
	import Flags from '$lib/components/Flags.svelte';
	import Backlink from '$lib/components/Backlink.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { api, type ContractRow } from '$lib/api';
	import { dateShort, eur, eurShortParts, num, pct } from '$lib/format';
	import { L, t } from '$lib/messages';
	import { untrack } from 'svelte';
	import { goto } from '$app/navigation';
	import { reveal } from '$lib/reveal';
	import { narrow } from '$lib/narrow.svelte';
	import Chart from '$lib/Chart.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import { mapKey, moneyMapOption, supplierYearsOption, type GeoFeature } from '$lib/charts';
	import echarts from '$lib/echarts';
	import { eurShort } from '$lib/format';

	let { data } = $props();

	const s = $derived(data.supplier);
	const [money, unit] = $derived(eurShortParts(s.total));

	// The share that skipped a tender, coloured by how large it is, and always
	// with the level written out beside it. Null takes no colour at all: an
	// unknown share must never borrow the green of a low one.
	const adPlate = $derived(
		s.ad_pct === null ? '' :
		s.ad_pct >= 70 ? 'plate-red' :
		s.ad_pct >= 35 ? 'plate-yellow' : 'plate-green'
	);
	const adLevel = $derived(
		s.ad_pct === null ? t('firm.adNotMeasurable') :
		s.ad_pct >= 70 ? t('firm.adAlmostAll') :
		s.ad_pct >= 35 ? t('firm.adGoodPart') : t('firm.adLittle')
	);

	/* ---- where the money came from, as a map --------------------------- */
	type View = 'mapa' | 'lista';
	let view = $state<View>('mapa');
	/** null = the country by district; a name = drilled into that district */
	let drill = $state<string | null>(null);

	let features = $state<GeoFeature[]>([]);
	let boxes = $state<Record<string, [[number, number], [number, number]]>>({});
	let geoError = $state(false);
	let geoBusy = $state(false);

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
				const out: Record<string, [[number, number], [number, number]]> = {};
				for (const f of distritos.features) {
					const box: [[number, number], [number, number]] = [[180, 90], [-180, -90]];
					walk(f.geometry?.coordinates, box);
					out[f.properties.name] = box;
				}
				boxes = out;
				features = municipios.features
					.map((f: any) => ({
						name: f.properties.name, key: f.properties.key ?? '',
						dkey: f.properties.dkey ?? '', district: f.properties.district ?? ''
					}))
					.filter((f: GeoFeature) => f.name);
			})
			.catch(() => (geoError = true))
			.finally(() => (geoBusy = false));
	});

	function walk(node: any, box: [[number, number], [number, number]]): void {
		if (!Array.isArray(node)) return;
		if (typeof node[0] === 'number' && typeof node[1] === 'number') {
			box[0][0] = Math.min(box[0][0], node[0]); box[0][1] = Math.min(box[0][1], node[1]);
			box[1][0] = Math.max(box[1][0], node[0]); box[1][1] = Math.max(box[1][1], node[1]);
			return;
		}
		for (const child of node) walk(child, box);
	}

	/** Only the câmaras whose name resolved to a territory can be drawn. */
	const yearsOption = $derived(supplierYearsOption(s.by_year ?? []));

	/** Above this the map and the list fit side by side and the toggle is noise. */
	const wide = $derived(!$narrow);

	/** The câmara this firm sold most to: the likeliest place the reader came from. */
	const topBuyer = $derived(s.by_buyer.find((b) => b.nif) ?? null);

	const placed = $derived(s.by_buyer.filter((b) => b.district && b.concelho));
	const unplaced = $derived(s.by_buyer.filter((b) => !b.district || !b.concelho));

	const areas = $derived.by(() => {
		if (!drill) {
			const byDistrict = new Map<string, { total: number; contracts: number; n: number }>();
			for (const b of placed) {
				const cur = byDistrict.get(b.district!) ?? { total: 0, contracts: 0, n: 0 };
				cur.total += b.total ?? 0;
				cur.contracts += b.contracts;
				cur.n += 1;
				byDistrict.set(b.district!, cur);
			}
			return [...byDistrict].map(([name, d]) => ({
				name,
				value: d.total,
				lines: [
					[t('firm.received'), eurShort(d.total)],
					[t('pan.tip.contracts'), num(d.contracts)],
					[t('firm.camaras'), t('firm.inDistrict', { n: num(d.n) })]
				] as [string, string][]
			}));
		}
		const byName = new Map(features.map((f) => [f.key, f]));
		return placed
			.filter((b) => b.district === drill)
			.map((b) => {
				const f = byName.get(mapKey(b.concelho!));
				return {
					name: f ? f.name : b.concelho!,
					value: b.total ?? 0,
					lines: [
						[t('firm.received'), eurShort(b.total)],
						[t('pan.tip.contracts'), num(b.contracts)],
						['', t('firm.tapForContracts')]
					] as [string, string][]
				};
			});
	});

	/**
	 * The box around the districts that actually have money in them.
	 *
	 * Fitted to the whole file, the Azores set the frame and the mainland sits
	 * in a corner of an otherwise empty card. A company that only ever sold to
	 * Lisboa should get Lisboa's neighbourhood, not the Atlantic.
	 */
	const dataBounds = $derived.by(() => {
		if (drill) return boxes[drill];
		const present = areas.map((a) => boxes[a.name]).filter(Boolean);
		if (!present.length) return undefined;
		const box: [[number, number], [number, number]] = [[180, 90], [-180, -90]];
		for (const b of present) {
			box[0][0] = Math.min(box[0][0], b[0][0]); box[0][1] = Math.min(box[0][1], b[0][1]);
			box[1][0] = Math.max(box[1][0], b[1][0]); box[1][1] = Math.max(box[1][1], b[1][1]);
		}
		// a little air, so the outermost district is not flush against the edge
		const padX = (box[1][0] - box[0][0]) * 0.12 + 0.15;
		const padY = (box[1][1] - box[0][1]) * 0.12 + 0.15;
		return [[box[0][0] - padX, box[0][1] - padY], [box[1][0] + padX, box[1][1] + padY]] as
			[[number, number], [number, number]];
	});

	const mapOption = $derived(
		features.length && areas.length
			? moneyMapOption(drill ? 'portugal' : 'pt-distritos', areas, dataBounds, $narrow)
			: null
	);

	function onMapPick(datum: any) {
		if (!datum?.name) return;
		if (!drill) {
			// Only into a district that has something in it. Drilling into one
			// with no money left `areas` empty, `mapOption` null, and the template
			// on the loading branch: a skeleton that shimmered forever.
			if (areas.some((a) => a.name === datum.name)) drill = datum.name;
			return;
		}
		const hit = placed.find((b) => {
			const f = features.find((x) => x.name === datum.name);
			return f && mapKey(b.concelho!) === f.key;
		});
		// Not the câmara's own page: the reader came here following one company,
		// so the answer is that company's contracts in that câmara.
		if (hit?.nif) {
			const q = new URLSearchParams({ tab: 'contratos', supplier: s.name ?? '' });
			goto(L(`/municipio/${hit.nif}?${q}`));
		}
	}

	const PAGE = 50;
	let rows = $state<ContractRow[]>(untrack(() => data.contracts));
	let busy = $state(false);
	let failed = $state(false);
	let done = $state(untrack(() => data.contracts.length < PAGE));

	// The same controls every other table on the site has. The endpoint already
	// takes them; only the interface was missing.
	const SORTS: Record<string, string> = {
		signed_date: t('tbl.date'),
		value: t('tbl.value'),
		object: t('tbl.object'),
		procedure: t('tbl.procedure')
	};
	let query = $state('');
	let buyerPick = $state('');
	let sort = $state('signed_date');
	let desc = $state(true);

	const buyerOptions = $derived(s.by_buyer.filter((b) => b.nif));
	const filtering = $derived(Boolean(query.trim() || buyerPick));

	function params(from: number) {
		return {
			q: query.trim() || undefined,
			buyer: buyerPick || undefined,
			sort, desc, limit: PAGE, offset: from
		};
	}

	async function fetchPage(from: number, replace: boolean) {
		if (busy) return;
		busy = true;
		failed = false;
		try {
			const page = await api<ContractRow[]>(`/suppliers/${data.nif}/contracts`, params(from));
			rows = replace ? page : [...rows, ...page];
			done = page.length < PAGE;
		} catch {
			// Not `done`. Swallowing the failure as "end of list" tells the reader
			// they have seen everything, which is the one thing it does not mean.
			failed = true;
		} finally {
			busy = false;
		}
	}

	const more = () => fetchPage(rows.length, false);

	function sortBy(key: string) {
		if (sort === key) desc = !desc;
		else { sort = key; desc = true; }
	}
	const arrow = (key: string) => (sort !== key ? '' : desc ? '▾' : '▴');

	let timer: ReturnType<typeof setTimeout> | undefined;
	let firstRun = true;
	$effect(() => {
		const key = [query.trim(), buyerPick, sort, String(desc)].join(' ');
		if (firstRun) { firstRun = false; return; }
		clearTimeout(timer);
		timer = setTimeout(() => { done = false; fetchPage(0, true); }, 250);
		return () => clearTimeout(timer);
	});
</script>

<svelte:head>
	<title>{s.name ?? data.nif} · {t('common.site')}</title>
	<meta name="description"
		content={t('firm.metaDescription', {
			name: s.name ?? data.nif, money: eur(s.total), n: num(s.contracts)
		})} />
</svelte:head>

<Nav municipalities={[]} current={null} />

<main>
	<section class="head" use:reveal>
		<div class="wrap">
			{#if topBuyer}
				<Backlink href={L(`/municipio/${topBuyer.nif}?tab=empresas`)}
					label={t('firm.backTo', { name: topBuyer.name ?? '' })}
					secondary={{ href: L('/'), label: t('firm.pickOther') }} />
			{:else}
				<Backlink href={L('/')} label={t('back.home')} />
			{/if}
			<p class="eyebrow" data-in style="--i:0">{t('firm.eyebrow')} <span class="num">{data.nif}</span></p>
			<h1 data-in style="--i:1">{s.name ?? t('firm.noName')}</h1>

			<div class="plates totals" data-in style="--i:2">
				<div class="plate plate-red lift">
					<b class="num">{money}<i class="unit">{unit}</i></b><span>{t('firm.received')}</span>
				</div>
				<div class="plate plate-blue lift">
					<b class="num">{num(s.contracts)}</b><span>{t('firm.contracts')}</span>
				</div>
				<div class="plate plate-yellow lift">
					<b class="num">{num(s.buyers)}</b><span>{s.buyers === 1 ? t('firm.camara') : t('firm.camaras')}</span>
				</div>
				<div class="plate lift {adPlate}">
					<b class="num">{pct(s.ad_pct)}</b><span>{t('firm.noTender')}</span>
					{#if adLevel}<i class="lvl">{adLevel}</i>{/if}
				</div>
			</div>

			<dl class="facts" data-in style="--i:3">
				<div><dt>{t('firm.mainSector')}</dt><dd>{s.sector}</dd></div>
				<div><dt>{t('firm.firstContract')}</dt><dd class="num">{dateShort(s.first_win)}</dd></div>
				<div><dt>{t('firm.lastContract')}</dt><dd class="num">{dateShort(s.last_win)}</dd></div>
			</dl>

			<p class="fine" data-in style="--i:4">{t('firm.scopeNote')}</p>
		</div>
	</section>

	<div class="wrap body">
		{#if yearsOption}
			<section>
				<h2 class="sectag">{t('firm.yearByYear')}</h2>
				<p class="note">{t('firm.yearByYearNote')}</p>
				<div class="card chartcard">
					<Chart option={yearsOption} height={$narrow ? '260px' : '320px'}
						ariaLabel={t('firm.yearsAria')} />
				</div>
			</section>
		{/if}

		<section>
			<h2 class="sectag">{t('firm.registry')}</h2>
			<div class="card profile-card">
				<CompanyProfile company={data.company} name={s.name ?? ''} />
			</div>
		</section>

		{#if s.by_buyer.length}
			<section>
				<div class="sechead">
					<h2 class="sectag">{t('firm.soldTo')}</h2>
					{#if !wide}
						<div class="vtoggle" role="group" aria-label={t('firm.howToView')}>
							<button type="button" class:on={view === 'mapa'}
								aria-pressed={view === 'mapa'} onclick={() => (view = 'mapa')}>{t('firm.viewMap')}</button>
							<button type="button" class:on={view === 'lista'}
								aria-pressed={view === 'lista'} onclick={() => (view = 'lista')}>{t('firm.viewList')}</button>
						</div>
					{/if}
				</div>

				<div class="sidebyside" class:mapview={view === 'mapa'}>
				{#if view === 'mapa' || wide}
					<div class="mapcol">
					<nav class="crumbs" aria-label={t('common.whereAmI')}>
						<button type="button" class:on={!drill} onclick={() => (drill = null)}>{t('common.portugal')}</button>
						{#if drill}<span aria-hidden="true">›</span>
							<button type="button" class="on" aria-current="page">{drill}</button>{/if}
					</nav>
					{#if geoError}
						<p class="nothing">{t('pan.mapError')}</p>
					{:else if mapOption}
						<div class="card mapcard mapframe">
							<Chart option={mapOption} height={$narrow ? '360px' : '520px'} onpick={onMapPick}
								ariaLabel={drill
									? t('firm.mapAriaDistrict', { district: drill })
									: t('firm.mapAriaCountry')} />
						</div>
						<p class="note">
							{drill ? t('firm.mapHintDrilled') : t('firm.mapHintCountry')}
							{t('firm.darker')}
						</p>
						{#if unplaced.length}
							<p class="fine">
								{unplaced.length === 1
									? t('firm.unplacedOne', { n: num(unplaced.length) })
									: t('firm.unplacedMany', { n: num(unplaced.length) })}
							</p>
						{/if}
					{:else if !features.length}
						<div class="card mapcard mapframe"><Skeleton h={$narrow ? '360px' : '520px'} /></div>
					{:else}
						<p class="nothing">{t('firm.noneHere')}</p>
					{/if}
					</div>
				{/if}
				{#if view === 'lista' || wide}
					<div class="listcol">
				<ul class="buyers">
					{#each s.by_buyer as b (b.nif ?? b.name)}
						{@const share = s.total ? (100 * (b.total ?? 0)) / s.total : 0}
						<li>
							<div class="row">
								<span class="name">
									{#if b.nif}<a href={L(`/municipio/${b.nif}`)}>{b.name ?? b.nif}</a>
									{:else}{b.name ?? t('common.na')}{/if}
								</span>
								<span class="val num">{eur(b.total)}</span>
							</div>
							<div class="track">
								<span class="fill" style:width="{Math.max(0, Math.min(100, share))}%"></span>
							</div>
							<p class="meta">{t('firm.shareOfIntake', { n: num(b.contracts), pct: pct(share) })}</p>
						</li>
					{/each}
				</ul>
					</div>
				{/if}
				</div>

				{#if s.by_buyer.length === 1}
					<p class="fine">{t('firm.oneBuyer')}</p>
				{/if}
			</section>
		{/if}

		<section>
			<h2 class="sectag">{t('firm.contractsTitle')}</h2>
			<p class="note">{t('firm.clickContract')}</p>

			<div class="filters">
				<label class="grow">
					<span class="eyebrow">{t('firm.searchObject')}</span>
					<input type="search" bind:value={query} placeholder={t('firm.searchPlaceholder')} />
				</label>
				{#if buyerOptions.length > 1}
					<label>
						<span class="eyebrow">{t('firm.buyer')}</span>
						<select bind:value={buyerPick}>
							<option value="">{t('common.allF')}</option>
							{#each buyerOptions as b (b.nif)}<option value={b.nif}>{b.name}</option>{/each}
						</select>
					</label>
				{/if}
				{#if filtering}
					<button class="clear lift" onclick={() => { query = ''; buyerPick = ''; }}>{t('common.clear')}</button>
				{/if}
			</div>

			<div class="msort">
				<label>
					<span class="eyebrow">{t('common.sortBy')}</span>
					<select bind:value={sort}>
						{#each Object.entries(SORTS) as [k, label] (k)}<option value={k}>{label}</option>{/each}
					</select>
				</label>
				<button type="button" onclick={() => (desc = !desc)}
					aria-label={desc ? t('common.sortDesc') : t('common.sortAsc')}>{desc ? '▾' : '▴'}</button>
			</div>

			<div class="card table-wrap" aria-busy={busy}>
				<table class="stack">
					<thead>
						<tr>
							{#each [['object', ''], ['buyer', ''], ['procedure', ''], ['value', 'r']] as [key, align] (key)}
								<th class={align}
									aria-sort={sort === key ? (desc ? 'descending' : 'ascending') : 'none'}>
									{#if SORTS[key]}
										<button type="button" onclick={() => sortBy(key)}>
											{SORTS[key]}<span class="arrow" aria-hidden="true">{arrow(key)}</span>
										</button>
									{:else}{t('firm.buyer')}{/if}
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each rows as c (c.id)}
							<tr>
								<td class="obj wide" data-label={t('tbl.object')}>
									<a href={L(`/contrato/${c.id}`)}>{c.object ?? t('common.noDescription')}</a>
									<span class="date num">{dateShort(c.signed_date)}</span>
									<Flags flags={c.flags} />
								</td>
								<td data-label={t('firm.buyer')}>
									{#if c.buyer_nif}<a href={L(`/municipio/${c.buyer_nif}`)}>{c.buyer_name ?? c.buyer_nif}</a>
									{:else}{c.buyer_name ?? t('common.na')}{/if}
								</td>
								<td data-label={t('tbl.procedure')}>
									<span class="proc" class:ad={/ajuste direto/i.test(c.procedure ?? '')}
										>{c.procedure ?? t('common.na')}</span>
								</td>
								<td class="r num money" data-label={t('tbl.value')}>{eur(c.value)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			{#if !rows.length}
				<p class="nothing">{t('firm.noContracts')}</p>
			{/if}
			<div class="more">
				{#if failed}
					<p class="err">{t('firm.moreFailed')}</p>
					<button class="lift" onclick={more} disabled={busy}>{t('common.retry')}</button>
					{:else if !done}
					<button class="lift" onclick={more} disabled={busy}>{busy ? t('common.loading') : t('common.loadMore')}</button>
					{:else if rows.length}
					<p class="fine">{t('common.endOfList')}</p>
				{/if}
			</div>
		</section>
	</div>
</main>

<Footer />

<style>
	.head { padding: 2.6rem 0 2.2rem; border-bottom: 2px solid var(--ink); }
	/* A firm name is long and arrives in whatever case the register used, so this
	   is sized to survive six words, not to shout one. */
	.head h1 {
		font-size: clamp(1.45rem, 3.6vw, 2.5rem); margin-top: .7rem;
		/* relative, and with leading to land in: at the 23px a phone clamps to,
		   a fixed 4px drop fell inside the next line's caps */
		line-height: 1.12; text-shadow: .06em .06em 0 var(--azulejo); text-wrap: balance;
		max-width: 22ch; overflow-wrap: anywhere;
	}
	.fine { margin-top: 1.2rem; font-size: .8rem; color: var(--ink-faint); max-width: 68ch; line-height: 1.5; }

	.totals { margin-top: 1.5rem; }
	.totals .num { display: inline-flex; align-items: baseline; }
	.totals .lvl {
		display: block; margin-top: .2rem; font-style: normal; font-size: .6rem;
		font-weight: 800; letter-spacing: .1em; text-transform: uppercase; opacity: .85;
	}

	/* label over value, in the body face, so the head has one display run and
	   not three competing ones */
	.facts {
		display: flex; flex-wrap: wrap; gap: .8rem 2.2rem; margin: 1.5rem 0 0;
	}
	.facts div { display: flex; flex-direction: column; gap: .15rem; }
	.facts dt {
		font-size: .62rem; font-weight: 800; letter-spacing: .12em;
		text-transform: uppercase; color: var(--ink-faint);
	}
	.facts dd { margin: 0; font-size: .95rem; font-weight: 700; }

	.body { display: grid; gap: 2.6rem; padding: 2.4rem 0 3.5rem; }

	.profile-card { margin-top: 1rem; padding-top: .8rem; }
	/* a card straight after a section label was sitting on top of it */
	.sectag + .card, .sectag + .note + .card { margin-top: .9rem; }
	.chartcard { padding: .8rem .6rem .4rem; margin-top: .9rem; }

	.sechead { display: flex; align-items: center; justify-content: space-between;
		gap: 1rem; flex-wrap: wrap; }
	.vtoggle { display: inline-flex; border: 2px solid var(--ink); border-radius: var(--radius);
		overflow: hidden; background: var(--paper-2); }
	.vtoggle button {
		border: 0; background: none; cursor: pointer; padding: .55rem .95rem;
		font-size: .82rem; font-weight: 700; color: var(--ink-soft); min-height: 2.75rem;
		transition: background var(--t-hover) var(--ease-out), color var(--t-hover) var(--ease-out);
	}
	.vtoggle button + button { border-left: 2px solid var(--ink); }
	.vtoggle button:hover { background: var(--paper-3); color: var(--ink); }
	.vtoggle button.on { background: var(--ink); color: var(--paper); }

	.mapcard { padding: .4rem; margin-top: .8rem; }
	/* The map is portrait and the card was landscape, so left-aligned it left the
	   right half of the page empty. The list goes there. */
	.sidebyside { display: grid; gap: 1.4rem; align-items: start; }
	@media (min-width: 1000px) {
		.sidebyside { grid-template-columns: minmax(0, 32rem) minmax(18rem, 1fr); }
		.listcol { padding-top: .8rem; }
	}
	.mapcol .mapframe { max-width: none; }
	.crumbs { display: flex; align-items: center; gap: .4rem; font-size: .78rem;
		font-weight: 700; color: var(--ink-faint); margin-top: .8rem; }
	.crumbs button {
		font: inherit; font-weight: 700; cursor: pointer; padding: .5rem .2rem;
		margin: -.5rem -.2rem; background: none; border: 0; color: var(--ink-soft);
		text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: .22em;
	}
	.crumbs button:hover { color: var(--sangria); }
	.crumbs button.on { color: var(--ink); text-decoration: none; cursor: default; }

	.buyers { list-style: none; margin: 1.1rem 0 0; padding: 0; display: grid; gap: 1rem; }
	.row { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; }
	.name { font-weight: 800; overflow-wrap: anywhere; }
	.name a { color: var(--ink); text-decoration-color: var(--azulejo); text-underline-offset: 2px; }
	.name a:hover { color: var(--sangria); }
	.val { font-weight: 700; white-space: nowrap; }
	.track { height: 12px; margin-top: .35rem; border: 2px solid var(--ink); border-radius: 99px;
		background: var(--paper-2); overflow: hidden; }
	.fill { display: block; height: 100%; background: var(--azulejo); }
	.meta { margin: .3rem 0 0; font-size: .78rem; color: var(--ink-faint); }

	.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: .75rem; margin: .9rem 0 .75rem; }
	.filters label { display: flex; flex-direction: column; gap: .2rem; }
	.filters .grow { flex: 1 1 18rem; }
	.filters input, .filters select {
		font: inherit; font-size: 1rem; font-weight: 600; color: var(--ink);
		background: var(--paper-2); border: 2px solid var(--ink); border-radius: var(--radius);
		padding: .38rem .7rem; max-width: 100%; height: 2.6rem;
	}
	.filters input { width: 100%; }
	.clear { border: 2px solid var(--ink); border-radius: var(--radius); background: var(--ink);
		color: var(--paper); font-weight: 700; font-size: .85rem; padding: .45rem .9rem;
		cursor: pointer; height: 2.6rem; }

	.msort { display: none; }
	@media (max-width: 820px) {
		.msort { display: flex; align-items: flex-end; gap: .5rem; margin-bottom: .75rem; }
		.msort label { display: flex; flex-direction: column; gap: .2rem; flex: 1 1 auto; min-width: 0; }
		.msort select {
			width: 100%; font: inherit; font-size: 1rem; font-weight: 600; color: var(--ink);
			background: var(--paper-2); border: 2px solid var(--ink); border-radius: var(--radius);
			padding: .38rem .7rem; min-height: 2.75rem;
		}
		.msort button {
			flex: none; cursor: pointer; font-weight: 800; font-size: 1rem;
			min-width: 3rem; min-height: 2.75rem; padding: 0 .75rem;
			color: var(--ink); background: var(--paper-2);
			border: 2px solid var(--ink); border-radius: var(--radius);
		}
		.filters label { flex: 1 1 100%; min-width: 0; }
		.filters select { width: 100%; }
	}

	thead th button {
		font: inherit; color: inherit; background: none; border: 0; padding: 0; cursor: pointer;
		text-transform: inherit; letter-spacing: inherit;
	}
	thead th button:hover { color: var(--sangria); }
	.arrow { display: inline-block; width: .9em; text-align: left; color: var(--sangria); }

	.table-wrap { overflow-x: auto; }
	table { width: 100%; border-collapse: collapse; font-size: .87rem; }
	thead th { text-align: left; font-size: .7rem; text-transform: uppercase; letter-spacing: .1em;
		color: var(--ink-faint); padding: .8rem .9rem; border-bottom: 2px solid var(--ink); white-space: nowrap; }
	thead th.r { text-align: right; }
	td { padding: .75rem .9rem; border-bottom: 1px solid var(--rule); vertical-align: top; }
	tbody tr:last-child td { border-bottom: 0; }
	tbody tr:hover { background: #fffdf3; }
	.r { text-align: right; }
	.obj a { color: var(--ink); font-weight: 600; text-decoration-color: var(--azulejo); text-underline-offset: 2px; }
	.obj a:hover { color: var(--sangria); }
	.date { display: block; font-size: .72rem; color: var(--ink-faint); margin-top: .2rem; }
	.money { font-weight: 700; }
	.proc { font-size: .78rem; border: 1.5px solid var(--rule); border-radius: 99px; padding: .12rem .5rem; }
	.proc.ad { border-color: var(--sev-critical); color: var(--sev-critical); font-weight: 700; }
	@media (min-width: 821px) { .obj { max-width: 38ch; } .money, .proc { white-space: nowrap; } }

	.nothing { padding: 2rem 1rem; text-align: center; color: var(--ink-faint); font-size: .9rem; }
	.err { margin: 0; font-size: .85rem; font-weight: 700; color: var(--sev-serious); }
	.more { display: flex; flex-direction: column; align-items: center; gap: .5rem; padding: 1.25rem 0 0; }
	.more button {
		font: inherit; font-weight: 700; font-size: .88rem; cursor: pointer;
		color: var(--ink); background: var(--paper-2); border: 2px solid var(--ink);
		border-radius: var(--radius); box-shadow: var(--shadow-hard); padding: .5rem 1.1rem;
	}
	.more button:hover:not(:disabled) { background: var(--amarelo); }
	.more button:disabled { opacity: .6; cursor: default; box-shadow: none; }
</style>
