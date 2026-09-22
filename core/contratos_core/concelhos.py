"""The 308 concelhos, with the administrative code everything else joins on.

Reference data, not configuration: DICO is the INE/administrative code for a
concelho and does not change with deployment. It is the only stable key between
three sources that otherwise share nothing:

  - the geometry file (carries dico, name, district)
  - the autárquicas results at eleicoes.mai.gov.pt (territoryKey = LOCAL-{dico}00)
  - the contract record, which carries neither, only a buyer name

Concelho names are not unique (Lagoa exists in Faro and in the Azores) and 87 of
the 308 differ only by particle casing, which is exactly why the join is on the
code and the name is only a label.

Generated from web/static/pt-municipios.geojson.
"""
from __future__ import annotations

import re
import unicodedata

# (dico, name, key, district)
CONCELHOS: tuple[tuple[str, str, str, str], ...] = (
    ("0101", "Águeda", "AGUEDA", "Aveiro"),
    ("0102", "Albergaria-a-velha", "ALBERGARIA-A-VELHA", "Aveiro"),
    ("0103", "Anadia", "ANADIA", "Aveiro"),
    ("0104", "Arouca", "AROUCA", "Aveiro"),
    ("0105", "Aveiro", "AVEIRO", "Aveiro"),
    ("0106", "Castelo de Paiva", "CASTELO DE PAIVA", "Aveiro"),
    ("0107", "Espinho", "ESPINHO", "Aveiro"),
    ("0108", "Estarreja", "ESTARREJA", "Aveiro"),
    ("0109", "Santa Maria da Feira", "SANTA MARIA DA FEIRA", "Aveiro"),
    ("0110", "Ílhavo", "ILHAVO", "Aveiro"),
    ("0111", "Mealhada", "MEALHADA", "Aveiro"),
    ("0112", "Murtosa", "MURTOSA", "Aveiro"),
    ("0113", "Oliveira de Azeméis", "OLIVEIRA DE AZEMEIS", "Aveiro"),
    ("0114", "Oliveira do Bairro", "OLIVEIRA DO BAIRRO", "Aveiro"),
    ("0115", "Ovar", "OVAR", "Aveiro"),
    ("0116", "São João da Madeira", "SAO JOAO DA MADEIRA", "Aveiro"),
    ("0117", "Sever do Vouga", "SEVER DO VOUGA", "Aveiro"),
    ("0118", "Vagos", "VAGOS", "Aveiro"),
    ("0119", "Vale de Cambra", "VALE DE CAMBRA", "Aveiro"),
    ("0201", "Aljustrel", "ALJUSTREL", "Beja"),
    ("0202", "Almodôvar", "ALMODOVAR", "Beja"),
    ("0203", "Alvito", "ALVITO", "Beja"),
    ("0204", "Barrancos", "BARRANCOS", "Beja"),
    ("0205", "Beja", "BEJA", "Beja"),
    ("0206", "Castro Verde", "CASTRO VERDE", "Beja"),
    ("0207", "Cuba", "CUBA", "Beja"),
    ("0208", "Ferreira do Alentejo", "FERREIRA DO ALENTEJO", "Beja"),
    ("0209", "Mértola", "MERTOLA", "Beja"),
    ("0210", "Moura", "MOURA", "Beja"),
    ("0211", "Odemira", "ODEMIRA", "Beja"),
    ("0212", "Ourique", "OURIQUE", "Beja"),
    ("0213", "Serpa", "SERPA", "Beja"),
    ("0214", "Vidigueira", "VIDIGUEIRA", "Beja"),
    ("0301", "Amares", "AMARES", "Braga"),
    ("0302", "Barcelos", "BARCELOS", "Braga"),
    ("0303", "Braga", "BRAGA", "Braga"),
    ("0304", "Cabeceiras de Basto", "CABECEIRAS DE BASTO", "Braga"),
    ("0305", "Celorico de Basto", "CELORICO DE BASTO", "Braga"),
    ("0306", "Esposende", "ESPOSENDE", "Braga"),
    ("0307", "Fafe", "FAFE", "Braga"),
    ("0308", "Guimarães", "GUIMARAES", "Braga"),
    ("0309", "Póvoa de Lanhoso", "POVOA DE LANHOSO", "Braga"),
    ("0310", "Terras de Bouro", "TERRAS DE BOURO", "Braga"),
    ("0311", "Vieira do Minho", "VIEIRA DO MINHO", "Braga"),
    ("0312", "Vila Nova de Famalicão", "VILA NOVA DE FAMALICAO", "Braga"),
    ("0313", "Vila Verde", "VILA VERDE", "Braga"),
    ("0314", "Vizela", "VIZELA", "Braga"),
    ("0401", "Alfândega da Fé", "ALFANDEGA DA FE", "Bragança"),
    ("0402", "Bragança", "BRAGANCA", "Bragança"),
    ("0403", "Carrazeda de Ansiães", "CARRAZEDA DE ANSIAES", "Bragança"),
    ("0404", "Freixo de Espada À Cinta", "FREIXO DE ESPADA A CINTA", "Bragança"),
    ("0405", "Macedo de Cavaleiros", "MACEDO DE CAVALEIROS", "Bragança"),
    ("0406", "Miranda do Douro", "MIRANDA DO DOURO", "Bragança"),
    ("0407", "Mirandela", "MIRANDELA", "Bragança"),
    ("0408", "Mogadouro", "MOGADOURO", "Bragança"),
    ("0409", "Torre de Moncorvo", "TORRE DE MONCORVO", "Bragança"),
    ("0410", "Vila Flor", "VILA FLOR", "Bragança"),
    ("0411", "Vimioso", "VIMIOSO", "Bragança"),
    ("0412", "Vinhais", "VINHAIS", "Bragança"),
    ("0501", "Belmonte", "BELMONTE", "Castelo Branco"),
    ("0502", "Castelo Branco", "CASTELO BRANCO", "Castelo Branco"),
    ("0503", "Covilhã", "COVILHA", "Castelo Branco"),
    ("0504", "Fundão", "FUNDAO", "Castelo Branco"),
    ("0505", "Idanha-a-nova", "IDANHA-A-NOVA", "Castelo Branco"),
    ("0506", "Oleiros", "OLEIROS", "Castelo Branco"),
    ("0507", "Penamacor", "PENAMACOR", "Castelo Branco"),
    ("0508", "Proença-a-nova", "PROENCA-A-NOVA", "Castelo Branco"),
    ("0509", "Sertã", "SERTA", "Castelo Branco"),
    ("0510", "Vila de Rei", "VILA DE REI", "Castelo Branco"),
    ("0511", "Vila Velha de Ródão", "VILA VELHA DE RODAO", "Castelo Branco"),
    ("0601", "Arganil", "ARGANIL", "Coimbra"),
    ("0602", "Cantanhede", "CANTANHEDE", "Coimbra"),
    ("0603", "Coimbra", "COIMBRA", "Coimbra"),
    ("0604", "Condeixa-a-nova", "CONDEIXA-A-NOVA", "Coimbra"),
    ("0605", "Figueira da Foz", "FIGUEIRA DA FOZ", "Coimbra"),
    ("0606", "Góis", "GOIS", "Coimbra"),
    ("0607", "Lousã", "LOUSA", "Coimbra"),
    ("0608", "Mira", "MIRA", "Coimbra"),
    ("0609", "Miranda do Corvo", "MIRANDA DO CORVO", "Coimbra"),
    ("0610", "Montemor-o-velho", "MONTEMOR-O-VELHO", "Coimbra"),
    ("0611", "Oliveira do Hospital", "OLIVEIRA DO HOSPITAL", "Coimbra"),
    ("0612", "Pampilhosa da Serra", "PAMPILHOSA DA SERRA", "Coimbra"),
    ("0613", "Penacova", "PENACOVA", "Coimbra"),
    ("0614", "Penela", "PENELA", "Coimbra"),
    ("0615", "Soure", "SOURE", "Coimbra"),
    ("0616", "Tábua", "TABUA", "Coimbra"),
    ("0617", "Vila Nova de Poiares", "VILA NOVA DE POIARES", "Coimbra"),
    ("0701", "Alandroal", "ALANDROAL", "Évora"),
    ("0702", "Arraiolos", "ARRAIOLOS", "Évora"),
    ("0703", "Borba", "BORBA", "Évora"),
    ("0704", "Estremoz", "ESTREMOZ", "Évora"),
    ("0705", "Évora", "EVORA", "Évora"),
    ("0706", "Montemor-o-novo", "MONTEMOR-O-NOVO", "Évora"),
    ("0707", "Mora", "MORA", "Évora"),
    ("0708", "Mourão", "MOURAO", "Évora"),
    ("0709", "Portel", "PORTEL", "Évora"),
    ("0710", "Redondo", "REDONDO", "Évora"),
    ("0711", "Reguengos de Monsaraz", "REGUENGOS DE MONSARAZ", "Évora"),
    ("0712", "Vendas Novas", "VENDAS NOVAS", "Évora"),
    ("0713", "Viana do Alentejo", "VIANA DO ALENTEJO", "Évora"),
    ("0714", "Vila Viçosa", "VILA VICOSA", "Évora"),
    ("0801", "Albufeira", "ALBUFEIRA", "Faro"),
    ("0802", "Alcoutim", "ALCOUTIM", "Faro"),
    ("0803", "Aljezur", "ALJEZUR", "Faro"),
    ("0804", "Castro Marim", "CASTRO MARIM", "Faro"),
    ("0805", "Faro", "FARO", "Faro"),
    ("0806", "Lagoa (Faro)", "LAGOA", "Faro"),
    ("0807", "Lagos", "LAGOS", "Faro"),
    ("0808", "Loulé", "LOULE", "Faro"),
    ("0809", "Monchique", "MONCHIQUE", "Faro"),
    ("0810", "Olhão", "OLHAO", "Faro"),
    ("0811", "Portimão", "PORTIMAO", "Faro"),
    ("0812", "São Brás de Alportel", "SAO BRAS DE ALPORTEL", "Faro"),
    ("0813", "Silves", "SILVES", "Faro"),
    ("0814", "Tavira", "TAVIRA", "Faro"),
    ("0815", "Vila do Bispo", "VILA DO BISPO", "Faro"),
    ("0816", "Vila Real de Santo António", "VILA REAL DE SANTO ANTONIO", "Faro"),
    ("0901", "Aguiar da Beira", "AGUIAR DA BEIRA", "Guarda"),
    ("0902", "Almeida", "ALMEIDA", "Guarda"),
    ("0903", "Celorico da Beira", "CELORICO DA BEIRA", "Guarda"),
    ("0904", "Figueira de Castelo Rodrigo", "FIGUEIRA DE CASTELO RODRIGO", "Guarda"),
    ("0905", "Fornos de Algodres", "FORNOS DE ALGODRES", "Guarda"),
    ("0906", "Gouveia", "GOUVEIA", "Guarda"),
    ("0907", "Guarda", "GUARDA", "Guarda"),
    ("0908", "Manteigas", "MANTEIGAS", "Guarda"),
    ("0909", "Mêda", "MEDA", "Guarda"),
    ("0910", "Pinhel", "PINHEL", "Guarda"),
    ("0911", "Sabugal", "SABUGAL", "Guarda"),
    ("0912", "Seia", "SEIA", "Guarda"),
    ("0913", "Trancoso", "TRANCOSO", "Guarda"),
    ("0914", "Vila Nova de Foz Côa", "VILA NOVA DE FOZ COA", "Guarda"),
    ("1001", "Alcobaça", "ALCOBACA", "Leiria"),
    ("1002", "Alvaiázere", "ALVAIAZERE", "Leiria"),
    ("1003", "Ansião", "ANSIAO", "Leiria"),
    ("1004", "Batalha", "BATALHA", "Leiria"),
    ("1005", "Bombarral", "BOMBARRAL", "Leiria"),
    ("1006", "Caldas da Rainha", "CALDAS DA RAINHA", "Leiria"),
    ("1007", "Castanheira de Pêra", "CASTANHEIRA DE PERA", "Leiria"),
    ("1008", "Figueiró dos Vinhos", "FIGUEIRO DOS VINHOS", "Leiria"),
    ("1009", "Leiria", "LEIRIA", "Leiria"),
    ("1010", "Marinha Grande", "MARINHA GRANDE", "Leiria"),
    ("1011", "Nazaré", "NAZARE", "Leiria"),
    ("1012", "Óbidos", "OBIDOS", "Leiria"),
    ("1013", "Pedrógão Grande", "PEDROGAO GRANDE", "Leiria"),
    ("1014", "Peniche", "PENICHE", "Leiria"),
    ("1015", "Pombal", "POMBAL", "Leiria"),
    ("1016", "Porto de Mós", "PORTO DE MOS", "Leiria"),
    ("1101", "Alenquer", "ALENQUER", "Lisboa"),
    ("1102", "Arruda dos Vinhos", "ARRUDA DOS VINHOS", "Lisboa"),
    ("1103", "Azambuja", "AZAMBUJA", "Lisboa"),
    ("1104", "Cadaval", "CADAVAL", "Lisboa"),
    ("1105", "Cascais", "CASCAIS", "Lisboa"),
    ("1106", "Lisboa", "LISBOA", "Lisboa"),
    ("1107", "Loures", "LOURES", "Lisboa"),
    ("1108", "Lourinhã", "LOURINHA", "Lisboa"),
    ("1109", "Mafra", "MAFRA", "Lisboa"),
    ("1110", "Oeiras", "OEIRAS", "Lisboa"),
    ("1111", "Sintra", "SINTRA", "Lisboa"),
    ("1112", "Sobral de Monte Agraço", "SOBRAL DE MONTE AGRACO", "Lisboa"),
    ("1113", "Torres Vedras", "TORRES VEDRAS", "Lisboa"),
    ("1114", "Vila Franca de Xira", "VILA FRANCA DE XIRA", "Lisboa"),
    ("1115", "Amadora", "AMADORA", "Lisboa"),
    ("1116", "Odivelas", "ODIVELAS", "Lisboa"),
    ("1201", "Alter do Chão", "ALTER DO CHAO", "Portalegre"),
    ("1202", "Arronches", "ARRONCHES", "Portalegre"),
    ("1203", "Avis", "AVIS", "Portalegre"),
    ("1204", "Campo Maior", "CAMPO MAIOR", "Portalegre"),
    ("1205", "Castelo de Vide", "CASTELO DE VIDE", "Portalegre"),
    ("1206", "Crato", "CRATO", "Portalegre"),
    ("1207", "Elvas", "ELVAS", "Portalegre"),
    ("1208", "Fronteira", "FRONTEIRA", "Portalegre"),
    ("1209", "Gavião", "GAVIAO", "Portalegre"),
    ("1210", "Marvão", "MARVAO", "Portalegre"),
    ("1211", "Monforte", "MONFORTE", "Portalegre"),
    ("1212", "Nisa", "NISA", "Portalegre"),
    ("1213", "Ponte de Sor", "PONTE DE SOR", "Portalegre"),
    ("1214", "Portalegre", "PORTALEGRE", "Portalegre"),
    ("1215", "Sousel", "SOUSEL", "Portalegre"),
    ("1301", "Amarante", "AMARANTE", "Porto"),
    ("1302", "Baião", "BAIAO", "Porto"),
    ("1303", "Felgueiras", "FELGUEIRAS", "Porto"),
    ("1304", "Gondomar", "GONDOMAR", "Porto"),
    ("1305", "Lousada", "LOUSADA", "Porto"),
    ("1306", "Maia", "MAIA", "Porto"),
    ("1307", "Marco de Canaveses", "MARCO DE CANAVESES", "Porto"),
    ("1308", "Matosinhos", "MATOSINHOS", "Porto"),
    ("1309", "Paços de Ferreira", "PACOS DE FERREIRA", "Porto"),
    ("1310", "Paredes", "PAREDES", "Porto"),
    ("1311", "Penafiel", "PENAFIEL", "Porto"),
    ("1312", "Porto", "PORTO", "Porto"),
    ("1313", "Póvoa de Varzim", "POVOA DE VARZIM", "Porto"),
    ("1314", "Santo Tirso", "SANTO TIRSO", "Porto"),
    ("1315", "Valongo", "VALONGO", "Porto"),
    ("1316", "Vila do Conde", "VILA DO CONDE", "Porto"),
    ("1317", "Vila Nova de Gaia", "VILA NOVA DE GAIA", "Porto"),
    ("1318", "Trofa", "TROFA", "Porto"),
    ("1401", "Abrantes", "ABRANTES", "Santarém"),
    ("1402", "Alcanena", "ALCANENA", "Santarém"),
    ("1403", "Almeirim", "ALMEIRIM", "Santarém"),
    ("1404", "Alpiarça", "ALPIARCA", "Santarém"),
    ("1405", "Benavente", "BENAVENTE", "Santarém"),
    ("1406", "Cartaxo", "CARTAXO", "Santarém"),
    ("1407", "Chamusca", "CHAMUSCA", "Santarém"),
    ("1408", "Constância", "CONSTANCIA", "Santarém"),
    ("1409", "Coruche", "CORUCHE", "Santarém"),
    ("1410", "Entroncamento", "ENTRONCAMENTO", "Santarém"),
    ("1411", "Ferreira do Zêzere", "FERREIRA DO ZEZERE", "Santarém"),
    ("1412", "Golegã", "GOLEGA", "Santarém"),
    ("1413", "Mação", "MACAO", "Santarém"),
    ("1414", "Rio Maior", "RIO MAIOR", "Santarém"),
    ("1415", "Salvaterra de Magos", "SALVATERRA DE MAGOS", "Santarém"),
    ("1416", "Santarém", "SANTAREM", "Santarém"),
    ("1417", "Sardoal", "SARDOAL", "Santarém"),
    ("1418", "Tomar", "TOMAR", "Santarém"),
    ("1419", "Torres Novas", "TORRES NOVAS", "Santarém"),
    ("1420", "Vila Nova da Barquinha", "VILA NOVA DA BARQUINHA", "Santarém"),
    ("1421", "Ourém", "OUREM", "Santarém"),
    ("1501", "Alcácer do Sal", "ALCACER DO SAL", "Setúbal"),
    ("1502", "Alcochete", "ALCOCHETE", "Setúbal"),
    ("1503", "Almada", "ALMADA", "Setúbal"),
    ("1504", "Barreiro", "BARREIRO", "Setúbal"),
    ("1505", "Grândola", "GRANDOLA", "Setúbal"),
    ("1506", "Moita", "MOITA", "Setúbal"),
    ("1507", "Montijo", "MONTIJO", "Setúbal"),
    ("1508", "Palmela", "PALMELA", "Setúbal"),
    ("1509", "Santiago do Cacém", "SANTIAGO DO CACEM", "Setúbal"),
    ("1510", "Seixal", "SEIXAL", "Setúbal"),
    ("1511", "Sesimbra", "SESIMBRA", "Setúbal"),
    ("1512", "Setúbal", "SETUBAL", "Setúbal"),
    ("1513", "Sines", "SINES", "Setúbal"),
    ("1601", "Arcos de Valdevez", "ARCOS DE VALDEVEZ", "Viana do Castelo"),
    ("1602", "Caminha", "CAMINHA", "Viana do Castelo"),
    ("1603", "Melgaço", "MELGACO", "Viana do Castelo"),
    ("1604", "Monção", "MONCAO", "Viana do Castelo"),
    ("1605", "Paredes de Coura", "PAREDES DE COURA", "Viana do Castelo"),
    ("1606", "Ponte da Barca", "PONTE DA BARCA", "Viana do Castelo"),
    ("1607", "Ponte de Lima", "PONTE DE LIMA", "Viana do Castelo"),
    ("1608", "Valença", "VALENCA", "Viana do Castelo"),
    ("1609", "Viana do Castelo", "VIANA DO CASTELO", "Viana do Castelo"),
    ("1610", "Vila Nova de Cerveira", "VILA NOVA DE CERVEIRA", "Viana do Castelo"),
    ("1701", "Alijó", "ALIJO", "Vila Real"),
    ("1702", "Boticas", "BOTICAS", "Vila Real"),
    ("1703", "Chaves", "CHAVES", "Vila Real"),
    ("1704", "Mesão Frio", "MESAO FRIO", "Vila Real"),
    ("1705", "Mondim de Basto", "MONDIM DE BASTO", "Vila Real"),
    ("1706", "Montalegre", "MONTALEGRE", "Vila Real"),
    ("1707", "Murça", "MURCA", "Vila Real"),
    ("1708", "Peso da Régua", "PESO DA REGUA", "Vila Real"),
    ("1709", "Ribeira de Pena", "RIBEIRA DE PENA", "Vila Real"),
    ("1710", "Sabrosa", "SABROSA", "Vila Real"),
    ("1711", "Santa Marta de Penaguião", "SANTA MARTA DE PENAGUIAO", "Vila Real"),
    ("1712", "Valpaços", "VALPACOS", "Vila Real"),
    ("1713", "Vila Pouca de Aguiar", "VILA POUCA DE AGUIAR", "Vila Real"),
    ("1714", "Vila Real", "VILA REAL", "Vila Real"),
    ("1801", "Armamar", "ARMAMAR", "Viseu"),
    ("1802", "Carregal do Sal", "CARREGAL DO SAL", "Viseu"),
    ("1803", "Castro Daire", "CASTRO DAIRE", "Viseu"),
    ("1804", "Cinfães", "CINFAES", "Viseu"),
    ("1805", "Lamego", "LAMEGO", "Viseu"),
    ("1806", "Mangualde", "MANGUALDE", "Viseu"),
    ("1807", "Moimenta da Beira", "MOIMENTA DA BEIRA", "Viseu"),
    ("1808", "Mortágua", "MORTAGUA", "Viseu"),
    ("1809", "Nelas", "NELAS", "Viseu"),
    ("1810", "Oliveira de Frades", "OLIVEIRA DE FRADES", "Viseu"),
    ("1811", "Penalva do Castelo", "PENALVA DO CASTELO", "Viseu"),
    ("1812", "Penedono", "PENEDONO", "Viseu"),
    ("1813", "Resende", "RESENDE", "Viseu"),
    ("1814", "Santa Comba Dão", "SANTA COMBA DAO", "Viseu"),
    ("1815", "São João da Pesqueira", "SAO JOAO DA PESQUEIRA", "Viseu"),
    ("1816", "São Pedro do Sul", "SAO PEDRO DO SUL", "Viseu"),
    ("1817", "Sátão", "SATAO", "Viseu"),
    ("1818", "Sernancelhe", "SERNANCELHE", "Viseu"),
    ("1819", "Tabuaço", "TABUACO", "Viseu"),
    ("1820", "Tarouca", "TAROUCA", "Viseu"),
    ("1821", "Tondela", "TONDELA", "Viseu"),
    ("1822", "Vila Nova de Paiva", "VILA NOVA DE PAIVA", "Viseu"),
    ("1823", "Viseu", "VISEU", "Viseu"),
    ("1824", "Vouzela", "VOUZELA", "Viseu"),
    ("3101", "Calheta", "CALHETA", "Ilha da Madeira (Madeira)"),
    ("3102", "Câmara de Lobos", "CAMARA DE LOBOS", "Ilha da Madeira (Madeira)"),
    ("3103", "Funchal", "FUNCHAL", "Ilha da Madeira (Madeira)"),
    ("3104", "Machico", "MACHICO", "Ilha da Madeira (Madeira)"),
    ("3105", "Ponta do Sol", "PONTA DO SOL", "Ilha da Madeira (Madeira)"),
    ("3106", "Porto Moniz", "PORTO MONIZ", "Ilha da Madeira (Madeira)"),
    ("3107", "Ribeira Brava", "RIBEIRA BRAVA", "Ilha da Madeira (Madeira)"),
    ("3108", "Santa Cruz", "SANTA CRUZ", "Ilha da Madeira (Madeira)"),
    ("3109", "Santana", "SANTANA", "Ilha da Madeira (Madeira)"),
    ("3110", "São Vicente", "SAO VICENTE", "Ilha da Madeira (Madeira)"),
    ("3201", "Porto Santo", "PORTO SANTO", "Ilha de Porto Santo (Madeira)"),
    ("4101", "Vila do Porto", "VILA DO PORTO", "Ilha de Santa Maria (Açores)"),
    ("4201", "Lagoa (Açores)", "LAGOA", "Ilha de São Miguel (Açores)"),
    ("4202", "Nordeste", "NORDESTE", "Ilha de São Miguel (Açores)"),
    ("4203", "Ponta Delgada", "PONTA DELGADA", "Ilha de São Miguel (Açores)"),
    ("4204", "Povoação", "POVOACAO", "Ilha de São Miguel (Açores)"),
    ("4205", "Ribeira Grande", "RIBEIRA GRANDE", "Ilha de São Miguel (Açores)"),
    ("4206", "Vila Franca do Campo", "VILA FRANCA DO CAMPO", "Ilha de São Miguel (Açores)"),
    ("4301", "Angra do Heroísmo", "ANGRA DO HEROISMO", "Ilha Terceira (Açores)"),
    ("4302", "Praia da Vitória", "PRAIA DA VITORIA", "Ilha Terceira (Açores)"),
    ("4401", "Santa Cruz da Graciosa", "SANTA CRUZ DA GRACIOSA", "Ilha da Graciosa (Açores)"),
    ("4501", "Calheta de S. Jorge", "CALHETA DE S. JORGE", "Ilha de São Jorge (Açores)"),
    ("4502", "Velas", "VELAS", "Ilha de São Jorge (Açores)"),
    ("4601", "Lajes do Pico", "LAJES DO PICO", "Ilha do Pico (Açores)"),
    ("4602", "Madalena", "MADALENA", "Ilha do Pico (Açores)"),
    ("4603", "São Roque do Pico", "SAO ROQUE DO PICO", "Ilha do Pico (Açores)"),
    ("4701", "Horta", "HORTA", "Ilha do Faial (Açores)"),
    ("4801", "Lajes das Flores", "LAJES DAS FLORES", "Ilha das Flores (Açores)"),
    ("4802", "Santa Cruz das Flores", "SANTA CRUZ DAS FLORES", "Ilha das Flores (Açores)"),
    ("4901", "Corvo", "CORVO", "Ilha Corvo (Açores)"),
)


