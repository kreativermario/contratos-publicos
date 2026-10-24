import { defineEnvVars } from '@sveltejs/kit/env';

// Every variable the frontend reads. Kit 3 wants them declared, which is also
// the one place to see what a build depends on.
export const variables = defineEnvVars({
	PUBLIC_SITE_URL: {
		public: true,
		static: true,
		description:
			'Canonical origin, compiled into canonicals, hreflang, the sitemap and robots.txt. vite.config.ts supplies the default.'
	},
	PUBLIC_API_BASE: {
		public: true,
		// Read when the app starts rather than inlined, so one image works behind
		// any hostname without a rebuild.
		static: false,
		schema: (value) => value || '/api/v1',
		description: 'Where the API lives, relative to the site.'
	}
});
