"""The registry parsers, offline. No network in a test."""

from contratos_api.services.company import (parse_aggregator, parse_nifpt,
                                            parse_sicae)

SICAE_PAGE = '''
<input name="ctl00$MainContent$ipFirma" type="text" id="ctl00_MainContent_ipFirma"
 size="43" class="text" disabled="disabled" value="GERTAL - COMPANHIA GERAL DE RESTAURANTES &amp; ALIMENTA&#199;&#195;O S.A." />
<table id="ctl00_MainContent_DetalheDataGrid">
<tr><td>Posi&#231;&#227;o</td><td>CAE</td></tr>
<tr><td class="upperFirma"><div id="letrasCAE">CAE Principal</div></td>
<td class="upperFirma"><div id="letrasCAE" title="Fornecimento de refei&#231;&#245;es por contrato">56220</div></td></tr>
<tr><td class="upperFirma"><div id="letrasCAE">CAE Secund&#225;rio 1</div></td>
<td class="upperFirma"><div id="letrasCAE" title="Refei&#231;&#245;es para eventos">56210</div></td></tr>
</table>
'''


def test_sicae_reads_name_and_every_cae():
    out = parse_sicae(SICAE_PAGE)
    assert out is not None
    # entities are unescaped, not left as &amp;
    assert out["sicae_name"].startswith("GERTAL - COMPANHIA GERAL DE RESTAURANTES & ")
    assert [c["code"] for c in out["cae"]] == ["56220", "56210"]
    assert [c["type"] for c in out["cae"]] == ["principal", "secundario"]
    assert out["cae"][0]["description"] == "Fornecimento de refeições por contrato"


def test_sicae_returns_none_for_an_unknown_nipc():
    assert parse_sicae("<html><body>Sem resultados</body></html>") is None
    assert parse_sicae("") is None


def test_aggregator_normalises_the_envelope():
    out = parse_aggregator({"data": {
        "nif": "503035173",
        "name": "CENTRO DE KARATE-DO SHOTOKAN DE ODIVELAS",
        "type": "Pessoa Coletiva",
        "address": "RUA X\nODIVELAS",
        "cae_codes": [{"code": "85510", "description": "Ensino desportivo", "type": "principal"}],
    }})
    assert out["legal_type"] == "Pessoa Coletiva"
    assert out["cae"] == [{"code": "85510", "description": "Ensino desportivo",
                           "type": "principal"}]


def test_aggregator_rejects_an_empty_answer():
    assert parse_aggregator({}) is None
    assert parse_aggregator({"data": {}}) is None
    # a NIF that exists but carries nothing useful is still a miss
    assert parse_aggregator({"data": {"nif": "500000000", "cae_codes": []}}) is None


NIFPT_OK = {
    "result": "success",
    "records": {"509442013": {
        "nif": 509442013,
        "title": "Nexperience Lda",
        "address": "Rua da Lionesa 446",
        "activity": "Desenvolvimento de software",
        "status": "active",
        "cae": "62010",
        "contacts": {"email": "info@nex.pt", "phone": "220198228"},
        "structure": {"capital": "5000.00"},
        "geo": {"region": "Porto", "county": "Matosinhos"},
    }},
}


def test_nifpt_reads_the_record_under_its_nif_key():
    out = parse_nifpt(NIFPT_OK)
    assert out["name"] == "Nexperience Lda"
    assert out["status"] == "active"
    assert out["county"] == "Matosinhos"
    assert out["cae"] == [{"code": "62010",
                           "description": "Desenvolvimento de software",
                           "type": "principal"}]


def test_nifpt_drops_contacts_and_capital():
    """A phone number belongs to somebody and this site has no use for it."""
    out = parse_nifpt(NIFPT_OK)
    assert "contacts" not in out and "capital" not in out
    assert not any("@" in str(v) for v in out.values())


def test_nifpt_rejects_a_miss():
    assert parse_nifpt({}) is None
    assert parse_nifpt({"result": "error", "records": []}) is None
    # success with an empty record is still a miss, not a company with no name
    assert parse_nifpt({"result": "success", "records": {}}) is None
    assert parse_nifpt({"result": "success", "records": {"1": {"nif": 1}}}) is None


def test_nifpt_survives_a_record_with_no_cae():
    payload = {"result": "success",
               "records": {"5": {"title": "Sem CAE Lda", "geo": {}}}}
    out = parse_nifpt(payload)
    assert out["cae"] == [] and out["county"] is None
