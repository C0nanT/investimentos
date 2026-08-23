"""invest.db.buscar_fiis_por_prefixo e invest.db.obter_por_papeis, sem Mongo real."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from invest import db
from tests.apoio_mongo import banco_com_papeis

FIIS = [
    {"papel": "MXRF11", "segmento": "Títulos e Val. Mob.", "dy": 12.0},
    {"papel": "MXRF12", "segmento": "Títulos e Val. Mob.", "dy": 11.0},
    {"papel": "HGLG11", "segmento": "Logística", "dy": 9.0},
    {"papel": "KNRI11", "segmento": "Lajes Corporativas", "dy": 8.0},
]


def _banco():
    return banco_com_papeis(acoes=[], fiis=FIIS)


class BuscarPorPrefixoTest(unittest.TestCase):
    def test_prefixo_case_insensitive(self):
        with patch("invest.db.banco", return_value=_banco()):
            resultado = db.buscar_fiis_por_prefixo("mxrf")
        self.assertEqual({d["papel"] for d in resultado}, {"MXRF11", "MXRF12"})

    def test_exclui_ja_selecionados(self):
        with patch("invest.db.banco", return_value=_banco()):
            resultado = db.buscar_fiis_por_prefixo("mxrf", excluir=["MXRF11"])
        self.assertEqual([d["papel"] for d in resultado], ["MXRF12"])

    def test_respeita_limite(self):
        with patch("invest.db.banco", return_value=_banco()):
            resultado = db.buscar_fiis_por_prefixo("", limite=1)
        self.assertEqual(resultado, [])  # termo vazio nao busca nada

    def test_sem_match_devolve_lista_vazia(self):
        with patch("invest.db.banco", return_value=_banco()):
            resultado = db.buscar_fiis_por_prefixo("zzzz")
        self.assertEqual(resultado, [])

    def test_limite_corta_resultado(self):
        with patch("invest.db.banco", return_value=_banco()):
            resultado = db.buscar_fiis_por_prefixo("m", limite=1)
        self.assertEqual(len(resultado), 1)


class ObterPorPapeisTest(unittest.TestCase):
    def test_preserva_ordem_pedida(self):
        with patch("invest.db.banco", return_value=_banco()):
            resultado = db.obter_por_papeis("fiis", ["KNRI11", "MXRF11"])
        self.assertEqual([d["papel"] for d in resultado], ["KNRI11", "MXRF11"])

    def test_omite_inexistentes(self):
        with patch("invest.db.banco", return_value=_banco()):
            resultado = db.obter_por_papeis("fiis", ["MXRF11", "XXXX11", "HGLG11"])
        self.assertEqual([d["papel"] for d in resultado], ["MXRF11", "HGLG11"])


if __name__ == "__main__":
    unittest.main()
