<script lang="ts">
	import '../app.css';
	import { locale } from '$lib/messages';

	let { children } = $props();

	// The shell is one static file for both languages, so `<html lang>` cannot be
	// written at build time. It has to follow the route, or a screen reader and
	// every translation tool read the English pages as Portuguese.
	$effect(() => {
		document.documentElement.lang = locale();
	});
</script>

{@render children()}
