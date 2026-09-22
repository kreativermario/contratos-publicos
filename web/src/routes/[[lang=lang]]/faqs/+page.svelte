<script lang="ts">
	import { lang, t, tl } from '$lib/messages';
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { num } from '$lib/format';
	import { L } from '$lib/messages';
	import { reveal } from '$lib/reveal';

	let { data } = $props();

	// Written out rather than inlined so a missing /config does not render "N/A"
	// in the middle of a sentence about the law.
	const l = $derived(data.limits);

	const SCORED = ['ajuste_direto', 'concentracao', 'single_bidder', 'threshold_surf', 'newcomer_value'];
	const CONTEXT = ['ad_contracts', 'undisclosed_bidders', 'top_supplier', 'top3_suppliers', 'repeat_winners'];

	/** What each scored signal is counted in, since the label does not say. */
	const UNIT: Record<string, string> = {
		ajuste_direto: '% do dinheiro',
		concentracao: 'índice de 0 a 100',
		single_bidder: '% do dinheiro',
		threshold_surf: '% do dinheiro',
		newcomer_value: '% do dinheiro',
		ad_contracts: 'contagem',
		undisclosed_bidders: 'contagem',
		top_supplier: '% do dinheiro',
		top3_suppliers: '% do dinheiro',
		repeat_winners: 'anos'
	};

	/** The colour of the edge, by how bad a high value usually is. */
	const EDGE: Record<string, string> = {
		ajuste_direto: 'red', concentracao: 'orange', single_bidder: 'amber',
		threshold_surf: 'orange', newcomer_value: 'red',
		ad_contracts: 'blue', undisclosed_bidders: 'blue',
		top_supplier: 'green', top3_suppliers: 'green', repeat_winners: 'green'
	};

	// The questions people actually arrive with. Split into two stacks rather
	// than a two-column grid: in a grid the pair in a row has to agree on a
	// height, so a closed card grew to match its open neighbour and sat there as
	// an empty box.
	const QUESTIONS = [
		{
			q: 'Isto acusa alguém de alguma coisa?',
			a: [
				'Não, e não é isso que os dados conseguem dizer. Todos os procedimentos medidos aqui são legais.',
				'Um índice alto quer dizer que vale a pena olhar, não que houve crime. Um índice baixo também não é um atestado de bom comportamento.'
			]
		},
		{
			q: 'Então o ajuste direto é ilegal?',
			a: [
				'Não. Está previsto na lei e, para compras pequenas, é o procedimento sensato: abrir um concurso público para comprar tinteiros custaria mais do que os tinteiros. O que medimos não é se houve ajuste direto, é quanto do dinheiro foi por aí.'
			]
		},
		{
			q: 'Porque é que os números caem todos em 2017?',
			a: [
				'Porque a lei mudou. A revisão do Código dos Contratos Públicos apertou os limites do ajuste direto a partir de agosto de 2017, e a queda vê-se em câmaras de todos os partidos, incluindo nas que não mudaram de mãos.'
			]
		},
		{
			q: 'O que é "encostado ao limite"?',
			a: [
				'Um contrato mesmo por baixo de um limite legal fica a poucos euros de obrigar a um procedimento mais exigente. Uma vez não quer dizer nada: os preços são o que são. Muitas vezes, no mesmo sítio, já é um padrão que vale a pena olhar.'
			]
		},
		{
			q: 'Porque falta tanta coisa nos dados?',
			a: [
				'Porque falta no registo original. Quem concorreu só é declarado em cerca de 42% dos contratos, e o valor final quase nunca. Não inventamos o que lá não está: onde não dá para calcular, dizemos "N/A".'
			]
		},
		{
			q: 'Encontrei um erro. E agora?',
			a: [
				'Se o erro é nosso, queremos saber e corrigimos. Se está no registo original não o podemos corrigir aqui, mas também queremos saber, porque vale a pena dizê-lo na página onde aparece.'
			]
		}
	];

	const half = Math.ceil(QUESTIONS.length / 2);
	const columns = $derived([QUESTIONS.slice(0, half), QUESTIONS.slice(half)]);
</script>

<svelte:head>
	<title>{t('faqs.title')} · {t('common.site')}</title>
	<meta name="description" content={t('faqs.description')} />
</svelte:head>

<Nav municipalities={[]} current={null} />

