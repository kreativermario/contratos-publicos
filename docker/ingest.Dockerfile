# Context is ./ingest ; the shared core package arrives as a named build context.
#   docker compose build ingest
FROM ghcr.io/astral-sh/uv:0.13.10@sha256:a3ea1357342c1a4bf9a0c53a3deb1b55379aefa037338d8113d5771efa01774f AS uv

FROM python:3.15-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd AS build
COPY --from=uv /uv /bin/uv
WORKDIR /src
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1
COPY --from=core . ./core
COPY . ./ingest
# musllinux wheels exist for psycopg-binary and pydantic-core, so no toolchain needed
RUN uv venv /venv \
 && VIRTUAL_ENV=/venv uv pip install --require-hashes -r ingest/requirements.txt \
 && VIRTUAL_ENV=/venv uv pip install --no-deps --no-build-isolation ./core ./ingest

FROM python:3.15-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd
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
