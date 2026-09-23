/**
 * Every word the interface says, in both languages.
 *
 * No i18n library. This is one object, one lookup and one `{x}` substitution,
 * which is the whole of what ~200 strings needs. A dependency here would buy
 * pluralisation rules and message extraction, neither of which this site uses.
 *
 * Portuguese is the source language and the fallback: a key missing from `en`
 * renders its Portuguese, which is worse than a translation and far better than
 * a blank or a raw key.
 *
 * What is NOT here, and never will be: anything the register wrote. Contract
 * objects, supplier names, buyer names, procedure names and CPV descriptions
 * arrive from IMPIC verbatim and are rendered verbatim, in Portuguese, in both
 * languages. `common.verbatim` is where the English pages say so.
 */
import { page } from '$app/state';

export type Lang = 'pt' | 'en';

/** The language of the page being rendered. `/en/...` is English, `/` is not. */
export const lang = (): Lang => (page.params?.lang === 'en' ? 'en' : 'pt');

/** An internal path in the current language. `/` becomes `/en` under English. */
export const L = (path: string): string =>
	lang() === 'en' ? (path === '/' ? '/en' : `/en${path}`) : path;

/** The same path in the other language, for the switcher. */
export function swap(pathname: string, to: Lang): string {
	const bare = pathname.replace(/^\/en(?=\/|$)/, '') || '/';
	return to === 'en' ? (bare === '/' ? '/en' : `/en${bare}`) : bare;
}

/** BCP 47 tag, for `Intl` and for `<html lang>`. */
export const locale = (): string => (lang() === 'en' ? 'en-GB' : 'pt-PT');

