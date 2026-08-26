"""invest.triagem.triar: Pedido -> Resultado, sem HTTP e sem Mongo real."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
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


# Recorte da aula com taxa baixa (dy min 6): A e B passam; FORA falha liquidez
# mas tem o maior DY do mercado — se o rank olhasse o mercado inteiro, A nao
# seria rank_dy 1. ALFA e melhor nos dois eixos (nota 2); BETA nota 4.
FIIS_RANKING = [
    {"papel": "ALFA11", "dy": 12.0, "pvp": 0.9, "liquidez": 3_000_000},
    {"papel": "BETA11", "dy": 10.0, "pvp": 1.1, "liquidez": 3_000_000},
    {"papel": "FORA11", "dy": 15.0, "pvp": 1.0, "liquidez": 500_000},
]

FIIS_EMPATE = [
    {"papel": "IGUA11", "dy": 10.0, "pvp": 1.0, "liquidez": 3_000_000},
    {"papel": "IGUB11", "dy": 10.0, "pvp": 0.9, "liquidez": 3_000_000},
]

FIIS_SEM_CAMPO = [
    {"papel": "COMP11", "dy": 10.0, "pvp": 1.0, "liquidez": 3_000_000},
    {"papel": "FALT11", "dy": 11.0, "liquidez": 3_000_000},  # sem pvp
]


def _banco_fiis_docs(fiis):
    return banco_com_papeis(acoes=[], fiis=fiis)


def _preset_rank_so_liquidez(banco):
    """Preset que ranqueia dy+pvp mas so filtra liquidez — deixa entrar quem nao tem pvp."""
    banco.presets.insert_one({
        "_id": "rank-liquidez",
        "nome": "rank-liquidez",
        "descricao": "Rank de teste: so liquidez, rank DY+P/VP",
        "tipo": "fiis",
        "criterios": [["liquidez", 2_000_000, None]],
        "ordenar_por": "nota",
        "crescente": True,
        "ranquear": [["dy", False], ["pvp", True]],
    })
    return banco


class RankingENotaTest(unittest.TestCase):
    def test_nota_calculada_so_no_recorte_filtrado(self):
        # FORA11 tem DY maior que ALFA11, mas fica de fora por liquidez.
        # No recorte, ALFA11 e rank_dy 1 (nao 2).
        pedido = triagem.Pedido(tipo="fiis", preset="fii-aula", taxa_base=5.0, spread=1.0)
        with patch("invest.db.banco", return_value=_banco_fiis_docs(FIIS_RANKING)):
            resultado = triagem.triar(pedido)
        por_papel = {r["papel"]: r for r in resultado.registros}
        self.assertNotIn("FORA11", por_papel)
        self.assertEqual(por_papel["ALFA11"]["rank_dy"], 1)
        self.assertEqual(por_papel["ALFA11"]["rank_pvp"], 1)
        self.assertEqual(por_papel["ALFA11"]["nota"], 2)
        self.assertEqual(por_papel["BETA11"]["rank_dy"], 2)
        self.assertEqual(por_papel["BETA11"]["rank_pvp"], 2)
        self.assertEqual(por_papel["BETA11"]["nota"], 4)

    def test_empate_recebe_a_mesma_posicao(self):
        pedido = triagem.Pedido(tipo="fiis", preset="fii-aula", taxa_base=5.0, spread=1.0)
        with patch("invest.db.banco", return_value=_banco_fiis_docs(FIIS_EMPATE)):
            resultado = triagem.triar(pedido)
        por_papel = {r["papel"]: r for r in resultado.registros}
        self.assertEqual(por_papel["IGUA11"]["rank_dy"], por_papel["IGUB11"]["rank_dy"])
        self.assertEqual(por_papel["IGUA11"]["rank_dy"], 1)

    def test_papel_sem_valor_no_campo_ranqueado_fica_sem_nota(self):
        banco = _preset_rank_so_liquidez(_banco_fiis_docs(FIIS_SEM_CAMPO))
        pedido = triagem.Pedido(tipo="fiis", preset="rank-liquidez")
        with patch("invest.db.banco", return_value=banco):
            resultado = triagem.triar(pedido)
        por_papel = {r["papel"]: r for r in resultado.registros}
        self.assertEqual(por_papel["COMP11"]["nota"], 3)  # rank_dy 2 + rank_pvp 1
        self.assertIsNone(por_papel["FALT11"]["nota"])
        self.assertIsNone(por_papel["FALT11"]["rank_pvp"])
        self.assertEqual(por_papel["FALT11"]["rank_dy"], 1)

    def test_ordenar_por_nota_forca_crescente(self):
        # Pedido pede decrescente; ordenar por nota ainda coloca melhor (menor nota) primeiro.
        pedido = triagem.Pedido(
            tipo="fiis", preset="fii-aula", taxa_base=5.0, spread=1.0, crescente=False,
        )
        with patch("invest.db.banco", return_value=_banco_fiis_docs(FIIS_RANKING)):
            resultado = triagem.triar(pedido)
        self.assertEqual([r["papel"] for r in resultado.registros], ["ALFA11", "BETA11"])
        self.assertEqual([r["nota"] for r in resultado.registros], [2, 4])

    def test_trocar_coluna_de_ordenacao_preserva_ranks(self):
        pedido = triagem.Pedido(
            tipo="fiis", preset="fii-aula", taxa_base=5.0, spread=1.0, ordenar_por="dy",
        )
        with patch("invest.db.banco", return_value=_banco_fiis_docs(FIIS_RANKING)):
            resultado = triagem.triar(pedido)
        por_papel = {r["papel"]: r for r in resultado.registros}
        self.assertEqual(por_papel["ALFA11"]["rank_dy"], 1)
        self.assertEqual(por_papel["ALFA11"]["nota"], 2)
        self.assertEqual(por_papel["BETA11"]["rank_pvp"], 2)
        # Ordenacao por dy decrescente (padrao do pedido): ALFA (12) antes de BETA (10).
        self.assertEqual([r["papel"] for r in resultado.registros], ["ALFA11", "BETA11"])

    def test_resultado_sinaliza_que_foi_ranqueado(self):
        pedido = triagem.Pedido(tipo="fiis", preset="fii-aula", taxa_base=5.0, spread=1.0)
        with patch("invest.db.banco", return_value=_banco_fiis_docs(FIIS_RANKING)):
            resultado = triagem.triar(pedido)
        self.assertTrue(resultado.ranqueado)

    def test_sem_ranking_delega_ordenacao_ao_banco_e_respeita_sentido(self):
        pedido = triagem.Pedido(
            tipo="acoes", criterios=[("roe", 15.0, None)],
            ordenar_por="roe", crescente=True,
        )
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertFalse(resultado.ranqueado)
        self.assertEqual([r["papel"] for r in resultado.registros], ["AAAA3", "BBBB3"])


class BordasTest(unittest.TestCase):
    def test_preset_inexistente_cai_para_triagem_sem_preset(self):
        # Link antigo com nome que sumiu: segue sem erro e sem descricao.
        pedido = triagem.Pedido(tipo="acoes", preset="preset-que-nao-existe-mais")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertIsNone(resultado.descricao)
        self.assertEqual(resultado.criterios, [])
        self.assertEqual(resultado.encontrados, resultado.total)

    def test_criterio_mal_escrito_mostra_formato_aceito(self):
        # Decodificacao na borda (web chama parse_criterio antes do Pedido).
        with self.assertRaises(ValueError) as ctx:
            filtros.parse_criterio("dy~~6")
        self.assertIn("use dy>=6, pvp<=1.2 ou pl=5:15", str(ctx.exception))

    def test_campos_de_data_voltam_como_texto(self):
        quando = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        acoes = [
            {"papel": "DATA3", "roe": 20.0, "atualizado_em": quando},
        ]
        pedido = triagem.Pedido(tipo="acoes")
        with patch("invest.db.banco", return_value=banco_com_papeis(acoes=acoes, fiis=[])):
            resultado = triagem.triar(pedido)
        valor = resultado.registros[0]["atualizado_em"]
        self.assertIsInstance(valor, str)
        self.assertEqual(valor, quando.isoformat())

    def test_sem_preset_e_sem_criterios_devolve_snapshot_inteiro(self):
        pedido = triagem.Pedido(tipo="acoes")
        with patch("invest.db.banco", return_value=_banco()):
            resultado = triagem.triar(pedido)
        self.assertEqual(resultado.encontrados, resultado.total)
        self.assertEqual(resultado.total, len(ACOES_QUALIDADE))
        self.assertEqual(
            {r["papel"] for r in resultado.registros},
            {a["papel"] for a in ACOES_QUALIDADE},
        )


if __name__ == "__main__":
    unittest.main()
