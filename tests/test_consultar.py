"""db.consultar sem Mongo: banco de papeis fixo em memoria (tests/apoio_mongo.py).

Cobre a regra que nunca foi exercitada por teste: campo com criterio nao pode
valer 0 (Fundamentus usa 0 pra dado ausente), a menos que zeros_valem=True.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from invest import db
from tests.apoio_mongo import banco_com_papeis


class FaixaTest(unittest.TestCase):
    def test_so_minimo(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in db.consultar("acoes", [("dy", 7.0, None)])}
        self.assertEqual(papeis, {"VALE3"})

    def test_so_maximo(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in db.consultar("fiis", [("dy", None, 10.0)])}
        self.assertEqual(papeis, {"HGLG11"})

    def test_minimo_e_maximo(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in db.consultar("acoes", [("pvp", 1.0, 1.2)])}
        self.assertEqual(papeis, {"PETR4", "VALE3"})


class ZeroTest(unittest.TestCase):
    def test_regra_padrao_exclui_papel_com_zero_no_campo_filtrado(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in db.consultar("acoes", [("dy", 0.0, None)])}
        self.assertNotIn("ITUB4", papeis)

        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis_fii = {r["papel"] for r in db.consultar("fiis", [("dy", 0.0, None)])}
        self.assertNotIn("KNRI11", papeis_fii)

    def test_zeros_valem_inclui_o_mesmo_papel(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in
                      db.consultar("acoes", [("dy", 0.0, None)], zeros_valem=True)}
        self.assertIn("ITUB4", papeis)

        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis_fii = {r["papel"] for r in
                          db.consultar("fiis", [("dy", 0.0, None)], zeros_valem=True)}
        self.assertIn("KNRI11", papeis_fii)

    def test_campo_ausente_continua_de_fora_mesmo_com_zeros_valem(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in
                      db.consultar("acoes", [("dy", 0.0, None)], zeros_valem=True)}
        self.assertNotIn("BBAS3", papeis)


class IgualdadeTest(unittest.TestCase):
    def test_filtro_por_setor_recorta_corretamente(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in
                      db.consultar("acoes", iguais={"setor": "Bancos"})}
        self.assertEqual(papeis, {"ITUB4", "BBAS3"})

    def test_filtro_por_lista_de_setores(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = {r["papel"] for r in
                      db.consultar("acoes", iguais={"setor": ["Bancos", "Mineração"]})}
        self.assertEqual(papeis, {"ITUB4", "BBAS3", "VALE3"})


class OrdenacaoTest(unittest.TestCase):
    def test_decrescente_e_o_padrao(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = [r["papel"] for r in
                      db.consultar("fiis", [("dy", 1.0, None)], ordenar_por="dy")]
        self.assertEqual(papeis, ["MXRF11", "HGLG11"])

    def test_crescente(self):
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            papeis = [r["papel"] for r in
                      db.consultar("fiis", [("dy", 1.0, None)],
                                   ordenar_por="dy", crescente=True)]
        self.assertEqual(papeis, ["HGLG11", "MXRF11"])


class SemRedeTest(unittest.TestCase):
    def test_nao_precisa_de_mongo_real(self):
        # Se este teste roda (sob `make test`, sem container Mongo de pe), a
        # troca via patch("invest.db.banco", ...) esta funcionando: nenhum
        # socket foi aberto.
        with patch("invest.db.banco", return_value=banco_com_papeis()):
            resultado = db.consultar("acoes")
        self.assertEqual(len(resultado), 4)


if __name__ == "__main__":
    unittest.main()
