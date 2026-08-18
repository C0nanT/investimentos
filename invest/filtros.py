"""Filtros e ordenacao sobre os registros do Fundamentus."""

from __future__ import annotations

from typing import Callable, Iterable

# Presets: pontos de partida para nao ter que lembrar de todo criterio.
# Cada valor eh (chave, minimo, maximo); None = sem limite daquele lado.
PRESETS: dict[str, dict] = {
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

    No Fundamentus, "0" costuma significar dado indisponivel. Por isso um
    valor ausente ou zerado reprova quando o criterio exige um minimo; quando
    o criterio so impoe um teto (divida, vacancia), zero passa normalmente.
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
    if valor == 0 and minimo is not None and minimo > 0 and not incluir_nulos:
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
