"""SQLAlchemy models - the single source of truth for the schema.

Both services import these: the API queries through them, the ingest creates the
tables from them (and then bulk-loads with COPY, which the ORM cannot match for
millions of rows).
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, Date, DateTime, ForeignKey, Index,
                        Integer, Numeric, SmallInteger, String, Text, func,
                        text, UniqueConstraint)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)          # idcontrato
    year: Mapped[int | None] = mapped_column(SmallInteger)
    procedure: Mapped[str | None] = mapped_column(Text)                    # tipoprocedimento
    contract_types: Mapped[list[str] | None] = mapped_column(ARRAY(Text))  # tipoContrato
    object: Mapped[str | None] = mapped_column(Text)                       # objectoContrato
    buyer_nif: Mapped[str | None] = mapped_column(String(20))
    buyer_name: Mapped[str | None] = mapped_column(Text)
    value: Mapped[float | None] = mapped_column(Numeric(16, 2))            # precoContratual
    base_price: Mapped[float | None] = mapped_column(Numeric(16, 2))       # precoBaseProcedimento
    signed_date: Mapped[date | None] = mapped_column(Date)
    pub_date: Mapped[date | None] = mapped_column(Date)
    exec_days: Mapped[int | None] = mapped_column(Integer)
    cpv: Mapped[str | None] = mapped_column(String(32))
    cpv_desc: Mapped[str | None] = mapped_column(Text)
    n_bidders: Mapped[int | None] = mapped_column(Integer)                 # NULL = not disclosed
    framework: Mapped[str | None] = mapped_column(Text)
    justification: Mapped[str | None] = mapped_column(Text)
    ad_justification: Mapped[str | None] = mapped_column(Text)
    centralized: Mapped[bool | None] = mapped_column(Boolean)
    green: Mapped[bool | None] = mapped_column(Boolean)
    criterion: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(16), default="impic")       # impic | apiaberta
    raw: Mapped[dict | None] = mapped_column(JSONB)

    suppliers: Mapped[list["ContractSupplier"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan")
    bidders: Mapped[list["ContractBidder"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan")
    locations: Mapped[list["ContractLocation"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_contracts_buyer", "buyer_nif", "signed_date"),
        Index("ix_contracts_year", "year"),
        Index("ix_contracts_procedure", "procedure"),
        Index("ix_contracts_cpv", "cpv"),
        Index("ix_contracts_fts",
              text("to_tsvector('portuguese', coalesce(object, ''))"),
              postgresql_using="gin"),
    )


class ContractSupplier(Base):
    """A contract may be awarded to a consortium - one row per winning firm."""
    __tablename__ = "contract_suppliers"

    contract_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("contracts.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(Text, primary_key=True)
    nif: Mapped[str | None] = mapped_column(String(20))

    contract: Mapped[Contract] = relationship(back_populates="suppliers")
    __table_args__ = (Index("ix_suppliers_nif", "nif"), Index("ix_suppliers_name", "name"))


class ContractBidder(Base):
    """concorrentes: everyone who bid, winner included. Disclosed for ~42% of contracts."""
    __tablename__ = "contract_bidders"

    contract_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("contracts.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(Text, primary_key=True)
    nif: Mapped[str | None] = mapped_column(String(20))

    contract: Mapped[Contract] = relationship(back_populates="bidders")
    __table_args__ = (Index("ix_bidders_nif", "nif"),)


class ContractLocation(Base):
    """localExecucao, e.g. 'Portugal, Lisboa, Odivelas'. A contract may span several.

    This is where the work happens, NOT where the supplier is based - no dataset
    publishes supplier addresses, only their country.
    """
    __tablename__ = "contract_locations"

    contract_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("contracts.id", ondelete="CASCADE"), primary_key=True)
    country: Mapped[str] = mapped_column(Text, primary_key=True, default="")
    district: Mapped[str] = mapped_column(Text, primary_key=True, default="")
    municipality: Mapped[str] = mapped_column(Text, primary_key=True, default="")

    contract: Mapped[Contract] = relationship(back_populates="locations")
    __table_args__ = (Index("ix_locations_municipality", "municipality"),)


class CompanyProfile(Base):
    """What the registries say about a supplier, cached.

    The procurement data carries no company profile at all, so this is filled
    from outside: SICAE (the Ministry of Justice CAE register, authoritative)
    and an aggregator that also reaches VIES. Capital social and incorporation
    date are deliberately absent, because no free source publishes them.
    """
    __tablename__ = "company_profiles"

    nif: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(Text)
    sicae_name: Mapped[str | None] = mapped_column(Text)
    legal_type: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    # [{"code": "56220", "description": "...", "type": "principal"}, ...]
    cae: Mapped[list | None] = mapped_column(JSONB)
    # Year of the first act published in the commercial register. That register
    # starts in 2006, so anything at or below 2006 means "2006 or earlier" and
    # must never be shown as an exact founding year.
    founded_year: Mapped[int | None] = mapped_column(Integer)
    # read off the firm name, not off a registry: free, and the only source that
    # tells "Unipessoal" apart without paying for a report
    legal_form: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(16))
    # a miss is cached too, so a firm with no registry entry is not refetched
    found: Mapped[bool] = mapped_column(Boolean, default=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Entity(Base):
    """entidades.json - the only published source of an entity's country."""
    __tablename__ = "entities"

    nif: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    n_contracts: Mapped[int | None] = mapped_column(Integer)
    n_as_supplier: Mapped[int | None] = mapped_column(Integer)
    n_as_buyer: Mapped[int | None] = mapped_column(Integer)
    total_won: Mapped[float | None] = mapped_column(Numeric(18, 2))
    total_spent: Mapped[float | None] = mapped_column(Numeric(18, 2))


class Mandate(Base):
    """Who held a câmara's presidency, and between which dates.

    Keyed by DICO rather than by the buyer NIF: the contract record carries no
    administrative code, and concelho names repeat, so DICO is the only stable
    join between the election results and the geometry.

    Dates matter more than years here. Handovers happen in late September or
    October, so a contract signed in October 2017 belongs to a different mandate
    from one signed that August, and a year-based join would silently misfile
    every autumn.
    """
    __tablename__ = "mandates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dico: Mapped[str] = mapped_column(String(4), index=True)
    election_date: Mapped[date] = mapped_column(Date)
    term_start: Mapped[date] = mapped_column(Date, index=True)
    # null while the mandate is the current one
    term_end: Mapped[date | None] = mapped_column(Date, index=True)
    # acronym as published: "PS", "PSD.CDS-PP", "PSD/CDS-PP/PPM"
    party: Mapped[str] = mapped_column(Text)
    # a coalition or a citizens' group is not a party and must not be counted as one
    coalition: Mapped[bool] = mapped_column(Boolean, default=False)
    citizens_group: Mapped[bool] = mapped_column(Boolean, default=False)
    president: Mapped[str | None] = mapped_column(Text)
    mandates: Mapped[int | None] = mapped_column(Integer)
    # These are the provisional count (escrutínio provisório). The legally
    # official record is the CNE Mapa Oficial, a PDF, and the UI says so.
    source: Mapped[str] = mapped_column(String(16), default="mai")

    __table_args__ = (
        UniqueConstraint("dico", "election_date", name="uq_mandate_dico_election"),
    )
