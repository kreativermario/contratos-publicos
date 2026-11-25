# Context is ./api ; the shared core package arrives as a named build context.
#   docker compose build api
FROM ghcr.io/astral-sh/uv:0.13.10@sha256:a3ea1357342c1a4bf9a0c53a3deb1b55379aefa037338d8113d5771efa01774f AS uv

FROM python:3.15-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd AS build
COPY --from=uv /uv /bin/uv
WORKDIR /src
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1
COPY --from=core . ./core
COPY . ./api
# musllinux wheels exist for psycopg-binary and pydantic-core, so no toolchain needed
RUN uv venv /venv \
 && VIRTUAL_ENV=/venv uv pip install --require-hashes -r api/requirements.txt \
 && VIRTUAL_ENV=/venv uv pip install --no-deps --no-build-isolation ./core ./api

FROM python:3.15-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd
RUN adduser -D -u 10001 -h /home/app app
COPY --from=build /venv /venv
ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app \
    UVICORN_ROOT_PATH=/api
# nginx proxies /api/ and strips the prefix, so the app is mounted at / but
# reached at /api. uvicorn's root path is what makes /api/docs ask for
# /api/openapi.json instead of /openapi.json, which the SPA fallback would answer
# with index.html. FastAPI's own root_path is deprecated in favour of this.
# Compose sets it from API_ROOT_PATH.
USER 10001
EXPOSE 8000
CMD ["uvicorn", "contratos_api.app:app", "--host", "0.0.0.0", "--port", "8000", \
     "--no-server-header"]
