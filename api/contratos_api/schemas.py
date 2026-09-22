"""Response shapes. Explicit models so the OpenAPI doc is worth reading."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class Flag(BaseModel):
    pct: float | None = None
    # `n` is not always a contract count: concentracao and top3_suppliers count
    # firms, and repeat_winners carries a fractional span of years. Declaring it
    # int made /score answer 500 the moment a municipality spanned 2.7 years.
    # The union is ordered so genuine counts stay ints in the JSON.
    n: int | float | None = None
    # What `n` counts, in the plural, so the card never has to guess. Read by
    # SignalCard.svelte; a flag without one falls back to contracts.
    unit: str | None = None
    disclosed: int | None = None


class Totals(BaseModel):
    contracts: int
    value: float
    suppliers: int


class SatiricalIndex(BaseModel):
    """No prose: the API ships keys and the client words them.

    `band` (clean | fishy | blatant) names the verdict, `tone`
    (ok | warn | critical) names the colour, so the words and the colour never
    disagree and neither language's phrasing is baked into the JSON.
    """
    score: float | None
    band: str = "clean"
    tone: str = "ok"
    units: dict[str, float]


class Score(BaseModel):
    nif: str
    name: str | None = None
    period: dict[str, int | None]
    totals: Totals
    risk_index: float | None
    # which keys of `flags` feed the index and which are shown beside it
    scored_flags: list[str] = []
    context_flags: list[str] = []
    satirical_index: SatiricalIndex
    flags: dict[str, Flag]
    #: disclaimer keys, worded by the client; see DISCLAIMER in scoring.py
    caveats: list[str]


class MandateOut(BaseModel):
    """One term, and what was contracted during it.

    These are the provisional count published by the SGMAI, not the CNE's Mapa
    Oficial, and an election result is not proof of who actually sat: mid-term
    resignations and intercalares do not appear here. The UI says both.
    """
    election_date: date
    term_start: date
    term_end: date | None = None
    party: str
    coalition: bool = False
    citizens_group: bool = False
    president: str | None = None
    contracts: int
    value: float
    ad_pct: float | None = None


class PartyRow(BaseModel):
    """One party, one era.

    `ad_pct` is value-weighted across every mandate in the bucket; `ad_low`,
    `ad_median` and `ad_high` are the spread across those mandates. Both are
    reported because the average alone hides whether a party held one outlier
    câmara or twenty ordinary ones.
    """
    party: str
    era: str                       # "antes" | "depois" (of the 2017 CCP reform)
    coalition: bool = False
    citizens_group: bool = False
    mandates: int
    municipalities: int
    contracts: int
    value: float
    ad_pct: float | None = None
    ad_low: float | None = None
    ad_median: float | None = None
    ad_high: float | None = None
    #: mandate-slices behind the range; small slices are excluded from it
    spread_n: int = 0


class DistrictRow(BaseModel):
    district: str
    era: str
    municipalities: int
    contracts: int
    value: float
    ad_pct: float | None = None
    ad_low: float | None = None
    ad_high: float | None = None
    spread_n: int = 0


class MandateMapRow(BaseModel):
    """Who holds one câmara, for the map. Covers all 308, not only the loaded ones."""
    dico: str
    concelho: str
    district: str | None = None
    election_date: date
    party: str
    coalition: bool = False
    citizens_group: bool = False
    president: str | None = None
    term_start: date | None = None
    term_end: date | None = None
    #: how long the term ran; the current one is counted up to today
    years: float | None = None
    #: the buyer NIF, set only where this câmara's contracts are loaded
    nif: str | None = None
    #: None, never zero, where this câmara's contracts are not loaded
    contracts: int | None = None
    value: float | None = None
    ad_pct: float | None = None


class Municipality(BaseModel):
    nif: str
    name: str | None
    contracts: int
    total: float | None
    since: date | None = None
    latest: date | None = None


class Supplier(BaseModel):
    name: str
    nif: str | None
    contracts: int
    total: float | None
    first_win: date | None
    last_win: date | None
    ad_pct: float | None
    country: str | None
    sector: str
    # first appearance anywhere in the record; None where the record starts too
    # late to tell, never a confident "established"
    first_seen: date | None = None
    debut_days: int | None = None
    newcomer: bool | None = None
    # read off the firm name, which by law carries the suffix
    legal_form: str | None = None


class StatRow(BaseModel):
    label: str | int | None
    contracts: int
    total: float | None
    mean: float | None = None


class Headline(BaseModel):
    contracts: int
    total: float | None
    mean: float | None
    median: float | None
    p90: float | None
    largest: float | None
    smallest: float | None
    mean_exec_days: float | None
    median_exec_days: float | None
    base_total: float | None
    with_base: int
    median_discount_pct: float | None
    no_discount: int
    suppliers_to_half: int | None
    cpv_codes: int
    framework_contracts: int
    zero_value: int


class Stats(BaseModel):
    headline: Headline
    by_procedure: list[StatRow]
    by_year: list[StatRow]
    by_sector: list[StatRow]
    #: money by the legal form of the firm that got it; "contratos" is firms
    by_form: list[StatRow] = []


class Cae(BaseModel):
    code: str
    description: str | None = None
    type: str | None = None


class Company(BaseModel):
    """What the registries say. No capital social, no incorporation date: no
    free source publishes either, and guessing them would be worse than N/A."""
    nif: str
    name: str | None = None
    sicae_name: str | None = None
    legal_type: str | None = None
    address: str | None = None
    cae: list[Cae] = []
    # year of the first act in the commercial register, which begins in 2006
    founded_year: int | None = None
    # False means the year is only a bound: the company predates the register
    founded_exact: bool = False
    legal_form: str | None = None
    source: str | None = None


class Rival(BaseModel):
    firm_a: str
    firm_b: str
    nif_a: str | None = None
    nif_b: str | None = None
    tenders: int


class ContractParty(BaseModel):
    name: str
    nif: str | None


class ContractOut(BaseModel):
    #: The legal ceiling this contract sits just under, if any. A contract of
    #: 74 994 EUR against a 75 000 EUR consulta prévia limit is six euros from
    #: needing a more demanding procedure, and that is worth pointing at even
    #: though it is perfectly legal.
    near_limit: float | None = None
    id: int
    object: str | None
    procedure: str | None
    value: float | None
    signed_date: date | None
    year: int | None
    cpv_desc: str | None
    n_bidders: int | None
    ad_justification: str | None
    suppliers: list[str]
    #: the same firms with their NIFs, so a row can link to a company page
    parties: list[ContractParty] = []
    #: patterns worth a second look, by key; every one of them is legal
    flags: list[str] = []
    # only filled when the row is read from a supplier's side, where the other
    # party is the câmara
    buyer_nif: str | None = None
    buyer_name: str | None = None


class SupplierBuyer(BaseModel):
    nif: str | None
    name: str | None
    contracts: int
    total: float | None
    #: territory, where the buyer name resolves to one unambiguously
    dico: str | None = None
    concelho: str | None = None
    district: str | None = None


class SupplierYear(BaseModel):
    label: int
    contracts: int
    total: float
    ad_pct: float | None = None


class SupplierDetail(BaseModel):
    """One firm across every câmara loaded, not one municipality's view of it."""
    nif: str
    name: str | None
    contracts: int
    total: float | None
    first_win: date | None
    last_win: date | None
    ad_pct: float | None
    buyers: int
    sector: str
    by_buyer: list[SupplierBuyer] = []
    #: one row per year, so the page can show a shape and not just a total
    by_year: list[SupplierYear] = []