const PT: Record<string, string> = {
	/* ---- shared ------------------------------------------------------- */
	'common.site': 'Onde Vai Parar',
	// The brand alone carries no search term. The landing page and the shell
	// title spell out what the site is; every other page keeps `· common.site`.
	'common.siteTitle': 'Onde Vai Parar: contratos públicos das câmaras municipais',
	'common.description':
		'Quem recebe o dinheiro das câmaras municipais portuguesas, e com qual procedimento.',
	'common.na': 'N/A',
	'common.loading': 'A carregar…',
	'common.loadMore': 'Carregar mais',
	'common.retry': 'Tentar de novo',
	'common.endOfList': 'Fim da lista.',
	'common.clear': 'Limpar',
	'common.all': 'Todos',
	'common.allF': 'Todas',
	'common.close': 'Fechar',
	'common.sortBy': 'Ordenar por',
	'common.sortDesc': 'A ordenar do maior para o menor',
	'common.sortAsc': 'A ordenar do menor para o maior',
	'common.contracts': 'contratos',
	'common.contract': 'contrato',
	'common.companies': 'empresas',
	'common.company': 'empresa',
	'common.years': 'anos',
	'common.year': 'ano',
	'common.noDescription': 'Sem descrição',
	'common.whereAmI': 'Onde estás',
	'common.portugal': 'Portugal',
	'common.notMeasurable': 'não medível',
	// Empty in Portuguese: a Portuguese reader has no reason to be told that
	// Portuguese source text was left in Portuguese. Rendered only where non-empty.
	'common.verbatim': '',

	/* ---- navigation ---------------------------------------------------- */
	'nav.menu': 'Menu',
	'nav.loading': 'A carregar a página',
	'nav.closeMenu': 'Fechar o menu',
	'nav.main': 'Principal',
	'nav.municipality': 'Município',
	'nav.panorama': 'Panorama',
	'nav.faqs': 'FAQs',
	'nav.language': 'Idioma',
	'nav.toEnglish': 'English',
	'nav.toPortuguese': 'Português',

	/* ---- footer -------------------------------------------------------- */
	'footer.blurb': 'Contratos públicos portugueses, lidos com má-língua mas com os números certos.',
	'footer.sourceHead': 'Fonte',
	'footer.rawData': 'dados em bruto',
	'footer.officialPortal': 'portal oficial',
	'footer.api': 'API',
	'footer.apiNote': 'os mesmos números em JSON',
	'footer.terms': 'Termos e condições',
	'footer.termsNote': 'o que isto é e o que não é',
	'footer.code': 'Código-fonte',
	'footer.codeNote': 'AGPL-3.0, tudo o que corre aqui',
	'footer.latest': 'Último contrato',
	'footer.disclaimerHead': 'Disclaimer',
	'footer.noCrimeStrong': 'Nada aqui é acusação de crime.',
	'footer.noCrimeBody':
		'Ajuste direto é um procedimento legal. Um número alto quer dizer “vale a pena olhar”.',
	'footer.termsFull': 'Os termos, por extenso',

	/* ---- the disclaimer, keyed by the API ------------------------------ */
	'disclaimer.source':
		'Os números vêm do portal BASE, o registo oficial dos contratos públicos portugueses, publicado pelo IMPIC. Não corrigimos nada: o que esteja errado ou em falta no registo original aparece aqui tal e qual.',
	'disclaimer.publication_lag':
		'Um contrato só entra no registo depois de publicado, e nem todos são publicados ao mesmo ritmo, por isso os meses mais recentes costumam estar incompletos.',
	'disclaimer.bidders':
		'Nem todos os contratos dizem quem concorreu. Os indicadores que dependem disso são calculados apenas sobre os que o declararam, e cada um diz sobre quantos foi calculado.',
	'disclaimer.map_overlap':
		'Um contrato pode abranger vários concelhos e conta em cada um deles, por isso a soma do mapa pode ser maior do que o total gasto.',
	'disclaimer.legal':
		'Os indicadores medem o que é observável nos dados, não irregularidades. Ajuste direto é um procedimento legal e muitas vezes o mais sensato.',

	/* ---- the satirical verdict, keyed by the API ----------------------- */
	'verdict.clean': 'Isto parece legítimo',
	'verdict.clean.quip': 'Concursos a sério, fornecedores a mais para caber num jantar.',
	'verdict.fishy': 'Cheira-me a cunhas',
	'verdict.fishy.quip': 'Nada de ilegal à vista, mas os mesmos nomes aparecem vezes de mais.',
	'verdict.blatant': 'Cunhas tão óbvias',
	'verdict.blatant.quip': 'Quase ninguém a concorrer e o dinheiro sempre a cair do mesmo lado.',

	/* ---- severity ------------------------------------------------------ */
	'sev.ok': 'baixo',
	'sev.warn': 'moderado',
	'sev.serious': 'elevado',
	'sev.critical': 'muito elevado',

	/* ---- money and dates ----------------------------------------------- */
	'unit.bn': 'mil M €',
	'unit.m': 'M €',
	'unit.k': 'mil €',
	'unit.eur': '€',
	'fmt.nearLimit': 'a {gap} do limite de {limit}',
	'fmt.nova.unknown': 'o primeiro contrato público desta empresa foi em {date}.',
	'fmt.nova.first': 'nunca tinha tido um contrato público e este, em {date}, foi o primeiro.',
	'fmt.nova.weeks': 'o primeiro contrato público desta empresa foi em {date}, poucas semanas antes.',
	'fmt.nova.days': 'o primeiro contrato público desta empresa foi em {date}, {days} dias antes.',

	/* ---- the indicators ------------------------------------------------ */
	'signal.ajuste_direto': 'Sem concurso',
	'signal.ajuste_direto.blurb':
		'Dinheiro entregue por ajuste direto: a câmara escolhe a empresa e contrata, sem pôr o trabalho a concurso. É legal abaixo de certos valores.',
	'signal.concentracao': 'Concentração',
	'signal.concentracao.blurb':
		'Mede se o dinheiro está espalhado por muitas empresas ou fechado em poucas. Perto de 0 são muitas a dividir, perto de 100 é quase tudo numa só.',
	'signal.single_bidder': 'Um só concorrente',
	'signal.single_bidder.blurb':
		'Dinheiro de concursos em que só apareceu uma empresa. Houve concurso, mas ninguém contra quem competir.',
	'signal.threshold_surf': 'Encostado ao limite',
	'signal.threshold_surf.blurb':
		'Contratos com o valor mesmo por baixo do limite legal. Um euro acima e obrigariam a um procedimento mais exigente.',
	'signal.newcomer_value': 'Dinheiro a empresas sem história',
	'signal.newcomer_value.blurb':
		'Dinheiro para empresas que não tinham nenhum contrato público antes deste período e que ganharam aqui sem concorrência, por ajuste direto ou como único concorrente. Ser nova não é irregular; aparecer do nada e ganhar sem ninguém a competir é que merece um olhar.',
	'signal.ad_contracts': 'Contratos sem concurso',
	'signal.ad_contracts.blurb':
		'A mesma prática contada em número de contratos e não em euros. Costuma ser muito mais alta, porque os ajustes diretos são muitos e pequenos.',
	'signal.undisclosed_bidders': 'Concorrentes por divulgar',
	'signal.undisclosed_bidders.blurb':
		'Contratos que não dizem quem concorreu. Sem essa lista não há forma de saber se houve concorrência a sério.',
	'signal.top_supplier': 'O maior fornecedor',
	'signal.top_supplier.blurb':
		'Quanto do dinheiro total ficou com uma única empresa, a que mais recebeu.',
	'signal.top3_suppliers': 'Nos 3 maiores',
	'signal.top3_suppliers.blurb':
		'Quanto do dinheiro total ficou com as três empresas que mais receberam.',
	'signal.repeat_winners': 'Clientes habituais',
	'signal.repeat_winners.blurb':
		'Dinheiro para empresas que ganham vezes sem conta. Pode ser só competência, mas depende de quantos anos estão a ser contados.',

	'unmeasurable.newcomer_value':
		'Faltam anos anteriores para saber que empresas não tinham contratos públicos antes.',
	'unmeasurable.single_bidder': 'Nenhum contrato deste período diz quem concorreu.',
	'unmeasurable.concentracao': 'Sem dinheiro registado, não há nada para repartir.',

	/* ---- signal card --------------------------------------------------- */
	'card.outsideIndex': 'fora do índice',
	'card.of': 'de',
	'card.disclosed': 'divulgados',
	'card.level': '{label}: {value}%, nível {level}',
	'card.indexLevel': '{label}: {value} de 100, nível {level}',

	/* ---- error pages --------------------------------------------------- */
	'err.404.title': 'Não encontrámos isso',
	'err.404.body':
		'A página que procuras não existe, mudou de sítio, ou nunca chegou a existir. Acontece.',
	'err.404.foot': 'Se chegaste aqui por um link nosso, o link é que está mal.',
	'err.429.title': 'Devagar, se faz favor',
	'err.429.body':
		'Chegaram pedidos a mais num espaço de tempo curto. Espera uns segundos e tenta outra vez.',
	'err.429.foot': 'O limite existe para o site continuar de pé para toda a gente.',
	'err.500.title': 'Isto foi culpa nossa',
	'err.500.body':
		'Alguma coisa do nosso lado tropeçou a meio do pedido. Os dados estão bem, o problema é o caminho até eles.',
	'err.500.foot': 'Tenta daqui a pouco. Se persistir, é porque ainda não demos por ela.',
	'err.home': 'Voltar ao início',

	/* ---- landing -------------------------------------------------------- */
	'landing.eyebrow': 'Onde Vai Parar · contratos públicos municipais',
	'landing.title': 'Quem anda a chular os nossos impostos?',
	'landing.sub':
		'Quem recebeu, com qual procedimento, e quantas vezes o mesmo nome volta a aparecer. Lemos os contratos que as câmaras são obrigadas a publicar e mostramos o que lá está, sem adjetivos.',
	'landing.awarded': 'adjudicados',
	'landing.contracts': 'contratos',
	'landing.municipalities': 'municípios',
	'landing.to': 'a {year}',
	'landing.crossTo': 'Ou vê {link}, por distrito e pelo partido que estava à frente da câmara.',
	'landing.crossToLink': 'quanto dinheiro foi entregue sem concurso',
	'landing.pickTitle': 'Escolhe o teu município',
	'landing.pickSub': 'três formas, a mesma resposta',
	'landing.howToPick': 'Como escolher o município',
	'landing.tab.name': 'Pelo nome',
	'landing.tab.district': 'Por distrito',
	'landing.tab.map': 'No mapa',
	'landing.search': 'Procurar município',
	'landing.searchPlaceholder': 'Procurar município…',
	'landing.noMatch': 'Nenhum município com esse nome entre os carregados.',
	'landing.noDistricts': 'Não foi possível carregar a lista de distritos.',
	'landing.district': 'Distrito',
	'landing.choose': 'Escolher…',
	'landing.pickDistrict': 'Escolha um distrito para ver os municípios carregados.',
	'landing.hintDrilled': 'A vermelho, os municípios já carregados. Toca num para o abrir.',
	'landing.hintCountry':
		'A vermelho, os distritos com municípios carregados. Toca num para o abrir concelho a concelho.',
	'landing.noMap': 'Não foi possível carregar o mapa.',
	'landing.mapAriaDistrict': 'Concelhos do distrito de {district}, para escolher um município',
	'landing.mapAriaCountry': 'Distritos de Portugal, para escolher por onde começar',

	/* ---- município ------------------------------------------------------ */
	'muni.noData': 'Ainda sem dados',
	'muni.noDataBody':
		'Não há contratos carregados para este município. Volta mais tarde, os dados são atualizados a partir do registo público de contratos.',
	'muni.fallbackName': 'Município',
	// Leads with the phrase a resident actually types. The brand goes last:
	// "Odivelas · Onde Vai Parar" put the one word nobody searches for first.
	// Read by the page AND by scripts/prerender.mjs, which writes it into the
	// static file a crawler receives before any JavaScript runs.
	'muni.metaTitle': 'Contratos públicos de {name} | Onde Vai Parar',
	'muni.metaDescription':
		'Contratos públicos de {name}: quem recebe o dinheiro, quanto foi por ajuste direto e que empresas ganham mais.',
	'muni.tab.overview': 'Visão geral',
	'muni.tab.map': 'Mapa',
	'muni.tab.network': 'Rede',
	'muni.tab.companies': 'Empresas',
	'muni.tab.stats': 'Estatísticas',
	'muni.tab.contracts': 'Contratos',
	'muni.sections': 'Secções',
	'muni.eyebrow': 'Contratos públicos',
	'muni.mandates': '{n} mandatos',
	'muni.period': 'Período',
	'muni.everything': 'Tudo',
	'muni.olderYears': 'Anos anteriores',
	'muni.fewerYears': 'Menos anos',
	'muni.moreYears': 'Mais {n} anos',
	'muni.nYears': '{n} anos',
	'muni.range': 'Intervalo…',
	'muni.lastNYears': 'Últimos {n} anos',
	'muni.from': 'De',
	'muni.until': 'Até',
	'muni.allYears': 'todos',
	'muni.maxSpan': 'no máximo {n} anos',
	'muni.spanTrimmed': 'O período foi encurtado para {n} anos, o máximo desta vista.',
	'muni.periodFromTo': '{from} a {to}',
	'muni.periodSince': 'desde {from}',
	'muni.periodUntil': 'até {to}',
	'muni.periodUnknown': 'sem período conhecido',
	'muni.spent': 'gastos',
	'muni.contracts': 'contratos',
	'muni.suppliers': 'fornecedores',
	'muni.riskIndex': 'Índice de risco',
	'muni.riskCaption':
		'Média dos {n} indicadores mensuráveis neste período, todos em percentagem do dinheiro.',
	'muni.satireIndex': 'Malandrómetro',
	'muni.satireCaption':
		'Os mesmos indicadores, mas com os mais reveladores a pesar mais: concursos com um só concorrente, dinheiro concentrado em poucas empresas, ajuste direto, contratos encostados ao limite e dinheiro a empresas novas.',
	'muni.units':
		'Dá para {bifanas} bifanas, ou {salarios} salários mínimos anuais.',
	'muni.chipRisk': 'risco',
	'muni.chipSatire': 'malandrómetro',
	'muni.indicators': 'Indicadores',
	'muni.whoGotMost': 'Quem recebeu mais',
	'muni.groupBy': 'Agrupar por',
	'muni.group.supplier': 'Fornecedor',
	'muni.group.sector': 'Setor',
	'muni.group.procedure': 'Procedimento',
	'muni.barsAria': 'Maiores destinos do dinheiro, agrupados por {grouping}',
	'muni.barsNoteSupplier': 'Clica numa barra para abrir a página da empresa.',
	'muni.barsNoteOther': 'Clica numa barra para ver só esses contratos.',
	'muni.legendNoAd': 'sem ajuste direto',
	'muni.legendSome': 'algum',
	'muni.legendMost': 'maioria',
	'muni.legendAlmostAll': 'quase tudo',
	'muni.legendCategory':
		'Cada barra é uma categoria inteira, por isso a cor identifica a categoria e não o grau de ajuste direto.',
	'muni.noGrouping': 'Sem dados suficientes para este agrupamento.',
	'muni.mapTitle': 'Onde o trabalho é executado',
	'muni.mapNote':
		'Isto é o local de execução do contrato, não a morada do fornecedor, que nenhum dataset publica. Um contrato que abrange vários concelhos conta em cada um, por isso a soma do mapa ({sum}) {tail}.',
	'muni.mapExceeds': 'excede o total gasto, {total}',
	'muni.mapMayExceed': 'pode exceder o total gasto',
	'muni.mapError': 'Não foi possível carregar o mapa. Tenta recarregar a página.',
	'muni.mapAria': 'Mapa de Portugal por concelho de execução',
	'muni.concelho': 'Concelho',
	'muni.areaBadge': '{money} em {n} contratos executados aqui.',
	'muni.areaError': 'Não foi possível carregar os contratos deste concelho. Tenta outra vez.',
	'muni.areaEmpty': 'Sem contratos registados neste concelho.',
	'muni.areaHint': 'Clica num concelho para ver os contratos executados lá.',
	'muni.islandsNote':
		'Açores e Madeira estão deslocados para junto do continente, como é hábito em mapas de Portugal, caso contrário o continente ficaria do tamanho de uma unha.',
	'muni.webTitle': 'A teia',
	'muni.graphSize': 'Fornecedores no grafo',
	'muni.graphHintNarrow': 'Toca numa empresa para ver os seus contratos.',
	'muni.graphHintWide':
		'Passa o rato numa empresa para isolar as suas ligações, clica para ver os contratos.',
	'muni.graphAria': 'Rede de pagamentos a fornecedores, agrupada por setor',
	'muni.hidingSectors': 'A esconder {n} setores.',
	'muni.hidingSector': 'A esconder 1 setor.',
	'muni.showAll': 'Mostrar tudo',
	'muni.symDiamond': 'Losango: empresa sem história anterior',
	'muni.symCircle': 'Círculo: restantes fornecedores',
	'muni.symSize': 'Quanto maior, mais dinheiro recebeu',
	'muni.graphNote':
		'A cor diz o setor. Os losangos marcam empresas que não tinham contratos públicos antes deste período e que ganharam aqui sem concorrência, por ajuste direto ou como único concorrente. Ser nova não é irregular, é só o que merece um segundo olhar.',
	'muni.supplier': 'Fornecedor',
	'muni.newHere': 'Empresa nova aqui: {sentence}',
	'muni.seeCompany': 'Ver a empresa',
	'muni.pickedError': 'Não foi possível carregar os contratos deste fornecedor. Tenta outra vez.',
	'muni.pickedEmpty': 'Sem contratos para este fornecedor.',
	'muni.col.object': 'Objeto',
	'muni.col.date': 'Data',
	'muni.col.procedure': 'Procedimento',
	'muni.col.bidders': 'Concorrentes',
	'muni.col.value': 'Valor',
	'muni.col.supplier': 'Fornecedor',
	'muni.col.company': 'Empresa',
	'muni.col.sector': 'Setor',
	'muni.col.firstPublic': '1.º contrato público',
	'muni.newcomersTitle': 'Empresas sem história anterior',
	'muni.newcomersUnknown':
		'Nenhum registo de constituição de empresas existe nestes dados, por isso o único indício de novidade é a estreia nos contratos públicos. O período disponível ({period}) é curto demais para distinguir uma empresa nova de outra que já existia antes: faltam anos anteriores para comparar.',
	'muni.newcomersNote':
		'Empresas cujo primeiro contrato público em todo o registo é recente e que, pouco depois, ganharam aqui. Ser nova não é ilegal nem suspeito por si só, mas uma empresa recém-chegada que arruma logo um contrato grande é o tipo de coisa que vale a pena olhar duas vezes.',
	'muni.newcomersNone':
		'Nenhum fornecedor estreou nos contratos públicos no ano anterior a ganhar aqui. Os losangos no grafo assinalariam esses casos.',
	'muni.rivalsTitle': 'Quem concorre contra quem',
	'muni.rivalsNote':
		'Pares de empresas que aparecem repetidamente no mesmo concurso. Só os contratos que divulgaram concorrentes podem gerar uma linha.',
	'muni.rivalsAlso': 'E também',
	'muni.rivalsTenders': 'Concursos',
	'muni.rivalsNone': 'Nenhum par repetido nestes dados.',
	'muni.statsTitle': 'Números de referência',
	'muni.statsNote':
		'Metade dos contratos custa pouco e alguns custam muito. Por isso o valor do meio e o valor mais alto estão lado a lado: é a diferença entre os dois que conta a história.',
	'muni.kpi.typical': 'Custo do contrato típico',
	'muni.kpi.typicalNote':
		'metade dos {n} contratos custou menos do que isto, metade custou mais',
	'muni.kpi.mean': 'Custo médio por contrato',
	'muni.kpi.meanSkewed':
		'bem acima do contrato típico, porque meia dúzia de contratos enormes puxa a conta para cima',
	'muni.kpi.meanFlat': 'parecido com o contrato típico, sem valores a destoar',
	'muni.kpi.priciest': 'Os contratos mais caros',
	'muni.kpi.priciestNote': 'só um em cada dez contratos custou mais do que isto',
	'muni.kpi.half': 'Metade do dinheiro',
	'muni.kpi.halfOne': 'uma única empresa recebeu metade de todo o dinheiro',
	'muni.kpi.halfMany': 'empresas chegaram para receber metade de todo o dinheiro',
	'muni.kpi.largest': 'Maior contrato',
	'muni.kpi.largestNote': 'um só contrato levou {pct} de todo o dinheiro',
	'muni.kpi.kinds': 'Tipos de compra',
	'muni.kpi.kindsNote': 'coisas diferentes compradas, do papel à obra pública',
	'muni.zeroOne': 'Um contrato está registado com valor zero.',
	'muni.zeroMany': '{n} contratos estão registados com valor zero.',
	'muni.noOverruns':
		'O valor realmente pago no fim quase nunca é publicado, por isso não há aqui derrapagens: só o valor pelo qual o contrato foi fechado.',
	'muni.distributions': 'Distribuições',
	'muni.byProcedure': 'Por procedimento',
	'muni.bySector': 'Por setor',
	'muni.byYear': 'Por ano',
	'muni.unit.procedure': 'Procedimento',
	'muni.unit.sector': 'Setor',
	'muni.unit.year': 'Ano',
	'muni.companiesTitle': 'Quem recebeu o dinheiro',
	'muni.companiesNote':
		'Todas as empresas que ganharam pelo menos um contrato neste período, ordenáveis por qualquer coluna. "Sem concurso" é a parte dos contratos desta empresa que foi por ajuste direto.',
	'muni.contractsTitle': 'Contratos',

	/* ---- mandate timeline ----------------------------------------------- */
	'mandate.title': 'Quem mandou, e quanto se contratou',
	'mandate.note':
		'Resultados das autárquicas, mandato a mandato. Um mandato começa no dia das eleições, por isso um contrato assinado em outubro conta para quem entrou, não para quem saiu.',
	'mandate.pickNote': 'Carrega num mandato para ler o resto da página só nesses anos.',
	'mandate.today': 'hoje',
	'mandate.to': 'a',
	'mandate.readOnly': 'Ler os números só de {from} a {to}',
	'mandate.flipped': 'mudou de mãos',
	'mandate.relabelled': 'mesma pessoa, outra lista',
	'mandate.coalition': 'coligação',
	'mandate.citizens': 'grupo de cidadãos',
	'mandate.independent': 'Independente',
	'mandate.barAria': '{money} contratados, {n} contratos',
	'mandate.noTender': '{pct} sem concurso',
	'mandate.reformFlag': 'a lei mudou a meio',
	'mandate.reformNote':
		'A lei dos contratos públicos mudou em agosto de 2017, a meio de um destes mandatos, e apertou os limites do ajuste direto. A descida que se vê a seguir acontece em câmaras de todos os partidos, incluindo nas que não mudaram de mãos.',
	'mandate.provisional':
		'Resultados provisórios publicados pela Administração Interna. O registo com valor legal é o Mapa Oficial da Comissão Nacional de Eleições. Ganhar a eleição também não é o mesmo que ter cumprido o mandato inteiro: demissões e eleições intercalares não aparecem aqui.',

	/* ---- panorama -------------------------------------------------------- */
	'pan.eyebrow': 'Onde Vai Parar · comparações',
	'pan.title': 'Quem manda, e quem compra sem concurso',
	'pan.lede':
		'A percentagem do dinheiro entregue por ajuste direto, sem pôr o trabalho a concurso. Está separada em dois períodos porque a lei mudou a meio: comparar um município de 2014 com outro de 2024 é comparar regras diferentes, não práticas diferentes.',
	'pan.howToCompare': 'Como comparar',
	'pan.view.map': 'Mapa político',
	'pan.view.party': 'Por partido',
	'pan.whoWon': 'Quem ganhou cada câmara',
	'pan.drilledNote':
		'As {n} câmaras do distrito, cada uma com a cor da lista que a ganhou. Carrega numa que tenha contratos carregados para abrir a sua página.',
	'pan.countryNote':
		'As 308 câmaras do país, agrupadas por distrito e pintadas com a cor do partido que ganhou mais câmaras em cada um. Toca num distrito para o abrir concelho a concelho.',
	'pan.election': 'Eleição',
	'pan.yearFailed': 'Não foi possível carregar essa eleição. Tenta outra vez.',
	'pan.mapError': 'Não foi possível carregar o mapa.',
	'pan.mapAriaDistrict':
		'Mapa do distrito de {district}, cada concelho com a cor da lista que ganhou a câmara',
	'pan.mapAriaCountry':
		'Mapa de Portugal por distrito, cada um com a cor do partido que ganhou mais câmaras',
	'pan.seeCountry': 'Ver o país',
	'pan.inCoalition': '{n} em coligação',
	'pan.showMore': 'Mostrar mais {n}',
	'pan.showLess': 'Mostrar menos',
	'pan.clearFilter': 'Limpar filtro',
	'pan.hoverNarrow': 'Toca',
	'pan.hoverWide': 'Passa o rato',
	'pan.hoverNote':
		'{verb} para ver o presidente eleito, a duração do mandato e o que a câmara contratou nesse período. O gasto só aparece nos municípios já carregados aqui, e a cor de uma coligação é a de quem a lidera.',
	'pan.withData': 'Com dados neste distrito:',
	'pan.noElection': 'Sem resultados carregados para esta eleição.',
	'pan.era.before': 'Até agosto de 2017',
	'pan.era.beforeNote': 'com a lei antiga',
	'pan.era.after': 'De agosto de 2017 em diante',
	'pan.era.afterNote': 'com a lei atual',
	'pan.noEraData': 'Sem dados carregados para este período.',
	'pan.mandatesIn': '{mandates} em {municipalities}',
	'pan.mandateOne': '{n} mandato',
	'pan.mandateMany': '{n} mandatos',
	'pan.municipalityOne': '{n} município',
	'pan.municipalityMany': '{n} municípios',
	'pan.spread': 'entre {low} e {high} conforme o mandato',
	'pan.singleCase': 'um só caso',
	'pan.singleCaseTail': ', sem margem para comparar',
	'pan.howToRead': 'Como ler isto, e como não ler',
	'pan.read1':
		'Estes números dizem como cada câmara comprou, não quem é honesto. A forma de comprar depende muito do tamanho do município, dos serviços que tem internamente e das empresas que existem na zona. Uma câmara pequena sem equipa de compras recorre mais ao ajuste direto do que uma capital com departamento jurídico próprio, e isso não é um partido.',
	'pan.read2':
		'A barra mais escura é a percentagem de todo o dinheiro. A barra fina por trás é a diferença entre o mandato mais baixo e o mais alto do mesmo grupo: quando é larga, a média não representa quase nada. Grupos com um só mandato não têm margem nenhuma e estão assinalados.',
	'pan.read3':
		'Só estão aqui os municípios já carregados, que são poucos e quase todos da zona de Lisboa. Não é uma amostra do país e não deve ser lida como tal.',
	'pan.tip.list': 'Lista',
	'pan.tip.president': 'Presidente',
	'pan.tip.term': 'Mandato',
	'pan.tip.contracts': 'Contratos',
	'pan.tip.notLoaded': 'não carregados',
	'pan.tip.spentInTerm': 'Gasto no mandato',
	'pan.tip.noTender': 'Sem concurso',
	'pan.tip.leadingParty': 'Partido com mais câmaras',
	'pan.tip.ofTotal': '{label} ({held} de {total})',
	'pan.tip.withData': 'Com dados',
	'pan.tip.camarasWithData': '{loaded} de {total} câmaras',
	'pan.tip.camaraWithData': '{loaded} de {total} câmara',
	'pan.tip.noneLoaded': 'nenhuma câmara carregada',
	'pan.months': '{n} meses',
	'pan.month': '{n} mês',

	/* ---- empresa --------------------------------------------------------- */
	'firm.eyebrow': 'Empresa · NIF',
	'firm.noName': 'Empresa sem nome no registo',
	'firm.metaDescription': '{name} recebeu {money} em {n} contratos públicos.',
	'firm.received': 'recebido',
	'firm.contracts': 'contratos',
	'firm.camara': 'câmara',
	'firm.camaras': 'câmaras',
	'firm.noTender': 'sem concurso',
	'firm.adNotMeasurable': 'não medível',
	'firm.adAlmostAll': 'quase tudo',
	'firm.adGoodPart': 'boa parte',
	'firm.adLittle': 'pouco',
	'firm.inDistrict': '{n} neste distrito',
	'firm.tapForContracts': 'toca para ver os contratos aqui',
	'firm.mainSector': 'Setor principal',
	'firm.firstContract': 'Primeiro contrato',
	'firm.lastContract': 'Último contrato',
	'firm.scopeNote':
		'Só conta os municípios já carregados aqui. Esta empresa pode ter contratos com o Estado ou com outras câmaras que não estão nesta base.',
	'firm.yearByYear': 'Ano a ano',
	'firm.yearByYearNote':
		'O mesmo total pode ser uma década de trabalho regular ou um único ano em que apareceu e levou tudo. A cor da coluna é a parte desse ano que foi por ajuste direto.',
	'firm.yearsAria': 'Valor adjudicado a esta empresa em cada ano',
	'firm.registry': 'No registo comercial',
	'firm.soldTo': 'A quem vendeu',
	'firm.howToView': 'Como ver',
	'firm.viewMap': 'Mapa',
	'firm.viewList': 'Lista',
	'firm.mapAriaDistrict':
		'Concelhos do distrito de {district}, pintados pelo que esta empresa recebeu de cada câmara',
	'firm.mapAriaCountry':
		'Distritos de Portugal, pintados pelo que esta empresa recebeu de cada um',
	'firm.mapHintDrilled': 'Toca num concelho para ver os contratos desta empresa nessa câmara.',
	'firm.mapHintCountry': 'Toca num distrito para o abrir concelho a concelho.',
	'firm.darker': 'Quanto mais escuro, mais dinheiro.',
	'firm.unplacedOne':
		'{n} câmara não pôde ser colocada no mapa porque o nome não resolve para um concelho só. Está na lista.',
	'firm.unplacedMany':
		'{n} câmaras não puderam ser colocadas no mapa porque o nome não resolve para um concelho só. Estão na lista.',
	'firm.noneHere': 'Esta empresa não recebeu nada neste distrito.',
	'firm.shareOfIntake': '{n} contratos · {pct} do que recebeu',
	'firm.oneBuyer':
		'Tudo o que esta empresa recebeu, nos dados carregados, veio de uma só câmara. Isso não é irregular: muitas empresas trabalham com um só cliente público. É apenas o que os números dizem.',
	'firm.contractsTitle': 'Contratos',
	'firm.clickContract': 'Clica num contrato para o ver todo.',
	'firm.searchObject': 'Procurar no objeto',
	'firm.searchPlaceholder': 'asfalto, refeições…',
	'firm.buyer': 'Câmara',
	'firm.noContracts':
		'Esta empresa não tem contratos nos municípios carregados. Se chegaste aqui a partir de um deles, o erro é nosso.',
	'firm.moreFailed': 'Não foi possível carregar mais contratos.',
	'firm.backTo': 'Voltar a {name}',
	'firm.pickOther': 'Escolher outro município',

	/* ---- company registry profile ---------------------------------------- */
	'reg.missing':
		'Esta empresa não tem registo comercial publicado nas fontes gratuitas, por isso não há aqui atividades nem sede.',
	'reg.registeredName': 'Nome no registo',
	'reg.form': 'Forma',
	'reg.type': 'Tipo',
	'reg.founded': 'Constituída',
	'reg.foundedIn': 'em',
	'reg.foundedOrEarlier': 'ou antes',
	'reg.address': 'Sede',
	'reg.activities': 'Atividades registadas (CAE)',
	'reg.principal': 'principal',
	'reg.sourceLine':
		'Registo comercial via {source}. A forma jurídica vem do nome da empresa, que por lei tem de a indicar.',
	'reg.floorNote':
		'O registo de atos só começa em {year}, por isso para empresas mais antigas essa é a data mais recuada que existe, não a data real.',
	'reg.noCapital':
		'O capital social e o número de trabalhadores não são publicados gratuitamente por nenhuma fonte, por isso não estão aqui.',

	/* ---- contract detail -------------------------------------------------- */
	'ct.title': 'Contrato {id}',
	'ct.metaFallback': 'Contrato público',
	'ct.noDescription': 'Contrato sem descrição no registo',
	'ct.backTo': 'Voltar a {name}',
	'ct.thisMunicipality': 'este município',
	'ct.procedureNA': 'Procedimento N/A',
	'ct.centralized': 'compra centralizada',
	'ct.green': 'critérios ambientais',
	'ct.value': 'valor do contrato',
	'ct.basePrice': 'preço base',
	'ct.bidders': 'concorrentes',
	'ct.execDays': 'dias de prazo',
	'ct.adCallout':
		'Este contrato foi por ajuste direto: a câmara escolheu a empresa sem abrir concurso. É legal abaixo dos limites que a lei fixa, e é o que acontece na maior parte das compras pequenas.',
	'ct.adCalloutStrong': 'ajuste direto',
	'ct.howItWorks': 'Como funciona',
	'ct.whoGotIt': 'Quem ficou com ele',
	'ct.noNif': 'sem NIF no registo',
	'ct.awardee': 'adjudicatário',
	'ct.noAwardee': 'O registo não identifica o adjudicatário.',
	'ct.whoBid': 'Quem concorreu',
	'ct.whoBidNote': 'As empresas que entraram neste procedimento. Quem ganhou está marcado.',
	'ct.result': 'Resultado',
	'ct.won': 'ganhou',
	'ct.lost': 'não ganhou',
	'ct.noBidders':
		'O registo não diz quem mais concorreu. Isso falta na maior parte dos contratos, por isso não é sinal de nada por si só.',
	'ct.whatRecordSays': 'O que o registo diz',
	'ct.signed': 'Assinado',
	'ct.published': 'Publicado',
	'ct.type': 'Tipo',
	'ct.sector': 'Setor',
	'ct.cpv': 'Classificação (CPV)',
	'ct.criterion': 'Critério',
	'ct.framework': 'Acordo-quadro',
	'ct.executedWhere': 'Onde é executado',
	'ct.centralizedLabel': 'Compra centralizada',
	'ct.greenLabel': 'Critérios ambientais',
	'ct.yes': 'sim',
	'ct.no': 'não',
	'ct.below': 'abaixo',
	'ct.above': 'acima',
	'ct.closedVsBase':
		'Fechou {direction} do preço base em {pct}. O valor realmente pago no fim não é publicado neste registo, por isso não há aqui derrapagens: isto compara o que a câmara previa com o que contratou.',
	'ct.reason': 'A razão invocada',
	'ct.reasonNote':
		'O fundamento legal que a câmara citou, tal como está no registo. Normalmente é a norma do Código dos Contratos Públicos que permite este procedimento. Citá-la é o que a lei exige; não diz nada sobre se a escolha foi acertada.',
	'ct.sourceTitle': 'A fonte',
	'ct.basePortal': 'Ficha no Portal BASE',
	'ct.basePortalNote': 'o registo oficial deste contrato',
	'ct.impicDataset': 'Conjunto de dados do IMPIC',
	'ct.impicDatasetNote': 'o ficheiro de onde esta página foi lida',
	'ct.announcement': 'Anúncio publicado',
	'ct.pieces': 'Peças do procedimento',
	'ct.sourceNote':
		'Tudo nesta página vem do registo que o IMPIC publica. Não corrigimos nada: o que esteja em falta ou errado na origem aparece aqui tal e qual. O Portal BASE tem estado indisponível de vez em quando e, quando está, a sua ficha responde "não foi possível obter os dados do servidor". Isso é do portal, não deste contrato: os números aqui vêm do ficheiro do IMPIC, que é o mesmo registo.',

	/* ---- tables ----------------------------------------------------------- */
	'tbl.searchCompany': 'Procurar empresa ou NIF',
	'tbl.searchCompanyPlaceholder': 'Gertal, 500123456…',
	'tbl.companyType': 'Tipo de empresa',
	'tbl.totalReceived': 'Total recebido',
	'tbl.contracts': 'Contratos',
	'tbl.noTender': 'Sem concurso',
	'tbl.lastContract': 'Último contrato',
	'tbl.searchFailed': 'A procura falhou. Tenta outra vez.',
	'tbl.noCompanies': 'Nenhuma empresa corresponde a esta procura.',
	'tbl.companiesSoFar': 'até agora',
	'tbl.companiesHint': 'Clica no nome para ver o que recebeu, de quem, e quando.',
	'tbl.company': 'Empresa',
	'tbl.sector': 'Setor',
	'tbl.type': 'Tipo',
	'tbl.noNif': 'sem NIF',
	'tbl.noNifTitle': 'Sem NIF no registo. Abre os contratos desta empresa neste município.',
	'tbl.newCompany': 'empresa nova',
	'tbl.searchObject': 'Procurar objeto ou fornecedor',
	'tbl.searchObjectPlaceholder': 'refeições, asfalto, Gertal…',
	'tbl.year': 'Ano',
	'tbl.procedure': 'Procedimento',
	'tbl.noContracts': 'Nenhum contrato corresponde a estes filtros.',
	'tbl.contractsSuffix': ', dos maiores para os menores.',
	'tbl.object': 'Objeto',
	'tbl.supplier': 'Fornecedor',
	'tbl.bidders': 'Concorrentes',
	'tbl.value': 'Valor',
	'tbl.date': 'Data',
	'tbl.loadedSoFar': 'Já carregaste {n}. Continua a pedir para veres o resto.',
	'tbl.count': 'N.º',
	'tbl.countLabel': 'N.º de contratos',
	'tbl.share': 'Quota',
	'tbl.loadingContracts': 'A carregar contratos.',
	'tbl.showingOf': 'A mostrar {shown} de {total}.',
	'tbl.showMoreN': 'Mostrar mais {n}',
	'tbl.loadFailed': 'Não foi possível carregar os contratos.',
	'tbl.nothingHere': 'Sem contratos para mostrar aqui.',

	/* ---- flags on a contract row ------------------------------------------ */
	'flag.limite': 'no limite',
	'flag.limite.why':
		'O valor fica mesmo por baixo de um limite legal. Um euro acima e obrigaria a um procedimento mais exigente.',
	'flag.limite.here': 'Aqui o limite é {limit}.',
	'flag.pessoa': 'pessoa',
	'flag.pessoa.why':
		'O nome não indica forma jurídica, e por lei uma empresa portuguesa tem de a indicar. É uma pessoa a receber diretamente, o que é legal e comum, mas raro neste valor.',
	'flag.sozinho': 'sem ninguém contra',
	'flag.sozinho.why':
		'Houve concurso e apareceu uma única empresa. Não se aplica ao ajuste direto, onde a lei não pede concorrência.',

	/* ---- charts ------------------------------------------------------------ */
	'chart.default': 'gráfico',
	'chart.noContracts': 'sem contratos',
	'chart.noData': 'sem dados',
	'chart.noContractsHere': 'sem contratos nestes dados',
	'chart.upTo': 'até {value}',
	'chart.moreThan': 'mais de {value}',
	'chart.nContracts': '{n} contrato(s)',
	'chart.byDirectAward': '{pct} por ajuste direto',
	'chart.buyer': 'entidade adjudicante',
	'chart.newHere': 'Empresa nova aqui',
	'chart.clickForContracts': 'clica para ver os contratos',
	'chart.ofAllMoney': '{pct} de todo o dinheiro',
	'chart.loadedContracts': '{n} contratos carregados',
	'chart.clickToOpen': 'clica para abrir',
	'chart.notLoaded': 'ainda sem contratos carregados',
	'chart.other': 'Outros',

	/* ---- back link --------------------------------------------------------- */
	'back.aria': 'Voltar',
	'back.home': 'Voltar ao início',

	/* ---- egg ---------------------------------------------------------------- */
	'egg.title': 'Oh malandro!! Está lá quieto com isso!',
	'egg.eyebrow': 'Apanhado',
	'egg.lede':
		'Seis vezes no mesmo sítio. Isto aqui é um site sobre contratos públicos, não é um berlinde.',
	'egg.back': 'Voltar ao trabalho',
	'egg.head': 'Oh malandro!',

	/* ---- pages that stay Portuguese ------------------------------------------ */
	'ptOnly.note': '',
	'faqs.title': 'Como isto funciona',
	'faqs.description': 'O que cada número conta, de onde vem, e o que a lei permite.',
	'terms.title': 'Termos e condições',
	'terms.description':
		'O que este site é, de onde vêm os dados, o que pode fazer com eles e o que fazer se encontrar um erro.'
};

