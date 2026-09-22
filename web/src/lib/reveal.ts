/**
 * Plays a page's load-in once it is actually on screen.
 *
 * Firing on mount would mean a section below the fold finished animating before
 * anyone scrolled to it, which is the same as not animating at all. Disconnects
 * after the first run: this is an entrance, not a scroll effect.
 */
export function reveal(node: HTMLElement) {
	// Marks the subtree as animated. The CSS hides `[data-in]` only under this
	// class, so an element tagged for the load-in whose ancestor never got the
	// action simply renders, instead of sitting at opacity 0 forever and leaving
	// a hole in the page. That bug cost the overview its whole index row.
	node.classList.add('reveal');

	if (typeof IntersectionObserver === 'undefined') {
		node.classList.add('run');
		return {};
	}
	const io = new IntersectionObserver(
		(entries) => {
			if (!entries.some((e) => e.isIntersecting)) return;
			node.classList.add('run');
			io.disconnect();
		},
		// threshold 0, not a fraction. A fraction of the element has to be on
		// screen for the callback to fire, and these sections are taller than the
		// window: 12% of a 9000px table of suppliers is 1080px, which never fits
		// in a 900px viewport, so the Empresas tab never ran and its whole table
		// sat at opacity 0. A small negative bottom margin gives the same "just
		// scrolled in" feel without depending on the element's height.
		{ threshold: 0, rootMargin: '0px 0px -8% 0px' }
	);
	io.observe(node);

	// If anything about the observer misbehaves, the content still appears. A
	// load-in is decoration; it must never be the reason a page is blank.
	const failsafe = setTimeout(() => {
		node.classList.add('run');
		io.disconnect();
	}, 2000);

	return {
		destroy: () => {
			clearTimeout(failsafe);
			io.disconnect();
		}
	};
}
