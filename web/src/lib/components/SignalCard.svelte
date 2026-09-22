<script lang="ts">
	import type { Flag } from '$lib/api';
	import { num, severity, severityLabel } from '$lib/format';
	import { locale, t } from '$lib/messages';

	let { label, blurb, flag, counted = true, reason = '' }: {
		label: string; blurb: string; flag: Flag; counted?: boolean;
		/** shown instead of the explanation when there is no value to explain */
		reason?: string;
	} = $props();

	// No value is not a low value. A signal that cannot be measured in this
	// window must not borrow the green of a genuinely clean one.
	const unknown = $derived(flag.pct === null || flag.pct === undefined);
	const sev = $derived(severity(flag.pct));
	const width = $derived(Math.max(0, Math.min(100, flag.pct ?? 0)));

	/** What `n` counts: the API says "contratos", "empresas" or "anos". */
	const unitWord = (unit: string | null | undefined, one: boolean) => {
		const key = unit === 'empresas' ? 'compan' : unit === 'anos' ? 'year' : 'contract';
		const map = { compan: ['common.company', 'common.companies'],
			year: ['common.year', 'common.years'],
			contract: ['common.contract', 'common.contracts'] } as const;
		return t(map[key][one ? 0 : 1]);
	};
	const level = $derived(unknown ? t('common.notMeasurable') : severityLabel(sev));
</script>

<article class="lift" data-sev={unknown ? 'unknown' : sev} class:muted={!counted} class:unknown>
	<header>
		<h3>{label}</h3>
		{#if !counted}<span class="tag">{t('card.outsideIndex')}</span>{/if}
	</header>

	<p class="value num">
		{flag.pct === null ? 'N/A' : flag.pct.toLocaleString(locale(), { maximumFractionDigits: 1 })}<span class="unit">%</span>
	</p>

	{#if !unknown}
		<div class="track" role="img" aria-label={t('card.level', { label, value: flag.pct ?? 0, level })}>
			<div class="fill" style:width="{width}%"></div>
		</div>
	{/if}

	<p class="meta">
		<span class="level">{level}</span>
		{#if flag.n !== null && flag.n !== undefined}
			<!-- `unit` arrives from the API as one of three plurals; the card words
			     it in the page's language rather than printing the API's Portuguese. -->
			{@const one = flag.n === 1}
			· <span class="num">{num(flag.n)}</span>
			{unitWord(flag.unit, one)}
		{/if}
		{#if flag.disclosed}
			· {t('card.of')} <span class="num">{num(flag.disclosed)}</span> {t('card.disclosed')}
		{/if}
	</p>
	<p class="blurb">{unknown ? reason || blurb : blurb}</p>
</article>

<style>
	article {
		--tone: var(--sev-ok);
		background: var(--paper-2);
		border: 2px solid var(--ink);
		border-radius: var(--radius);
		box-shadow: var(--shadow-hard);
		padding: 1rem 1.1rem 1.15rem;
		display: flex; flex-direction: column;
		transition: transform .15s ease, box-shadow .15s ease;
	}

	article[data-sev='warn']     { --tone: var(--sev-warn); }
	article[data-sev='serious']  { --tone: var(--sev-serious); }
	article[data-sev='critical'] { --tone: var(--sev-critical); }
	article[data-sev='unknown']  { --tone: var(--ink-faint); }
	/* :global, because the band class is on an ancestor this component does not
	   own, and Svelte would otherwise scope the selector to nothing. */
	:global(.band-ink) article[data-sev='ok']       { --tone: var(--on-ink-ok); }
	:global(.band-ink) article[data-sev='warn']     { --tone: var(--on-ink-warn); }
	:global(.band-ink) article[data-sev='serious']  { --tone: var(--on-ink-serious); }
	:global(.band-ink) article[data-sev='critical'] { --tone: var(--on-ink-critical); }
	:global(.band-ink) article[data-sev='unknown']  { --tone: rgba(255,245,216,.55); }

	/* On the dark band the card has to be dark too. Left cream, it inherited the
	   band's cream text colour into its own heading and blurb, so the labels
	   vanished into the card, and the lifted severity colours (chosen for
	   contrast against ink) landed on cream, where they have none. */
	:global(.band-ink) article {
		background: rgba(255,245,216,.07);
		border-color: rgba(255,245,216,.32);
		box-shadow: 4px 4px 0 rgba(0,0,0,.4);
		color: var(--paper);
	}
	:global(.band-ink) article.muted { background: rgba(255,245,216,.035); box-shadow: none; }
	:global(.band-ink) h3      { color: var(--paper); }
	:global(.band-ink) .tag    { color: rgba(255,245,216,.6); border-color: rgba(255,245,216,.3); }
	:global(.band-ink) .unit   { color: rgba(255,245,216,.55); }
	:global(.band-ink) .meta,
	:global(.band-ink) .blurb  { color: rgba(255,245,216,.72); }
	:global(.band-ink) .track  { background: rgba(255,245,216,.12); border-color: rgba(255,245,216,.4); }
	article.unknown .value { font-size: clamp(1.8rem, 4vw, 2.4rem); }
	article.unknown .unit { display: none; }
	article.muted { opacity: .82; box-shadow: var(--shadow-soft); border-style: dashed; }

	header { display: flex; align-items: baseline; gap: .5rem; justify-content: space-between; }
	h3 { font-size: .95rem; letter-spacing: 0; }
	.tag { font-size: .62rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase;
		color: var(--ink-faint); border: 1.5px dashed var(--rule); border-radius: 99px; padding: .1rem .45rem; }
	.value {
		font-family: 'Bowlby One', Impact, sans-serif;
		font-size: clamp(2.5rem, 6vw, 3.4rem);
		line-height: 1; margin: .45rem 0 .1rem; color: var(--tone); letter-spacing: -.02em;
	}
	.unit { font-size: .34em; margin-left: .12rem; color: var(--ink-faint); }
	.track { height: 8px; background: var(--paper-3); border: 1.5px solid var(--ink); border-radius: 99px; overflow: hidden; margin: .55rem 0 .45rem; }
	.fill { height: 100%; background: var(--tone); transition: width .7s cubic-bezier(.22,1,.36,1); }
	.level { font-weight: 800; text-transform: uppercase; letter-spacing: .07em; color: var(--tone); }
	.meta { margin: 0; font-size: .78rem; color: var(--ink-soft); }
	.blurb { margin: .55rem 0 0; font-size: .83rem; color: var(--ink-soft); line-height: 1.45; }
</style>
