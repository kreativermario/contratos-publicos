# Context is ./web ; nginx config arrives as a named build context.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . ./
# The canonical origin is compiled in: canonical, hreflang, og:* and the
# generated sitemap/robots all carry it, and none of them can be rewritten at
# runtime because the files are static.
# The .pt, never the .com. The .com is registered and 301s to it at Cloudflare,
# so building with it here bakes a redirecting domain into every canonical link,
# the hreflang pair, the sitemap and robots.txt, which is the one thing a
# canonical must never be. vite.config.ts was corrected for this and this file
# was missed, so production has been shipping the .com.
ARG PUBLIC_SITE_URL=https://ondevaiparar.pt
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.31-alpine
COPY --from=nginxconf security-headers.conf /etc/nginx/security-headers.conf
COPY --from=nginxconf default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/build /usr/share/nginx/html
USER 101
EXPOSE 8080
