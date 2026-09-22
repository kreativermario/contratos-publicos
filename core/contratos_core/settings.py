"""Every knob lives here, and every knob comes from the environment.

Nothing in this codebase is specific to one municipality: `municipality_nifs`
scopes ingest and may be empty, meaning the whole country.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# pydantic-settings JSON-decodes complex types straight from the environment,
# before any validator runs - so MUNICIPALITY_NIFS=504293125 or API_CORS_ORIGINS=*
# would raise before we ever see them. NoDecode hands us the raw string instead.
CsvList = Annotated[list[str], NoDecode]
YearList = Annotated[list[int], NoDecode]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    database_url: str = Field(..., alias="DATABASE_URL")
    db_pool_max: int = Field(10, alias="DB_POOL_MAX")

    # ---- ingest scope ----
    municipality_nifs: CsvList = Field(default_factory=list, alias="MUNICIPALITY_NIFS")
    impic_years: YearList = Field(default_factory=list, alias="IMPIC_YEARS")
    impic_dataset_contracts: str = Field("", alias="IMPIC_DATASET_CONTRACTS")
    impic_dataset_entities: str = Field("", alias="IMPIC_DATASET_ENTITIES")
    dados_gov_api: str = Field("https://dados.gov.pt/api/1", alias="DADOS_GOV_API")
    workdir: str = Field("/data", alias="WORKDIR")
    batch_size: int = Field(20_000, alias="INGEST_BATCH_SIZE")

    # ---- apiaberta ----
    apiaberta_base: str = Field("https://api.apiaberta.pt/v1/base", alias="APIABERTA_BASE")
    apiaberta_key: str = Field("", alias="APIABERTA_KEY")
    apiaberta_rate_per_min: int = Field(30, alias="APIABERTA_RATE_PER_MIN")
    apiaberta_page_size: int = Field(100, alias="APIABERTA_PAGE_SIZE")
    apiaberta_delta_stop_after: int = Field(200, alias="APIABERTA_DELTA_STOP_AFTER")

    # ---- api ----
    api_cors_origins: CsvList = Field(default_factory=lambda: ["*"], alias="API_CORS_ORIGINS")
    default_municipality_nif: str = Field("", alias="DEFAULT_MUNICIPALITY_NIF")
    # Four numbers, because a browser and a CDN want different answers.
    # cache_seconds is the SHARED ttl (s-maxage): how long Cloudflare may hold a
    # response. The browser gets a much shorter one, so a reader who refreshes
    # sees movement, while the expensive aggregate is still served from the edge.
    cache_seconds: int = Field(3600, alias="CACHE_SECONDS")
    cache_browser_seconds: int = Field(300, alias="CACHE_BROWSER_SECONDS")
    # Serve the stale copy instantly and refresh behind it. On two cores this is
    # the difference between a reader waiting for a cold aggregate and never
    # knowing one ran.
    cache_stale_while_revalidate: int = Field(86400, alias="CACHE_STALE_WHILE_REVALIDATE")
    # If the origin is down, keep serving the last good answer rather than an
    # error page. Contract data is a slow public record; week-old figures beat
    # no figures.
    cache_stale_if_error: int = Field(604800, alias="CACHE_STALE_IF_ERROR")
    # nginx proxies /api/ and strips the prefix, so the app is mounted at / but
    # reached at /api. Without this the docs page asks for /openapi.json, which
    # the SPA fallback answers with index.html and Swagger UI rejects.
    api_root_path: str = Field("/api", alias="API_ROOT_PATH")
    # Versioned surface. nginx keeps proxying /api/ generically, so a future /v2
    # is a change here and nowhere else. /health stays outside it.
    api_version_prefix: str = Field("/v1", alias="API_VERSION_PREFIX")

    # ---- scoring: procurement ceilings are statutory and get amended ----
    ad_limit_services: float = Field(20_000, alias="AD_LIMIT_SERVICES")
    ad_limit_works: float = Field(30_000, alias="AD_LIMIT_WORKS")
    consulta_previa_limit: float = Field(75_000, alias="CONSULTA_PREVIA_LIMIT")
    threshold_surf_band: float = Field(0.05, alias="THRESHOLD_SURF_BAND")
    # A firm counts as a newcomer if it won here within this many days of its
    # first appearance anywhere in the public-contract record. No dataset
    # publishes incorporation dates, so that debut is the only proxy there is.
    newcomer_days: int = Field(365, alias="NEWCOMER_DAYS")
    # A supplier whose name carries no legal form is, in practice, a person
    # rather than a company: Portuguese firm names must state the form by law.
    # One person invoicing a câmara is perfectly legal and extremely common at
    # small values, so the flag only fires above a value a single person being
    # paid directly starts to look worth a second look at.
    person_flag_min: float = Field(25_000, alias="PERSON_FLAG_MIN")

    # ---- company registry lookup (off by default: it calls out to the internet)
    company_lookup_enabled: bool = Field(False, alias="COMPANY_LOOKUP_ENABLED")
    company_api_base: str = Field("https://api.ptdata.org/v1", alias="COMPANY_API_BASE")
    # sicae.pt refuses port 443 outright, so this is plain HTTP by necessity.
    # It carries no credentials and asks a public register a public question.
    company_sicae_base: str = Field("http://www.sicae.pt", alias="COMPANY_SICAE_BASE")
    # the only free source that carries a founding year at all; empty disables it
    company_founded_base: str = Field("https://empresadb.pt", alias="COMPANY_FOUNDED_BASE")
    company_timeout: float = Field(6.0, alias="COMPANY_TIMEOUT")
    company_cache_days: int = Field(30, alias="COMPANY_CACHE_DAYS")

    @field_validator("database_url", mode="after")
    @classmethod
    def _use_psycopg3(cls, v: str) -> str:
        """SQLAlchemy maps a bare postgresql:// URL to psycopg2, which we do not
        ship. Keep DATABASE_URL plain in .env and fix the driver here."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg://", 1)
        return v

    @field_validator("municipality_nifs", "api_cors_origins", mode="before")
    @classmethod
    def _csv(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("impic_years", mode="before")
    @classmethod
    def _years(cls, v):
        """Accepts '2012-2026', '2024,2025' or ''  (= whatever IMPIC publishes)."""
        if not isinstance(v, str):
            return v
        out: set[int] = set()
        for part in (p.strip() for p in v.split(",") if p.strip()):
            lo, sep, hi = part.partition("-")
            out.update(range(int(lo), int(hi) + 1) if sep else [int(part)])
        return sorted(out)

    @property
    def scope_nifs(self) -> set[str]:
        return set(self.municipality_nifs)

    @property
    def thresholds(self) -> tuple[float, ...]:
        return (self.ad_limit_services, self.ad_limit_works, self.consulta_previa_limit)


@lru_cache
def get_settings() -> Settings:
    return Settings()
