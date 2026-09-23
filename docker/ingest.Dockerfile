# Context is ./ingest ; the shared core package arrives as a named build context.
#   docker compose build ingest
FROM ghcr.io/astral-sh/uv:0.12.17 AS uv

FROM python:3.13-alpine AS build
COPY --from=uv /uv /bin/uv
WORKDIR /src
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1
COPY --from=core . ./core
COPY . ./ingest
# musllinux wheels exist for psycopg-binary and pydantic-core, so no toolchain needed
RUN uv venv /venv \
 && VIRTUAL_ENV=/venv uv pip install ./core ./ingest

FROM python:3.13-alpine
RUN adduser -D -u 10001 -h /home/app app
COPY --from=build /venv /venv
ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app \
    WORKDIR=/data
# A fresh named volume inherits ownership from the image path it mounts over,
# so creating /data as uid 10001 here avoids needing a root init container.
RUN mkdir -p /data && chown 10001:10001 /data
WORKDIR /app
USER 10001
# multi-hundred-MB year files land in /data, a volume - never the read-only rootfs
ENTRYPOINT ["python", "-m", "contratos_ingest"]
CMD ["all"]
