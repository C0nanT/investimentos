"""Modulo de triagem: Pedido (decodificado) -> Resultado (pronto pra JSON).

Concentra a composicao que antes vivia no handler HTTP: resolver preset,
aplicar taxa quando o preset declara taxa base, concatenar criterios do
preset com os avulsos, ordenar no banco quando nao ha ranking, consultar,
ranquear e ordenar em memoria quando ha ranking, montar o resultado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import db, filtros


@dataclass
class Pedido:
    tipo: str
    preset: str | None = None
    criterios: list[tuple[str, float | None, float | None]] = field(default_factory=list)
    ordenar_por: str | None = None
    crescente: bool = False
    zeros_valem: bool = False
    setor: str | None = None
    subsetor: str | None = None
    tipo_fundo: str | None = None
    taxa_base: float | None = None
    spread: float | None = None


@dataclass
class Resultado:
    tipo: str
    total: int
    encontrados: int
    criterios: list[tuple[str, float | None, float | None]]
    descricao: str | None
    ranqueado: bool
    registros: list[dict]


def triar(pedido: Pedido) -> Resultado:
    criterios = list(pedido.criterios)
    ordenar_por = pedido.ordenar_por
    crescente = pedido.crescente
    ranquear_por = None
    descricao = None

    if pedido.preset:
        config = db.obter_preset(pedido.preset)
        if config:
            if config.get("taxa_base") is not None:
                taxa_base = pedido.taxa_base if pedido.taxa_base is not None else config["taxa_base"]
                spread = pedido.spread if pedido.spread is not None else (config.get("spread") or 0)
                config = filtros.aplicar_taxa(config, float(taxa_base), float(spread))
            criterios = list(config["criterios"]) + criterios
            ordenar_por = ordenar_por or config["ordenar_por"]
            ranquear_por = config.get("ranquear")
            descricao = config["descricao"]
            if ordenar_por == "nota":
                crescente = True

    iguais = None
    if pedido.tipo == "acoes":
        iguais = (
            {"subsetor": pedido.subsetor} if pedido.subsetor
            else filtros.iguais_setorial(pedido.setor)
        )

    documentos = db.consultar(
        pedido.tipo, criterios,
        None if ranquear_por else ordenar_por,
        crescente, zeros_valem=pedido.zeros_valem,
        iguais=iguais,
    )
    if pedido.tipo == "fiis":
        filtro_tipo = filtros.iguais_tipo_fii(pedido.tipo_fundo)
        if filtro_tipo:
            documentos = [
                doc for doc in documentos
                if filtros.classificar_tipo_fii(doc) == filtro_tipo
            ]
    if ranquear_por:
        documentos = filtros.ranquear(documentos, ranquear_por)
        documentos = filtros.ordenar(documentos, ordenar_por or "nota", crescente)

    return Resultado(
        tipo=pedido.tipo,
        total=db.contar(pedido.tipo),
        encontrados=len(documentos),
        criterios=criterios,
        descricao=descricao,
        ranqueado=bool(ranquear_por),
        registros=db.serializavel(documentos),
    )
