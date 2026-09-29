-- One-off: move the two links out of contracts.raw and drop the column.
--
-- Run AFTER the deploy that replaced `raw` with link_pieces/link_announcement
-- in the ORM, never before: until then the API maps `raw`, `select(Contract)`
-- names it, and dropping it would 500 every page.
--
--   ssh deploy@<box> "podman exec -i stack-db-1 sh -c \
--     'psql -U \"\$POSTGRES_USER\" -d \"\${POSTGRES_DB:-\$POSTGRES_USER}\" -v ON_ERROR_STOP=1'" \
--     < scripts/shed_raw.sql
--
-- Why a rewrite and not an UPDATE: UPDATE writes a second version of all 2.26M
-- rows, grows the file, and leaves VACUUM FULL still to do. One ALTER TABLE
-- with USING rewrites the table once; every USING is evaluated against the old
-- row, so the links are read out of `raw` in the same pass that empties it.
-- The coalesce keeps a link the new ingest may already have written.
--
-- Takes an ACCESS EXCLUSIVE lock for the length of the rewrite, a few minutes:
-- uncached API requests wait, cached ones are served from the edge. Needs free
-- disk for the new copy (about 1.5 GB) while the old one still exists.
\timing on

ALTER TABLE contracts
    ADD COLUMN IF NOT EXISTS link_pieces text,
    ADD COLUMN IF NOT EXISTS link_announcement text;

ALTER TABLE contracts
    ALTER COLUMN link_pieces TYPE text
        USING coalesce(link_pieces, nullif(raw->>'linkPecasProc', '')),
    ALTER COLUMN link_announcement TYPE text
        USING coalesce(link_announcement, nullif(raw->>'linkAnuncio', '')),
    ALTER COLUMN raw TYPE jsonb USING NULL::jsonb;

-- Every value is NULL now, so this is a catalogue change, not another rewrite.
ALTER TABLE contracts DROP COLUMN raw;

VACUUM (ANALYZE) contracts;

SELECT pg_size_pretty(pg_relation_size('contracts')) AS heap,
       pg_size_pretty(pg_total_relation_size('contracts')) AS total;
