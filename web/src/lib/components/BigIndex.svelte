<script lang="ts">
	import { severity, severityLabel } from '$lib/format';
	import { locale, t } from '$lib/messages';

	let { value, label, caption, tone = 'auto' }: {
		value: number | null; label: string; caption?: string; tone?: 'auto' | 'brand';
	} = $props();

	// An index that could not be computed is not a low one. severity() answers
	// 'ok' for null so that a missing signal drops out of a mean rather than
	// scoring zero, which is right there and wrong here: rendering that 'ok'
	// painted an unmeasurable index green and called it "baixo".
	const unknown = $derived(value === null || value === undefined);
	const sev = $derived(severity(value));
	const pctFull = $derived(Math.max(0, Math.min(100, value ?? 0)));
</script>

<div class="idx lift" data-sev={unknown ? 'unknown' : tone === 'auto' ? sev : undefined}
	class:brand={tone === 'brand' && !unknown} class:unknown>
	<p class="eyebrow">{label}</p>
	<p class="figure num">
		{unknown ? 'N/A' : value!.toLocaleString(locale(), { maximumFractionDigits: 1 })}<span class="of">/100</span>
	</p>
	{#if unknown}
		<p class="level">{t('common.notMeasurable')}</p>
	{:else}
		<!-- the bar repeats the number positionally; the written level repeats it in words -->
		<div class="track" role="img"
			aria-label={t('card.indexLevel', { label, value: value ?? 0, level: severityLabel(sev) })}>
			<div class="fill" style:width="{pctFull}%"></div>
		</div>
		<p class="level">{severityLabel(sev)}</p>
	{/if}
	{#if caption}<p class="caption">{caption}</p>{/if}
</div>

<style>
	.idx.unknown { --tone: var(--ink-faint); }
	.idx {
		--tone: var(--sev-ok);
		background: var(--paper-2);
		border: 2px solid var(--ink);
		border-radius: var(--radius);
		box-shadow: var(--shadow-hard);
		padding: 1.25rem 1.4rem 1.4rem;
		position: relative;
		overflow: hidden;
	}
	.idx::before {
		content: ''; position: absolute; inset: 0 auto 0 0; width: 8px; background: var(--tone);
	}
	.idx[data-sev='warn']     { --tone: var(--sev-warn); }
	.idx[data-sev='serious']  { --tone: var(--sev-serious); }
	.idx[data-sev='critical'] { --tone: var(--sev-critical); }
	.idx.brand { --tone: var(--azulejo); }

	.figure {
		font-family: 'Bowlby One', Impact, sans-serif;
		font-size: clamp(3.4rem, 9vw, 5.6rem);
		line-height: .9;
		margin: .35rem 0 .1rem;
		color: var(--tone);
		letter-spacing: -.02em;
	}
	.of { font-size: .26em; color: var(--ink-faint); margin-left: .25rem; letter-spacing: 0; }
	.track { height: 10px; background: var(--paper-3); border: 1.5px solid var(--ink); border-radius: 99px; overflow: hidden; margin: .7rem 0 .5rem; }
	.fill { height: 100%; background: var(--tone); transition: width .7s cubic-bezier(.22,1,.36,1); }
	.level { margin: 0; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; font-size: .78rem; color: var(--tone); }
	.caption { margin: .5rem 0 0; font-size: .86rem; color: var(--ink-soft); line-height: 1.4; }
</style>
