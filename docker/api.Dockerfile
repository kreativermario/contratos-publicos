# Context is ./api ; the shared core package arrives as a named build context.
#   docker compose build api
FROM ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 AS uv

FROM python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741 AS build
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

FROM python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741
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
