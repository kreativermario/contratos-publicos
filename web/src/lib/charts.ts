import type { ContractRow, MapCell, StatRow, Supplier } from './api';
import { DISPLAY, FONT, INK, INK_SOFT, RULE, tooltipBase } from './echarts';
import { novaSentence, eur, eurShort, num, pct, shortMunicipality } from './format';
import { t } from './messages';

/** Severity steps, reused by graph nodes so colour means the same thing everywhere. */
const SEV = ['#0a6e3a', '#a06a00', '#d4530b', '#c1121f'];
const SEQ = ['#fde8d8', '#f9c2a5', '#ef8f6e', '#dd5340', '#bb2026', '#7d0a17'];

function adColour(adPct: number | null): string {
	const v = adPct ?? 0;
	if (v >= 75) return SEV[3];
	if (v >= 40) return SEV[2];
	if (v > 0) return SEV[1];
	return SEV[0];
}

/**
 * Panning on touch.
 *
 * `roam: true` captures a one-finger drag, and these charts are 560 to 640px
 * tall: on a phone a reader who lands inside one has no page left to swipe on
 * and simply cannot scroll past it. 'scale' keeps pinch-zoom and lets the drag
 * fall through to the document.
 */
export const roamMode = (narrow: boolean): boolean | 'scale' => (narrow ? 'scale' : true);

/**
 * The mainland's own box.
 *
 * Every geometry file here spans the Azores, twenty-five degrees of longitude
 * west of Lisbon, so a map fitted to the whole file squeezes the mainland into
 * a strip and leaves most of a portrait card empty: on a phone the tappable
 * geometry became a band a few dozen pixels wide. The mainland is what a thumb
 * can actually hit; the islands stay reachable by pinching out, and each has
 * its own district to drill into.
 */
export const MAINLAND: [[number, number], [number, number]] = [[-9.8, 36.8], [-6.0, 42.25]];

const esc = (s: string) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]!);

/**
 * Money on a map, by area, drillable.
 *
 * Piecewise rather than a continuous ramp: with one big buyer and a long tail,
 * a linear scale puts every small area within a percent of the floor and the
 * ramp encodes nothing. Quantile-ish breaks separate them.
 */
export function moneyMapOption(
	mapName: string,
	areas: { name: string; value: number; lines: [string, string][] }[],
	bounds?: [[number, number], [number, number]],
	narrow = false
) {
	if (!areas.length) return null;
	const values = areas.map((a) => a.value).filter((v) => v > 0).sort((a, b) => a - b);
	const at = (q: number) => values[Math.min(values.length - 1, Math.floor(q * values.length))] || 0;
	const breaks = [...new Set([at(0.25), at(0.5), at(0.75), at(0.9)])].filter((v) => v > 0);

	return {
		tooltip: {
			...tooltipBase,
			formatter: (p: any) => {
				const tip = p.data?.tip;
				if (!tip) return `<b>${esc(p.name)}</b><br><span style="color:#9c8078">${esc(t('chart.noContracts'))}</span>`;
				const rows = tip
					.map(([k, v]: [string, string]) =>
						`<div style="display:flex;gap:1.1rem;justify-content:space-between">` +
						`<span style="color:#6b4a44">${esc(k)}</span><b>${esc(v)}</b></div>`)
					.join('');
				return `<b>${esc(p.name)}</b><div style="margin-top:.35rem;min-width:10rem">${rows}</div>`;
			}
		},
		visualMap: {
			type: 'piecewise',
			pieces: [
				...breaks.map((b, i) => ({
					min: i === 0 ? 0.01 : breaks[i - 1],
					max: b,
					color: ['#fde8d8', '#f9c2a5', '#ef8f6e', '#dd5340'][i] ?? '#bb2026',
					label: t('chart.upTo', { value: eurShort(b) })
				})),
				{
					min: breaks[breaks.length - 1] ?? 0.01,
					color: '#7d0a17',
					label: t('chart.moreThan', { value: eurShort(breaks[breaks.length - 1] ?? 0) })
				}
			],
			// swatches with no words are a colour ramp nobody can read
			showLabel: true,
			itemWidth: 13,
			itemHeight: 11,
			itemGap: 4,
			left: 10,
			bottom: 10,
			textStyle: { fontFamily: FONT, fontSize: 11, color: INK_SOFT }
		},
		series: [{
			type: 'map',
			map: mapName,
			roam: roamMode(narrow),
			scaleLimit: { min: 1, max: 12 },
			layoutCenter: ['50%', '50%'],
			layoutSize: '96%',
			...(bounds ? { boundingCoords: bounds } : narrow ? { boundingCoords: MAINLAND } : {}),
			label: { show: false },
			emphasis: { label: { show: false }, itemStyle: { areaColor: INK } },
			select: { disabled: true },
			itemStyle: { areaColor: 'rgba(156,128,120,.14)', borderColor: '#fff5d8', borderWidth: .6 },
			data: areas.map((a) => ({ name: a.name, value: a.value, tip: a.lines }))
		}]
	};
}

