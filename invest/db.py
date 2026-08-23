"""Persistencia no MongoDB.

Colecoes:
    acoes / fiis  -> um documento por papel, sempre o dado mais recente
    empresas      -> nome, razao social e setor (muda pouco; separado do snapshot)
    historico     -> um documento por papel por dia, para acompanhar a evolucao
                     dos indicadores (util para ver se o DY se repete ou foi
                     evento isolado)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient, UpdateOne

URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
NOME_BANCO = os.environ.get("MONGO_DB", "investimentos")

_cliente: MongoClient | None = None


def banco():
    global _cliente
    if _cliente is None:
        _cliente = MongoClient(URI, serverSelectionTimeoutMS=5000)
    return _cliente[NOME_BANCO]


def garantir_indices() -> None:
    bd = banco()
    for tipo in ("acoes", "fiis"):
        bd[tipo].create_index([("papel", ASCENDING)], unique=True)
        bd[tipo].create_index([("dy", ASCENDING)])
        bd[tipo].create_index([("pvp", ASCENDING)])
    bd.acoes.create_index([("setor", ASCENDING)])
    bd.empresas.create_index([("papel", ASCENDING)], unique=True)
    bd.empresas.create_index([("setor", ASCENDING)])
    bd.historico.create_index([("papel", ASCENDING), ("data", ASCENDING)], unique=True)
    bd.historico.create_index([("tipo", ASCENDING), ("data", ASCENDING)])


def gravar(tipo: str, registros: list[dict]) -> dict:
    """Grava o snapshot atual e registra o dia no historico."""
    bd = banco()
    garantir_indices()

    agora = datetime.now(timezone.utc)
    dia = agora.strftime("%Y-%m-%d")

    atuais = [
        UpdateOne(
            {"papel": r["papel"]},
            {"$set": {**r, "tipo": tipo, "atualizado_em": agora}},
            upsert=True,
        )
        for r in registros
    ]
    resultado = bd[tipo].bulk_write(atuais, ordered=False)

    diario = [
        UpdateOne(
            {"papel": r["papel"], "data": dia},
            {"$set": {**r, "tipo": tipo, "data": dia, "registrado_em": agora}},
            upsert=True,
        )
        for r in registros
    ]
    bd.historico.bulk_write(diario, ordered=False)

    # modified_count nao serve como medida de mudanca real: o campo
    # atualizado_em muda em todo sync. Reportamos novos vs. ja conhecidos.
    novos = resultado.upserted_count
    return {
        "tipo": tipo,
        "total": len(registros),
        "novos": novos,
        "existentes": len(registros) - novos,
        "data": dia,
    }


def gravar_empresas(registros: list[dict]) -> dict:
    """Upsert da ficha da empresa (nome, razao social, setor). Sem historico."""
    bd = banco()
    garantir_indices()
    agora = datetime.now(timezone.utc)
    ops = [
        UpdateOne(
            {"papel": r["papel"]},
            {"$set": {**r, "atualizado_em": agora}},
            upsert=True,
        )
        for r in registros
    ]
    resultado = bd.empresas.bulk_write(ops, ordered=False)
    novos = resultado.upserted_count
    return {
        "tipo": "empresas",
        "total": len(registros),
        "novos": novos,
        "existentes": len(registros) - novos,
        "com_setor": sum(1 for r in registros if r.get("setor")),
    }


def consultar(
    tipo: str,
    criterios: list[tuple[str, float | None, float | None]] | None = None,
    ordenar_por: str | None = None,
    crescente: bool = False,
    limite: int = 0,
    zeros_valem: bool = False,
    iguais: dict[str, str] | None = None,
) -> list[dict]:
    """Traduz os criterios (campo, minimo, maximo) para um filtro do Mongo.

    Por padrao, um campo com criterio nao pode valer 0: no Fundamentus o zero
    quase sempre significa dado ausente (bancos sem ROIC, FIIs de papel sem
    vacancia nem cap rate), e deixa-lo passar polui a triagem. Com
    zeros_valem=True o zero conta como numero de verdade.

    `iguais` filtra igualdade exata (setor, segmento).
    """
    consulta: dict = {}
    for campo, minimo, maximo in criterios or []:
        if minimo is None and maximo is None:
            continue
        faixa: dict = consulta.setdefault(campo, {})
        if minimo is not None:
            faixa["$gte"] = minimo
        if maximo is not None:
            faixa["$lte"] = maximo
        if not zeros_valem:
            faixa["$ne"] = 0
    for campo, valor in (iguais or {}).items():
        if valor:
            consulta[campo] = valor

    cursor = banco()[tipo].find(consulta, {"_id": 0})
    if ordenar_por:
        cursor = cursor.sort(ordenar_por, ASCENDING if crescente else -1)
    if limite:
        cursor = cursor.limit(limite)
    return list(cursor)


def status() -> dict:
    bd = banco()
    info: dict = {"uri": URI, "banco": NOME_BANCO, "colecoes": {}}
    for tipo in ("acoes", "fiis"):
        recente = bd[tipo].find_one({}, {"atualizado_em": 1}, sort=[("atualizado_em", -1)])
        info["colecoes"][tipo] = {
            "documentos": bd[tipo].count_documents({}),
            "atualizado_em": recente["atualizado_em"].astimezone().strftime("%d/%m/%Y %H:%M")
            if recente else None,
        }
    info["historico"] = {
        "documentos": bd.historico.count_documents({}),
        "dias": len(bd.historico.distinct("data")),
    }
    recente_emp = bd.empresas.find_one({}, {"atualizado_em": 1}, sort=[("atualizado_em", -1)])
    info["empresas"] = {
        "documentos": bd.empresas.count_documents({}),
        "setores": len([v for v in bd.empresas.distinct("setor") if v]),
        "atualizado_em": recente_emp["atualizado_em"].astimezone().strftime("%d/%m/%Y %H:%M")
        if recente_emp else None,
    }
    return info


def valores_distintos(tipo: str, campo: str) -> list[str]:
    return sorted(v for v in banco()[tipo].distinct(campo) if v)


def serializavel(documentos: list[dict]) -> list[dict]:
    """Converte datetime em texto para poder virar JSON."""
    saida = []
    for doc in documentos:
        limpo = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in doc.items()}
        saida.append(limpo)
    return saida
