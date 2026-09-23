<script lang="ts">
	import { eur } from '$lib/format';
	import { t } from '$lib/messages';

	/**
	 * Patterns worth a second look on one contract.
	 *
	 * Every one of them is legal, and the chip states the fact with its numbers
	 * rather than naming a category: "3 contratos, todos abaixo de 20 000 €"
	 * needs no glossary, where "fracionamento" needs a tooltip and a law degree.
	 * The tooltip carries the caveat, never the meaning.
	 *
	 * The colour never carries meaning on its own: the sentence is always there.
	 */
	type Flag = { key: string; data?: Record<string, number | string> };

	let { flags = [], max = 3 }: { flags?: Flag[]; max?: number } = $props();

	// Keys whose value is money. The API ships numbers, not strings, because a
	// formatted euro amount is prose and prose does not go on the wire.
	const MONEY = new Set(['limit', 'gap', 'value']);

	const TONES: Record<string, string> = {
		fatias: 'critical',
		limite: 'serious',
		pessoa: 'person',
		estreante: 'warn',
		nunca_a_concurso: 'serious',
		sozinho: 'warn',
		fechada: 'critical',
		unipessoal: 'person',
		sem_explicacao: 'warn'
	};

	const vars = (data: Record<string, number | string> = {}) =>
		Object.fromEntries(
			Object.entries(data).map(([k, v]) => [
				k,
				MONEY.has(k) && typeof v === 'number' ? eur(v) : v
			])
		);

	// A row wearing seven chips teaches nobody anything except to stop reading
	// chips. The service already orders them by what matters most.
	const shown = $derived(
		flags
			.filter((f) => f.key in TONES)
			.slice(0, max)
			.map((f) => ({
				key: f.key,
				tone: TONES[f.key],
				label: t(`flag.${f.key}`, vars(f.data)),
				why: t(`flag.${f.key}.why`)
			}))
	);
</script>

{#if shown.length}
	<span class="flags">
		{#each shown as f (f.key)}
			<span class="flag" data-tone={f.tone} title={f.why}>{f.label}</span>
		{/each}
	</span>
{/if}

<style>
	.flags { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .35rem; }
	/* Archivo, not the display face: these carry a sentence now, and Bowlby One
	   set small and uppercase was legible as one word and a smudge as six.
	   Filled rather than outlined, because an outlined pill in a dark hue at
	   this size is a grey smudge on cream. */
	.flag {
		display: inline-flex; align-items: center;
		font-weight: 700; font-size: .7rem; line-height: 1.25;
		padding: .22rem .45rem; border-radius: 4px; cursor: help;
		border: 1.5px solid var(--ink); box-shadow: 1.5px 1.5px 0 var(--ink);
		color: var(--paper);
	}
	.flag[data-tone='critical'] { background: var(--sev-critical); }
	.flag[data-tone='serious']  { background: var(--sev-serious); }
	/* Festival yellow cannot hold white; this is the project's own warn amber. */
	.flag[data-tone='warn']     { background: var(--sev-warn); }
	.flag[data-tone='person']   { background: #7a2fa0; }
</style>
