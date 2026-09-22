// Static build: nginx serves the shell, the browser talks to the API.
// No Node runtime in production, which is what makes the container read-only.
export const ssr = false;
export const prerender = false;
