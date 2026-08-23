"""Recorte por tipo de FII no painel (heurística sobre o snapshot do Fundamentus)."""

from __future__ import annotations

import unittest

from invest import filtros


class PrincipaisTiposTest(unittest.TestCase):
    def test_ordem_bate_com_o_painel_em_3_colunas(self):
        self.assertEqual(filtros.TIPOS_PRINCIPAIS_FII, [
            "Todos os Tipos",
            "Fundo Misto",
            "Fundo de Desenvolvimento",
            "Fundo de Fundos",
            "Fundo de Papel",
            "Fundo de Tijolo",
            "Outro",
        ])
        self.assertEqual(len(filtros.TIPOS_PRINCIPAIS_FII), 7)


class IguaisTipoFiiTest(unittest.TestCase):
    def test_todos_nao_filtra(self):
        self.assertIsNone(filtros.iguais_tipo_fii(""))
        self.assertIsNone(filtros.iguais_tipo_fii("Todos os Tipos"))
        self.assertIsNone(filtros.iguais_tipo_fii("  "))

    def test_tipo_retorna_rotulo(self):
        self.assertEqual(filtros.iguais_tipo_fii("Fundo de Papel"), "Fundo de Papel")


class ClassificarTipoFiiTest(unittest.TestCase):
    def test_papel_por_segmento_ou_multicategoria_sem_imoveis(self):
        self.assertEqual(
            filtros.classificar_tipo_fii({"segmento": "Títulos e Val. Mob."}),
            "Fundo de Papel",
        )
        self.assertEqual(
            filtros.classificar_tipo_fii({"segmento": "Multicategoria", "qtd_imoveis": 0}),
            "Fundo de Papel",
        )

    def test_tijolo_por_segmento_fisico_ou_imoveis(self):
        self.assertEqual(
            filtros.classificar_tipo_fii({"segmento": "Shoppings", "qtd_imoveis": 12}),
            "Fundo de Tijolo",
        )
        self.assertEqual(
            filtros.classificar_tipo_fii({"segmento": "Multicategoria", "qtd_imoveis": 60}),
            "Fundo de Tijolo",
        )

    def test_misto_por_hibrido_ou_sinais_mistos(self):
        self.assertEqual(
            filtros.classificar_tipo_fii({"segmento": "Híbrido"}),
            "Fundo Misto",
        )
        self.assertEqual(
            filtros.classificar_tipo_fii({
                "segmento": "Multicategoria",
                "qtd_imoveis": 6,
                "cap_rate": 8.5,
                "vacancia_media": 0.6,
            }),
            "Fundo Misto",
        )

    def test_fundo_de_fundos_por_ticker(self):
        self.assertEqual(
            filtros.classificar_tipo_fii({"papel": "HFOF11", "segmento": "Multicategoria"}),
            "Fundo de Fundos",
        )

    def test_desenvolvimento_por_pvp_baixo_com_imoveis(self):
        self.assertEqual(
            filtros.classificar_tipo_fii({
                "segmento": "Multicategoria",
                "qtd_imoveis": 4,
                "pvp": 0.4,
            }),
            "Fundo de Desenvolvimento",
        )

    def test_outros(self):
        self.assertEqual(
            filtros.classificar_tipo_fii({"segmento": "Outros"}),
            "Outro",
        )


if __name__ == "__main__":
    unittest.main()