/**
 * A firm's year-by-year take, with the share that skipped a tender on top.
 *
 * Columns rather than a line: the years are discrete and a firm can miss one
 * entirely, which a line would draw straight through as if it had been there.
 */
export function supplierYearsOption(
	years: { label: number; total: number; contracts: number; ad_pct: number | null }[]
) {
	if (years.length < 2) return null;
	return {
		grid: { left: 8, right: 8, top: 24, bottom: 4, containLabel: true },
		tooltip: {
			...tooltipBase,
			trigger: 'axis',
			formatter: (ps: any) => {
				const y = years[ps[0].dataIndex];
				return `<b>${y.label}</b><br>${eur(y.total)} · ${esc(t('chart.nContracts', { n: num(y.contracts) }))}<br>` +
					esc(t('chart.byDirectAward', { pct: pct(y.ad_pct) }));
			}
		},
		xAxis: {
			type: 'category',
			data: years.map((y) => String(y.label)),
			axisTick: { show: false },
			axisLine: { lineStyle: { color: RULE } },
			axisLabel: { color: INK_SOFT, fontFamily: FONT, fontSize: 11 }
		},
		yAxis: {
			type: 'value',
			splitLine: { lineStyle: { color: RULE, type: 'dashed' } },
			axisLabel: { color: INK_SOFT, fontFamily: FONT, fontSize: 11,
				formatter: (v: number) => eurShort(v) }
		},
		series: [{
			type: 'bar',
			data: years.map((y) => ({
				value: y.total,
				// the same ramp the supplier bars use, so "mostly ajuste direto"
				// looks the same wherever it appears
				itemStyle: { color: adColour(y.ad_pct), borderRadius: [4, 4, 0, 0] }
			})),
			barMaxWidth: 46
		}]
	};
}

/** Validated categorical hues, fixed order, never cycled. Beyond five, "Outros". */
export const CATEGORICAL = ['#c1121f', '#0077b6', '#a06a00', '#8e3bb0', '#0a6e3a'];
const OUTROS_COLOUR = '#8a7a6d';

export type Category = { name: string; colour: string };

/** The five sectors holding the most money here, plus a catch-all. */
export function sectorCategories(suppliers: Supplier[]): Category[] {
	const bySector = new Map<string, number>();
	for (const s of suppliers) {
		bySector.set(s.sector, (bySector.get(s.sector) ?? 0) + (s.total ?? 0));
	}
	const top = [...bySector].sort((a, b) => b[1] - a[1]).slice(0, CATEGORICAL.length);
	const cats = top.map(([name], i) => ({ name, colour: CATEGORICAL[i] }));
	if (bySector.size > CATEGORICAL.length) cats.push({ name: t('chart.other'), colour: OUTROS_COLOUR });
	return cats;
}

/**
 * Which legend entry a supplier belongs to. Sectors outside the top five fall
 * into "Outros", exactly as the graph groups them, so the legend can filter on
 * the same rule the colours use.
 */