const EN: Record<string, string> = {
	/* ---- shared ------------------------------------------------------- */
	'common.site': 'Onde Vai Parar',
	'common.siteTitle': 'Onde Vai Parar: Portuguese municipal public contracts',
	'common.description':
		'Who gets the money from Portuguese municipal councils, and under which procedure.',
	'common.na': 'N/A',
	'common.loading': 'Loading…',
	'common.loadMore': 'Load more',
	'common.retry': 'Try again',
	'common.endOfList': 'End of the list.',
	'common.clear': 'Clear',
	'common.all': 'All',
	'common.allF': 'All',
	'common.close': 'Close',
	'common.sortBy': 'Sort by',
	'common.sortDesc': 'Sorting from largest to smallest',
	'common.sortAsc': 'Sorting from smallest to largest',
	'common.contracts': 'contracts',
	'common.contract': 'contract',
	'common.companies': 'companies',
	'common.company': 'company',
	'common.years': 'years',
	'common.year': 'year',
	'common.noDescription': 'No description',
	'common.whereAmI': 'Where you are',
	'common.portugal': 'Portugal',
	'common.notMeasurable': 'not measurable',
	'common.verbatim':
		'Contract descriptions, company names, council names and purchase categories are quoted from the official Portuguese register exactly as published, so they stay in Portuguese. Nothing is broken: only our own writing is translated.',

	/* ---- navigation ---------------------------------------------------- */
	'nav.menu': 'Menu',
	'nav.loading': 'Loading the page',
	'nav.closeMenu': 'Close the menu',
	'nav.main': 'Main',
	'nav.municipality': 'Council',
	'nav.panorama': 'Overview',
	'nav.faqs': 'FAQs',
	'nav.language': 'Language',
	'nav.toEnglish': 'English',
	'nav.toPortuguese': 'Português',

	/* ---- footer -------------------------------------------------------- */
	'footer.blurb': 'Portuguese public contracts, read with a sharp tongue and the right numbers.',
	'footer.sourceHead': 'Source',
	'footer.rawData': 'raw data',
	'footer.officialPortal': 'official portal',
	'footer.api': 'API',
	'footer.apiNote': 'the same figures in JSON',
	'footer.terms': 'Terms and conditions',
	'footer.termsNote': 'what this is and what it is not',
	'footer.code': 'Source code',
	'footer.codeNote': 'AGPL-3.0, everything that runs here',
	'footer.latest': 'Latest contract',
	'footer.disclaimerHead': 'Disclaimer',
	'footer.noCrimeStrong': 'Nothing here accuses anyone of a crime.',
	'footer.noCrimeBody':
		'A direct award is a lawful procedure. A high number means “this is worth a look”.',
	'footer.termsFull': 'The terms, in full',

	/* ---- the disclaimer, keyed by the API ------------------------------ */
	'disclaimer.source':
		'The figures come from the BASE portal, the official register of Portuguese public contracts, published by IMPIC. We correct nothing: whatever is wrong or missing in the original register appears here exactly as it is.',
	'disclaimer.publication_lag':
		'A contract only enters the register once it has been published, and not all of them are published at the same pace, so the most recent months are usually incomplete.',
	'disclaimer.bidders':
		'Not every contract says who bid. Indicators that depend on that are computed only over the contracts that disclosed it, and each one says how many it was computed over.',
	'disclaimer.map_overlap':
		'A contract can cover several municipalities and counts in each of them, so the map can add up to more than the total spend.',
	'disclaimer.legal':
		'The indicators measure what is observable in the data, not wrongdoing. A direct award is a lawful procedure and often the sensible one.',

	/* ---- the satirical verdict, keyed by the API ----------------------- */
	'verdict.clean': 'This looks legitimate',
	'verdict.clean.quip': 'Real tenders, and more suppliers than would fit round a dinner table.',
	'verdict.fishy': 'Smells of favours',
	'verdict.fishy.quip': 'Nothing unlawful in sight, but the same names turn up far too often.',
	'verdict.blatant': 'Favours this obvious',
	'verdict.blatant.quip': 'Almost nobody bidding, and the money always falls on the same side.',

	/* ---- severity ------------------------------------------------------ */
	'sev.ok': 'low',
	'sev.warn': 'moderate',
	'sev.serious': 'high',
	'sev.critical': 'very high',

	/* ---- money and dates ----------------------------------------------- */
	'unit.bn': 'bn €',
	'unit.m': 'M €',
	'unit.k': 'k €',
	'unit.eur': '€',
	'fmt.nearLimit': '{gap} below the {limit} ceiling',
	'fmt.nova.unknown': "this company's first public contract was in {date}.",
	'fmt.nova.first': 'it had never held a public contract, and this one, in {date}, was the first.',
	'fmt.nova.weeks':
		"this company's first public contract was in {date}, a few weeks earlier.",
	'fmt.nova.days': "this company's first public contract was in {date}, {days} days earlier.",

	/* ---- the indicators ------------------------------------------------ */
	'signal.ajuste_direto': 'No tender',
	'signal.ajuste_direto.blurb':
		'Money handed over by direct award: the council picks the company and signs, without putting the work out to tender. It is lawful below certain amounts.',
	'signal.concentracao': 'Concentration',
	'signal.concentracao.blurb':
		'Measures whether the money is spread across many companies or locked into a few. Near 0 means many sharing it, near 100 means almost all of it in one.',
	'signal.single_bidder': 'Only one bidder',
	'signal.single_bidder.blurb':
		'Money from tenders where only one company turned up. There was a tender, but nobody to compete against.',
	'signal.threshold_surf': 'Hugging the ceiling',
	'signal.threshold_surf.blurb':
		'Contracts priced just under a statutory ceiling. One euro more and they would have required a more demanding procedure.',
	'signal.newcomer_value': 'Money to companies with no track record',
	'signal.newcomer_value.blurb':
		'Money to companies that held no public contract at all before this period and that won here without competition, by direct award or as the only bidder. Being new is not irregular; appearing from nowhere and winning with nobody competing is what deserves a look.',
	'signal.ad_contracts': 'Contracts without a tender',
	'signal.ad_contracts.blurb':
		'The same practice counted in contracts rather than in euros. It tends to be much higher, because direct awards are many and small.',
	'signal.undisclosed_bidders': 'Bidders not disclosed',
	'signal.undisclosed_bidders.blurb':
		'Contracts that do not say who bid. Without that list there is no way to know whether there was real competition.',
	'signal.top_supplier': 'The largest supplier',
	'signal.top_supplier.blurb':
		'How much of the total money went to a single company, the one that received the most.',
	'signal.top3_suppliers': 'In the top 3',
	'signal.top3_suppliers.blurb':
		'How much of the total money went to the three companies that received the most.',
	'signal.repeat_winners': 'Regular winners',
	'signal.repeat_winners.blurb':
		'Money to companies that win over and over. It may be plain competence, but it depends on how many years are being counted.',

	'unmeasurable.newcomer_value':
		'Earlier years are missing, so there is no way to tell which companies held no public contracts before.',
	'unmeasurable.single_bidder': 'No contract in this period says who bid.',
	'unmeasurable.concentracao': 'With no money on record there is nothing to share out.',

	/* ---- signal card --------------------------------------------------- */
	'card.outsideIndex': 'outside the index',
	'card.of': 'of',
	'card.disclosed': 'disclosed',
	'card.level': '{label}: {value}%, level {level}',
	'card.indexLevel': '{label}: {value} out of 100, level {level}',

	/* ---- error pages --------------------------------------------------- */
	'err.404.title': 'We could not find that',
	'err.404.body':
		'The page you are looking for does not exist, has moved, or never existed at all. It happens.',
	'err.404.foot': 'If you got here from a link of ours, the link is the thing that is wrong.',
	'err.429.title': 'Steady on',
	'err.429.body':
		'Too many requests arrived in a short space of time. Wait a few seconds and try again.',
	'err.429.foot': 'The limit exists so the site stays up for everybody.',
	'err.500.title': 'That one was our fault',
	'err.500.body':
		'Something on our side tripped up halfway through the request. The data is fine, the path to it is not.',
	'err.500.foot': 'Try again shortly. If it persists, it means we have not noticed yet.',
	'err.home': 'Back to the start',

	/* ---- landing -------------------------------------------------------- */
	'landing.eyebrow': 'Onde Vai Parar · municipal public contracts',
	'landing.title': 'Who is milking our taxes?',
	'landing.sub':
		'Who was paid, under which procedure, and how often the same name comes back. We read the contracts councils are required to publish and show what is in them, with no adjectives.',
	'landing.awarded': 'awarded',
	'landing.contracts': 'contracts',
	'landing.municipalities': 'councils',
	'landing.to': 'to {year}',
	'landing.crossTo': 'Or see {link}, by district and by the party running the council.',
	'landing.crossToLink': 'how much money was handed over without a tender',
	'landing.pickTitle': 'Pick your council',
	'landing.pickSub': 'three ways, the same answer',
	'landing.howToPick': 'How to pick a council',
	'landing.tab.name': 'By name',
	'landing.tab.district': 'By district',
	'landing.tab.map': 'On the map',
	'landing.search': 'Search for a council',
	'landing.searchPlaceholder': 'Search for a council…',
	'landing.noMatch': 'No loaded council matches that name.',
	'landing.noDistricts': 'The list of districts could not be loaded.',
	'landing.district': 'District',
	'landing.choose': 'Choose…',
	'landing.pickDistrict': 'Pick a district to see the councils loaded in it.',
	'landing.hintDrilled': 'In red, the councils already loaded. Tap one to open it.',
	'landing.hintCountry':
		'In red, the districts with councils loaded. Tap one to open it municipality by municipality.',
	'landing.noMap': 'The map could not be loaded.',
	'landing.mapAriaDistrict': 'Municipalities of {district} district, to pick a council',
	'landing.mapAriaCountry': 'Districts of Portugal, to choose where to start',

	/* ---- município ------------------------------------------------------ */
	'muni.noData': 'No data yet',
	'muni.noDataBody':
		'No contracts are loaded for this council. Come back later: the data is refreshed from the public contract register.',
	'muni.fallbackName': 'Council',
	'muni.metaTitle': 'Public contracts in {name} | Onde Vai Parar',
	'muni.metaDescription':
		'Public contracts in {name}: who gets the money, how much skipped a tender and which firms win most.',
	'muni.tab.overview': 'Overview',
	'muni.tab.map': 'Map',
	'muni.tab.network': 'Network',
	'muni.tab.companies': 'Companies',
	'muni.tab.stats': 'Statistics',
	'muni.tab.contracts': 'Contracts',
	'muni.sections': 'Sections',
	'muni.eyebrow': 'Public contracts',
	'muni.mandates': '{n} terms',
	'muni.period': 'Period',
	'muni.everything': 'All',
	'muni.olderYears': 'Earlier years',
	'muni.fewerYears': 'Fewer years',
	'muni.moreYears': '{n} more years',
	'muni.nYears': '{n} years',
	'muni.range': 'Range…',
	'muni.lastNYears': 'Last {n} years',
	'muni.from': 'From',
	'muni.until': 'To',
	'muni.allYears': 'all',
	'muni.maxSpan': '{n} years at most',
	'muni.spanTrimmed': 'The period was shortened to {n} years, the maximum for this view.',
	'muni.periodFromTo': '{from} to {to}',
	'muni.periodSince': 'since {from}',
	'muni.periodUntil': 'up to {to}',
	'muni.periodUnknown': 'no known period',
	'muni.spent': 'spent',
	'muni.contracts': 'contracts',
	'muni.suppliers': 'suppliers',
	'muni.riskIndex': 'Risk index',
	'muni.riskCaption':
		'The average of the {n} indicators measurable in this period, all of them as a share of the money.',
	'muni.satireIndex': 'Favour-meter',
	'muni.satireCaption':
		'The same indicators, with the most telling ones weighing more: tenders with a single bidder, money concentrated in few companies, direct awards, contracts hugging a ceiling, and money to brand new companies.',
	'muni.units': 'That buys {bifanas} pork sandwiches, or {salarios} annual minimum wages.',
	'muni.chipRisk': 'risk',
	'muni.chipSatire': 'favour-meter',
	'muni.indicators': 'Indicators',
	'muni.whoGotMost': 'Who was paid most',
	'muni.groupBy': 'Group by',
	'muni.group.supplier': 'Supplier',
	'muni.group.sector': 'Sector',
	'muni.group.procedure': 'Procedure',
	'muni.barsAria': 'Largest destinations of the money, grouped by {grouping}',
	'muni.barsNoteSupplier': 'Click a bar to open that company page.',
	'muni.barsNoteOther': 'Click a bar to see only those contracts.',
	'muni.legendNoAd': 'no direct awards',
	'muni.legendSome': 'some',
	'muni.legendMost': 'most',
	'muni.legendAlmostAll': 'almost all',
	'muni.legendCategory':
		'Each bar is a whole category, so the colour identifies the category and not how much of it was a direct award.',
	'muni.noGrouping': 'Not enough data for this grouping.',
	'muni.mapTitle': 'Where the work is carried out',
	'muni.mapNote':
		'This is where the contract is performed, not the supplier address, which no dataset publishes. A contract covering several municipalities counts in each one, so the map total ({sum}) {tail}.',
	'muni.mapExceeds': 'exceeds the total spend, {total}',
	'muni.mapMayExceed': 'may exceed the total spend',
	'muni.mapError': 'The map could not be loaded. Try reloading the page.',
	'muni.mapAria': 'Map of Portugal by municipality of performance',
	'muni.concelho': 'Municipality',
	'muni.areaBadge': '{money} across {n} contracts performed here.',
	'muni.areaError': 'The contracts for this municipality could not be loaded. Try again.',
	'muni.areaEmpty': 'No contracts on record for this municipality.',
	'muni.areaHint': 'Click a municipality to see the contracts performed there.',
	'muni.islandsNote':
		'The Azores and Madeira are moved next to the mainland, as Portuguese maps usually do, or the mainland would end up the size of a fingernail.',
	'muni.webTitle': 'The web',
	'muni.graphSize': 'Suppliers in the graph',
	'muni.graphHintNarrow': 'Tap a company to see its contracts.',
	'muni.graphHintWide': 'Hover a company to isolate its links, click to see the contracts.',
	'muni.graphAria': 'Network of payments to suppliers, grouped by sector',
	'muni.hidingSectors': 'Hiding {n} sectors.',
	'muni.hidingSector': 'Hiding 1 sector.',
	'muni.showAll': 'Show everything',
	'muni.symDiamond': 'Diamond: company with no earlier track record',
	'muni.symCircle': 'Circle: every other supplier',
	'muni.symSize': 'The bigger it is, the more money it received',
	'muni.graphNote':
		'Colour is the sector. Diamonds mark companies that held no public contracts before this period and that won here without competition, by direct award or as the only bidder. Being new is not irregular, it is simply what deserves a second look.',
	'muni.supplier': 'Supplier',
	'muni.newHere': 'New company here: {sentence}',
	'muni.seeCompany': 'See the company',
	'muni.pickedError': 'The contracts for this supplier could not be loaded. Try again.',
	'muni.pickedEmpty': 'No contracts for this supplier.',
	'muni.col.object': 'Object',
	'muni.col.date': 'Date',
	'muni.col.procedure': 'Procedure',
	'muni.col.bidders': 'Bidders',
	'muni.col.value': 'Value',
	'muni.col.supplier': 'Supplier',
	'muni.col.company': 'Company',
	'muni.col.sector': 'Sector',
	'muni.col.firstPublic': 'First public contract',
	'muni.newcomersTitle': 'Companies with no earlier track record',
	'muni.newcomersUnknown':
		'No company incorporation record exists in this data, so the only hint of novelty is a debut in public contracts. The available period ({period}) is too short to tell a brand new company from one that already existed: earlier years are missing for comparison.',
	'muni.newcomersNote':
		'Companies whose first public contract anywhere in the register is recent and that, shortly afterwards, won here. Being new is neither unlawful nor suspicious in itself, but a newcomer that immediately lands a large contract is the kind of thing worth looking at twice.',
	'muni.newcomersNone':
		'No supplier made its public-contract debut in the year before winning here. The diamonds in the graph would mark such cases.',
	'muni.rivalsTitle': 'Who bids against whom',
	'muni.rivalsNote':
		'Pairs of companies that repeatedly show up in the same tender. Only contracts that disclosed their bidders can produce a row.',
	'muni.rivalsAlso': 'And also',
	'muni.rivalsTenders': 'Tenders',
	'muni.rivalsNone': 'No repeated pair in this data.',
	'muni.statsTitle': 'Reference figures',
	'muni.statsNote':
		'Half the contracts cost little and a few cost a great deal. That is why the middle value and the highest value sit side by side: the difference between them is the story.',
	'muni.kpi.typical': 'Cost of the typical contract',
	'muni.kpi.typicalNote': 'half of the {n} contracts cost less than this, half cost more',
	'muni.kpi.mean': 'Average cost per contract',
	'muni.kpi.meanSkewed':
		'well above the typical contract, because a handful of enormous ones pulls the total up',
	'muni.kpi.meanFlat': 'close to the typical contract, with no outliers',
	'muni.kpi.priciest': 'The most expensive contracts',
	'muni.kpi.priciestNote': 'only one contract in ten cost more than this',
	'muni.kpi.half': 'Half the money',
	'muni.kpi.halfOne': 'a single company received half of all the money',
	'muni.kpi.halfMany': 'companies were enough to take half of all the money',
	'muni.kpi.largest': 'Largest contract',
	'muni.kpi.largestNote': 'one contract alone took {pct} of all the money',
	'muni.kpi.kinds': 'Kinds of purchase',
	'muni.kpi.kindsNote': 'different things bought, from paper to public works',
	'muni.zeroOne': 'One contract is on record with a value of zero.',
	'muni.zeroMany': '{n} contracts are on record with a value of zero.',
	'muni.noOverruns':
		'The amount actually paid at the end is almost never published, so there are no overruns here: only the value the contract was signed for.',
	'muni.distributions': 'Distributions',
	'muni.byProcedure': 'By procedure',
	'muni.bySector': 'By sector',
	'muni.byYear': 'By year',
	'muni.unit.procedure': 'Procedure',
	'muni.unit.sector': 'Sector',
	'muni.unit.year': 'Year',
	'muni.companiesTitle': 'Who got the money',
	'muni.companiesNote':
		'Every company that won at least one contract in this period, sortable by any column. "No tender" is the share of this company\'s contracts that came by direct award.',
	'muni.contractsTitle': 'Contracts',

	/* ---- mandate timeline ----------------------------------------------- */
	'mandate.title': 'Who was in charge, and how much was contracted',
	'mandate.note':
		'Local election results, term by term. A term begins on election day, so a contract signed in October counts for whoever came in, not for whoever left.',
	'mandate.pickNote': 'Click a term to read the rest of the page for those years only.',
	'mandate.today': 'today',
	'mandate.to': 'to',
	'mandate.readOnly': 'Read the figures for {from} to {to} only',
	'mandate.flipped': 'changed hands',
	'mandate.relabelled': 'same person, different list',
	'mandate.coalition': 'coalition',
	'mandate.citizens': 'citizens group',
	'mandate.independent': 'Independent',
	'mandate.barAria': '{money} contracted, {n} contracts',
	'mandate.noTender': '{pct} without a tender',
	'mandate.reformFlag': 'the law changed midway',
	'mandate.reformNote':
		'The public contracts law changed in August 2017, halfway through one of these terms, and tightened the direct award ceilings. The drop that follows shows up in councils of every party, including those that did not change hands.',
	'mandate.provisional':
		'Provisional results published by the Interior Ministry. The legally binding record is the Official Map of the National Elections Commission. Winning an election is also not the same as serving a full term: resignations and by-elections do not appear here.',

	/* ---- panorama -------------------------------------------------------- */
	'pan.eyebrow': 'Onde Vai Parar · comparisons',
	'pan.title': 'Who is in charge, and who buys without a tender',
	'pan.lede':
		'The share of the money handed over by direct award, without putting the work out to tender. It is split into two periods because the law changed midway: comparing a 2014 council with a 2024 one compares different rules, not different practices.',
	'pan.howToCompare': 'How to compare',
	'pan.view.map': 'Political map',
	'pan.view.party': 'By party',
	'pan.whoWon': 'Who won each council',
	'pan.drilledNote':
		'The {n} councils in the district, each in the colour of the list that won it. Click one with contracts loaded to open its page.',
	'pan.countryNote':
		"Portugal's 308 councils, grouped by district and painted in the colour of the party that won the most councils in each. Tap a district to open it municipality by municipality.",
	'pan.election': 'Election',
	'pan.yearFailed': 'That election could not be loaded. Try again.',
	'pan.mapError': 'The map could not be loaded.',
	'pan.mapAriaDistrict':
		'Map of {district} district, each municipality in the colour of the list that won the council',
	'pan.mapAriaCountry':
		'Map of Portugal by district, each in the colour of the party that won the most councils',
	'pan.seeCountry': 'See the country',
	'pan.inCoalition': '{n} in coalition',
	'pan.showMore': 'Show {n} more',
	'pan.showLess': 'Show fewer',
	'pan.clearFilter': 'Clear filter',
	'pan.hoverNarrow': 'Tap',
	'pan.hoverWide': 'Hover',
	'pan.hoverNote':
		'{verb} to see the elected mayor, the length of the term and what the council contracted in that period. Spending only appears for councils already loaded here, and a coalition takes the colour of whoever leads it.',
	'pan.withData': 'With data in this district:',
	'pan.noElection': 'No results loaded for this election.',
	'pan.era.before': 'Up to August 2017',
	'pan.era.beforeNote': 'under the old law',
	'pan.era.after': 'From August 2017 onwards',
	'pan.era.afterNote': 'under the current law',
	'pan.noEraData': 'No data loaded for this period.',
	'pan.mandatesIn': '{mandates} in {municipalities}',
	'pan.mandateOne': '{n} term',
	'pan.mandateMany': '{n} terms',
	'pan.municipalityOne': '{n} council',
	'pan.municipalityMany': '{n} councils',
	'pan.spread': 'between {low} and {high} depending on the term',
	'pan.singleCase': 'a single case',
	'pan.singleCaseTail': ', with nothing to compare it against',
	'pan.howToRead': 'How to read this, and how not to',
	'pan.read1':
		'These figures say how each council bought, not who is honest. How a council buys depends heavily on its size, on the services it runs in house and on the companies that exist nearby. A small council with no procurement team leans on direct awards more than a capital with its own legal department, and that is not a party.',
	'pan.read2':
		'The darker bar is the share of all the money. The thin bar behind it is the gap between the lowest and the highest term in the same group: when it is wide, the average means almost nothing. Groups with a single term have no spread at all and are marked.',
	'pan.read3':
		'Only the councils already loaded are here, and they are few and almost all around Lisbon. This is not a sample of the country and must not be read as one.',
	'pan.tip.list': 'List',
	'pan.tip.president': 'Mayor',
	'pan.tip.term': 'Term',
	'pan.tip.contracts': 'Contracts',
	'pan.tip.notLoaded': 'not loaded',
	'pan.tip.spentInTerm': 'Spent during the term',
	'pan.tip.noTender': 'Without a tender',
	'pan.tip.leadingParty': 'Party with the most councils',
	'pan.tip.ofTotal': '{label} ({held} of {total})',
	'pan.tip.withData': 'With data',
	'pan.tip.camarasWithData': '{loaded} of {total} councils',
	'pan.tip.camaraWithData': '{loaded} of {total} council',
	'pan.tip.noneLoaded': 'no council loaded',
	'pan.months': '{n} months',
	'pan.month': '{n} month',

	/* ---- empresa --------------------------------------------------------- */
	'firm.eyebrow': 'Company · tax number',
	'firm.noName': 'Company with no name on record',
	'firm.metaDescription': '{name} received {money} across {n} public contracts.',
	'firm.received': 'received',
	'firm.contracts': 'contracts',
	'firm.camara': 'council',
	'firm.camaras': 'councils',
	'firm.noTender': 'without a tender',
	'firm.adNotMeasurable': 'not measurable',
	'firm.adAlmostAll': 'almost all',
	'firm.adGoodPart': 'a good part',
	'firm.adLittle': 'little',
	'firm.inDistrict': '{n} in this district',
	'firm.tapForContracts': 'tap to see the contracts here',
	'firm.mainSector': 'Main sector',
	'firm.firstContract': 'First contract',
	'firm.lastContract': 'Latest contract',
	'firm.scopeNote':
		'This counts only the councils loaded here. The company may hold contracts with central government or with other councils that are not in this database.',
	'firm.yearByYear': 'Year by year',
	'firm.yearByYearNote':
		'The same total can be a decade of steady work or a single year in which it appeared and took everything. The colour of the column is the share of that year that came by direct award.',
	'firm.yearsAria': 'Value awarded to this company in each year',
	'firm.registry': 'In the commercial register',
	'firm.soldTo': 'Who it sold to',
	'firm.howToView': 'How to view',
	'firm.viewMap': 'Map',
	'firm.viewList': 'List',
	'firm.mapAriaDistrict':
		'Municipalities of {district} district, shaded by what this company received from each council',
	'firm.mapAriaCountry': 'Districts of Portugal, shaded by what this company received from each',
	'firm.mapHintDrilled': "Tap a municipality to see this company's contracts with that council.",
	'firm.mapHintCountry': 'Tap a district to open it municipality by municipality.',
	'firm.darker': 'The darker it is, the more money.',
	'firm.unplacedOne':
		'{n} council could not be placed on the map because its name does not resolve to a single municipality. It is in the list.',
	'firm.unplacedMany':
		'{n} councils could not be placed on the map because their names do not resolve to a single municipality. They are in the list.',
	'firm.noneHere': 'This company received nothing in this district.',
	'firm.shareOfIntake': '{n} contracts · {pct} of what it received',
	'firm.oneBuyer':
		'Everything this company received, in the loaded data, came from a single council. That is not irregular: plenty of companies work with one public client. It is simply what the numbers say.',
	'firm.contractsTitle': 'Contracts',
	'firm.clickContract': 'Click a contract to see all of it.',
	'firm.searchObject': 'Search the object',
	'firm.searchPlaceholder': 'asfalto, refeições…',
	'firm.buyer': 'Council',
	'firm.noContracts':
		'This company has no contracts in the loaded councils. If you got here from one of them, the mistake is ours.',
	'firm.moreFailed': 'More contracts could not be loaded.',
	'firm.backTo': 'Back to {name}',
	'firm.pickOther': 'Pick another council',

	/* ---- company registry profile ---------------------------------------- */
	'reg.missing':
		'This company has no commercial register entry published in the free sources, so there are no activities or registered office here.',
	'reg.registeredName': 'Name on the register',
	'reg.form': 'Legal form',
	'reg.type': 'Type',
	'reg.founded': 'Incorporated',
	'reg.foundedIn': 'in',
	'reg.foundedOrEarlier': 'or earlier',
	'reg.address': 'Registered office',
	'reg.activities': 'Registered activities (Portuguese CAE codes)',
	'reg.principal': 'main',
	'reg.sourceLine':
		'Commercial register via {source}. The legal form is read off the company name, which by law has to carry it.',
	'reg.floorNote':
		'The register of acts only begins in {year}, so for older companies that is the earliest date that exists, not the real one.',
	'reg.noCapital':
		'Share capital and headcount are not published free of charge by any source, so they are not here.',

	/* ---- contract detail -------------------------------------------------- */
	'ct.title': 'Contract {id}',
	'ct.metaFallback': 'Public contract',
	'ct.noDescription': 'Contract with no description on record',
	'ct.backTo': 'Back to {name}',
	'ct.thisMunicipality': 'this council',
	'ct.procedureNA': 'Procedure N/A',
	'ct.centralized': 'centralised purchase',
	'ct.green': 'environmental criteria',
	'ct.value': 'contract value',
	'ct.basePrice': 'base price',
	'ct.bidders': 'bidders',
	'ct.execDays': 'days allowed',
	'ct.adCallout':
		'This contract was a direct award: the council picked the company without opening a tender. It is lawful below the ceilings the law sets, and it is what happens with most small purchases.',
	'ct.adCalloutStrong': 'direct award',
	'ct.howItWorks': 'How it works',
	'ct.whoGotIt': 'Who got it',
	'ct.noNif': 'no tax number on record',
	'ct.awardee': 'awardee',
	'ct.noAwardee': 'The register does not identify the awardee.',
	'ct.whoBid': 'Who bid',
	'ct.whoBidNote': 'The companies that entered this procedure. The winner is marked.',
	'ct.result': 'Result',
	'ct.won': 'won',
	'ct.lost': 'did not win',
	'ct.noBidders':
		'The register does not say who else bid. That is missing from most contracts, so on its own it means nothing.',
	'ct.whatRecordSays': 'What the register says',
	'ct.signed': 'Signed',
	'ct.published': 'Published',
	'ct.type': 'Type',
	'ct.sector': 'Sector',
	'ct.cpv': 'Classification (CPV)',
	'ct.criterion': 'Criterion',
	'ct.framework': 'Framework agreement',
	'ct.executedWhere': 'Where it is performed',
	'ct.centralizedLabel': 'Centralised purchase',
	'ct.greenLabel': 'Environmental criteria',
	'ct.yes': 'yes',
	'ct.no': 'no',
	'ct.below': 'below',
	'ct.above': 'above',
	'ct.closedVsBase':
		'It closed {direction} the base price by {pct}. The amount actually paid at the end is not published in this register, so there are no overruns here: this compares what the council expected with what it signed.',
	'ct.reason': 'The reason given',
	'ct.reasonNote':
		'The legal ground the council cited, exactly as it stands in the register. It is usually the article of the Public Contracts Code that allows this procedure. Citing it is what the law requires; it says nothing about whether the choice was a good one.',
	'ct.sourceTitle': 'The source',
	'ct.basePortal': 'Record on the BASE portal',
	'ct.basePortalNote': 'the official record of this contract',
	'ct.impicDataset': 'IMPIC dataset',
	'ct.impicDatasetNote': 'the file this page was read from',
	'ct.announcement': 'Published notice',
	'ct.pieces': 'Procedure documents',
	'ct.sourceNote':
		'Everything on this page comes from the register IMPIC publishes. We correct nothing: whatever is missing or wrong at the source appears here exactly as it is. The BASE portal has been intermittently unavailable and, when it is up, its record answers "the data could not be obtained from the server". That is the portal, not this contract: the figures here come from the IMPIC file, which is the same register.',

	/* ---- tables ----------------------------------------------------------- */
	'tbl.searchCompany': 'Search company or tax number',
	'tbl.searchCompanyPlaceholder': 'Gertal, 500123456…',
	'tbl.companyType': 'Company type',
	'tbl.totalReceived': 'Total received',
	'tbl.contracts': 'Contracts',
	'tbl.noTender': 'No tender',
	'tbl.lastContract': 'Latest contract',
	'tbl.searchFailed': 'The search failed. Try again.',
	'tbl.noCompanies': 'No company matches this search.',
	'tbl.companiesSoFar': 'so far',
	'tbl.companiesHint': 'Click a name to see what it received, from whom, and when.',
	'tbl.company': 'Company',
	'tbl.sector': 'Sector',
	'tbl.type': 'Type',
	'tbl.noNif': 'no tax number',
	'tbl.noNifTitle':
		'No tax number on record. Opens this company contracts in this council.',
	'tbl.newCompany': 'new company',
	'tbl.searchObject': 'Search object or supplier',
	'tbl.searchObjectPlaceholder': 'refeições, asfalto, Gertal…',
	'tbl.year': 'Year',
	'tbl.procedure': 'Procedure',
	'tbl.noContracts': 'No contract matches these filters.',
	'tbl.contractsSuffix': ', largest first.',
	'tbl.object': 'Object',
	'tbl.supplier': 'Supplier',
	'tbl.bidders': 'Bidders',
	'tbl.value': 'Value',
	'tbl.date': 'Date',
	'tbl.loadedSoFar': 'You have loaded {n}. Keep asking to see the rest.',
	'tbl.count': 'No.',
	'tbl.countLabel': 'Number of contracts',
	'tbl.share': 'Share',
	'tbl.loadingContracts': 'Loading contracts.',
	'tbl.showingOf': 'Showing {shown} of {total}.',
	'tbl.showMoreN': 'Show {n} more',
	'tbl.loadFailed': 'The contracts could not be loaded.',
	'tbl.nothingHere': 'No contracts to show here.',

	/* ---- flags on a contract row ------------------------------------------ */
	'flag.limite': 'at the ceiling',
	'flag.limite.why':
		'The value sits just under a statutory ceiling. One euro more and it would require a more demanding procedure.',
	'flag.limite.here': 'Here the ceiling is {limit}.',
	'flag.pessoa': 'person',
	'flag.pessoa.why':
		'The name carries no legal form, and by law a Portuguese company has to carry one. This is a person being paid directly, which is lawful and common, but rare at this amount.',
	'flag.sozinho': 'nobody against them',
	'flag.sozinho.why':
		'There was a tender and a single company turned up. It does not apply to direct awards, where the law asks for no competition.',

	/* ---- charts ------------------------------------------------------------ */
	'chart.default': 'chart',
	'chart.noContracts': 'no contracts',
	'chart.noData': 'no data',
	'chart.noContractsHere': 'no contracts in this data',
	'chart.upTo': 'up to {value}',
	'chart.moreThan': 'more than {value}',
	'chart.nContracts': '{n} contract(s)',
	'chart.byDirectAward': '{pct} by direct award',
	'chart.buyer': 'contracting authority',
	'chart.newHere': 'New company here',
	'chart.clickForContracts': 'click to see the contracts',
	'chart.ofAllMoney': '{pct} of all the money',
	'chart.loadedContracts': '{n} contracts loaded',
	'chart.clickToOpen': 'click to open',
	'chart.notLoaded': 'no contracts loaded yet',
	'chart.other': 'Other',

	/* ---- back link --------------------------------------------------------- */
	'back.aria': 'Back',
	'back.home': 'Back to the start',

	/* ---- egg ---------------------------------------------------------------- */
	'egg.title': 'Oi! Leave that alone!',
	'egg.eyebrow': 'Caught',
	'egg.lede':
		'Six times in the same spot. This is a site about public contracts, not a marble.',
	'egg.back': 'Back to work',
	'egg.head': 'Oi!',

	/* ---- pages that stay Portuguese ------------------------------------------ */
	'ptOnly.note':
		'This page is only available in Portuguese. It is long-form writing about Portuguese law and about this site, and a rough translation would be worse than none. The rest of the site is in English.',
	'faqs.title': 'How this works',
	'faqs.description': 'What each number counts, where it comes from, and what the law allows.',
	'terms.title': 'Terms and conditions',
	'terms.description':
		'What this site is, where the data comes from, what you can do with it, and what to do if you find a mistake.'
};

const MESSAGES: Record<Lang, Record<string, string>> = { pt: PT, en: EN };

/**
 * One string, in the page's language.
 *
 * `vars` fills `{name}` placeholders. A missing key falls back to Portuguese
 * and then to the key itself, which is ugly on screen and therefore gets fixed.
 */
export function t(key: string, vars?: Record<string, string | number>): string {
	const raw = MESSAGES[lang()][key] ?? PT[key] ?? key;
	if (!vars) return raw;
	return raw.replace(/\{(\w+)\}/g, (whole, name) =>
		name in vars ? String(vars[name]) : whole
	);
}

/**
 * One string in a language of your choosing.
 *
 * For the two pages that stay Portuguese whatever the route says: /faqs and
 * /termos are long-form writing about Portuguese law, and half-translating the
 * glossary inside them would be worse than leaving the page whole.
 */
export const tl = (l: Lang, key: string): string => MESSAGES[l][key] ?? PT[key] ?? key;

/** Like `t`, but an unknown key is empty rather than the key itself. For the
 *  optional strings, such as the reason a signal is unmeasurable here. */
export const maybe = (key: string): string => MESSAGES[lang()][key] ?? PT[key] ?? '';
