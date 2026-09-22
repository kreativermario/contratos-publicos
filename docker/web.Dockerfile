# Context is ./web ; nginx config arrives as a named build context.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . ./
# The canonical origin is compiled in: canonical, hreflang, og:* and the
# generated sitemap/robots all carry it, and none of them can be rewritten at
# runtime because the files are static.
ARG PUBLIC_SITE_URL=https://ondevaiparar.com
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.31-alpine
COPY --from=nginxconf security-headers.conf /etc/nginx/security-headers.conf
COPY --from=nginxconf default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/build /usr/share/nginx/html
USER 101
EXPOSE 8080