class ContractDetail(BaseModel):
    """The full record for one contract. Fields absent from the source stay
    None: this page reports the register, it does not fill its gaps."""
    id: int
    object: str | None
    procedure: str | None
    contract_types: list[str] = []
    value: float | None
    base_price: float | None
    signed_date: date | None
    pub_date: date | None
    exec_days: int | None
    cpv: str | None
    cpv_desc: str | None
    sector: str
    n_bidders: int | None
    framework: str | None
    justification: str | None
    ad_justification: str | None
    centralized: bool | None
    green: bool | None
    criterion: str | None
    buyer_nif: str | None
    buyer_name: str | None
    suppliers: list[ContractParty] = []
    bidders: list[ContractParty] = []
    locations: list[str] = []
    link_pieces: str | None = None
    link_announcement: str | None = None
    near_limit: float | None = None


class MapCell(BaseModel):
    municipality: str
    district: str | None
    contracts: int
    total: float | None


class Limits(BaseModel):
    ajuste_direto_servicos: float
    ajuste_direto_obras: float
    consulta_previa: float
    banda_limite: float
    dias_estreante: int


class Config(BaseModel):
    default: Municipality | None
    cache_seconds: int
    # Declared explicitly: response_model drops any field the schema does not
    # name, so the router can serve these and the JSON still arrive without them.
    limits: Limits | None = None
    legal_forms: list[str] = []