def normalise(name: str) -> str:
    """Accents stripped, uppercased. Mirrors mapKey() in the frontend."""
    return "".join(
        c for c in unicodedata.normalize("NFD", name or "")
        if unicodedata.category(c) != "Mn"
    ).upper().strip()


#: "Município de Odivelas" -> "Odivelas". The particle varies, and a pattern
#: that missed "da" once left the whole legal name rendering at display size.
_PREFIX = re.compile(r"^(?:Munic[ií]pio|C[âa]mara\s+Municipal)\s+d[aeo]\s*", re.IGNORECASE)


def concelho_name(buyer_name: str) -> str:
    """The concelho a buyer name refers to, stripped of its administrative style."""
    return _PREFIX.sub("", buyer_name or "").strip()


_BY_KEY: dict[str, list[tuple[str, str, str, str]]] = {}
for _row in CONCELHOS:
    _BY_KEY.setdefault(_row[2], []).append(_row)

#: District prefixes, derived rather than listed. The two autonomous regions are
#: 3x (Madeira) and 4x (Açores) per island, but the election sites publish them
#: as one region each, so callers that fetch by district want 30 and 40.
DISTRICT_PREFIXES: tuple[str, ...] = tuple(sorted({r[0][:2] for r in CONCELHOS if r[0] < "30"}))
REGION_PREFIXES: tuple[str, ...] = ("30", "40")


