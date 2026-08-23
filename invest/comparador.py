"""Modulo comparador: monta uma shortlist de FIIs lado a lado (sem tocar o mercado inteiro).

Duas interfaces publicas: `sugerir` para o autocomplete de tickers e `comparar`
para montar a tabela comparativa, com destaque de melhor/pior por indicador e,
opcionalmente, o rank/nota do preset `fii-aula` calculado so entre os selecionados.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import db, filtros

LIMITE_SELECAO = 10

# Direcao de "melhor" por indicador numerico, reaproveitada dos presets/ranking
# existentes: True = menor e melhor, False = maior e melhor. Colunas textuais
# (papel, segmento) e sem direcao definida (cotacao, qtd_imoveis) ficam fora.
DIRECOES_DESTAQUE: dict[str, bool] = {
    "dy": False,
    "ffo_yield": False,
    "cap_rate": False,
    "liquidez": False,
    "valor_mercado": False,
    "pvp": True,
    "vacancia_media": True,
}


@dataclass
class Sugestao:
    papel: str
    segmento: str | None = None


@dataclass
class PedidoComparacao:
    papeis: list[str] = field(default_factory=list)
    zeros_valem: bool = False
    ranquear: bool = False
    taxa_base: float | None = None
    spread: float | None = None


@dataclass
class ResultadoComparacao:
    registros: list[dict]
    nao_encontrados: list[str]
    colunas_destaque: dict[str, dict[str, list[str]]]
    ranqueado: bool
    aprovados_fii_aula: dict[str, bool] | None = None


def sugerir(termo: str, *, ja_selecionados: set[str] | None = None, limite: int = 8) -> list[Sugestao]:
    documentos = db.buscar_fiis_por_prefixo(termo, excluir=list(ja_selecionados or []), limite=limite)
    return [Sugestao(papel=doc["papel"], segmento=doc.get("segmento")) for doc in documentos]


def comparar(pedido: PedidoComparacao) -> ResultadoComparacao:
    if len(pedido.papeis) > LIMITE_SELECAO:
        raise ValueError(f"comparacao aceita no maximo {LIMITE_SELECAO} papeis")

    # obter_por_papeis ja devolve na ordem pedida — so falta apontar quem ficou de fora.
    registros = [dict(doc) for doc in db.obter_por_papeis("fiis", pedido.papeis)]
    achados = {r["papel"] for r in registros}
    nao_encontrados = [p.upper() for p in pedido.papeis if p.upper() not in achados]

    ranqueado = False
    aprovados = None
    if pedido.ranquear and registros:
        config = filtros.PRESETS["fii-aula"]
        taxa_base = pedido.taxa_base if pedido.taxa_base is not None else config["taxa_base"]
        spread = pedido.spread if pedido.spread is not None else config["spread"]
        config = filtros.aplicar_taxa(config, float(taxa_base), float(spread))
        registros = filtros.ranquear(registros, config["ranquear"])
        registros = filtros.ordenar(registros, "nota", True)
        ranqueado = True
        aprovados = {
            registro["papel"]: bool(
                filtros.aplicar([registro], config["criterios"], incluir_nulos=pedido.zeros_valem)
            )
            for registro in registros
        }

    return ResultadoComparacao(
        registros=registros,
        nao_encontrados=nao_encontrados,
        colunas_destaque=_colunas_destaque(registros, pedido.zeros_valem),
        ranqueado=ranqueado,
        aprovados_fii_aula=aprovados,
    )


def _colunas_destaque(registros: list[dict], zeros_valem: bool) -> dict[str, dict[str, list[str]]]:
    destaques: dict[str, dict[str, list[str]]] = {}
    for campo, menor_melhor in DIRECOES_DESTAQUE.items():
        validos = []
        for r in registros:
            valor = r.get(campo)
            if isinstance(valor, (int, float)) and (zeros_valem or valor != 0):
                validos.append(r)
        if not validos:
            continue
        valores = [r[campo] for r in validos]
        melhor_valor = min(valores) if menor_melhor else max(valores)
        pior_valor = max(valores) if menor_melhor else min(valores)
        destaques[campo] = {
            "melhor": [r["papel"] for r in validos if r[campo] == melhor_valor],
            "pior": [r["papel"] for r in validos if r[campo] == pior_valor],
        }
    return destaques
