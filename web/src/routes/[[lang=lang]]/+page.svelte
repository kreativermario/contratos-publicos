<script lang="ts">
	import Footer from '$lib/components/Footer.svelte';
	import Landing from '$lib/components/Landing.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { t } from '$lib/messages';

	let { data } = $props();
</script>

<svelte:head>
	<title>{t('common.site')}</title>
	<meta name="description" content={t('common.description')} />
</svelte:head>

<!-- The landing has no município of its own, so the nav picker has nothing to
     show as current; the page itself is the picker. -->
<Nav municipalities={[]} current={null} />

<main>
	<Landing municipalities={data.municipalities} />
</main>

<Footer />
