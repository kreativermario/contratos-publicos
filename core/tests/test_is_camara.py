"""The 308 câmaras against the ~5 700 other public buyers IMPIC publishes.

This is the only thing separating them. While MUNICIPALITY_NIFS scoped the
ingest the distinction never had to be made; emptying it for national coverage
put hospitals, agrupamentos de escolas and misericórdias into the município
picker, the nav, the prerendered pages and the sitemap.
"""
from contratos_core import is_camara


def test_accepts_every_spelling_the_register_uses():
    for name in ("Município de Odivelas", "Municipio de Odivelas",
                 "Município da Amadora", "Município do Porto",
                 "Câmara Municipal de Lisboa", "Camara Municipal de Lisboa",
                 "  Município de Sintra"):
        assert is_camara(name), name


def test_rejects_bodies_that_merely_name_a_concelho():
    # Each of these resolves to a real concelho through concelho_name, which is
    # how "Universidade do Porto" once shadowed the câmara do Porto.
    for name in ("Universidade do Porto", "Agrupamento de Escolas de Lousada",
                 "Centro Hospitalar de Lisboa Central, E. P. E.",
                 "Santa Casa da Misericórdia de Lisboa",
                 "EP Estradas de Portugal, S.A.",
                 "Serviços Municipalizados de Água e Saneamento de Sintra"):
        assert not is_camara(name), name


def test_camara_de_lobos_is_a_place_not_a_camara():
    # A concelho in Madeira. "câmara" alone can never be the test; its own
    # council is spelled in full and must still pass.
    assert not is_camara("Câmara de Lobos")
    assert is_camara("Câmara Municipal de Câmara de Lobos")


def test_empty_is_not_a_camara():
    assert not is_camara(None)
    assert not is_camara("")
