<script lang="ts">
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { lang, t } from '$lib/messages';
	import { reveal } from '$lib/reveal';
</script>

<svelte:head>
	<title>{t('terms.title')} · {t('common.site')}</title>
	<meta name="description" content={t('terms.description')} />
</svelte:head>

<Nav municipalities={[]} current={null} />

<main>
	<section class="head" use:reveal>
		<div class="wrap">
			<p class="eyebrow" data-in style="--i:0">Onde Vai Parar · termos e condições</p>
			<h1 class="poster" data-in style="--i:1"><span>Termos e condições</span></h1>
			<p class="lede" data-in style="--i:2">
				O que este site é, de onde vêm os números, o que podes fazer com eles, e
				o que fazer se encontrares um erro. Em português simples, porque o
				objetivo do site é exatamente esse.
			</p>
			<!-- Untranslated on purpose: these are terms, and an approximate English
			     version of terms is worse than none. -->
			{#if lang() === 'en'}
				<p class="ptonly" data-in style="--i:3">{t('ptOnly.note')}</p>
			{/if}
		</div>
	</section>

	<div class="stripe" aria-hidden="true"><b></b><b></b><b></b><b></b></div>

	<div class="wrap prose">
		<h2 class="sectag">O que isto é</h2>
		<p>
			Este site lê o registo público de contratos que as câmaras municipais
			portuguesas são obrigadas a publicar, e mostra o que lá está. O tom é
			satírico; os números não são. Nada aqui é uma investigação, um parecer
			jurídico ou um relatório de auditoria.
		</p>

		<h2 class="sectag">Nada aqui é acusação de crime</h2>
		<p>
			Todos os procedimentos medidos neste site são legais. O ajuste direto está
			previsto na lei. Os indicadores medem sinais observáveis no registo, como
			a percentagem do dinheiro entregue sem concurso ou o número de concursos
			com um só concorrente, e <b>um valor alto quer dizer que vale a pena
			olhar, não que houve irregularidade</b>. Um valor baixo também não é um
			atestado de bom comportamento.
		</p>
		<p>
			Os nomes de empresas, de autarcas e de adjudicatários aparecem aqui porque
			constam de um registo público, e apenas nessa qualidade. Não fazemos
			juízos sobre pessoas.
		</p>

		<h2 class="sectag">De onde vêm os dados</h2>
		<ul class="sources">
			<li>
				<b>Contratos públicos:</b> ficheiros que o IMPIC publica em
				<a href="https://dados.gov.pt/" target="_blank" rel="noreferrer noopener">dados.gov.pt</a>,
				o mesmo registo que alimenta o Portal BASE.
			</li>
			<li>
				<b>Resultados autárquicos:</b> publicações da Administração Interna.
				São a contagem provisória; o registo com valor legal é o Mapa Oficial
				da Comissão Nacional de Eleições.
			</li>
			<li>
				<b>Atividades e sede das empresas:</b> o SICAE, o registo de CAE do
				Ministério da Justiça, e o VIES da Comissão Europeia.
			</li>
			<li>
				<b>Geografia:</b> os limites dos concelhos, agregados por nós em
				distritos.
			</li>
		</ul>
		<p>
			<b>Não corrigimos nada.</b> O que esteja errado, em falta ou escrito de
			três maneiras diferentes na origem aparece aqui tal e qual, porque a
			alternativa seria inventar. Onde um número não pode ser calculado,
			dizemos "N/A" e explicamos porquê, em vez de mostrar um zero.
		</p>

		<h2 class="sectag">O que não conseguimos saber</h2>
		<p>
			Vale a pena dizer o que falta, porque a ausência também é informação:
		</p>
		<ul class="sources">
			<li><b>Quem concorreu</b> só é declarado em cerca de 42% dos contratos.</li>
			<li><b>O valor realmente pago</b> quase nunca é publicado, por isso não há aqui derrapagens.</li>
			<li><b>A data de constituição de uma empresa</b> não existe de forma gratuita: o registo comercial só está publicado online a partir de 2006.</li>
			<li><b>O capital social e o número de trabalhadores</b> não estão disponíveis por nenhuma via gratuita e automatizável. Não inventamos um substituto.</li>
		</ul>

		<h2 class="sectag">O que podes fazer com isto</h2>
		<p>
			Os dados de origem são públicos e continuam a pertencer a quem os publica,
			com as licenças que essas entidades definem. O que é nosso, ou seja o
			texto, o desenho, os indicadores e a forma como são calculados, podes
			usar livremente desde que digas de onde veio e ligues para aqui.
		</p>
		<p>
			A API está aberta e sem autenticação. Há um limite de pedidos por minuto
			para o serviço não cair; se precisares de mais do que isso, diz, é mais
			fácil dar-te o ficheiro do que veres-te às voltas com o limite.
		</p>

		<h2 class="sectag">O que sabemos sobre quem lê</h2>
		<p>
			Nada que te identifique. Este site não usa cookies próprios, não guarda
			nada no teu browser e não corre nenhum serviço de estatísticas de
			terceiros: não há Google Analytics, não há píxeis de seguimento e não há
			publicidade. É também por isso que não encontras aqui uma janela a pedir
			consentimento para cookies. Não haveria nada para consentir, e uma janela
			dessas num site que não recolhe nada seria só teatro.
		</p>
		<p>
			O que existe são registos técnicos, do tipo que qualquer servidor mantém.
			O site é servido através da Cloudflare, que termina a ligação e guarda
			registos de curta duração, incluindo o endereço IP, para proteger o
			serviço de abuso e de ataques; os nossos servidores mantêm registos de
			acesso pela mesma razão. Quando essa proteção é acionada, a Cloudflare
			pode colocar um cookie técnico no teu browser, apenas para distinguir uma
			pessoa de um robô. Serve só para isso, não te segue entre sites e não
			alimenta publicidade nenhuma.
		</p>
		<p>
			Esse tratamento assenta no interesse legítimo em manter o serviço de pé e
			seguro, nos termos do RGPD. Não cruzamos esses registos com mais nada, não
			os vendemos e não os damos a ninguém. Se quiseres saber o que existe sobre
			ti, ou pedir que seja apagado, escreve para o endereço no fim desta página.
		</p>

		<h2 class="sectag">Sem garantias</h2>
		<p>
			O site é fornecido como está. Fazemos o possível para que os números
			estejam certos e o código é verificável, mas não garantimos exatidão,
			disponibilidade nem adequação a qualquer fim. Antes de agir com base em
			alguma coisa que leste aqui, <b>confirma no registo original</b>: cada
			contrato traz a ligação para a sua ficha.
		</p>

		<h2 class="sectag">Encontrei um erro, ou o meu nome está aqui</h2>
		<p>
			Se o erro é nosso, queremos saber e corrigimos. Se está no registo
			original não o podemos corrigir aqui, mas também queremos saber, porque
			vale a pena dizê-lo na página onde aparece.
		</p>
		<p>
			Se és uma pessoa singular e o teu nome aparece por teres contratado com
			uma câmara, esse facto consta de um registo público e é dele que vem. Se
			mesmo assim quiseres falar sobre isso, fala.
		</p>
		<!-- The only address published anywhere on the site. It is a catch-all, so
		     if it ever drowns in spam it can be replaced without touching the
		     mailbox behind it. -->
		<p>
			Em qualquer destes casos, escreve para
			<a href="mailto:contacto@ondevaiparar.com">contacto@ondevaiparar.com</a>.
		</p>

		<p class="fine">
			Última atualização destes termos: setembro de 2026.
		</p>
	</div>
</main>

<Footer />

<style>
	/* The English note on a page that stays Portuguese. */
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

	.prose { padding: 2.4rem 0 3.5rem; }
	.prose p { margin: .8rem 0 0; max-width: 66ch; font-size: 1rem;
		font-weight: 500; line-height: 1.65; color: var(--ink-soft); }
	.prose p b { color: var(--ink); font-weight: 700; }
	.prose .sectag { margin-top: 2.4rem; }
	.prose .sectag:first-child { margin-top: 0; }

	.sources { margin: 1rem 0 0; padding: 0; list-style: none; display: grid; gap: .6rem; }
	.sources li {
		position: relative; padding-left: 1.1rem; max-width: 66ch;
		font-size: .98rem; font-weight: 500; line-height: 1.6; color: var(--ink-soft);
	}
	.sources li::before {
		content: ''; position: absolute; left: 0; top: .62em;
		width: .45rem; height: .45rem; border-radius: 2px; background: var(--sangria);
	}
	.sources b { color: var(--ink); font-weight: 700; }

	.fine { margin-top: 2.4rem; font-size: .84rem; color: var(--ink-faint); }
</style>
