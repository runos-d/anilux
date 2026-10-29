ARG NODE_IMAGE=registry-1.docker.io/library/node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402
ARG NGINX_IMAGE=registry-1.docker.io/library/nginx:alpine@sha256:892bb2152464f0c5d8972593a5f5afaf8054552580b699d95f8ff4af08c2d33d
FROM ${NODE_IMAGE} AS build
WORKDIR /app
ARG VITE_YANDEX_METRIKA_ENABLED=false
ARG VITE_YANDEX_METRIKA_ID=
ARG VITE_GOOGLE_ANALYTICS_ENABLED=false
ARG VITE_GOOGLE_ANALYTICS_ID=
ENV VITE_YANDEX_METRIKA_ENABLED=$VITE_YANDEX_METRIKA_ENABLED \
    VITE_YANDEX_METRIKA_ID=$VITE_YANDEX_METRIKA_ID \
    VITE_GOOGLE_ANALYTICS_ENABLED=$VITE_GOOGLE_ANALYTICS_ENABLED \
    VITE_GOOGLE_ANALYTICS_ID=$VITE_GOOGLE_ANALYTICS_ID
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM ${NGINX_IMAGE}
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY --chmod=755 40-seo-shell.sh /docker-entrypoint.d/40-seo-shell.sh
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/health || exit 1
