"""invest.triagem.triar: Pedido -> Resultado, sem HTTP e sem Mongo real."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from invest import filtros, triagem
from tests.apoio_mongo import banco_com_papeis

ACOES_QUALIDADE = [
    {"papel": "AAAA3", "setor": "Bancos", "roe": 20.0, "roic": 18.0,
     "margem_liquida": 10.0, "div_liq_patrim": 1.0, "liquidez_2meses": 3_000_000},
    {"papel": "BBBB3", "setor": "Mineração", "roe": 25.0, "roic": 20.0,
     "margem_liquida": 12.0, "div_liq_patrim": 0.5, "liquidez_2meses": 5_000_000},
    {"papel": "CCCC3", "setor": "Bancos", "roe": 10.0, "roic": 5.0,
     "margem_liquida": 3.0, "div_liq_patrim": 3.0, "liquidez_2meses": 500_000},
]


def _banco():
    return banco_com_papeis(acoes=ACOES_QUALIDADE, fiis=[])


class PresetSozinhoTest(unittest.TestCase):
    def test_devolve_so_os_papeis_que_batem_com_os_criterios_do_preset(self):
        pedido = triagem.Pedido(tipo="acoes", preset="qualidade")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        papeis = {r["papel"] for r in resultado.registros}
        self.assertEqual(papeis, {"AAAA3", "BBBB3"})

    def test_ordena_pela_coluna_do_preset_por_padrao(self):
        pedido = triagem.Pedido(tipo="acoes", preset="qualidade")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertEqual([r["papel"] for r in resultado.registros], ["BBBB3", "AAAA3"])

    def test_descricao_do_preset_volta_no_resultado(self):
        pedido = triagem.Pedido(tipo="acoes", preset="qualidade")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertEqual(resultado.descricao, filtros.PRESETS["qualidade"]["descricao"])
        self.assertFalse(resultado.ranqueado)


class CriteriosAvulsosTest(unittest.TestCase):
    def test_avulso_entra_depois_do_preset_e_reforca_o_recorte(self):
        pedido = triagem.Pedido(
            tipo="acoes", preset="qualidade",
            criterios=[("roic", None, 19.0)],
        )
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        papeis = {r["papel"] for r in resultado.registros}
        self.assertEqual(papeis, {"AAAA3"})

    def test_criterios_do_resultado_tem_preset_primeiro_depois_avulso(self):
        pedido = triagem.Pedido(
            tipo="acoes", preset="qualidade",
            criterios=[("roic", None, 19.0)],
        )
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertEqual(resultado.criterios[-1], ("roic", None, 19.0))
        self.assertEqual(
            [c[0] for c in resultado.criterios[:5]],
            [c[0] for c in filtros.PRESETS["qualidade"]["criterios"]],
        )


class SetorTest(unittest.TestCase):
    def test_filtro_por_setor_recorta_o_resultado(self):
        pedido = triagem.Pedido(tipo="acoes", setor="Mineração")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        papeis = {r["papel"] for r in resultado.registros}
        self.assertEqual(papeis, {"BBBB3"})


class ZerosValemTest(unittest.TestCase):
    def _banco_com_zero(self):
        acoes = [
            {"papel": "ZERO3", "dy": 0},
            {"papel": "CHEIA3", "dy": 7.0},
        ]
        return banco_com_papeis(acoes=acoes, fiis=[])

    def test_regra_padrao_exclui_papel_com_zero(self):
        pedido = triagem.Pedido(tipo="acoes", criterios=[("dy", 0.0, None)])
        with patch("invest.db.banco", return_value=self._banco_com_zero()):
            resultado = triagem.triar(pedido)
        papeis = {r["papel"] for r in resultado.registros}
        self.assertEqual(papeis, {"CHEIA3"})

    def test_zeros_valem_inclui_o_mesmo_papel(self):
        pedido = triagem.Pedido(tipo="acoes", criterios=[("dy", 0.0, None)], zeros_valem=True)
        with patch("invest.db.banco", return_value=self._banco_com_zero()):
            resultado = triagem.triar(pedido)
        papeis = {r["papel"] for r in resultado.registros}
        self.assertEqual(papeis, {"ZERO3", "CHEIA3"})


FIIS_AULA = [
    {"papel": "HGLG11", "dy": 9.0, "pvp": 1.0, "liquidez": 3_000_000},
    {"papel": "MXRF11", "dy": 12.0, "pvp": 1.05, "liquidez": 500_000},
]


def _banco_fiis():
    return banco_com_papeis(acoes=[], fiis=FIIS_AULA)


class TaxaSpreadTest(unittest.TestCase):
    def test_override_recalcula_dy_minimo_e_mantem_demais_criterios(self):
        pedido = triagem.Pedido(tipo="fiis", preset="fii-aula", taxa_base=5.0, spread=1.0)
        with patch("invest.db.banco", return_value=_banco_fiis()):
            resultado = triagem.triar(pedido)
        criterios = {c[0]: c for c in resultado.criterios}
        self.assertEqual(criterios["dy"], ("dy", 6.0, 18.0))
        self.assertEqual(criterios["liquidez"], ("liquidez", 2_000_000, None))
        self.assertEqual(criterios["pvp"], ("pvp", 0.8, 1.2))

    def test_maximo_do_dy_nao_muda_com_o_override(self):
        pedido = triagem.Pedido(tipo="fiis", preset="fii-aula", taxa_base=12.0, spread=2.0)
        with patch("invest.db.banco", return_value=_banco_fiis()):
            resultado = triagem.triar(pedido)
        criterios = {c[0]: c for c in resultado.criterios}
        self.assertEqual(criterios["dy"], ("dy", 14.0, 18.0))

    def test_preset_sem_taxa_base_ignora_override(self):
        pedido = triagem.Pedido(
            tipo="acoes", preset="qualidade", taxa_base=5.0, spread=1.0,
        )
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertEqual(
            resultado.criterios,
            list(filtros.PRESETS["qualidade"]["criterios"]),
        )

    def test_sem_override_usa_taxa_e_spread_do_preset(self):
        pedido = triagem.Pedido(tipo="fiis", preset="fii-aula")
        with patch("invest.db.banco", return_value=_banco_fiis()):
            resultado = triagem.triar(pedido)
        criterios = {c[0]: c for c in resultado.criterios}
        dy_minimo_padrao = round(filtros.TAXA_BASE_PADRAO + filtros.SPREAD_PADRAO, 2)
        self.assertEqual(criterios["dy"], ("dy", dy_minimo_padrao, 18.0))
        papeis = {r["papel"] for r in resultado.registros}
        self.assertEqual(papeis, set())

    def test_criterios_no_resultado_refletem_o_dy_minimo_recalculado(self):
        pedido = triagem.Pedido(tipo="fiis", preset="fii-aula", taxa_base=5.0, spread=1.0)
        with patch("invest.db.banco", return_value=_banco_fiis()):
            resultado = triagem.triar(pedido)
        papeis = {r["papel"] for r in resultado.registros}
        self.assertEqual(papeis, {"HGLG11"})


class TotalEEncontradosTest(unittest.TestCase):
    def test_total_conta_o_snapshot_e_encontrados_o_recorte(self):
        pedido = triagem.Pedido(tipo="acoes", preset="qualidade")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertEqual(resultado.total, 3)
        self.assertEqual(resultado.encontrados, 2)
        self.assertEqual(resultado.encontrados, len(resultado.registros))

    def test_tipo_e_repassado_no_resultado(self):
        pedido = triagem.Pedido(tipo="acoes", preset="qualidade")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertEqual(resultado.tipo, "acoes")


if __name__ == "__main__":
    unittest.main()
