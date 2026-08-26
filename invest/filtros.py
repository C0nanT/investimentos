"""Filtros, ranking e ordenacao sobre os registros do Fundamentus."""

from __future__ import annotations

from typing import Iterable

# Semente do preset fii-aula (usada so no primeiro insert no Mongo). O painel
# busca a taxa real do Tesouro IPCA+ em invest.tesouro e ignora este valor
# depois disso — ver tesouro.obter_taxa_ipca().
TAXA_BASE_PADRAO = 8.17
SPREAD_PADRAO = 1.0

# Painel de ações: principais da B3 (nível 1) misturados com segmentos
# populares. Fundamentus.setor ≈ subsetor B3; grupos abaixo expandem.
# Ordem = preenchimento vertical em 3 colunas.
SETORES_PRINCIPAIS = [
    "Todos os setores",
    "Água e Saneamento",
    "Bancos",
    "Bens Industriais",
    "Construção Civil",
    "Consumo Cíclico",
    "Consumo Não Cíclico",
    "Energia Elétrica",
    "Financeiro",
    "Materiais Básicos",
    "Mineração",
    "Petróleo, Gás e Biocombustíveis",
    "Previdência e Seguros",
    "Saúde",
    "Seguradoras",
    "Tecnologia da Informação",
    "Telecomunicações",
    "Utilidade Pública",
]

SEGMENTOS_PRINCIPAIS = {
    "Bancos": "Bancos",
    "Seguradoras": "Seguradoras",
}

# Setor econômico B3 -> setores do Fundamentus que entram no recorte.
GRUPOS_SETORIAIS = {
    "Bens Industriais": [
        "Equipamentos",
        "Máquinas e Equipamentos",
        "Material de Transporte",
        "Construção e Engenharia",
        "Transporte",
        "Serviços Diversos",
    ],
    "Consumo Cíclico": [
        "Construção Civil",
        "Tecidos, Vestuário e Calçados",
        "Utilidades Domésticas",
        "Automóveis e Motocicletas",
        "Hoteis e Restaurantes",
        "Viagens e Lazer",
        "Diversos",
        "Comércio",
    ],
    "Consumo Não Cíclico": [
        "Agropecuária",
        "Alimentos Processados",
        "Bebidas",
        "Produtos de Uso Pessoal e de Limpeza",
        "Comércio e Distribuição",
    ],
    "Financeiro": [
        "Intermediários Financeiros",
        "Serviços Financeiros Diversos",
        "Previdência e Seguros",
        "Exploração de Imóveis",
        "Holdings Diversificadas",
    ],
    "Materiais Básicos": [
        "Mineração",
        "Siderurgia e Metalurgia",
        "Químicos",
        "Madeira e Papel",
        "Embalagens",
        "Materiais Diversos",
    ],
    "Saúde": [
        "Medicamentos e Outros Produtos",
        "Serv.Méd.Hospit. Análises e Diagnósticos",
    ],
    "Tecnologia da Informação": [
        "Computadores e Equipamentos",
        "Programas e Serviços",
    ],
    "Utilidade Pública": [
        "Energia Elétrica",
        "Água e Saneamento",
        "Gás",
    ],
}

# Painel de FIIs: tipos regulatórios (ANBIMA/B3), no mesmo layout de 3 colunas
# do Investidor10. Fundamentus não traz o rótulo pronto — classificar_tipo_fii()
# infere a partir de segmento e indicadores físicos.
TIPOS_PRINCIPAIS_FII = [
    "Todos os Tipos",
    "Fundo Misto",
    "Fundo de Desenvolvimento",
    "Fundo de Fundos",
    "Fundo de Papel",
    "Fundo de Tijolo",
    "Outro",
]

SEGMENTOS_TIJOLO = {
    "Escritórios",
    "Hospital",
    "Hotel",
    "Lajes Corporativas",
    "Logística",
    "Residencial",
    "Shoppings",
    "Varejo",
}


def classificar_tipo_fii(registro: dict) -> str:
    """Infere o tipo do FII a partir do snapshot do Fundamentus."""
    segmento = (registro.get("segmento") or "").strip()
    papel = (registro.get("papel") or "").upper()
    imoveis = registro.get("qtd_imoveis") or 0
    cap_rate = registro.get("cap_rate") or 0
    vacancia = registro.get("vacancia_media") or 0
    pvp = registro.get("pvp") or 0

    if papel.endswith("OF11") or "FOF" in papel:
        return "Fundo de Fundos"
    if segmento == "Títulos e Val. Mob.":
        return "Fundo de Papel"
    if segmento == "Híbrido":
        return "Fundo Misto"
    if segmento in SEGMENTOS_TIJOLO:
        return "Fundo de Tijolo" if imoveis > 0 else "Fundo de Papel"
    if segmento == "Outros":
        return "Outro"
    if segmento == "Multicategoria":
        if imoveis == 0 and cap_rate == 0 and vacancia == 0:
            return "Fundo de Papel"
        if imoveis > 0 and 0 < pvp < 0.55:
            return "Fundo de Desenvolvimento"
        if imoveis > 0 and cap_rate > 0 and vacancia > 0:
            return "Fundo Misto"
        if imoveis > 0:
            return "Fundo de Tijolo"
        return "Fundo de Papel"
    if not segmento:
        return "Outro"
    return "Outro"


