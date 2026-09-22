<script lang="ts">
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { Municipality } from '$lib/api';
	import { L, lang, swap, t } from '$lib/messages';

	let { municipalities = [], current, onpick }: {
		municipalities?: Municipality[];
		current?: Municipality | null;
		onpick?: (nif: string) => void;
	} = $props();

	let open = $state(false);

	// Picking a município from the menu navigates within the same route, so this
	// component is reused and `open` survived: the panel stayed over the newly
	// loaded page. afterNavigate covers that case and every other one.
	afterNavigate(() => (open = false));

	function onKey(event: KeyboardEvent) {
		if (event.key === 'Escape' && open) open = false;
	}

	// Six quick taps on the wordmark. Each one still goes home as usual, so the
	// counting costs the ordinary click nothing; only the sixth is intercepted.
	// The Nav survives client-side navigation, which is what lets the run carry
	// across those five trips to the homepage.
	const EGG_CLICKS = 6;
	const EGG_WINDOW = 1500;
	let taps = 0;
	let lastTap = 0;

	function onBrand(event: MouseEvent) {
		const now = Date.now();
		taps = now - lastTap < EGG_WINDOW ? taps + 1 : 1;
		lastTap = now;
		if (taps < EGG_CLICKS) return;
		taps = 0;
		event.preventDefault();
		goto(L('/malandro'));
	}
</script>

<svelte:window onkeydown={onKey} />

{#if open}
	<!-- a catcher, so a tap anywhere else closes the panel the way a menu should -->
	<button type="button" class="scrim" aria-label={t('nav.closeMenu')} onclick={() => (open = false)}></button>
{/if}

<header>
	<div class="wrap bar">
		<a class="brand" href={L('/')} onclick={onBrand}>
			<img class="mark" src="/favicon.svg" alt="" width="26" height="26" />
			<span class="word">Onde Vai Parar</span>
		</a>

		<button class="burger" aria-expanded={open} aria-controls="navmenu"
			onclick={() => (open = !open)}>
			<span class="sr">{t('nav.menu')}</span>☰
		</button>

		<nav id="navmenu" class:open aria-label={t('nav.main')}>
			{#if municipalities.length > 1}
				<label class="picker">
					<span class="sr">{t('nav.municipality')}</span>
					<select value={current?.nif} onchange={(e) => onpick?.(e.currentTarget.value)}>
						{#each municipalities as m (m.nif)}
							<option value={m.nif}>{m.name}</option>
						{/each}
					</select>
				</label>
			{:else if current}
				<span class="single">{current.name}</span>
			{/if}
			<a href={L('/panorama')}>{t('nav.panorama')}</a>
			<a href={L('/faqs')}>{t('nav.faqs')}</a>
			<!-- The same page in the other language, never the home page: dropping
			     the reader back at the root on a language switch loses whatever they
			     were reading, which is the one thing a switch must not do. -->
			<a class="lang" href={swap(page.url.pathname, lang() === 'en' ? 'pt' : 'en')}
				hreflang={lang() === 'en' ? 'pt-PT' : 'en'}
				data-sveltekit-reload
				aria-label={t('nav.language')}
				>{lang() === 'en' ? t('nav.toPortuguese') : t('nav.toEnglish')}</a>
		</nav>
	</div>
	<div class="stripe" aria-hidden="true"></div>
</header>

<style>
	header { position: sticky; top: 0; z-index: 20; background: var(--paper-2); border-bottom: 2px solid var(--ink); }
	.bar { display: flex; align-items: center; gap: 1rem; min-height: 4rem; }
	.brand { display: flex; align-items: center; gap: .55rem; text-decoration: none; color: var(--ink); margin-right: auto; }
	/* the gauge, matching the favicon and the preview card; the emoji it replaced
	   was the last of a decorative layer that was already removed elsewhere */
	.mark { width: 1.6rem; height: 1.6rem; flex: none; }
	.word { font-family: 'Bowlby One', Impact, sans-serif; font-size: 1.35rem; text-transform: uppercase; letter-spacing: -.01em; }
	nav { display: flex; align-items: center; gap: 1.25rem; font-size: .9rem; font-weight: 600; }
	nav a { color: var(--ink-soft); text-decoration: none; }
	nav a:hover { color: var(--sangria); text-decoration: underline; }
	.single { font-weight: 700; color: var(--ink); }
	/* A switch, not a menu item: boxed so it does not read as a fourth section. */
	nav a.lang {
		font-size: .78rem; font-weight: 800; letter-spacing: .04em;
		padding: .3rem .6rem; border: 2px solid var(--ink); border-radius: 999px;
		color: var(--ink); background: var(--paper);
	}
	nav a.lang:hover { background: var(--amarelo); color: var(--ink); text-decoration: none; }
	select {
		/* 16px minimum, or iOS zooms the page when this takes focus */
		font: inherit; font-size: max(1rem, .9rem); font-weight: 700;
		color: var(--ink); background: var(--paper);
		border: 2px solid var(--ink); border-radius: var(--radius); padding: .3rem 2rem .3rem .6rem;
		appearance: none;
		background-image: linear-gradient(45deg, transparent 50%, var(--ink) 50%), linear-gradient(135deg, var(--ink) 50%, transparent 50%);
		background-position: calc(100% - 15px) 52%, calc(100% - 10px) 52%;
		background-size: 5px 5px, 5px 5px; background-repeat: no-repeat;
	}
	/* four festival stripes; the page never starts on a plain edge */
	.stripe { height: 5px; background: linear-gradient(90deg,
		var(--sangria) 0 25%, var(--amarelo) 25% 50%, var(--azulejo) 50% 75%, var(--manjerico) 75% 100%); }
	/* The only door to the whole menu on a phone, so it gets a real target: the
	   padding grows it to about 47px square and the negative margin keeps the
	   bar looking exactly as it did. */
	.burger {
		display: none; background: none; border: 0; font-size: 1.4rem; cursor: pointer;
		color: var(--ink); line-height: 1;
		/* measured at 37x40 with .55rem; a 22px glyph needs more than symmetric
		   padding to clear 44 in both axes */
		min-width: 2.75rem; min-height: 2.75rem; padding: .5rem;
		margin: -.5rem -.5rem -.5rem 0;
		display: none; align-items: center; justify-content: center;
	}
	.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
	.scrim { display: none; }
	@media (max-width: 720px) {
		.scrim {
			display: block; position: fixed; inset: 0; z-index: 19;
			border: 0; padding: 0; cursor: default;
			background: rgba(36, 7, 6, .35);
		}
	}
	@media (max-width: 720px) {
		.burger { display: inline-flex; }
		nav { display: none; position: absolute; inset: calc(4rem + 5px) 0 auto; flex-direction: column; align-items: flex-start;
			gap: .85rem; padding: 1rem 1.25rem; background: var(--paper-2); border-bottom: 2px solid var(--ink); }
		nav.open { display: flex; }
	}
</style>
