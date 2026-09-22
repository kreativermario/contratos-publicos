"""Reading the legal form off a firm name, and the register's 2006 floor."""
import sys

from contratos_api.services.company import (REGISTER_FLOOR, legal_form_from_name,
                                             parse_founded)


def test_unipessoal_wins_over_a_bare_lda():
    # the string also contains "Lda"; the more specific form must come out
    assert legal_form_from_name("Traços Infinitos, Unipessoal, Lda") == "Unipessoal por quotas"
    assert legal_form_from_name("Rebel Heart, Unipessoal,Ldª") == "Unipessoal por quotas"


def test_common_portuguese_suffixes():
    assert legal_form_from_name("CLARANET PORTUGAL, S.A.") == "Sociedade anónima"
    assert legal_form_from_name("Paredes & Paredes, Lda.") == "Sociedade por quotas"
    assert legal_form_from_name("MANUEL GOMES DE ALMEIDA & FILHO, LDA") == "Sociedade por quotas"
    assert legal_form_from_name("Município de Odivelas") == "Entidade pública"
    assert legal_form_from_name("CENTRO DE KARATE-DO SHOTOKAN DE ODIVELAS") is None


def test_no_name_no_guess():
    assert legal_form_from_name(None) is None
    assert legal_form_from_name("") is None


def test_founded_year_is_read_from_the_meta_description():
    page = '<meta name="description" content="Oeiras, engenharia. Constituída em 2016." />'
    assert parse_founded(page) == 2016
    assert parse_founded("<meta content='nada aqui' />") is None
    assert parse_founded("") is None


def test_the_register_floor_is_a_bound_not_a_date():
    # GERTAL really dates from 1973 but the register only starts in 2006
    page = '<meta name="description" content="Amadora, refeições. Constituída em 2006." />'
    year = parse_founded(page)
    assert year == REGISTER_FLOOR
    assert not (year > REGISTER_FLOOR), "2006 must never be treated as exact"



def test_sql_and_python_readings_come_from_one_table():
    """The filter and the label must not be able to disagree.

    `legal_form_sql` builds its CASE from the same `_FORMS` tuple, in the same
    order, so this only has to check that the advertised list is that tuple's
    full range: a form offered in the UI that the reading never produces would
    filter to an empty list forever.
    """
    from contratos_api.services.company import _FORMS, LEGAL_FORMS

    assert {form for _, form in _FORMS} == set(LEGAL_FORMS)


def test_a_person_is_not_a_sociedade_anonima():
    """`" sa"` without a trailing boundary matched "dos SAntos"."""
    assert legal_form_from_name("Maria dos Santos Ferreira") is None
    assert legal_form_from_name("Joaquim Dias Antunes") is None


def test_the_record_writes_sa_three_different_ways():
    for spelling in ("TECNORÉM - Engenharia e Construções, S.A",
                     "CLARANET PORTUGAL, S.A.",
                     "UNISELF SA"):
        assert legal_form_from_name(spelling) == "Sociedade anónima", spelling


def test_dotted_ace():
    assert (legal_form_from_name("COMANSEGUR & POWERSHIELD, A.C.E")
            == "Agrupamento complementar de empresas")


def test_a_person_is_read_off_the_nif_not_the_name():
    from contratos_api.services.company import is_person_nif

    assert is_person_nif("123456789")
    assert is_person_nif("234567890")
    assert is_person_nif("456789012")          # 45, non-resident individual
    assert not is_person_nif("503504564")      # EDP Comercial
    assert not is_person_nif("600000000")      # a public body
    assert not is_person_nif(None)
    assert not is_person_nif("12345")


def test_a_name_that_reads_as_a_person():
    """The real cases from the record, and the firms they sit beside."""
    from contratos_api.services.company import looks_like_person_name

    for name in ("Francisco Simões Gomes",
                 "Susana Nicole Lopes Garcia Norte",
                 "Maria da Graça Pinto de Almeida Morais",
                 "FERNANDO CARLOS SIMÕES BELOTO",
                 "David Manuel Cardoso de Sousa Correia"):
        assert looks_like_person_name(name), name

    for name in ("LUBRIFUEL",                       # one word
                 "FCC ENVIRONMENT",                 # two words
                 "STRONG CHARON",
                 "C2C Creación y Gestión de Proyectos Culturales, SL",  # digits
                 "OBRAGOITO - Construções e Obras Públicas, Lda",       # has a form
                 "Acciona Construcción, S.A.",
                 "Signinum, Gestão de Património Cultural",             # a comma name
                 None, ""):
        assert not looks_like_person_name(name), name


if __name__ == "__main__":
    # Defined at the bottom on purpose: it runs whatever is in globals() at the
    # time, so a test added after it would silently never run.
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("all passed")