def iguais_tipo_fii(nome: str) -> str | None:
    """Traduz o rótulo do painel para o tipo inferido. Vazio = mercado inteiro."""
    nome = (nome or "").strip()
    if not nome or nome == "Todos os Tipos":
        return None
    return nome


def iguais_setorial(nome: str) -> dict[str, str | list[str]] | None:
    """Traduz o rótulo do painel para o filtro Mongo (setor, subsetor ou $in).

    Vazio / "Todos os setores" = mercado inteiro. Nome fora da lista principal
    cai em igualdade exata de setor (filtro completo e clique na tabela).
    """
    nome = (nome or "").strip()
    if not nome or nome == "Todos os setores":
        return None
    if nome in SEGMENTOS_PRINCIPAIS:
        return {"subsetor": SEGMENTOS_PRINCIPAIS[nome]}
    if nome in GRUPOS_SETORIAIS:
        return {"setor": list(GRUPOS_SETORIAIS[nome])}
    return {"setor": nome}


def preset_fii_aula(taxa_base: float = TAXA_BASE_PADRAO, spread: float = SPREAD_PADRAO) -> dict:
    """Triagem quantitativa de FIIs descrita em notes/aula-live-geracao-dividendos.md.

    1. liquidez minima de R$ 2 milhoes;
    2. DY de no maximo 18% e com pelo menos `spread` acima do IPCA+ do Tesouro;
    3. P/VP entre 0,8 e 1,2;
    4. rank de DY (maior primeiro) + rank de P/VP (menor primeiro) = nota final.
    """
    dy_minimo = round(taxa_base + spread, 2)
    return {
        "descricao": (f"Triagem da aula: liquidez > R$2mi, DY {dy_minimo}%–18% "
                      f"(IPCA+{taxa_base}% + spread {spread}%), P/VP 0,8–1,2, rank DY+P/VP"),
        "tipo": "fiis",
        "criterios": [
            ("liquidez", 2_000_000, None),
            ("dy", dy_minimo, 18.0),
            ("pvp", 0.8, 1.2),
        ],
        "ordenar_por": "nota",
        "crescente": True,
        "ranquear": [("dy", False), ("pvp", True)],
        "taxa_base": taxa_base,
        "spread": spread,
    }


def aplicar_taxa(config: dict, taxa_base: float, spread: float) -> dict:
    """Recalcula o DY minimo do preset a partir da taxa + spread, sem mexer no resto."""
    dy_minimo = round(taxa_base + spread, 2)
    criterios = [
        (("dy", dy_minimo, maximo) if chave == "dy" else (chave, minimo, maximo))
        for chave, minimo, maximo in config["criterios"]
    ]
    novo = dict(config)
    novo["criterios"] = criterios
    novo["taxa_base"] = taxa_base
    novo["spread"] = spread
    return novo

# Presets: pontos de partida para nao ter que lembrar de todo criterio.
# Cada valor eh (chave, minimo, maximo); None = sem limite daquele lado.
PRESETS: dict[str, dict] = {
    "fii-aula": preset_fii_aula(),
    "dividendos": {
        "descricao": "Acoes pagadoras: DY alto, lucro real, endividamento sob controle",
        "tipo": "acoes",
        "criterios": [
            ("dy", 6.0, 20.0),          # DY acima de 20% costuma ser evento nao recorrente
            ("pl", 0.1, 15.0),
            ("pvp", 0.1, 3.0),
            ("roe", 10.0, None),
            ("div_liq_patrim", None, 2.0),
            ("liquidez_2meses", 1_000_000, None),
            ("cagr_receita_5a", 0.0, None),
        ],
        "ordenar_por": "dy",
    },
    "valor": {
        "descricao": "Barganhas: multiplos baixos com rentabilidade decente",
        "tipo": "acoes",
        "criterios": [
            ("pvp", 0.1, 1.5),
            ("pl", 0.1, 10.0),
            ("ev_ebit", 0.1, 8.0),
            ("roic", 10.0, None),
            ("liquidez_2meses", 1_000_000, None),
        ],
        "ordenar_por": "ev_ebit",
        "crescente": True,
    },
    "qualidade": {
        "descricao": "Empresas rentaveis e pouco alavancadas, sem exigir preco baixo",
        "tipo": "acoes",
        "criterios": [
            ("roe", 15.0, None),
            ("roic", 12.0, None),
            ("margem_liquida", 8.0, None),
            ("div_liq_patrim", None, 1.5),
            ("liquidez_2meses", 2_000_000, None),
        ],
        "ordenar_por": "roic",
    },
    "fii-renda": {
        "descricao": "FIIs de renda: DY consistente, desconto no P/VP, liquidez real",
        "tipo": "fiis",
        "criterios": [
            ("dy", 8.0, 20.0),
            ("pvp", 0.5, 1.05),
            ("liquidez", 500_000, None),
            ("vacancia_media", None, 15.0),
        ],
        "ordenar_por": "dy",
    },
    "fii-tijolo-desconto": {
        "descricao": "FIIs negociados abaixo do patrimonio, com cap rate atrativo",
        "tipo": "fiis",
        "criterios": [
            ("pvp", 0.3, 0.95),
            ("cap_rate", 6.0, None),
            ("liquidez", 300_000, None),
            ("qtd_imoveis", 1, None),
        ],
        "ordenar_por": "pvp",
        "crescente": True,
    },
}


