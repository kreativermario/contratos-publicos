# Context is ./api ; the shared core package arrives as a named build context.
#   docker compose build api
FROM ghcr.io/astral-sh/uv:0.12.17 AS uv

FROM python:3.13-alpine AS build
COPY --from=uv /uv /bin/uv
WORKDIR /src
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1
COPY --from=core . ./core
COPY . ./api
# musllinux wheels exist for psycopg-binary and pydantic-core, so no toolchain needed
RUN uv venv /venv \
 && VIRTUAL_ENV=/venv uv pip install ./core ./api

FROM python:3.13-alpine
RUN adduser -D -u 10001 -h /home/app app
COPY --from=build /venv /venv
ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "contratos_api.app:app", "--host", "0.0.0.0", "--port", "8000", \
     "--no-server-header"]