export function categoryNameOf(sector: string, categories: Category[]): string {
	return categories.some((c) => c.name === sector) ? sector : t('chart.other');
}

/**
 * Money graph: buyer at the centre, one edge per supplier, grouped by sector.
 *
 * The clutter fix is entirely about labels. Every node labelled at once is an
 * unreadable hairball, so only the `labelTop` biggest carry a permanent label;
 * the rest surface on hover via emphasis focus.
 */
export function graphOption(
	buyer: string,
	suppliers: Supplier[],
	categories: Category[],
	labelTop = 6,
	narrow = false
) {
	if (!suppliers.length) return null;
	const max = Math.max(...suppliers.map((s) => s.total ?? 0)) || 1;
	const cut = [...suppliers].sort((a, b) => (b.total ?? 0) - (a.total ?? 0))[labelTop - 1]?.total ?? 0;

	const index = new Map(categories.map((c, i) => [c.name, i]));
	const outros = index.get(t('chart.other')) ?? 0;
	const catOf = (sector: string) => index.get(sector) ?? outros;

	const nodes = [
		{
			name: buyer,
			value: 0,
			category: undefined,
			isBuyer: true,
			symbolSize: 62,
			itemStyle: { color: INK, borderColor: '#f6ce00', borderWidth: 3 },
			label: {
				show: true, position: 'bottom', distance: 10,
				fontFamily: DISPLAY, fontSize: 13, color: INK,
				formatter: () => shortMunicipality(buyer).toUpperCase()
			}
		},
		...suppliers.map((s) => ({
			name: s.name,
			value: s.total ?? 0,
			category: catOf(s.sector),
			contracts: s.contracts,
			adPct: s.ad_pct,
			sector: s.sector,
			nif: s.nif,
			newcomer: s.newcomer,
			debutDays: s.debut_days,
			firstSeen: s.first_seen,
			// a diamond, not a tint: novelty must not be carried by colour alone
			symbol: s.newcomer ? 'diamond' : 'circle',
			symbolSize: 9 + 40 * Math.sqrt((s.total ?? 0) / max),
			itemStyle: { borderColor: '#fffcef', borderWidth: 1.5 },
			label: {
				show: (s.total ?? 0) >= cut && cut > 0,
				position: 'right', fontFamily: FONT, fontSize: 11, color: INK_SOFT,
				formatter: (p: any) => (p.name.length > 26 ? p.name.slice(0, 24) + '…' : p.name)
			}
		}))
	];

	return {
		tooltip: {
			...tooltipBase,
			formatter: (p: any) => {
				if (p.dataType === 'edge') return '';
				const d = p.data;
				if (d.isBuyer) return `<b>${esc(d.name)}</b><br>${esc(t('chart.buyer'))}`;
				const nova = d.newcomer
					? `<br><b style="color:#c1121f">${esc(t('chart.newHere'))}</b>: ` +
					  esc(novaSentence(d.firstSeen, d.debutDays))
					: '';
				return `<b>${esc(d.name)}</b><br>` +
					`<span style="color:#6b4a44">${esc(d.sector)}</span><br>` +
					`${eur(d.value)} · ${esc(t('chart.nContracts', { n: num(d.contracts) }))}<br>` +
					esc(t('chart.byDirectAward', { pct: pct(d.adPct) })) + nova +
					`<br><span style="color:#9c8078">${esc(t('chart.clickForContracts'))}</span>`;
			}
		},
		// No canvas legend. tooltipBase sets confine:true so a tooltip near the
		// bottom of the graph is pinned inside the chart and lands squarely on
		// the legend strip, which is what made this look broken. The legend is
		// HTML under the chart instead, where it can also explain the symbols.
		animationDuration: 600,
		series: [{
			type: 'graph',
			layout: 'force',
			// Same as the maps: at full roam a 420px canvas on a 4600px page eats
			// the finger and the reader cannot scroll past it.
			roam: roamMode(narrow),
			// Unbounded, a scroll or a pinch shrinks the whole graph to a speck
			// with no way back except reloading the page.
			scaleLimit: { min: 0.7, max: 5 },
			draggable: true,
			// the legend moved to HTML, so the force field gets the height back
			top: 16, bottom: 16, left: 24, right: 24,
			categories: categories.map((c) => ({ name: c.name, itemStyle: { color: c.colour } })),
			// Long edges and hard repulsion are what stop the hairball, but the same
			// numbers in a 322px box throw most of the nodes off the canvas.
			//
			// layoutAnimation off: the default animates every step of the
			// simulation, and with friction this low the nodes drift for seconds
			// before they settle, which reads as the tab still loading rather
			// than as a flourish. Off, ECharts solves the layout and paints it
			// settled. At forty nodes that costs nothing measurable, and it is
			// the right answer for prefers-reduced-motion anyway.
			force: {
				layoutAnimation: false,
				...(narrow
					? { repulsion: 120, edgeLength: [24, 70], gravity: 0.22, friction: 0.22 }
					: { repulsion: 420, edgeLength: [70, 240], gravity: 0.06, friction: 0.18 })
			},
			// labels that overprint each other read as a smear; ECharts can just
			// drop the ones that would collide
			labelLayout: { hideOverlap: true },
			emphasis: {
				focus: 'adjacency',
				label: { show: true, fontWeight: 700, color: INK },
				itemStyle: { borderColor: INK, borderWidth: 2 }
			},
			blur: { itemStyle: { opacity: 0.18 }, label: { opacity: 0.1 } },
			data: nodes,
			edges: suppliers.map((s) => ({
				source: buyer,
				target: s.name,
				value: s.total,
				lineStyle: {
					width: 0.6 + 5 * ((s.total ?? 0) / max),
					color: categories[catOf(s.sector)]?.colour ?? OUTROS_COLOUR,
					opacity: 0.28,
					curveness: 0.12
				}
			}))
		}]
	};
}

