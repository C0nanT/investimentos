"""Persistencia no MongoDB.

Colecoes:
    acoes / fiis  -> um documento por papel, sempre o dado mais recente
    empresas      -> nome, razao social e setor (muda pouco; separado do snapshot)
    historico     -> um documento por papel por dia, para acompanhar a evolucao
                     dos indicadores (util para ver se o DY se repete ou foi
                     evento isolado)
    presets       -> filtros predefinidos do painel (semente no codigo; edicao no banco)
    config        -> valores auxiliares avulsos (ex.: ultima taxa do Tesouro IPCA+)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient, UpdateOne

from . import filtros

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
    bd.presets.create_index([("tipo", ASCENDING)])
    garantir_presets()


def _documento_de_preset(nome: str, config: dict) -> dict:
    doc = {
        "_id": nome,
        "nome": nome,
        "descricao": config["descricao"],
        "tipo": config["tipo"],
        "criterios": [list(c) for c in config["criterios"]],
        "ordenar_por": config["ordenar_por"],
        "crescente": bool(config.get("crescente", False)),
        "ranquear": [list(p) for p in config["ranquear"]] if config.get("ranquear") else None,
    }
    if config.get("taxa_base") is not None:
        doc["taxa_base"] = config["taxa_base"]
        doc["spread"] = config["spread"]
    return doc


def _de_documento(doc: dict) -> dict:
    saida = {
        "nome": doc.get("nome") or doc.get("_id"),
        "descricao": doc["descricao"],
        "tipo": doc["tipo"],
        "criterios": [tuple(c) for c in doc.get("criterios", [])],
        "ordenar_por": doc.get("ordenar_por"),
        "crescente": bool(doc.get("crescente", False)),
        "ranquear": [tuple(p) for p in doc["ranquear"]] if doc.get("ranquear") else None,
    }
    if doc.get("taxa_base") is not None:
        saida["taxa_base"] = doc["taxa_base"]
        saida["spread"] = doc.get("spread")
    return saida


def garantir_presets() -> None:
    """Insere os presets do codigo que ainda nao existem. Nunca sobrescreve edicao salva."""
    col = banco().presets
    for nome, config in filtros.PRESETS.items():
        col.update_one(
            {"_id": nome},
            {"$setOnInsert": _documento_de_preset(nome, config)},
            upsert=True,
        )


def listar_presets() -> dict[str, dict]:
    garantir_presets()
    por_nome = {}
    for doc in banco().presets.find():
        preset = _de_documento(doc)
        por_nome[preset["nome"]] = preset
    saida: dict[str, dict] = {}
    for nome in filtros.PRESETS:
        if nome in por_nome:
            saida[nome] = por_nome.pop(nome)
    saida.update(por_nome)
    return saida


def obter_preset(nome: str) -> dict | None:
    garantir_presets()
    doc = banco().presets.find_one({"_id": nome})
    return _de_documento(doc) if doc else None


def salvar_preset(
    nome: str,
    criterios: list[tuple[str, float | None, float | None]],
    taxa_base: float | None = None,
    spread: float | None = None,
) -> dict:
    """Sobrescreve os criterios (e taxa/spread, se vierem) de um preset ja existente."""
    if obter_preset(nome) is None:
        raise KeyError(f"preset desconhecido: {nome}")
    campos: dict = {"criterios": [list(c) for c in criterios]}
    if taxa_base is not None:
        campos["taxa_base"] = float(taxa_base)
    if spread is not None:
        campos["spread"] = float(spread)
    banco().presets.update_one({"_id": nome}, {"$set": campos})
    return obter_preset(nome)


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
    iguais: dict[str, str | list[str]] | None = None,
) -> list[dict]:
    """Traduz os criterios (campo, minimo, maximo) para um filtro do Mongo.

    Por padrao, um campo com criterio nao pode valer 0: no Fundamentus o zero
    quase sempre significa dado ausente (bancos sem ROIC, FIIs de papel sem
    vacancia nem cap rate), e deixa-lo passar polui a triagem. Com
    zeros_valem=True o zero conta como numero de verdade.

    `iguais` filtra igualdade (setor, subsetor). Lista vira $in (grupo B3).
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
        if not valor:
            continue
        consulta[campo] = {"$in": list(valor)} if isinstance(valor, (list, tuple)) else valor

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


def salvar_ipca(taxa: float, vencimento: str, data_base: str) -> dict:
    """Guarda a ultima taxa do Tesouro IPCA+ (mais curto) obtida com sucesso."""
    doc = {
        "taxa": float(taxa),
        "vencimento": vencimento,
        "data_base": data_base,
        "atualizado_em": datetime.now(timezone.utc),
    }
    banco().config.update_one({"_id": "ipca"}, {"$set": doc}, upsert=True)
    return doc


def obter_ipca() -> dict | None:
    """Ultima taxa do Tesouro IPCA+ salva, ou None se nunca foi obtida com sucesso."""
    doc = banco().config.find_one({"_id": "ipca"})
    if not doc:
        return None
    return {
        "taxa": doc["taxa"],
        "vencimento": doc["vencimento"],
        "data_base": doc["data_base"],
        "atualizado_em": doc["atualizado_em"].astimezone().strftime("%d/%m/%Y %H:%M"),
    }


def contar(tipo: str) -> int:
    return banco()[tipo].count_documents({})


def buscar_fiis_por_prefixo(
    termo: str, excluir: list[str] | None = None, limite: int = 8,
) -> list[dict]:
    """Busca FIIs cujo papel comeca com `termo`, ignorando maiusculas/minusculas.

    Tickers em `excluir` nao voltam no resultado (ja escolhidos na comparacao).
    Termo vazio nao busca nada — evita listar o mercado inteiro por engano.
    """
    termo = (termo or "").strip().upper()
    if not termo:
        return []
    excluidos = {p.upper() for p in (excluir or [])}
    candidatos = [
        doc for doc in banco()["fiis"].find({}, {"_id": 0})
        if doc.get("papel", "").upper().startswith(termo)
        and doc.get("papel", "").upper() not in excluidos
    ]
    candidatos.sort(key=lambda d: d.get("papel", ""))
    return candidatos[:limite] if limite else candidatos


def obter_por_papeis(tipo: str, papeis: list[str]) -> list[dict]:
    """Devolve documentos de `tipo` para os `papeis` pedidos, na ordem recebida.

    Papeis inexistentes ficam de fora; quem chamar pode comparar `papeis`
    com os `papel` devolvidos para saber quais nao foram encontrados.
    """
    normalizados = [p.upper() for p in papeis]
    encontrados = {
        doc["papel"].upper(): doc
        for doc in banco()[tipo].find({"papel": {"$in": normalizados}}, {"_id": 0})
    }
    return [encontrados[p] for p in normalizados if p in encontrados]


def valores_distintos(tipo: str, campo: str) -> list[str]:
    return sorted(v for v in banco()[tipo].distinct(campo) if v)


def serializavel(documentos: list[dict]) -> list[dict]:
    """Converte datetime em texto para poder virar JSON."""
    saida = []
    for doc in documentos:
        limpo = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in doc.items()}
        saida.append(limpo)
    return saida
