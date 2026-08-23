"""Parser e cruzamento de nome/setor das empresas, sem rede."""

from __future__ import annotations

import unittest

from invest import fundamentus

HTML_LISTAGEM = """
<table>
<thead><tr><th>Papel</th><th>Nome Comercial</th><th>Razão Social</th></tr></thead>
<tbody>
<tr><td><a href="detalhes.php?papel=SAPR11">SAPR11</a></td><td>SANEPAR</td>
    <td>COMPANHIA DE SANEAMENTO DO PARANA - SANEPAR</td></tr>
<tr><td><a href="detalhes.php?papel=PETR4">PETR4</a></td><td>PETROBRAS</td>
    <td>PETROLEO BRASILEIRO S.A. PETROBRAS</td></tr>
</tbody>
</table>
"""

HTML_FICHA = """
<table class="w728">
<tr>
  <td class="label"><span class="help tips" title="x">?</span><span class="txt">Papel</span></td>
  <td class="data"><span class="txt">SAPR11</span></td>
  <td class="label"><span class="txt">Cotação</span></td>
  <td class="data"><span class="txt">33,23</span></td>
</tr>
<tr>
  <td class="label"><span class="help tips" title="x">?</span><span class="txt">Tipo</span></td>
  <td class="data"><span class="txt">UNT N2</span></td>
</tr>
<tr>
  <td class="label"><span class="help tips" title="x">?</span><span class="txt">Empresa</span></td>
  <td class="data"><span class="txt">SANEPAR UNT N2</span></td>
</tr>
<tr>
  <td class="label"><span class="help tips" title="x">?</span><span class="txt">Setor</span></td>
  <td class="data"><span class="txt"><a href="resultado.php?setor=2">Água e Saneamento</a></span></td>
</tr>
<tr>
  <td class="label"><span class="help tips" title="x">?</span><span class="txt">Subsetor</span></td>
  <td class="data"><span class="txt"><a href="resultado.php?segmento=2">Água e Saneamento</a></span></td>
</tr>
</table>
"""


class ListagemEmpresasTest(unittest.TestCase):
    def test_extrai_nome_e_razao_social(self):
        registros = fundamentus._montar_registros(
            HTML_LISTAGEM, fundamentus.CAMPOS_EMPRESAS)
        por_papel = {r["papel"]: r for r in registros}
        self.assertEqual(por_papel["SAPR11"]["nome_comercial"], "SANEPAR")
        self.assertIn("SANEAMENTO", por_papel["SAPR11"]["razao_social"])
        self.assertEqual(por_papel["PETR4"]["nome_comercial"], "PETROBRAS")


class FichaTest(unittest.TestCase):
    def test_extrai_tipo_setor_e_subsetor(self):
        ficha = fundamentus._extrair_ficha(HTML_FICHA)
        self.assertEqual(ficha["papel"], "SAPR11")
        self.assertEqual(ficha["tipo"], "UNT N2")
        self.assertEqual(ficha["empresa"], "SANEPAR UNT N2")
        self.assertEqual(ficha["setor"], "Água e Saneamento")
        self.assertEqual(ficha["subsetor"], "Água e Saneamento")
        self.assertNotIn("cotacao", ficha)


class MontarEmpresasTest(unittest.TestCase):
    def test_prefiro_nome_da_listagem_e_setor_da_ficha(self):
        listagem = fundamentus._montar_registros(
            HTML_LISTAGEM, fundamentus.CAMPOS_EMPRESAS)
        fichas = {"SAPR11": fundamentus._extrair_ficha(HTML_FICHA)}
        registros = fundamentus._montar_empresas(["SAPR11", "XXXX3"], listagem, fichas)
        por_papel = {r["papel"]: r for r in registros}
        self.assertEqual(por_papel["SAPR11"]["empresa"], "SANEPAR")
        self.assertEqual(por_papel["SAPR11"]["setor"], "Água e Saneamento")
        self.assertEqual(por_papel["SAPR11"]["subsetor"], "Água e Saneamento")
        self.assertIsNone(por_papel["XXXX3"]["setor"])


class EnriquecerTest(unittest.TestCase):
    def test_copia_empresa_e_setor_para_o_papel(self):
        acoes = [{"papel": "SAPR11", "dy": 6.0}, {"papel": "XXXX3", "dy": 1.0}]
        empresas = [{
            "papel": "SAPR11",
            "empresa": "SANEPAR",
            "razao_social": "SANEPAR S.A.",
            "setor": "Água e Saneamento",
            "subsetor": "Água e Saneamento",
        }]
        fundamentus.enriquecer(acoes, empresas)
        self.assertEqual(acoes[0]["empresa"], "SANEPAR")
        self.assertEqual(acoes[0]["setor"], "Água e Saneamento")
        self.assertEqual(acoes[0]["subsetor"], "Água e Saneamento")
        self.assertEqual(acoes[0]["razao_social"], "SANEPAR S.A.")
        self.assertNotIn("empresa", acoes[1])


if __name__ == "__main__":
    unittest.main()