/**
 * The same ranking, cut a different way: by sector or by procedure instead of
 * by firm. Fewer bars and no ajuste-direto shading, because the severity scale
 * belongs to a supplier, not to a whole category.
 */
export function statBarOption(rows: StatRow[], top = 10) {
	const list = [...rows]
		.filter((r) => (r.total ?? 0) > 0)
		.sort((a, b) => (b.total ?? 0) - (a.total ?? 0))
		.slice(0, top)
		.reverse();
	if (!list.length) return null;
	const grand = rows.reduce((acc, r) => acc + (r.total ?? 0), 0) || 1;
	const label = (r: StatRow) => String(r.label ?? t('common.na'));

	return {
		grid: { left: 4, right: 88, top: 8, bottom: 8, containLabel: true },
		tooltip: {
			...tooltipBase,
			formatter: (p: any) => {
				const r = list[p.dataIndex];
				return `<b>${esc(label(r))}</b><br>${eur(r.total)} · ${esc(t('chart.nContracts', { n: num(r.contracts) }))}<br>` +
					esc(t('chart.ofAllMoney', { pct: pct((100 * (r.total ?? 0)) / grand) }));
			}
		},
		xAxis: { type: 'value', show: false },
		yAxis: {
			type: 'category',
			data: list.map((r) => (label(r).length > 34 ? label(r).slice(0, 32) + '\u2026' : label(r))),
			axisLine: { show: false },
			axisTick: { show: false },
			axisLabel: { color: INK_SOFT, fontFamily: FONT, fontSize: 12 }
		},
		series: [{
			type: 'bar',
			// fixed order, never cycled; past the fifth everything shares the catch-all
			data: list.map((r, i) => ({
				value: r.total ?? 0,
				// the untruncated label, so a click can hand it to the contracts filter
				name: label(r),
				itemStyle: {
					color: CATEGORICAL[list.length - 1 - i] ?? OUTROS_COLOUR,
					borderRadius: [0, 4, 4, 0],
					cursor: 'pointer'
				}
			})),
			barWidth: 14,
			label: {
				show: true, position: 'right', distance: 8,
				fontFamily: FONT, fontSize: 12, fontWeight: 600, color: INK,
				formatter: (p: any) => eurShort(p.value)
			}
		}]
	};
}

