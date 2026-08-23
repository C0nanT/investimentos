"""Presets persistidos no Mongo: semente do codigo e overwrite ao salvar."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from invest import db, filtros


class ColecaoMemoria:
    def __init__(self):
        self.docs = {}

    def find(self, filtro=None, proj=None):
        saida = []
        for doc in self.docs.values():
            if proj:
                saida.append({k: doc[k] for k in proj if k in doc})
            else:
                saida.append(dict(doc))
        return saida

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


def _banco_falso(colecao):
    class Banco:
        presets = colecao
    return Banco()


class SementePresetsTest(unittest.TestCase):
    def test_colecao_vazia_recebe_presets_do_codigo(self):
        col = ColecaoMemoria()
        with patch("invest.db.banco", return_value=_banco_falso(col)):
            db.garantir_presets()
        self.assertEqual(set(col.docs), set(filtros.PRESETS))
        self.assertEqual(col.docs["dividendos"]["criterios"][0], ["dy", 6.0, 20.0])
        self.assertEqual(col.docs["fii-aula"]["taxa_base"], filtros.TAXA_BASE_PADRAO)
        self.assertEqual(col.docs["fii-aula"]["spread"], filtros.SPREAD_PADRAO)

    def test_nao_sobrescreve_preset_ja_salvo(self):
        col = ColecaoMemoria()
        col.insert_one({
            "_id": "dividendos", "descricao": "meu", "tipo": "acoes",
            "criterios": [["dy", 9.0, 12.0]], "ordenar_por": "dy",
        })
        with patch("invest.db.banco", return_value=_banco_falso(col)):
            db.garantir_presets()
        self.assertEqual(col.docs["dividendos"]["criterios"], [["dy", 9.0, 12.0]])
        self.assertEqual(col.docs["dividendos"]["descricao"], "meu")
        self.assertIn("valor", col.docs)


class SalvarPresetTest(unittest.TestCase):
    def test_sobrescreve_criterios_e_mantem_o_resto(self):
        col = ColecaoMemoria()
        with patch("invest.db.banco", return_value=_banco_falso(col)):
            db.garantir_presets()
            original = db.obter_preset("dividendos")
            salvo = db.salvar_preset(
                "dividendos", [("dy", 7.0, 15.0), ("roe", 12.0, None)])
        self.assertEqual(
            [tuple(c) for c in salvo["criterios"]],
            [("dy", 7.0, 15.0), ("roe", 12.0, None)])
        self.assertEqual(salvo["descricao"], original["descricao"])
        self.assertEqual(salvo["tipo"], "acoes")
        self.assertEqual(salvo["ordenar_por"], "dy")

    def test_salva_taxa_e_spread_do_fii_aula(self):
        col = ColecaoMemoria()
        with patch("invest.db.banco", return_value=_banco_falso(col)):
            db.garantir_presets()
            salvo = db.salvar_preset(
                "fii-aula",
                [("liquidez", 2_000_000, None), ("dy", 11.17, 18.0), ("pvp", 0.8, 1.2)],
                taxa_base=8.17, spread=3.0,
            )
        self.assertEqual(salvo["spread"], 3.0)
        self.assertEqual(salvo["taxa_base"], 8.17)
        dy = next(c for c in salvo["criterios"] if c[0] == "dy")
        self.assertEqual(tuple(dy), ("dy", 11.17, 18.0))


class AplicarTaxaTest(unittest.TestCase):
    def test_recalcula_dy_minimo(self):
        config = filtros.preset_fii_aula(8.17, 1.0)
        novo = filtros.aplicar_taxa(config, 8.17, 3.0)
        dy = next(c for c in novo["criterios"] if c[0] == "dy")
        self.assertEqual(dy, ("dy", 11.17, 18.0))
        self.assertEqual(novo["spread"], 3.0)


class ListarPresetsTest(unittest.TestCase):
    def test_devolve_dict_por_nome_na_ordem_do_codigo(self):
        col = ColecaoMemoria()
        with patch("invest.db.banco", return_value=_banco_falso(col)):
            lista = db.listar_presets()
        self.assertEqual(list(lista), list(filtros.PRESETS))
        self.assertEqual(lista["qualidade"]["tipo"], "acoes")
        self.assertTrue(lista["fii-aula"]["ranquear"])


if __name__ == "__main__":
    unittest.main()
