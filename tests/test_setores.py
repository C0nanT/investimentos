"""Recorte setorial do painel: principais da B3 + segmentos do Fundamentus."""

from __future__ import annotations

import unittest

from invest import filtros


class PrincipaisTest(unittest.TestCase):
    def test_ordem_bate_com_o_painel_em_3_colunas(self):
        self.assertEqual(filtros.SETORES_PRINCIPAIS, [
            "Todos os setores",
            "Água e Saneamento",
            "Bancos",
            "Bens Industriais",
            "Construção Civil",
            "Consumo Cíclico",
            "Consumo Não Cíclico",
            "Energia Elétrica",
            "Financeiro",
            "Materiais Básicos",
            "Mineração",
            "Petróleo, Gás e Biocombustíveis",
            "Previdência e Seguros",
            "Saúde",
            "Seguradoras",
            "Tecnologia da Informação",
            "Telecomunicações",
            "Utilidade Pública",
        ])
        self.assertEqual(len(filtros.SETORES_PRINCIPAIS), 18)


class IguaisSetorialTest(unittest.TestCase):
    def test_todos_nao_filtra(self):
        self.assertIsNone(filtros.iguais_setorial(""))
        self.assertIsNone(filtros.iguais_setorial("Todos os setores"))
        self.assertIsNone(filtros.iguais_setorial("  "))

    def test_segmento_usa_subsetor(self):
        self.assertEqual(filtros.iguais_setorial("Bancos"), {"subsetor": "Bancos"})
        self.assertEqual(filtros.iguais_setorial("Seguradoras"), {"subsetor": "Seguradoras"})

    def test_setor_exato_do_fundamentus(self):
        self.assertEqual(
            filtros.iguais_setorial("Água e Saneamento"),
            {"setor": "Água e Saneamento"},
        )
        self.assertEqual(
            filtros.iguais_setorial("Petróleo, Gás e Biocombustíveis"),
            {"setor": "Petróleo, Gás e Biocombustíveis"},
        )

    def test_grupo_b3_vira_lista_de_setores(self):
        financeiro = filtros.iguais_setorial("Financeiro")
        self.assertEqual(set(financeiro["setor"]), {
            "Intermediários Financeiros",
            "Serviços Financeiros Diversos",
            "Previdência e Seguros",
            "Exploração de Imóveis",
            "Holdings Diversificadas",
        })
        materiais = filtros.iguais_setorial("Materiais Básicos")
        self.assertIn("Mineração", materiais["setor"])
        self.assertIn("Siderurgia e Metalurgia", materiais["setor"])

    def test_nome_fora_da_lista_filtra_setor_exato(self):
        self.assertEqual(
            filtros.iguais_setorial("Intermediários Financeiros"),
            {"setor": "Intermediários Financeiros"},
        )

    def test_utilidade_publica_junta_energia_agua_e_gas(self):
        self.assertEqual(set(filtros.iguais_setorial("Utilidade Pública")["setor"]), {
            "Energia Elétrica",
            "Água e Saneamento",
            "Gás",
        })


if __name__ == "__main__":
    unittest.main()