/** Ranking is a bar chart's job, not a force graph's. */
export function topSuppliersOption(suppliers: Supplier[], top = 10) {
	const rows = [...suppliers].sort((a, b) => (b.total ?? 0) - (a.total ?? 0)).slice(0, top).reverse();
	if (!rows.length) return null;
	return {
		grid: { left: 4, right: 88, top: 8, bottom: 8, containLabel: true },
		tooltip: {
			...tooltipBase,
			formatter: (p: any) => {
				const s = rows[p.dataIndex];
				return `<b>${esc(s.name)}</b><br>${eur(s.total)} · ${esc(t('chart.nContracts', { n: num(s.contracts) }))}<br>` +
					esc(t('chart.byDirectAward', { pct: pct(s.ad_pct) }));
			}
		},
		xAxis: { type: 'value', show: false },
		yAxis: {
			type: 'category',
			data: rows.map((s) => (s.name.length > 34 ? s.name.slice(0, 32) + '…' : s.name)),
			axisLine: { show: false },
			axisTick: { show: false },
			axisLabel: { color: INK_SOFT, fontFamily: FONT, fontSize: 12 }
		},
		series: [{
			type: 'bar',
			data: rows.map((s) => ({
				value: s.total ?? 0,
				// carried so a click can open the firm rather than dead-ending on a bar
				nif: s.nif,
				name: s.name,
				itemStyle: { color: adColour(s.ad_pct), borderRadius: [0, 4, 4, 0], cursor: 'pointer' }
			})),
			barWidth: 14,
			label: {
				show: true, position: 'right', distance: 8,
				fontFamily: FONT, fontSize: 12, fontWeight: 600, color: INK,
				formatter: (p: any) => eurShort(p.value)
			}
		}]
	};
}

