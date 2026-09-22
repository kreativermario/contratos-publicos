<script lang="ts">
	import type { Mandate } from '$lib/api';
	import { eurShort, num, pct } from '$lib/format';
	import { t } from '$lib/messages';

	let { mandates = [], onpick, activeFrom = null, activeTo = null }: {
		mandates?: Mandate[];
		/** reads the page to this term's exact dates; omitted, cards do not click */
		onpick?: (from: string, to?: string) => void;
		activeFrom?: string | null;
		activeTo?: string | null;
	} = $props();

	/** Whether the page is currently reading exactly this term. */
	const isActive = (m: Mandate) =>
		activeFrom === m.term_start && (activeTo ?? null) === (m.term_end ?? null);

	const year = (d: string | null) => (d ? d.slice(0, 4) : t('mandate.today'));

	// The law changed in the middle of this series, and it moved the numbers more
	// than any election did. Without saying so, a reader attributes the 2017 drop
	// in ajuste direto to whoever took office that October.
	const CCP_REFORM = '2017-08-30';
	const spansReform = (m: Mandate) =>
		m.term_start <= CCP_REFORM && (m.term_end ?? '9999') > CCP_REFORM;

	// "Mudou de mãos" needs both the list and the person to change. Independent
	// movements are re-registered under a new name almost every cycle (IN-OV
	// becomes INOV25) with the same president continuing, and comparing party
	// strings alone flagged that as a change of hands.
	const changed = (m: Mandate, i: number) => {
		if (i === 0) return false;
		const prev = mandates[i - 1];
		return prev.party !== m.party && (prev.president ?? '') !== (m.president ?? '');
	};

	// Same person, new list. Worth showing, and it is not the same event.
	const relabelled = (m: Mandate, i: number) => {
		if (i === 0) return false;
		const prev = mandates[i - 1];
		return prev.party !== m.party && (prev.president ?? '') === (m.president ?? '') && !!m.president;
	};

	// "I" is the code the results carry for an independent candidacy. Expanding
	// an abbreviation is not the same as merging two acronyms into one party:
	// nothing is grouped here, only spelled out, because a bare "I" on a card
	// tells a reader nothing at all.
	const partyLabel = (p: string) => (p === 'I' ? t('mandate.independent') : p);

	// Bars are read against each other, so they share one scale.
	const maxValue = $derived(Math.max(1, ...mandates.map((m) => m.value ?? 0)));
</script>

