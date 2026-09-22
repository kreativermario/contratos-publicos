import type { ParamMatcher } from '@sveltejs/kit';

/**
 * The only language segment there is.
 *
 * `[[lang=lang]]` sits at the top of the route tree, so `/faqs` matches with
 * the parameter absent and `/en/faqs` matches with it set. Rejecting everything
 * but "en" is what keeps `/faqs` from being read as a language: without the
 * matcher, SvelteKit would happily bind lang="faqs" and render the landing.
 */
export const match: ParamMatcher = (param) => param === 'en';