/** Accent- and case-insensitive, so a join can never fail on "de" vs "De". */
/** Normalised join key: accents stripped, uppercased. Matches the geometry's own `key`. */
export const mapKey = (s: string) =>
	(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim();

export type PickTarget = { key: string; nif: string; name: string; contracts: number };

/**
 * The landing map: every concelho drawn, only the loaded ones clickable.
 *
 * Not a choropleth. This one answers "where do I live", so the fill is binary,
 * loaded or not, and the shading of amounts would only compete with that.
 * `roam` gives wheel zoom and drag pan for free, which is the whole reason this
 * is an ECharts map rather than hand-rolled SVG.
 */
export function pickerMapOption(mapName: string, features: GeoFeature[], targets: PickTarget[],
	narrow = false, bounds?: [[number, number], [number, number]]) {
	const byKey = new Map(targets.map((t) => [t.key, t]));
	const data = features.map((f) => {
		const hit = byKey.get(f.key);
		return {
			name: f.name,
			value: hit ? hit.contracts : 0,
			nif: hit ? hit.nif : null,
			label: hit ? hit.name : f.name,
			itemStyle: hit
				? { areaColor: '#c1121f', borderColor: '#fffcef', borderWidth: 0.8 }
				: { areaColor: 'rgba(156,128,120,.18)', borderColor: '#fff5d8', borderWidth: 0.6 }
		};
	});

	return {
		tooltip: {
			...tooltipBase,
			formatter: (p: any) => {
				const d = p.data;
				if (!d) return '';
				return `<b>${esc(d.label)}</b><br>` + (d.nif
					? `${esc(t('chart.loadedContracts', { n: num(d.value) }))}<br>` +
					  `<span style="color:#9c8078">${esc(t('chart.clickToOpen'))}</span>`
					: `<span style="color:#9c8078">${esc(t('chart.notLoaded'))}</span>`);
			}
		},
		series: [{
			type: 'map',
			map: mapName,
			roam: roamMode(narrow),
			...(bounds ? { boundingCoords: bounds } : narrow ? { boundingCoords: MAINLAND } : {}),
			
			zoom: bounds ? 1 : 1.15,
			scaleLimit: { min: 1, max: 12 },
			// Never labelled on the shape: at 308 concelhos the names are far too
			// dense at rest, and on hover the label painted ink on the ink-filled
			// shape, leaving a smear of half a name. The tooltip says it instead.
			label: { show: false },
			emphasis: { label: { show: false }, itemStyle: { areaColor: INK } },
			select: { disabled: true },
			data
		}]
	};
}

/** One painted area, with its tooltip already written by the caller. */
export type PoliticalCell = {
	/** the geometry's own disambiguated name, which is what ECharts matches on */
	name: string;
	colour: string;
	title: string;
	/** label/value pairs, rendered as rows under the title */
	lines: [string, string][];
	muted?: boolean;
};

/**
 * The political map: areas filled with the colour of whoever holds them.
 *
 * Not a choropleth and not a scale. The fill is categorical and the categories
 * are parties, so the colours are the conventional election-night ones rather
 * than this project's data palette. An area with no result is left blank
 * instead of being folded into "other".
 *
 * `bounds` fits the view to a box in lng/lat, which is how drilling into one
 * district works: same geometry, different frame.
 */
export function politicalMapOption(
	mapName: string,
	cells: PoliticalCell[],
	bounds?: [[number, number], [number, number]],
	narrow = false
) {
	const data = cells.map((c) => ({
		name: c.name,
		value: 1,
		tip: { title: c.title, lines: c.lines },
		itemStyle: {
			areaColor: c.colour,
			opacity: c.muted ? 0.28 : 1,
			borderColor: '#fff5d8',
			borderWidth: c.muted ? 0.4 : 0.8
		}
	}));

	return {
		tooltip: {
			...tooltipBase,
			formatter: (p: any) => {
				const tip = p.data?.tip;
				if (!tip) return `<b>${esc(p.name)}</b><br><span style="color:#9c8078">${esc(t('chart.noData'))}</span>`;
				const rows = tip.lines
					.map(
						([k, v]: [string, string]) =>
							`<div style="display:flex;gap:1.1rem;justify-content:space-between">` +
							`<span style="color:#6b4a44">${esc(k)}</span>` +
							`<b>${esc(v)}</b></div>`
					)
					.join('');
				return `<b style="font-size:1.02em">${esc(tip.title)}</b>` +
					`<div style="margin-top:.35rem;min-width:11rem">${rows}</div>`;
			}
		},
		series: [
			{
				type: 'map',
				map: mapName,
				roam: roamMode(narrow),
				// Without these the country renders at about a fifth of its card,
				// with the islands as specks in an ocean of cream.
				layoutCenter: ['50%', '50%'],
				layoutSize: '96%',
				...(bounds
					? { boundingCoords: bounds }
					: narrow
						? { boundingCoords: MAINLAND }
						: { zoom: 1 }),
				scaleLimit: { min: 0.8, max: 14 },
				label: { show: false },
				// no ink-on-ink label: the tooltip carries the name
				emphasis: { label: { show: false }, itemStyle: { areaColor: INK } },
				select: { disabled: true },
				itemStyle: {
					areaColor: 'rgba(156,128,120,.16)',
					borderColor: '#fff5d8',
					borderWidth: 0.5
				},
				data
			}
		]
	};
}

/**
 * Choropleth over concelhos. Sequential: one hue, light to dark.
 *
 * `features` carries the geometry's own names so series rows can be emitted under
 * the exact string ECharts matches on. The contract data spells municipalities
 * its own way, and 87 of the 308 differ by particle casing alone.
 */
/** What the geometry file carries: display name plus normalised join keys. */
export type GeoFeature = { name: string; key: string; dkey: string; district?: string };

export function mapOption(cells: MapCell[], mapName: string, features: GeoFeature[] = [],
	narrow = false) {
	const values = cells.map((c) => c.total ?? 0).filter((v) => v > 0);
	const max = values.length ? Math.max(...values) : 1;

	// Concelho names are not unique (Lagoa exists in Faro and in the Azores), so
	// resolve by name and disambiguate on district only when the name is shared.
	// District wording differs between sources ("Ilha de São Miguel" vs
	// "... (Açores)"), hence prefix matching rather than equality.
	const byKey = new Map<string, GeoFeature[]>();
	for (const f of features) {
		const list = byKey.get(f.key);
		list ? list.push(f) : byKey.set(f.key, [f]);
	}

	const byName = new Map<string, MapCell>();
	const unmatched: string[] = [];
	for (const c of cells) {
		const candidates = byKey.get(mapKey(c.municipality)) ?? [];
		let hit: GeoFeature | undefined;
		if (candidates.length === 1) {
			hit = candidates[0];
		} else if (candidates.length > 1) {
			const d = mapKey(c.district ?? '');
			hit = d
				? candidates.find((f) => f.dkey === d) ??
					candidates.find((f) => f.dkey.startsWith(d) || d.startsWith(f.dkey)) ??
					// last resort: "Açores" inside "Ilha de São Miguel (Açores)"
					candidates.find((f) => f.dkey.includes(d) || d.includes(f.dkey))
				: undefined;
		}
		if (hit) byName.set(hit.name, c);
		else if ((c.total ?? 0) > 0) unmatched.push(`${c.municipality} (${c.district ?? '?'})`);
	}
	if (unmatched.length) console.warn('[mapa] concelhos sem geometria:', unmatched);

	return {
		tooltip: {
			...tooltipBase,
			formatter: (p: any) => {
				const c = byName.get(p.name);
				if (!c) return `<b>${esc(p.name)}</b><br><span style="color:#9c8078">${esc(t('chart.noContractsHere'))}</span>`;
				return `<b>${esc(c.municipality)}</b>` +
					(c.district ? ` <span style="color:#9c8078">${esc(c.district)}</span>` : '') +
					`<br>${eur(c.total)}<br>${esc(t('chart.nContracts', { n: num(c.contracts) }))}`;
			}
		},
		visualMap: {
			type: 'continuous',
			min: 0,
			max,
			left: 12,
			bottom: 16,
			calculable: true,
			inRange: { color: SEQ },
			outOfRange: { color: ['#efe6d2'] },
			textStyle: { color: INK_SOFT, fontFamily: FONT, fontSize: 11 },
			formatter: (v: number) => eurShort(v)
		},
		series: [{
			type: 'map',
			map: mapName,
			roam: roamMode(narrow),
			scaleLimit: { min: 1, max: 12 },
			...(narrow ? { boundingCoords: MAINLAND } : {}),
			// Açores and Madeira are inset beside the mainland in the source file.
			// The bounding box is wider than tall, so fit to the box rather than
			// letting ECharts letterbox the country inside a wide panel.
			layoutCenter: ['50%', '50%'],
			layoutSize: '98%',
			aspectScale: 0.82,
			zoom: 1.02,
			itemStyle: { areaColor: '#efe6d2', borderColor: '#c9ab8e', borderWidth: 0.6 },
			emphasis: {
				itemStyle: { areaColor: '#f6ce00', borderColor: INK, borderWidth: 1.5 },
				label: { show: true, fontFamily: FONT, fontWeight: 700, color: INK }
			},
			select: { disabled: true },
			// the cell rides along so a click knows which concelho it hit: the
			// feature name is disambiguated ("Lagoa (Faro)") and will not match
			// the municipality string the contracts are filed under
			data: [...byName].filter(([, c]) => (c.total ?? 0) > 0)
				.map(([geoName, c]) => ({ name: geoName, value: c.total ?? 0, cell: c }))
		}]
	};
}
