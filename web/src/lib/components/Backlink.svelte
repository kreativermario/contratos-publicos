<script lang="ts">
	/**
	 * The way back out of a detail page.
	 *
	 * `/empresa` and `/contrato` are reached from inside a município, but they
	 * render the nav with no município selected, so the tabs and the picker are
	 * gone and the only route back is the browser's own button. This puts the
	 * trail back on the page: where you came from, and the place it belongs to.
	 */
	import { t } from '$lib/messages';

	let { href, label, secondary = null }: {
		href: string;
		label: string;
		secondary?: { href: string; label: string } | null;
	} = $props();
</script>

<nav class="back" aria-label={t('back.aria')}>
	<a href={href}><span aria-hidden="true">←</span> {label}</a>
	{#if secondary}
		<span class="sep" aria-hidden="true">·</span>
		<a href={secondary.href}>{secondary.label}</a>
	{/if}
</nav>

<style>
	.back {
		display: flex; align-items: center; gap: .5rem; flex-wrap: wrap;
		font-size: .82rem; font-weight: 700; margin-bottom: 1rem;
	}
	.back a { color: var(--ink-soft); text-decoration-thickness: 2px; }
	.back a:hover { color: var(--sangria); }
	.sep { color: var(--ink-faint); }
</style>
