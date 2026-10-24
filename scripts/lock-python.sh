#!/bin/sh
# Regenerate the hash-locked Python requirements. Every image and the CI suite
# install from these with --require-hashes, so a package that changes on PyPI
# under the same version number fails the build instead of shipping.
#
# setuptools is locked too: it builds the three local packages, and an unpinned
# build backend is as much a way in as an unpinned dependency. The local
# packages themselves are never emitted; they are installed from the tree.
set -eu
cd "$(dirname "$0")/.."
UV_IMAGE=ghcr.io/astral-sh/uv:0.13.5-python3.13-alpine
lock() {
  out=$1; shift
  printf '%s\n' "$@" setuptools | docker run --rm -i -v "$PWD:/w" -w /w "$UV_IMAGE" \
    uv pip compile - --universal --python-version 3.13 --generate-hashes \
      --quiet --no-header --no-emit-package contratos-core \
      --no-emit-package contratos-api --no-emit-package contratos-ingest -o "$out"
}
lock api/requirements.txt ./core ./api
lock ingest/requirements.txt ./core ./ingest
lock requirements-test.txt './core[test]' ./api ./ingest