def _same_district(candidate: str, wanted: str) -> bool:
    """Do two district names refer to the same place?

    They are written differently by different sources: the geometry says
    "Ilha de São Miguel (Açores)" where the election results say
    "Região Autónoma dos Açores". Prefix matching handles the mainland; the
    archipelagos need the region name on its own.
    """
    c, w = normalise(candidate), normalise(wanted)
    if not c or not w:
        return False
    if c.startswith(w) or w.startswith(c):
        return True
    return any(region in c and region in w for region in ("ACORES", "MADEIRA"))


def dico_for(name: str, district: str | None = None) -> str | None:
    """DICO for a concelho name, or None when it is unknown or ambiguous.

    A supplied district is always checked, never treated as a tiebreak of last
    resort. There is exactly one concelho named "Calheta" in the table (Madeira),
    but the Azores have one too, spelled "Calheta de S. Jorge"; returning on the
    single name match without looking at the district filed every Azorean result
    under Madeira. Ambiguity is likewise never guessed at: without a district,
    "Lagoa" has two answers and the honest result is None.
    """
    key = normalise(name)
    hits = _BY_KEY.get(key, [])
    if not hits:
        # Some sources carry the administrative style: the election results say
        # "Vila da Praia da Vitória" for "Praia da Vitória".
        hits = [r for r in CONCELHOS if key.endswith(" " + r[2])]

    if not district:
        return hits[0][0] if len(hits) == 1 else None

    narrowed = [h for h in hits if _same_district(h[3], district)]
    if len(narrowed) == 1:
        return narrowed[0][0]
    if narrowed:
        return None

    # The name matched somewhere else entirely, or nowhere. Search within the
    # district instead, allowing the fuller local spelling ("Calheta" for
    # "Calheta de S. Jorge").
    alt = [
        r for r in CONCELHOS
        if _same_district(r[3], district)
        and (r[2] == key or r[2].startswith(key + " ") or key.endswith(" " + r[2]))
    ]
    return alt[0][0] if len(alt) == 1 else None


