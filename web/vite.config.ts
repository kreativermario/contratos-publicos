import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// The canonical origin, baked into the shell, the sitemap and robots.txt at
// build time. It is an environment variable because nothing here is hardcoded;
// the default is only so a bare `npm run build` produces a usable site.
//
// Reached through globalThis rather than a bare `process` so the frontend
// tsconfig does not need @types/node for one assignment.
const nodeEnv = (globalThis as { process?: { env: Record<string, string | undefined> } })
	.process?.env;
if (nodeEnv && !nodeEnv.PUBLIC_SITE_URL) nodeEnv.PUBLIC_SITE_URL = 'https://ondevaiparar.pt';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			adapter: adapter({ fallback: 'index.html' }),

			// Hash-based CSP: SvelteKit emits a hash for its one inline bootstrap
			// script, so we never need 'unsafe-inline' for scripts. frame-ancestors
			// is set by nginx instead - a meta-tag CSP cannot carry it.
			csp: {
				mode: 'hash',
				directives: {
					'default-src': ['self'],
					'script-src': ['self'],
					// ECharts writes inline style attributes on the canvas host
					'style-src': ['self', 'unsafe-inline'],
					'img-src': ['self', 'data:'],
					'font-src': ['self'],
					'connect-src': ['self'],
					'object-src': ['none'],
					'base-uri': ['self'],
					'form-action': ['self']
				}
			}
		})
	]
});
