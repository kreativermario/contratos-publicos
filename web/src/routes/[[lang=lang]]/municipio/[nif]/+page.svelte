<script lang="ts">
	import { untrack } from 'svelte';
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import SkeletonTable from '$lib/components/SkeletonTable.svelte';
	import { L, t } from '$lib/messages';
	import Municipio from './Municipio.svelte';
	import type { Loaded } from './+page';

	let { data } = $props();

	// The load returns at once and hands over one promise, so this is where the
	// wait is shown. A new município starts from the skeleton. A new window on
	// the same one keeps the page it has, dimmed, until the new numbers land:
	// flashing back to a skeleton on every year chip would throw away the tab,
	// the scroll and every open row for what is only a change of period.
	let shown = $state<Loaded | null>(null);
	let pending = $state(true);
	let failed = $state<number | null>(null);

	$effect(() => {
		const { rest, ...win } = data;
		let live = true;
		pending = true;
		failed = null;
		untrack(() => { if (shown && shown.nif !== win.nif) shown = null; });
		rest.then(
			(r) => { if (live) { shown = { ...win, ...r }; pending = false; } },
			// `api()` puts the status first in its message; a 404 is a NIF with no
			// contracts, anything else is ours
			(e: Error) => { if (live) { failed = Number(e?.message?.slice(0, 3)) || 500; pending = false; } }
		);
		return () => { live = false; };
	});

	const errKey = $derived(failed === 404 ? 404 : 500);
</script>

{#if failed}
	<Nav />
	<main class="wrap failed">
		<h1>{t(`err.${errKey}.title`)}</h1>
		<p>{t(`err.${errKey}.body`)}</p>
		<a href={L('/')}>{t('err.home')}</a>
	</main>
	<Footer />
{:else if shown}
	<div class="live" class:stale={pending} aria-busy={pending}>
		<Municipio data={shown} />
	</div>
{:else}
	<!-- Shaped like the page it stands in for: the hero, its three plates, the
	     two indices and the tab bar, so nothing jumps when the data arrives. -->
	<Nav />
	<main class="skeleton" aria-busy="true">
		<span class="sr" role="status">{t('nav.loading')}</span>
		<section class="hero">
			<div class="wrap">
				<Skeleton w="18rem" h=".75rem" />
				<span class="title"><Skeleton w="min(34rem, 80%)" h="clamp(2.8rem, 11vw, 6rem)" /></span>
				<div class="plates">
					{#each [0, 1, 2] as i (i)}<span><Skeleton h="4.2rem" /></span>{/each}
				</div>
				<div class="indices">
					<Skeleton h="11rem" />
					<Skeleton h="11rem" />
				</div>
			</div>
		</section>
		<div class="tabbar"><div class="wrap"><Skeleton w="min(30rem, 100%)" h="1.1rem" /></div></div>
		<div class="wrap body"><SkeletonTable rows={4} /></div>
	</main>
{/if}

<style>
	/* opacity only, so it runs on the compositor and never reflows the page */
	.live { transition: opacity .2s ease; }
	.live.stale { opacity: .55; pointer-events: none; transition-delay: .15s; }

	.hero { padding: 2.75rem 0 2rem; border-bottom: 2px solid var(--ink); }
	.title { display: block; margin: 1.1rem 0 1.4rem; }
	.plates { display: grid; grid-template-columns: repeat(3, minmax(0, 11rem)); gap: .9rem; margin-bottom: 1.6rem; }
	.indices { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.6fr); gap: 1.25rem; }
	.tabbar { background: var(--paper-3); border-bottom: 2px solid var(--ink); padding: 1rem 0; }
	.body { padding: 2rem 0 4rem; }

	.failed { padding: 4rem 0 5rem; }
	.failed p { color: var(--ink-soft); }

	.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }

	@media (max-width: 820px) {
		.indices { grid-template-columns: 1fr; }
		.plates { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .5rem; }
	}
</style>
