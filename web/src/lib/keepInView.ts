import { tick } from 'svelte';

/**
 * Keep `el` on screen after the content around it changed height.
 *
 * Filtering a table, switching a tab and expanding a row all replace a tall
 * block with a short one or the other way round. The reader's scroll position
 * is a number of pixels, not a place, so the same number lands somewhere else
 * the moment the document is a different height: filter a 9000px table down to
 * four rows and the browser clamps you to the new bottom, which is a part of
 * the page you never asked to see. On a phone, where the whole viewport is one
 * or two of these blocks, it happens on nearly every interaction.
 *
 * So: after the DOM has settled, if the thing the reader just used has drifted
 * above the top of the window, bring it back to the top. If it is still in
 * view, do nothing, because moving the page under someone who can already see
 * what they clicked is its own kind of wrong.
 *
 * Awaits `tick()` on purpose. Measuring before Svelte has applied the update
 * reads the old layout, which is the geometry that just stopped being true.
 */
export async function keepInView(el: HTMLElement | undefined) {
	if (!el) return;
	await tick();
	if (el.getBoundingClientRect().top >= 0) return;
	const still = typeof matchMedia === 'function'
		&& matchMedia('(prefers-reduced-motion: reduce)').matches;
	el.scrollIntoView({ block: 'start', behavior: still ? 'auto' : 'smooth' });
}
