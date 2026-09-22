/**
 * Is the viewport a phone right now?
 *
 * Several charts need a different option object below the stacking breakpoint,
 * not just different CSS: a 640px map with one-finger panning leaves a phone
 * reader no page to scroll on. One shared listener rather than one per chart.
 */
import { readable } from 'svelte/store';

const QUERY = '(max-width: 820px)';

export const narrow = readable(false, (set) => {
	if (typeof window === 'undefined' || !window.matchMedia) return;
	const mq = window.matchMedia(QUERY);
	set(mq.matches);
	const on = (e: MediaQueryListEvent) => set(e.matches);
	mq.addEventListener('change', on);
	return () => mq.removeEventListener('change', on);
});
