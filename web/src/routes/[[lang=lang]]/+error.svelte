<script lang="ts">
	import { page } from '$app/state';
	import Footer from '$lib/components/Footer.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import { L, t } from '$lib/messages';

	// Copy per status, so a 404 does not apologise for a server fault and a 500
	// does not tell the reader they typed the address wrong.
	// Copy per status, keyed so both languages carry the same three.
	const KNOWN = [404, 429, 500];

	const status = $derived(page.status ?? 500);
	const key = $derived(KNOWN.includes(status) ? status : status < 500 ? 404 : 500);
	const copy = $derived({
		title: t(`err.${key}.title`),
		body: t(`err.${key}.body`),
		foot: t(`err.${key}.foot`)
	});
	const tone = $derived(status >= 500 ? 'critical' : status === 429 ? 'warn' : 'info');
</script>

<svelte:head>
	<title>{copy.title} · {t('common.site')}</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<Nav />

<main class="wrap">
	<div class="card" data-tone={tone}>
		<p class="eyebrow">{t('common.site')}</p>
		<p class="code num">{status}</p>
		<h1>{copy.title}</h1>
		<p class="body">{copy.body}</p>
		<a class="home" href={L('/')}>{t('err.home')}</a>
		<p class="foot">{copy.foot}</p>
	</div>
</main>

<Footer />

<style>
	main { display: grid; place-items: center; padding: 4rem 0 5rem; }
	.card {
		--tone: var(--azulejo);
		background: var(--paper-2); border: 2px solid var(--ink); border-radius: var(--radius);
		box-shadow: var(--shadow-hard); padding: 2rem 2.2rem 2.2rem; max-width: 34rem; width: 100%;
	}
	.card[data-tone='warn']     { --tone: var(--sev-warn); }
	.card[data-tone='critical'] { --tone: var(--sev-critical); }
	.code {
		font-family: 'Bowlby One', Impact, sans-serif;
		font-size: clamp(3.5rem, 14vw, 6rem); line-height: .9;
		margin: .4rem 0 .2rem; color: var(--tone); letter-spacing: -.02em;
	}
	h1 { font-size: clamp(1.2rem, 4vw, 1.8rem); margin: 0 0 .75rem; }
	.body { margin: 0 0 1rem; color: var(--ink-soft); }
	.home {
		display: inline-block; text-decoration: none; font-weight: 700; font-size: .9rem;
		color: var(--paper); background: var(--ink); border: 2px solid var(--ink);
		border-radius: var(--radius); padding: .5rem 1rem;
	}
	.home:hover { background: var(--sangria); }
	.foot { margin: 1.25rem 0 0; font-size: .78rem; color: var(--ink-faint); }
</style>