def aplicar(
    registros: Iterable[dict],
    criterios: Iterable[tuple[str, float | None, float | None]],
    incluir_nulos: bool = False,
) -> list[dict]:
    """Mantem apenas os registros que satisfazem todos os criterios.

    No Fundamentus, "0" costuma significar dado indisponivel, entao um campo
    com criterio nao pode valer 0 — a menos que incluir_nulos seja True, que
    aceita zeros e campos ausentes como valores legitimos.
    """
    criterios = list(criterios)
    resultado = []
    for registro in registros:
        if all(_passa(registro.get(chave), minimo, maximo, incluir_nulos)
               for chave, minimo, maximo in criterios):
            resultado.append(registro)
    return resultado


def _passa(valor, minimo, maximo, incluir_nulos: bool) -> bool:
    if valor is None:
        return incluir_nulos
    if valor == 0 and not incluir_nulos:
        return False
    if minimo is not None and valor < minimo:
        return False
    if maximo is not None and valor > maximo:
        return False
    return True


def ordenar(registros: list[dict], chave: str, crescente: bool = False) -> list[dict]:
    def valor(registro: dict):
        v = registro.get(chave)
        return v if isinstance(v, (int, float)) else (float("inf") if crescente else float("-inf"))

    return sorted(registros, key=valor, reverse=not crescente)


def parse_criterio(expressao: str) -> tuple[str, float | None, float | None]:
    """Converte "dy>=6", "pvp<=1.2" ou "pl=5:15" em (chave, minimo, maximo)."""
    for operador, monta in (
        (">=", lambda c, v: (c, v, None)),
        ("<=", lambda c, v: (c, None, v)),
        (">", lambda c, v: (c, v, None)),
        ("<", lambda c, v: (c, None, v)),
    ):
        if operador in expressao:
            chave, _, bruto = expressao.partition(operador)
            return monta(chave.strip(), float(bruto))
    if "=" in expressao and ":" in expressao:
        chave, _, faixa = expressao.partition("=")
        minimo, _, maximo = faixa.partition(":")
        return (chave.strip(), float(minimo) if minimo else None, float(maximo) if maximo else None)
    raise ValueError(f"criterio invalido: {expressao!r} (use dy>=6, pvp<=1.2 ou pl=5:15)")


def ranquear(registros: list[dict], campos: Iterable[tuple[str, bool]]) -> list[dict]:
    """Adiciona rank_<campo> para cada campo e a coluna `nota` (soma dos ranks).

    Cada par e (campo, crescente): crescente=True significa que o menor valor
    recebe o rank 1 (caso do P/VP); False, que o maior recebe o rank 1 (DY).
    Empates recebem o mesmo rank. Nota menor = melhor colocacao combinada.
    """
    campos = list(campos)
    registros = [dict(r) for r in registros]

    for campo, crescente in campos:
        validos = [r for r in registros if isinstance(r.get(campo), (int, float))]
        ordenados = sorted(validos, key=lambda r: r[campo], reverse=not crescente)

        posicao, anterior, rank = 0, object(), 0
        for registro in ordenados:
            posicao += 1
            if registro[campo] != anterior:
                rank = posicao
                anterior = registro[campo]
            registro[f"rank_{campo}"] = rank

        for registro in registros:
            registro.setdefault(f"rank_{campo}", None)

    for registro in registros:
        ranks = [registro.get(f"rank_{campo}") for campo, _ in campos]
        registro["nota"] = sum(ranks) if all(r is not None for r in ranks) else None

    return registros
