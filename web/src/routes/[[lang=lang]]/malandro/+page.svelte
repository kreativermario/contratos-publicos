<script lang="ts">
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { L, t } from '$lib/messages';
</script>

<svelte:head>
	<title>{t('egg.head')} · {t('common.site')}</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<Nav municipalities={[]} current={null} />

<main>
	<div class="wrap">
		<section class="egg">
			<p class="eyebrow">{t('egg.eyebrow')}</p>
			<h1 class="poster"><span>{t('egg.title')}</span></h1>
			<p class="lede">{t('egg.lede')}</p>
			<a class="back lift" href={L('/')}>{t('egg.back')}</a>
		</section>
	</div>
</main>

<Footer />

<style>
	main { padding: clamp(2.5rem, 9vw, 6rem) 0; }
	/* rem, not ch: `ch` resolves against the body face, which gave 312px, and a
	   70px display title then broke into seven one-word lines */
	.egg { max-width: 38rem; }
	.egg .lede { max-width: 34ch; }
	.eyebrow { color: var(--sangria); }
	h1 {
		font-size: clamp(2.2rem, 8vw, 4.4rem); margin-top: .9rem;
		text-wrap: balance;
	}
	.lede { margin-top: 1.2rem; font-size: 1.05rem; font-weight: 600; color: var(--ink-soft); }
	.back {
		display: inline-block; margin-top: 1.8rem; padding: .6rem 1.2rem;
		font-weight: 800; font-size: .9rem; text-decoration: none; color: var(--ink);
		background: var(--paper-2); border: 2.5px solid var(--ink);
		border-radius: var(--radius); box-shadow: var(--shadow-hard);
	}
	.back:hover { background: var(--amarelo); }
</style>
