<script lang="ts">
	import Backlink from '$lib/components/Backlink.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { dateShort, eur, eurShortParts, nearLimitLabel, num } from '$lib/format';
	import { L, t } from '$lib/messages';
	import { reveal } from '$lib/reveal';

	let { data } = $props();
	const c = $derived(data.contract);
	const [money, unit] = $derived(eurShortParts(c.value));
	// Same treatment as the plate beside it. Set through eur() the symbol landed
	// in the fallback face, because the display face carries no euro glyph.
	const [base, baseUnit] = $derived(eurShortParts(c.base_price));

	const isAd = $derived(/ajuste direto/i.test(c.procedure ?? ''));

	// The base price is what the câmara said it expected to pay. Comparing it to
	// the contracted value is the only before/after this record allows: the
	// amount actually paid at the end is published for about 6% of contracts, so
	// there is no overrun figure to show.
	const savedPct = $derived(
		c.base_price && c.value !== null && c.base_price > 0
			? (100 * (c.base_price - c.value)) / c.base_price
			: null
	);

	const yesNo = (v: boolean | null) => (v === null ? t('common.na') : v ? t('ct.yes') : t('ct.no'));

	const basePortal = $derived(
		`https://www.base.gov.pt/Base4/pt/detalhe/?type=contratos&id=${c.id}`
	);
</script>

<svelte:head>
	<title>{t('ct.title', { id: c.id })} · {t('common.site')}</title>
	<meta name="description" content="{c.object ?? t('ct.metaFallback')}, {eur(c.value)}." />
</svelte:head>

<Nav municipalities={[]} current={null} />

