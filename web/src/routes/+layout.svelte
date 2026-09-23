<script lang="ts">
	import { navigating, page } from '$app/state';
	import { PUBLIC_SITE_URL } from '$env/static/public';
	import '../app.css';
	import { lang, locale, t } from '$lib/messages';
	import { seoUrls } from '$lib/seo';

	let { children } = $props();

	// The shell is one static file for both languages, so `<html lang>` cannot be
	// written at build time. It has to follow the route, or a screen reader and
	// every translation tool read the English pages as Portuguese.
	$effect(() => {
		document.documentElement.lang = locale();
	});

	// Same reason: one shell serves every route, so the canonical link cannot be
	// baked into app.html. See $lib/seo.
	const urls = $derived(seoUrls(PUBLIC_SITE_URL, page.url.pathname));
</script>

<svelte:head>
	<link rel="canonical" href={lang() === 'en' ? urls.en : urls.pt} />
	<link rel="alternate" hreflang="pt-PT" href={urls.pt} />
	<link rel="alternate" hreflang="en" href={urls.en} />
	<link rel="alternate" hreflang="x-default" href={urls.pt} />
</svelte:head>

<!-- Every page's `load` blocks the navigation while it runs, and the município
     page alone makes seven API calls. Without this the old page simply sits
     there, unchanged, for the whole wait, so clicking again is the correct
     reading of what the interface is showing. One bar in the root layout covers
     every navigation on the site: the picker, the map, a supplier row, a
     contract row, the language switch.

     The delayed fade is not decoration. A cached navigation resolves in tens of
     milliseconds, and a bar that flashes on for one frame reads as a glitch, so
     nothing paints until the wait is long enough to be worth reporting. It is
     an animation-delay rather than a timer because CSS already does this. -->
{#if navigating.to}
	<div class="loading" role="status">
		<span class="sr">{t('nav.loading')}</span>
		<b></b><b></b><b></b><b></b>
	</div>
{/if}

{@render children()}

<style>
	.loading {
		position: fixed;
		inset: 0 0 auto;
		z-index: 100;
		display: flex;
		height: 4px;
		opacity: 0;
		animation: show .12s linear .15s forwards;
		pointer-events: none;
	}
	/* The four-colour stripe, the same divider used under the nav, sliding.
	   Each band is wider than its quarter so the run never shows a gap. */
	.loading b {
		flex: 1;
		animation: slide 1.1s ease-in-out infinite;
	}
	.loading b:nth-child(2) { background: var(--sangria); }
	.loading b:nth-child(3) { background: var(--amarelo); animation-delay: .08s; }
	.loading b:nth-child(4) { background: var(--azulejo); animation-delay: .16s; }
	.loading b:nth-child(5) { background: var(--manjerico); animation-delay: .24s; }

	@keyframes show { to { opacity: 1; } }
	@keyframes slide {
		0%, 100% { transform: scaleX(.35); transform-origin: left; }
		50%      { transform: scaleX(1); transform-origin: left; }
	}

	/* Still tells the reader something is happening, without the motion. */
	@media (prefers-reduced-motion: reduce) {
		.loading b { animation: none; }
	}

	.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
</style>