{#if mandates.length}
	<h2 class="sectag">{t('mandate.title')}</h2>
	<p class="note">{t('mandate.note')}</p>
	{#if onpick}
		<p class="note">{t('mandate.pickNote')}</p>
	{/if}

	<ol class="terms">
		{#each mandates as m, i (m.term_start)}
			<li class="term" class:now={!m.term_end} class:on={isActive(m)} class:lift={Boolean(onpick)}>
				{#if onpick}
					<!-- the whole card reads the page to this term; a term is the natural
					     window for "what did this lot actually contract" -->
					<button type="button" class="pick"
						aria-pressed={isActive(m)}
						onclick={() => onpick(m.term_start, m.term_end ?? undefined)}>
						<span class="sr">
							{t('mandate.readOnly', { from: year(m.term_start), to: year(m.term_end) })}
						</span>
					</button>
				{/if}
				<div class="when">
					<b>{year(m.term_start)}</b><span class="to">{t('mandate.to')}</span><b>{year(m.term_end)}</b>
					{#if changed(m, i)}<span class="flip">{t('mandate.flipped')}</span>
					{:else if relabelled(m, i)}<span class="flip same">{t('mandate.relabelled')}</span>{/if}
				</div>

				<p class="party">
					{partyLabel(m.party)}
					{#if m.coalition}<span class="kind">{t('mandate.coalition')}</span>
					{:else if m.citizens_group}<span class="kind">{t('mandate.citizens')}</span>{/if}
				</p>
				{#if m.president}<p class="who">{m.president}</p>{/if}

				<div class="bar" role="img"
					aria-label={t('mandate.barAria', { money: eurShort(m.value), n: num(m.contracts) })}>
					<span style:width="{(100 * (m.value ?? 0)) / maxValue}%"></span>
				</div>
				<p class="figs">
					<b>{eurShort(m.value)}</b>
					<span>{num(m.contracts)} {t('common.contracts')}</span>
					{#if m.ad_pct !== null && m.ad_pct !== undefined}
						<span class="ad">{t('mandate.noTender', { pct: pct(m.ad_pct) })}</span>
					{/if}
				</p>

				{#if spansReform(m)}
					<span class="reformflag">{t('mandate.reformFlag')}</span>
				{/if}
			</li>
		{/each}
	</ol>

	{#if mandates.some(spansReform)}
		<p class="note reform">{t('mandate.reformNote')}</p>
	{/if}

	<p class="note small">{t('mandate.provisional')}</p>
{/if}

<style>
	.terms {
		list-style: none; margin: 1rem 0 0; padding: 0; display: grid;
		grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); align-items: stretch; gap: .7rem;
	}
	/* the button covers the card, so the whole thing is the target, and the
	   content sits above it */
	/* stretch, not start: a ragged row of five cards reads as broken. They are
	   the same shape now because the reform note moved out from inside one of
	   them and became a line under the whole row, which is what it describes. */
	.term { position: relative; height: 100%; display: flex; flex-direction: column; }
	.terms { align-items: stretch; }
	.term > :not(.pick) { position: relative; z-index: 1; pointer-events: none; }
	.pick {
		position: absolute; inset: 0; z-index: 0; cursor: pointer;
		background: none; border: 0; padding: 0; border-radius: var(--radius);
	}
	.term:has(.pick):hover { background: var(--paper-3); }
	.term.on { border-color: var(--sangria); box-shadow: 4px 4px 0 var(--sangria); }
	.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
	.term {
		margin: 0; padding: .85rem .9rem;
		border: 2px solid var(--ink); border-radius: var(--radius);
		background: var(--paper-2); box-shadow: 4px 4px 0 var(--ink);
	}
	/* the current term is the one a reader is standing in */
	.term.now { border-width: 3px; box-shadow: 5px 5px 0 var(--azulejo); }

	.when { display: flex; flex-wrap: wrap; align-items: baseline; gap: .3rem; }
	.when b { font-family: 'Bowlby One', Impact, sans-serif; font-weight: 400; font-size: 1.15rem; }
	.to { font-size: .72rem; color: var(--ink-faint); font-weight: 700; }
	.flip {
		font-size: .62rem; font-weight: 800; letter-spacing: .06em; text-transform: uppercase;
		padding: .1rem .4rem; border-radius: 999px; background: var(--amarelo); color: var(--ink);
	}
	/* a rename is not a handover, so it must not read like one */
	.flip.same { background: none; border: 1.5px solid var(--ink-faint); color: var(--ink-soft); }

	.party { margin: .45rem 0 0; font-weight: 800; overflow-wrap: anywhere; }
	.kind {
		margin-left: .35rem; font-size: .62rem; font-weight: 700; letter-spacing: .05em;
		text-transform: uppercase; color: var(--ink-faint);
	}
	.who { margin: .1rem 0 0; font-size: .82rem; color: var(--ink-soft); overflow-wrap: anywhere; }

	.bar { margin-top: .6rem; height: 8px; background: rgba(156,128,120,.22); border-radius: 99px; overflow: hidden; }
	.bar span { display: block; height: 100%; background: var(--ink); }

	.figs { display: flex; flex-wrap: wrap; align-items: baseline; gap: .2rem .6rem; margin-top: .4rem; }
	.figs b { font-size: 1rem; }
	.figs span { font-size: .76rem; color: var(--ink-soft); font-weight: 600; }
	.figs .ad { color: var(--ink); }

	.reformflag {
		display: inline-block; margin-top: auto; padding-top: .6rem;
		font-size: .66rem; font-weight: 800; letter-spacing: .06em;
		text-transform: uppercase; color: var(--sev-warn);
	}
	.reform {
		margin: .6rem 0 0; padding-top: .5rem; border-top: 2px dashed var(--ink-faint);
		font-size: .76rem; color: var(--ink-soft); font-weight: 600;
	}
</style>
