"""Substituto em memoria do Mongo para os testes de consulta.

Reproduz so o pedaco de comportamento que invest.db.consultar usa: filtro por
faixa ($gte/$lte), exclusao de zero ($ne), igualdade simples ou por lista
($in), projecao de _id, sort e limit. Nao e um Mongo de verdade — so o
suficiente para exercitar a regra "zero nao entra, a menos que zeros_valem".
"""

from __future__ import annotations


def _bate(doc: dict, filtro: dict) -> bool:
    for campo, condicao in filtro.items():
        valor = doc.get(campo)
        if not isinstance(condicao, dict):
            if valor != condicao:
                return False
            continue
        if "$gte" in condicao and not (valor is not None and valor >= condicao["$gte"]):
            return False
        if "$lte" in condicao and not (valor is not None and valor <= condicao["$lte"]):
            return False
        if "$ne" in condicao and valor == condicao["$ne"]:
            return False
        if "$in" in condicao and valor not in condicao["$in"]:
            return False
    return True


class _Cursor(list):
    def sort(self, campo: str, direcao: int = 1):
        self[:] = sorted(self, key=lambda d: d.get(campo), reverse=direcao != 1)
        return self

    def limit(self, n: int):
        if n:
            del self[n:]
        return self


class ColecaoSnapshot:
    """Substitui `banco()[tipo]` (acoes/fiis): so find() precisa existir."""

    def __init__(self, documentos: list[dict]):
        self.documentos = [dict(d) for d in documentos]

    def find(self, filtro: dict | None = None, proj: dict | None = None):
        cursor = _Cursor(dict(d) for d in self.documentos if _bate(d, filtro or {}))
        if proj and proj.get("_id") == 0:
            for d in cursor:
                d.pop("_id", None)
        return cursor

    def count_documents(self, filtro: dict | None = None) -> int:
        return sum(1 for d in self.documentos if _bate(d, filtro or {}))


class ColecaoPresets:
    """Substitui `banco().presets`: colecao chaveada por _id, como no Mongo real."""

    def __init__(self):
        self.docs: dict[str, dict] = {}

    def find(self, filtro=None, proj=None):
        return [dict(d) for d in self.docs.values()]

    def find_one(self, filtro, proj=None):
        doc = self.docs.get(filtro["_id"])
        if not doc:
            return None
        copiado = dict(doc)
        if proj and proj.get("_id") == 0:
            copiado.pop("_id", None)
        return copiado

    def insert_one(self, doc):
        self.docs[doc["_id"]] = dict(doc)

    def update_one(self, filtro, update, upsert=False):
        _id = filtro["_id"]
        if _id not in self.docs:
            if not upsert:
                return
            self.docs[_id] = {"_id": _id}
            self.docs[_id].update(update.get("$setOnInsert", {}))
        self.docs[_id].update(update.get("$set", {}))


class BancoFalso:
    """Substitui o retorno de invest.db.banco(): so subscript e `.presets` sao usados."""

    def __init__(self, colecoes: dict[str, ColecaoSnapshot]):
        self._colecoes = colecoes
        self.presets = ColecaoPresets()

    def __getitem__(self, tipo: str) -> ColecaoSnapshot:
        return self._colecoes[tipo]


# Conjunto fixo e pequeno de papeis, com casos de zero e de campo ausente.
ACOES = [
    {"papel": "PETR4", "setor": "Petróleo, Gás e Biocombustíveis", "dy": 6.5, "pvp": 1.2, "pl": 5.0},
    {"papel": "VALE3", "setor": "Mineração", "dy": 9.0, "pvp": 1.1, "pl": 6.0},
    {"papel": "ITUB4", "setor": "Bancos", "dy": 0, "pvp": 1.5, "pl": 8.0},  # dy=0 = dado ausente no Fundamentus
    {"papel": "BBAS3", "setor": "Bancos", "pvp": 0.9, "pl": 4.0},  # dy nem existe no documento
]

FIIS = [
    {"papel": "HGLG11", "dy": 9.0, "pvp": 1.0, "liquidez": 3_000_000},
    {"papel": "MXRF11", "dy": 12.0, "pvp": 1.05, "liquidez": 500_000},
    {"papel": "KNRI11", "dy": 0, "pvp": 0.95, "liquidez": 2_000_000},  # dy=0 = dado ausente
    {"papel": "XPML11", "pvp": 0.9, "liquidez": 1_000_000},  # dy nem existe no documento
]


def banco_com_papeis(acoes: list[dict] | None = None, fiis: list[dict] | None = None) -> BancoFalso:
    return BancoFalso({
        "acoes": ColecaoSnapshot(ACOES if acoes is None else acoes),
        "fiis": ColecaoSnapshot(FIIS if fiis is None else fiis),
    })