<main>
	<section class="head" use:reveal>
		<div class="wrap">
			{#if c.buyer_nif}
				<Backlink href={L(`/municipio/${c.buyer_nif}?tab=contratos`)}
					label={t('ct.backTo', { name: c.buyer_name ?? t('ct.thisMunicipality') })}
					secondary={{ href: L('/'), label: t('firm.pickOther') }} />
			{:else}
				<Backlink href={L('/')} label={t('back.home')} />
			{/if}
			<p class="eyebrow" data-in style="--i:0">
				{t('ct.title', { id: c.id })}
				{#if c.buyer_nif}· <a href={L(`/municipio/${c.buyer_nif}`)}>{c.buyer_name}</a>{/if}
			</p>
			<h1 data-in style="--i:1">{c.object ?? t('ct.noDescription')}</h1>

			<div class="chips" data-in style="--i:2">
				<span class="chip pchip" class:ad={isAd}>{c.procedure ?? t('ct.procedureNA')}</span>
				{#if c.near_limit}
					<span class="chip warnchip">{nearLimitLabel(c.value, c.near_limit)}</span>
				{/if}
				{#if c.centralized}<span class="chip">{t('ct.centralized')}</span>{/if}
				{#if c.green}<span class="chip">{t('ct.green')}</span>{/if}
			</div>

			<div class="plates totals" data-in style="--i:3">
				<div class="plate plate-red lift">
					<b class="num">{money}<i class="unit">{unit}</i></b><span>{t('ct.value')}</span>
				</div>
				{#if c.base_price}
					<div class="plate plate-blue lift">
						<b class="num">{base}<i class="unit">{baseUnit}</i></b><span>{t('ct.basePrice')}</span>
					</div>
				{/if}
				<div class="plate plate-yellow lift">
					<b class="num">{c.n_bidders === null ? t('common.na') : num(c.n_bidders)}</b>
					<span>{t('ct.bidders')}</span>
				</div>
				{#if c.exec_days}
					<div class="plate lift">
						<b class="num">{num(c.exec_days)}</b><span>{t('ct.execDays')}</span>
					</div>
				{/if}
			</div>
		</div>
	</section>

	<div class="wrap body">
		{#if isAd}
			<p class="callout">
				{t('ct.adCallout')}
				<a href={L('/faqs')}>{t('ct.howItWorks')}</a>
			</p>
		{/if}

		<section>
			<h2 class="sectag">{t('ct.whoGotIt')}</h2>
			{#if c.suppliers.length}
				<ul class="parties">
					{#each c.suppliers as sup (sup.name)}
						<li class="card lift party">
							<b>
								{#if sup.nif}<a href={L(`/empresa/${sup.nif}`)}>{sup.name}</a>
								{:else}{sup.name}{/if}
							</b>
							<span class="nifline num">
								{sup.nif ? `NIF ${sup.nif}` : t('ct.noNif')}
							</span>
							<span class="wonbadge">{t('ct.awardee')}</span>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="none">{t('ct.noAwardee')}</p>
			{/if}
		</section>

		<section>
			<h2 class="sectag">{t('ct.whoBid')}</h2>
			{#if c.bidders.length}
				<p class="note">{t('ct.whoBidNote')}</p>
				<div class="card table-wrap">
					<table class="stack">
						<thead>
							<tr><th>{t('tbl.company')}</th><th>NIF</th><th class="r">{t('ct.result')}</th></tr>
						</thead>
						<tbody>
							{#each c.bidders as b (b.name)}
								{@const won = c.suppliers.some((sup) => sup.name === b.name || (b.nif && sup.nif === b.nif))}
								<tr class:won>
									<td data-label={t('tbl.company')}>
										{#if b.nif}<a href={L(`/empresa/${b.nif}`)}>{b.name}</a>{:else}{b.name}{/if}
									</td>
									<td class="num" data-label="NIF">{b.nif ?? t('common.na')}</td>
									<td class="r" data-label={t('ct.result')}>
										{#if won}<span class="tagwon">{t('ct.won')}</span>
										{:else}<span class="taglost">{t('ct.lost')}</span>{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="note">{t('ct.noBidders')}</p>
			{/if}
		</section>

		<section>
			<h2 class="sectag">{t('ct.whatRecordSays')}</h2>
			<div class="card facts">
				<dl>
					<dt>{t('ct.signed')}</dt><dd class="num">{dateShort(c.signed_date)}</dd>
					<dt>{t('ct.published')}</dt><dd class="num">{dateShort(c.pub_date)}</dd>
					<dt>{t('ct.type')}</dt><dd>{c.contract_types.join(', ') || t('common.na')}</dd>
					<dt>{t('ct.sector')}</dt><dd>{c.sector}</dd>
					<dt>{t('ct.cpv')}</dt>
					<dd>{c.cpv_desc ?? t('common.na')}{#if c.cpv}<span class="code num">{c.cpv}</span>{/if}</dd>
					<dt>{t('ct.criterion')}</dt><dd>{c.criterion ?? t('common.na')}</dd>
					<dt>{t('ct.framework')}</dt><dd>{c.framework ?? t('common.na')}</dd>
					<dt>{t('ct.executedWhere')}</dt><dd>{c.locations.join(', ') || t('common.na')}</dd>
					<dt>{t('ct.centralizedLabel')}</dt><dd>{yesNo(c.centralized)}</dd>
					<dt>{t('ct.greenLabel')}</dt><dd>{yesNo(c.green)}</dd>
				</dl>
			</div>

			{#if savedPct !== null}
				<p class="fine">
					{t('ct.closedVsBase', {
						direction: savedPct >= 0 ? t('ct.below') : t('ct.above'),
						pct: `${num(Math.abs(savedPct), 1)}%`
					})}
				</p>
			{/if}
		</section>

		{#if c.ad_justification || c.justification}
			<section>
				<h2 class="sectag">{t('ct.reason')}</h2>
				{#if c.justification}<p class="quote">{c.justification}</p>{/if}
				{#if c.ad_justification}<p class="quote">{c.ad_justification}</p>{/if}
				<p class="fine">{t('ct.reasonNote')}</p>
			</section>
		{/if}

		<section>
			<h2 class="sectag">{t('ct.sourceTitle')}</h2>
			<ul class="links">
				<li>
					<a href={basePortal} target="_blank" rel="noreferrer noopener">{t('ct.basePortal')}</a>
					<small>{t('ct.basePortalNote')}</small>
				</li>
				<li>
					<a href="https://dados.gov.pt/pt/datasets/contratos-publicos-2/"
						target="_blank" rel="noreferrer noopener">{t('ct.impicDataset')}</a>
					<small>{t('ct.impicDatasetNote')}</small>
				</li>
				{#if c.link_announcement}
					<li><a href={c.link_announcement} target="_blank" rel="noreferrer noopener">{t('ct.announcement')}</a></li>
				{/if}
				{#if c.link_pieces}
					<li><a href={c.link_pieces} target="_blank" rel="noreferrer noopener">{t('ct.pieces')}</a></li>
				{/if}
			</ul>
			<p class="fine">{t('ct.sourceNote')}</p>
		</section>
	</div>
</main>

<Footer />

<style>
	.head { padding: 2.6rem 0 2.2rem; border-bottom: 2px solid var(--ink); }
	.head h1 {
		font-size: clamp(1.4rem, 3.6vw, 2.3rem); line-height: 1.16; margin-top: .6rem;
		text-wrap: balance; max-width: 32ch; overflow-wrap: anywhere;
	}
	.eyebrow a { color: inherit; }
	.eyebrow a:hover { color: var(--sangria); }

	.chips { display: flex; flex-wrap: wrap; gap: .45rem; margin-top: 1rem; }
	.chip { display: inline-flex; align-items: center; min-height: 1.9rem; padding: 0 .75rem;
		font-size: .78rem; font-weight: 700; line-height: 1; white-space: nowrap;
		border: 2px solid var(--ink); border-radius: 99px; background: var(--paper-2); }
	.pchip.ad { border-color: var(--sev-critical); color: var(--sev-critical); }
	/* IMPIC procedure names run to forty characters, and this chip has no wide
	   breakpoint guarding its nowrap the way the table pills do. */
	@media (max-width: 820px) {
		.pchip { white-space: normal; border-radius: var(--radius); max-width: 100%;
			padding: .3rem .75rem; line-height: 1.3; }
	}
	.warnchip { background: var(--sev-serious, #d4530b); color: var(--paper); border-color: var(--ink); }

	.totals { margin-top: 1.5rem; }
	.totals .num { display: inline-flex; align-items: baseline; }

	.body { display: grid; gap: 2.6rem; padding: 2.4rem 0 3.5rem; }
	.fine { margin-top: .7rem; font-size: .8rem; color: var(--ink-faint); max-width: 68ch; line-height: 1.5; }
	.none { font-size: .88rem; color: var(--ink-soft); }

	.callout {
		margin: 0; padding: .9rem 1rem; font-size: .88rem; font-weight: 500; line-height: 1.5;
		border: 2px solid var(--ink); border-left-width: 8px; border-left-color: var(--sev-critical);
		border-radius: var(--radius); background: var(--paper-2); max-width: 70ch;
	}
	.callout a { color: var(--azulejo); font-weight: 700; }

	.parties {
		list-style: none; margin: 1rem 0 0; padding: 0; display: grid; gap: .7rem;
		grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
	}
	.party { padding: .9rem 1rem 1rem; border-top-width: 7px; border-top-color: var(--manjerico); }
	.party b { display: block; font-size: 1.02rem; overflow-wrap: anywhere; }
	.nifline { display: block; font-size: .74rem; font-weight: 600; color: var(--ink-faint); margin-top: .2rem; }
	/* `wonbadge`, not `won`: the bidder table marks its winning row with
	   `class:won`, and Svelte scopes component CSS but not class *names*, so a
	   badge called `.won` reached into the row and made it an inline-block with
	   its own border and shadow. */
	.wonbadge {
		display: inline-block; margin-top: .6rem;
		font-family: 'Bowlby One', Impact, sans-serif; font-size: .6rem;
		letter-spacing: .02em; text-transform: uppercase; line-height: 1;
		padding: .28rem .5rem .22rem; border-radius: 4px;
		background: var(--manjerico); color: #fff;
		border: 1.5px solid var(--ink); box-shadow: 1.5px 1.5px 0 var(--ink);
	}

	.table-wrap { overflow-x: auto; margin-top: .8rem; }
	table { width: 100%; border-collapse: collapse; font-size: .88rem; }
	thead th { text-align: left; font-size: .68rem; text-transform: uppercase; letter-spacing: .1em;
		color: var(--ink-faint); padding: .7rem .9rem; border-bottom: 2px solid var(--ink); white-space: nowrap; }
	thead th.r { text-align: right; }
	td { padding: .7rem .9rem; border-bottom: 1px solid var(--rule); }
	tbody tr:last-child td { border-bottom: 0; }
	tbody tr.won { background: rgba(17, 173, 50, .07); }
	.r { text-align: right; }
	.tagwon, .taglost {
		display: inline-block; font-family: 'Bowlby One', Impact, sans-serif;
		font-size: .58rem; letter-spacing: .02em; text-transform: uppercase; line-height: 1;
		padding: .26rem .45rem .2rem; border-radius: 4px; white-space: nowrap;
	}
	.tagwon { background: var(--manjerico); color: #fff; border: 1.5px solid var(--ink);
		box-shadow: 1.5px 1.5px 0 var(--ink); }
	.taglost { color: var(--ink-faint); border: 1.5px solid var(--rule); }

	/* the label sat directly on the card's top border */
	.sectag + .card, .sectag + .note + .card { margin-top: .9rem; }
	.card dl { display: grid; grid-template-columns: max-content minmax(0, 1fr);
		gap: .55rem 1.1rem; margin: 0; padding: 1rem; font-size: .88rem; align-items: baseline; }
	.card dt { font-size: .66rem; font-weight: 700; text-transform: uppercase;
		letter-spacing: .09em; color: var(--ink-faint); white-space: nowrap; }
	.card dd { margin: 0; overflow-wrap: anywhere; }
	.code { display: block; font-size: .72rem; color: var(--ink-faint); margin-top: .1rem; }

	.quote {
		margin: .6rem 0 0; padding: .8rem 1rem; font-size: .9rem; line-height: 1.55;
		background: var(--paper-2); border: 2px solid var(--ink); border-radius: var(--radius);
		max-width: 70ch; white-space: pre-line; overflow-wrap: anywhere;
	}

	.links { list-style: none; margin: .4rem 0 0; padding: 0; display: grid; gap: .7rem; font-weight: 700; }
	.links small { display: block; font-size: .74rem; font-weight: 500; color: var(--ink-faint); }
	.links a { color: var(--azulejo); text-underline-offset: 3px; }
	.links a:hover { color: var(--sangria); }

	@media (max-width: 560px) {
		.card dl { grid-template-columns: 1fr; gap: .15rem; }
		.card dt { margin-top: .7rem; }
	}
</style>
