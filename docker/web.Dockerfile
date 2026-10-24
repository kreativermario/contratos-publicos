# Context is ./web ; nginx config arrives as a named build context.
FROM node:24-alpine@sha256:06d7adf3e0ef61a13f1d28682726366f97a15aa1888c934d3ecec86c33918b53 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . ./
# The canonical origin is compiled in: canonical, hreflang, og:* and the
# generated sitemap/robots all carry it, and none of them can be rewritten at
# runtime because the files are static.
# It is spelled in four defaults (here, vite.config.ts, deploy.yml and
# docker-compose.yml) and vars.PUBLIC_SITE_URL beats them all: change one,
# check the rest, or a stale domain ships in every canonical link.
ARG PUBLIC_SITE_URL=https://ondevaiparar.com
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL
# A second sitemap for an alternate domain, should one ever redirect here. Nothing
# else in the build reads it and empty writes no file. See scripts/prerender.mjs.
ARG PRERENDER_ALT_SITE=
ENV PRERENDER_ALT_SITE=$PRERENDER_ALT_SITE
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.31-alpine@sha256:b5047b9b76845eac124358373c6852377c52e4b05834a47647e955dd91cb8f1e
COPY --from=nginxconf security-headers.conf /etc/nginx/security-headers.conf
COPY --from=nginxconf default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/build /usr/share/nginx/html
USER 101
EXPOSE 8080
