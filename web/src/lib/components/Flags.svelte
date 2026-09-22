<script lang="ts">
	import { eur } from '$lib/format';
	import { t } from '$lib/messages';

	/**
	 * Patterns worth a second look on one contract.
	 *
	 * Every one of them is legal, and the label says what it is rather than
	 * passing judgement. The colour never carries the meaning on its own: the
	 * word is always there, and the title explains it in a sentence.
	 */
	let { flags = [], nearLimit = null, value = null }: {
		flags?: string[];
		nearLimit?: number | null;
		value?: number | null;
	} = $props();

	// The keys the API sends. Words and reasons come from the message bundle, so
	// the same flag reads in whichever language the page is in.
	const TONES: Record<string, string> = {
		limite: 'serious',
		pessoa: 'person',
		sozinho: 'warn'
	};

	const shown = $derived(
		flags.filter((f) => f in TONES).map((f) => ({ key: f, tone: TONES[f], label: t(`flag.${f}`) }))
	);

	const title = (key: string) =>
		key === 'limite' && nearLimit
			? `${t('flag.limite.why')} ${t('flag.limite.here', { limit: eur(nearLimit) })}`
			: t(`flag.${key}.why`);
</script>

{#if shown.length}
	<span class="flags">
		{#each shown as f (f.key)}
			<span class="flag" data-tone={f.tone} title={title(f.key)}>{f.label}</span>
		{/each}
	</span>
{/if}

<style>
	.flags { display: inline-flex; flex-wrap: wrap; gap: .25rem; margin-top: .25rem; }
	/* Filled, not outlined: at this size an outlined pill in a dark hue is a
	   grey smudge on cream. The word carries the meaning; the fill only makes
	   it findable while scanning a long table. */
	.flag {
		display: inline-flex; align-items: center;
		font-family: 'Bowlby One', Impact, sans-serif; font-weight: 400;
		font-size: .6rem; letter-spacing: .02em; text-transform: uppercase;
		line-height: 1; white-space: nowrap; cursor: help;
		padding: .26rem .45rem .2rem; border-radius: 4px;
		border: 1.5px solid var(--ink); box-shadow: 1.5px 1.5px 0 var(--ink);
		color: var(--paper);
	}
	.flag[data-tone='serious'] { background: var(--sev-serious); }
	.flag[data-tone='warn']    { background: var(--amarelo); color: var(--ink); }
	.flag[data-tone='person']  { background: #7a2fa0; }
</style>
