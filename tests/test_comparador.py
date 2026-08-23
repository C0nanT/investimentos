"""invest.comparador: sugerir e comparar, sem HTTP e sem Mongo real."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from invest import comparador
from tests.apoio_mongo import banco_com_papeis

FIIS = [
    {"papel": "MXRF11", "segmento": "Títulos e Val. Mob.", "cotacao": 10.0,
     "dy": 12.0, "pvp": 1.05, "liquidez": 3_000_000, "vacancia_media": 0},
    {"papel": "HGLG11", "segmento": "Logística", "cotacao": 160.0,
     "dy": 9.0, "pvp": 1.0, "liquidez": 5_000_000, "vacancia_media": 3.0},
    {"papel": "KNRI11", "segmento": "Lajes Corporativas", "cotacao": 150.0,
     "dy": 8.0, "pvp": 0.95, "liquidez": 2_500_000, "vacancia_media": 6.0},
]

# Recorte pensado pra passar no fii-aula com a taxa/spread padrao (IPCA+8.17 + 1 = 9.17):
# so HGLG11 teria DY dentro de 9.17-18 e P/VP 0.8-1.2, com liquidez > 2mi.
FIIS_AULA = [
    {"papel": "HGLG11", "dy": 10.0, "pvp": 1.0, "liquidez": 3_000_000},
    {"papel": "MXRF11", "dy": 12.0, "pvp": 1.05, "liquidez": 3_000_000},
    {"papel": "KNRI11", "dy": 7.0, "pvp": 0.9, "liquidez": 3_000_000},  # DY abaixo do minimo padrao
]


def _banco(fiis=FIIS):
    return banco_com_papeis(acoes=[], fiis=fiis)


class SugerirTest(unittest.TestCase):
    def test_devolve_papel_e_segmento(self):
        with patch("invest.db.banco", return_value=_banco()):
            sugestoes = comparador.sugerir("mxrf")
        self.assertEqual(len(sugestoes), 1)
        self.assertEqual(sugestoes[0].papel, "MXRF11")
        self.assertEqual(sugestoes[0].segmento, "Títulos e Val. Mob.")

    def test_exclui_ja_selecionados(self):
        with patch("invest.db.banco", return_value=_banco()):
            sugestoes = comparador.sugerir("h", ja_selecionados={"HGLG11"})
        self.assertEqual(sugestoes, [])


class CompararBasicoTest(unittest.TestCase):
    def test_ordem_dos_papeis_preservada(self):
        pedido = comparador.PedidoComparacao(papeis=["KNRI11", "MXRF11", "HGLG11"])
        with patch("invest.db.banco", return_value=_banco()):
            resultado = comparador.comparar(pedido)
        self.assertEqual([r["papel"] for r in resultado.registros], ["KNRI11", "MXRF11", "HGLG11"])

    def test_papeis_inexistentes_contabilizados(self):
        pedido = comparador.PedidoComparacao(papeis=["MXRF11", "ZZZZ11"])
        with patch("invest.db.banco", return_value=_banco()):
            resultado = comparador.comparar(pedido)
        self.assertEqual([r["papel"] for r in resultado.registros], ["MXRF11"])
        self.assertEqual(resultado.nao_encontrados, ["ZZZZ11"])

    def test_limite_de_dez_papeis_rejeitado(self):
        pedido = comparador.PedidoComparacao(papeis=[f"P{i}11" for i in range(11)])
        with patch("invest.db.banco", return_value=_banco()):
            with self.assertRaises(ValueError):
                comparador.comparar(pedido)


class DestaqueTest(unittest.TestCase):
    def test_melhor_e_pior_por_coluna(self):
        pedido = comparador.PedidoComparacao(papeis=["MXRF11", "HGLG11", "KNRI11"])
        with patch("invest.db.banco", return_value=_banco()):
            resultado = comparador.comparar(pedido)
        # DY: maior melhor -> MXRF11 (12.0); menor pior -> KNRI11 (8.0)
        self.assertEqual(resultado.colunas_destaque["dy"]["melhor"], ["MXRF11"])
        self.assertEqual(resultado.colunas_destaque["dy"]["pior"], ["KNRI11"])
        # P/VP: menor melhor -> KNRI11 (0.95); maior pior -> MXRF11 (1.05)
        self.assertEqual(resultado.colunas_destaque["pvp"]["melhor"], ["KNRI11"])
        self.assertEqual(resultado.colunas_destaque["pvp"]["pior"], ["MXRF11"])

    def test_colunas_textuais_nao_recebem_destaque(self):
        pedido = comparador.PedidoComparacao(papeis=["MXRF11", "HGLG11"])
        with patch("invest.db.banco", return_value=_banco()):
            resultado = comparador.comparar(pedido)
        self.assertNotIn("papel", resultado.colunas_destaque)
        self.assertNotIn("segmento", resultado.colunas_destaque)

    def test_empates_recebem_mesmo_destaque(self):
        fiis = [
            {"papel": "AAAA11", "dy": 10.0},
            {"papel": "BBBB11", "dy": 10.0},
            {"papel": "CCCC11", "dy": 5.0},
        ]
        pedido = comparador.PedidoComparacao(papeis=["AAAA11", "BBBB11", "CCCC11"])
        with patch("invest.db.banco", return_value=_banco(fiis)):
            resultado = comparador.comparar(pedido)
        self.assertEqual(set(resultado.colunas_destaque["dy"]["melhor"]), {"AAAA11", "BBBB11"})

    def test_valores_ausentes_fora_do_destaque(self):
        fiis = [
            {"papel": "AAAA11", "dy": 10.0},
            {"papel": "BBBB11", "dy": 0},  # zero tratado como ausente por padrao
            {"papel": "CCCC11"},  # dy nem existe
        ]
        pedido = comparador.PedidoComparacao(papeis=["AAAA11", "BBBB11", "CCCC11"])
        with patch("invest.db.banco", return_value=_banco(fiis)):
            resultado = comparador.comparar(pedido)
        self.assertEqual(resultado.colunas_destaque["dy"]["melhor"], ["AAAA11"])
        self.assertEqual(resultado.colunas_destaque["dy"]["pior"], ["AAAA11"])

    def test_zeros_valem_entra_no_destaque(self):
        fiis = [
            {"papel": "AAAA11", "dy": 10.0},
            {"papel": "BBBB11", "dy": 0},
        ]
        pedido = comparador.PedidoComparacao(papeis=["AAAA11", "BBBB11"], zeros_valem=True)
        with patch("invest.db.banco", return_value=_banco(fiis)):
            resultado = comparador.comparar(pedido)
        self.assertEqual(resultado.colunas_destaque["dy"]["melhor"], ["AAAA11"])
        self.assertEqual(resultado.colunas_destaque["dy"]["pior"], ["BBBB11"])


class RankingFiiAulaTest(unittest.TestCase):
    def test_nota_calculada_so_entre_selecionados(self):
        # Ranking so entre HGLG11 e KNRI11 (MXRF11 fica de fora, mesmo com DY maior
        # que os dois no universo inteiro): HGLG11 tem melhor DY, KNRI11 tem
        # melhor P/VP, nota = rank_dy + rank_pvp em cada um, so nesse recorte.
        pedido = comparador.PedidoComparacao(
            papeis=["HGLG11", "KNRI11"], ranquear=True,
        )
        with patch("invest.db.banco", return_value=_banco(FIIS_AULA)):
            resultado = comparador.comparar(pedido)
        self.assertTrue(resultado.ranqueado)
        por_papel = {r["papel"]: r for r in resultado.registros}
        self.assertNotIn("MXRF11", por_papel)
        self.assertEqual(por_papel["HGLG11"]["rank_dy"], 1)
        self.assertEqual(por_papel["KNRI11"]["rank_pvp"], 1)
        self.assertEqual(por_papel["HGLG11"]["nota"], 3)
        self.assertEqual(por_papel["KNRI11"]["nota"], 3)

    def test_override_de_taxa_e_spread_altera_quem_passa_e_a_nota(self):
        # Com taxa+spread baixos, KNRI11 (DY 7.0) passa a bater no minimo de DY.
        pedido = comparador.PedidoComparacao(
            papeis=["HGLG11", "KNRI11"], ranquear=True, taxa_base=5.0, spread=1.0,
        )
        with patch("invest.db.banco", return_value=_banco(FIIS_AULA)):
            resultado = comparador.comparar(pedido)
        self.assertTrue(resultado.aprovados_fii_aula["KNRI11"])

        pedido_padrao = comparador.PedidoComparacao(
            papeis=["HGLG11", "KNRI11"], ranquear=True,
        )
        with patch("invest.db.banco", return_value=_banco(FIIS_AULA)):
            resultado_padrao = comparador.comparar(pedido_padrao)
        self.assertFalse(resultado_padrao.aprovados_fii_aula["KNRI11"])

    def test_aprovacao_reflete_criterios_efetivos_do_fii_aula(self):
        pedido = comparador.PedidoComparacao(papeis=["HGLG11", "KNRI11"], ranquear=True)
        with patch("invest.db.banco", return_value=_banco(FIIS_AULA)):
            resultado = comparador.comparar(pedido)
        self.assertTrue(resultado.aprovados_fii_aula["HGLG11"])
        self.assertFalse(resultado.aprovados_fii_aula["KNRI11"])


if __name__ == "__main__":
    unittest.main()