# --- cleaning what the election sites publish -------------------------------
#
# The same party is written differently across the five sites, and names arrive
# in whatever case the local registry typed them. Neither is worth a lookup
# table: the variation is punctuation and case, not identity.

_SEP_SPACES = re.compile(r"\s*([-./])\s*")
_WS = re.compile(r"\s+")

#: Particles that stay lower case inside a Portuguese name.
_PARTICLES = frozenset(
    ("de", "da", "do", "das", "dos", "e", "d'", "van", "von", "y")
)


def canonical_party(acronym: str) -> str:
    """One spelling per party or coalition.

    The 2013 site writes "PCP - PEV" where 2009 and 2017 write "PCP-PEV". They
    are the same coalition, and grouping by the raw string would split it in
    three. Only whitespace and case are touched; nothing is mapped to anything
    else, because that would be a judgement about who is whom.
    """
    out = _WS.sub(" ", (acronym or "").strip()).upper()
    return _SEP_SPACES.sub(r"\1", out)


def clean_person_name(name: str | None) -> str | None:
    """Trim, collapse spaces, and de-shout a name that arrived in capitals.

    Some municípios publish "HUGO MANUEL DOS SANTOS MARTINS" and others publish
    the same person in mixed case. Only all-caps input is recased: a name that
    already carries case was typed deliberately and is left alone.
    """
    if not name:
        return None
    cleaned = _WS.sub(" ", name.strip())
    if not cleaned:
        return None
    if not cleaned.isupper():
        return cleaned
    words = []
    for i, word in enumerate(cleaned.lower().split(" ")):
        if i and word in _PARTICLES:
            words.append(word)
        elif "-" in word:                       # Vila-Chã, Sá-Carneiro
            words.append("-".join(p.capitalize() for p in word.split("-")))
        else:
            words.append(word.capitalize())
    return " ".join(words)
