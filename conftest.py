"""Nothing in the suite connects to a database: the router test binds signatures
and the rest are pure functions. `Settings` still demands a URL to import, so
give it one that is syntactically valid and points at nothing.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql://ci:ci@127.0.0.1:5432/ci")