<main>
	<section class="head" use:reveal>
		<div class="wrap">
			<p class="eyebrow" data-in style="--i:0">Onde Vai Parar · FAQs</p>
			<h1 class="poster" data-in style="--i:1"><span>Como isto funciona</span></h1>
			<p class="lede" data-in style="--i:2">
				O que cada número conta, de onde vem, e o que a lei permite. Se alguma
				coisa aqui não bater certo com o que vês nas páginas dos municípios,
				<b>o erro é nosso</b>.
			</p>
			<!-- This page is deliberately not translated: it is long-form writing about
			     Portuguese procurement law, and a rough English version of it would be
			     worse than none. The note says so, in English, only under /en. -->
			{#if lang() === 'en'}
				<p class="ptonly" data-in style="--i:3">{t('ptOnly.note')}</p>
			{/if}
		</div>
	</section>

	<div class="seam" aria-hidden="true"></div>

	<!-- the questions ---------------------------------------------------- -->
	<section class="band band-cream" use:reveal>
		<div class="wrap">
			<h2 class="sectag" data-in style="--i:0">As perguntas</h2>
			<p class="note" data-in style="--i:1">Abre a que te interessa.</p>

			<div class="acc" data-in style="--i:2">
				{#each columns as column, ci (ci)}
					<div class="col">
						{#each column as item (item.q)}
							<details>
								<summary>
									{item.q}<span class="plus" aria-hidden="true">+</span>
								</summary>
								<div class="drop"><div class="clip"><div class="answer">
									{#each item.a as para (para)}<p>{para}</p>{/each}
								</div></div></div>
							</details>
						{/each}
					</div>
				{/each}
			</div>
		</div>
	</section>

	<div class="stripe" aria-hidden="true"><b></b><b></b><b></b><b></b></div>

	<!-- the ceilings, the one thing the whole site measures against ------- -->
	<section class="band band-ink" use:reveal>
		<div class="wrap">
			<h2 class="sectag" data-in style="--i:0">Os limites da lei</h2>
			<p class="note" data-in style="--i:1">
				Uma câmara não pode escolher uma empresa e pagar-lhe o que quiser.
				Acima destes valores o trabalho tem de ir a concurso público, aberto a
				quem quiser concorrer.
			</p>
			{#if l}
				<div class="ceilings" data-in style="--i:2">
					{#each [
						{ v: l.ajuste_direto_servicos, t: 'Ajuste direto', s: 'bens e serviços' },
						{ v: l.ajuste_direto_obras, t: 'Ajuste direto', s: 'empreitadas, isto é, obra' },
						{ v: l.consulta_previa, t: 'Consulta prévia', s: 'convida pelo menos três' }
					] as c (c.s)}
						<div>
							<!-- the exact figure, not the short form: "20 mil €" is a rounding
							     of a statutory ceiling, and the whole point of the number is
							     that a contract can sit six euros under it. The euro sign goes
							     in the body face because the display face has no glyph for it. -->
							<b class="num">{num(c.v)}<i class="unit">€</i></b>
							<span>{c.t}</span>
							<small>{c.s}</small>
						</div>
					{/each}
				</div>
				<p class="fine" data-in style="--i:3">
					Marcamos um contrato como "encostado ao limite" quando o valor cai nos
					últimos {num(100 * l.banda_limite)}% abaixo de um destes.
				</p>
			{/if}
		</div>
	</section>

	<div class="stripe" aria-hidden="true"><b></b><b></b><b></b><b></b></div>

	<!-- what the index is made of ----------------------------------------- -->
	<section class="band band-cream" use:reveal>
		<div class="wrap">
			<h2 class="sectag" data-in style="--i:0">O que entra no índice</h2>
			<p class="note" data-in style="--i:1">
				Todos são <b>percentagens do dinheiro</b>, nunca contagens de casos. É
				isso que permite fazer a média deles: somar "54% dos concursos" com "9%
				do dinheiro" dá um número que não quer dizer nada.
			</p>
			<div class="gloss" data-in style="--i:2">
				{#each SCORED as key (key)}
					<div class="card term lift term-{EDGE[key] ?? 'blue'}">
						<h3>{tl('pt', `signal.${key}`)}</h3>
						<p>{tl('pt', `signal.${key}.blurb`)}</p>
						<span class="how">{UNIT[key] ?? ''}</span>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<div class="seam" aria-hidden="true"></div>

	<section class="band band-deep" use:reveal>
		<div class="wrap">
			<h2 class="sectag" data-in style="--i:0">O que fica de fora</h2>
			<p class="note" data-in style="--i:1">
				Contam contratos em vez de euros, ou dependem de quantos anos estão
				carregados. Mostram-se ao lado do índice, nunca lá dentro.
			</p>
			<div class="gloss" data-in style="--i:2">
				{#each CONTEXT as key (key)}
					<div class="card term lift term-{EDGE[key] ?? 'blue'}">
						<h3>{tl('pt', `signal.${key}`)}</h3>
						<p>{tl('pt', `signal.${key}.blurb`)}</p>
						<span class="how">{UNIT[key] ?? ''}</span>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<div class="seam" aria-hidden="true"></div>

	<!-- the gaps and the source ------------------------------------------- -->
	<section class="band band-cream" use:reveal>
		<div class="wrap">
			<h2 class="sectag" data-in style="--i:0">O que falta nos dados</h2>
			<ul class="gaps" data-in style="--i:1">
				<li><b>Quem concorreu</b> só é declarado em cerca de 42% dos contratos. Cada indicador diz sobre quantos foi calculado.</li>
				<li><b>O valor final</b> quase nunca é publicado, só o valor pelo qual o contrato foi fechado. Por isso não há aqui derrapagens.</li>
				<li><b>A morada das empresas</b> não existe nestes dados. O local de execução é onde o trabalho é feito, não onde a empresa tem sede.</li>
				<li><b>A data de constituição</b> não existe de forma gratuita: o registo comercial só está publicado online a partir de 2006.</li>
				<li><b>Um contrato pode abranger vários concelhos</b> e conta em cada um, por isso a soma do mapa pode ser maior do que o total gasto.</li>
			</ul>

			<h2 class="sectag later" data-in style="--i:2">De onde vêm os dados</h2>
			<p class="note" data-in style="--i:3">
				Dos ficheiros que o IMPIC publica em dados.gov.pt, o mesmo registo que
				alimenta o Portal BASE. Não corrigimos nada: o que esteja errado ou em
				falta na origem aparece aqui tal e qual.
				<a href={L('/termos')}>Os termos e as fontes, por extenso</a>.
			</p>
		</div>
	</section>
</main>

<Footer />

<style>
	/* The English note on a page that stays Portuguese: quiet, but unmissable. */
		.ptonly {
			margin-top: 1.2rem; max-width: 58ch; padding: .7rem .9rem;
			font-size: .88rem; font-weight: 600; color: var(--ink-soft);
			background: var(--paper-2); border: 2px solid var(--ink);
			border-radius: var(--radius);
		}
		.head { padding: clamp(2.6rem, 7vw, 4rem) 0 2.4rem; }
	.head h1 { font-size: clamp(1.9rem, 5.4vw, 3.2rem); margin-top: 1.1rem; }
	.lede { margin-top: 1.4rem; max-width: 58ch; font-size: 1.05rem;
		font-weight: 500; line-height: 1.6; color: var(--ink-soft); }
	.lede b { color: var(--ink); font-weight: 700; }

	.note { margin: .7rem 0 0; max-width: 64ch; font-size: 1rem; font-weight: 500;
		line-height: 1.65; color: var(--ink-soft); }
	.note b { color: var(--ink); font-weight: 700; }
	.fine { margin: 1rem 0 0; font-size: .86rem; color: rgba(255,245,216,.62); max-width: 62ch; }

	/* ---- the questions ------------------------------------------------- */

	/* Two independent stacks, not a two-column grid. In a grid the pair in a row
	   has to agree on a height, so a closed card grew to match its open
	   neighbour and sat there as an empty box. */
	.acc { display: grid; gap: 1rem; margin-top: 1.1rem; align-items: start; }
	@media (min-width: 1100px) { .acc { grid-template-columns: 1fr 1fr; } }
	.col { display: grid; gap: .6rem; align-content: start; }

	details {
		border: 2px solid var(--ink); border-radius: var(--radius);
		background: var(--paper-2); box-shadow: var(--shadow-hard); overflow: hidden;
		transition: transform var(--t-hover) var(--ease-out), box-shadow var(--t-hover) var(--ease-out);
	}
	details:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0 var(--ink); }

	summary {
		cursor: pointer; list-style: none; padding: .9rem 1rem;
		display: flex; align-items: center; gap: .9rem;
		/* Body face at 700, not the display face: a question is a sentence, and
		   Bowlby One at this size read as a headline shouting at the reader. */
		font-family: 'Archivo', sans-serif; font-weight: 700; font-size: .98rem;
		line-height: 1.35; color: var(--ink);
		transition: background .32s var(--ease-out);
	}
	summary::-webkit-details-marker { display: none; }
	summary:hover { background: var(--paper-3); }
	details[open] summary { background: var(--amarelo); }

	.plus {
		margin-left: auto; flex: none; width: 1.5rem; height: 1.5rem;
		display: grid; place-items: center; border-radius: 50%;
		border: 2px solid var(--ink); background: var(--paper);
		font-weight: 800; font-size: .95rem; line-height: 1;
		transition: transform .34s var(--ease-out), background var(--t-hover) var(--ease-out);
	}
	details[open] .plus { transform: rotate(135deg); background: var(--paper-2); }

	/* A `details` cannot transition its own height, so the answer sits in a grid
	   row that goes from 0fr to 1fr, which can. The text fades and rises inside
	   it: the row alone slid the paragraph up out of nothing and read as a jolt
	   rather than as something opening. */
	.drop { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .46s var(--ease-out); }
	details[open] .drop { grid-template-rows: 1fr; }
	.clip { overflow: hidden; }
	.answer {
		padding: .9rem 1rem 1.05rem; border-top: 2px solid var(--ink);
		opacity: 0; transform: translateY(-6px);
		transition: opacity .3s var(--ease-out), transform .42s var(--ease-out);
	}
	details[open] .answer { opacity: 1; transform: none; transition-delay: .1s; }
	.answer p { margin: 0; font-size: .95rem; font-weight: 500; line-height: 1.6;
		color: var(--ink-soft); max-width: 62ch; }
	.answer p + p { margin-top: .6rem; }

	@media (prefers-reduced-motion: reduce) {
		details, .plus, .drop, .answer { transition: none; }
	}

	/* ---- the glossary --------------------------------------------------- */

	.gloss { display: grid; gap: .8rem; margin-top: 1.1rem;
		grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr)); }
	.term { padding: 1rem 1.1rem 1.15rem; border-top-width: 7px;
		display: flex; flex-direction: column; }
	.term h3 { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: .95rem;
		line-height: 1.25; letter-spacing: -.01em; text-transform: none; }
	.term p { margin: .5rem 0 0; font-size: .88rem; font-weight: 500;
		line-height: 1.55; color: var(--ink-soft); }
	.term .how { margin-top: auto; padding-top: .85rem; font-size: .68rem;
		font-weight: 800; color: var(--ink-faint); letter-spacing: .08em; text-transform: uppercase; }
	.term-red { border-top-color: var(--sev-critical); }
	.term-orange { border-top-color: var(--sev-serious); }
	.term-amber { border-top-color: var(--sev-warn); }
	.term-blue { border-top-color: var(--azulejo); }
	.term-green { border-top-color: var(--manjerico); }

	/* ---- the ceilings --------------------------------------------------- */

	.ceilings { display: grid; gap: 1.2rem 2.2rem; margin-top: 1.3rem;
		grid-template-columns: repeat(auto-fit, minmax(min(100%, 11rem), 1fr)); }
	.ceilings > div { border-left: 4px solid var(--amarelo); padding-left: .9rem; }
	.ceilings b { display: block; font-family: 'Bowlby One', Impact, sans-serif;
		font-weight: 400; font-size: clamp(1.8rem, 5vw, 2.6rem); line-height: 1;
		color: var(--amarelo); }
	.ceilings .unit { font-family: 'Archivo', sans-serif; font-style: normal;
		font-weight: 800; font-size: .42em; margin-left: .14em; color: inherit; }
	.ceilings span { display: block; margin-top: .4rem; font-size: .7rem;
		font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
	.ceilings small { display: block; margin-top: .2rem; font-size: .82rem;
		color: rgba(255,245,216,.68); }

	/* ---- the gaps ------------------------------------------------------- */

	.gaps { margin: 1.1rem 0 0; padding: 0; list-style: none; display: grid; gap: .6rem; }
	.gaps li { position: relative; padding-left: 1.1rem; max-width: 64ch;
		font-size: .98rem; font-weight: 500; line-height: 1.6; color: var(--ink-soft); }
	.gaps li::before { content: ''; position: absolute; left: 0; top: .62em;
		width: .45rem; height: .45rem; border-radius: 2px; background: var(--sangria); }
	.gaps b { color: var(--ink); font-weight: 700; }
	.later { margin-top: 2.6rem; }
</style>
