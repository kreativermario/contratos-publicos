"""CPV division -> sector, in Portuguese.

The contract data carries a full CPV code ("45211310-5 - Construção de
casas-de-banho"); its first two digits are the division, which is the coarsest
useful grouping. Anything unlisted falls back to "Outros".
"""
from __future__ import annotations

CPV_SECTORS: dict[str, str] = {
    "03": "Agricultura e pescas",
    "09": "Combustíveis e energia",
    "14": "Minerais e metais",
    "15": "Alimentação",
    "16": "Máquinas agrícolas",
    "18": "Vestuário e calçado",
    "19": "Couro e têxteis",
    "22": "Impressão e publicações",
    "24": "Produtos químicos",
    "30": "Equipamento de escritório",
    "31": "Material elétrico",
    "32": "Telecomunicações e audiovisual",
    "33": "Saúde e farmácia",
    "34": "Veículos e transportes",
    "35": "Segurança e emergência",
    "37": "Música, desporto e lazer",
    "38": "Equipamento laboratorial",
    "39": "Mobiliário e limpeza",
    "41": "Água",
    "42": "Máquinas industriais",
    "43": "Máquinas de construção",
    "44": "Materiais de construção",
    "45": "Obras e construção civil",
    "48": "Software",
    "50": "Reparação e manutenção",
    "51": "Instalação de equipamento",
    "55": "Restauração e hotelaria",
    "60": "Serviços de transporte",
    "63": "Apoio a transportes",
    "64": "Correios e telecomunicações",
    "65": "Serviços públicos",
    "66": "Banca e seguros",
    "70": "Imobiliário",
    "71": "Arquitetura e engenharia",
    "72": "Serviços informáticos",
    "73": "Investigação e desenvolvimento",
    "75": "Administração pública",
    "76": "Serviços petrolíferos",
    "77": "Jardinagem e agricultura",
    "79": "Serviços a empresas e eventos",
    "80": "Educação e formação",
    "85": "Saúde e ação social",
    "90": "Ambiente e resíduos",
    "92": "Cultura, desporto e recreio",
    "98": "Limpeza e outros serviços",
}

OUTROS = "Outros"


def sector_for(cpv: str | None) -> str:
    return CPV_SECTORS.get((cpv or "")[:2], OUTROS)


def divisions_for(sector: str) -> list[str]:
    """The CPV divisions behind a sector label, so a sector can filter contracts.

    "Outros" is the catch-all and has no divisions of its own; it is every
    division the table does not name, which the caller has to express as a
    negation rather than a list.
    """
    return sorted(d for d, name in CPV_SECTORS.items() if name == sector)
