<script lang="ts">
	import { page } from '$app/state';
	import { PUBLIC_SITE_URL } from '$env/static/public';
	import '../app.css';
	import { lang, locale } from '$lib/messages';
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

{@render children()}
