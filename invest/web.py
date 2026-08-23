"""Servidor local do painel: serve a pagina e uma API JSON lida do MongoDB."""

from __future__ import annotations

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import db, filtros, fundamentus

PAGINA = Path(__file__).resolve().parent / "painel.html"

COLUNAS = {
    "acoes": [
        ("papel", "Papel", "texto", "Código de negociação da ação na bolsa (ticker)."),
        ("empresa", "Empresa", "texto", "Nome comercial da companhia emissora."),
        ("setor", "Setor", "texto",
         "Setor de atuação no Fundamentus. Use para comparar múltiplos com os pares, "
         "não com o mercado inteiro."),
        ("subsetor", "Subsetor", "texto",
         "Segmento dentro do setor (ex.: Bancos dentro de Intermediários Financeiros)."),
        ("cotacao", "Cotação", "reais", "Preço atual de uma ação."),
        ("dy", "DY", "percentual",
         "Dividend Yield: quanto a empresa pagou em dividendos nos últimos 12 meses, "
         "em relação à cotação atual."),
        ("pl", "P/L", "numero",
         "Preço sobre Lucro: quantos anos de lucro atual seriam necessários para "
         "pagar o preço da ação. Quanto menor, em geral mais barata está a ação."),
        ("pvp", "P/VP", "numero",
         "Preço sobre Valor Patrimonial: compara a cotação com o patrimônio líquido "
         "por ação. Abaixo de 1 sugere ação negociada abaixo do valor contábil."),
        ("roe", "ROE", "percentual",
         "Return on Equity: retorno que a empresa gera sobre o patrimônio líquido dos sócios."),
        ("roic", "ROIC", "percentual",
         "Return on Invested Capital: retorno que a empresa gera sobre o capital "
         "total investido (próprio + de terceiros)."),
        ("margem_liquida", "Mrg. Líq.", "percentual",
         "Margem Líquida: percentual da receita que sobra como lucro líquido."),
        ("ev_ebit", "EV/EBIT", "numero",
         "Enterprise Value sobre EBIT: valor da empresa (incluindo dívida) dividido "
         "pelo lucro operacional. Similar ao P/L, mas considera o endividamento."),
        ("div_liq_patrim", "Dív.Líq/PL", "numero",
         "Dívida Líquida sobre Patrimônio Líquido: nível de endividamento da empresa "
         "em relação ao seu patrimônio."),
        ("cagr_receita_5a", "CAGR Rec. 5a", "percentual",
         "Crescimento anual composto da receita nos últimos 5 anos."),
        ("liquidez_2meses", "Liquidez 2m", "compacto",
         "Volume médio negociado por dia nos últimos 2 meses, em reais."),
        ("patrimonio_liquido", "Patrimônio", "compacto", "Patrimônio líquido total da empresa."),
    ],
    "fiis": [
        ("papel", "Papel", "texto", "Código de negociação do fundo imobiliário na bolsa (ticker)."),
        ("segmento", "Segmento", "texto",
         "Tipo de ativo do fundo (ex.: lajes corporativas, shoppings, papel/recebíveis)."),
        ("cotacao", "Cotação", "reais", "Preço atual de uma cota do fundo."),
        ("dy", "DY", "percentual",
         "Dividend Yield: quanto o fundo distribuiu em rendimentos nos últimos 12 meses, "
         "em relação à cotação atual."),
        ("pvp", "P/VP", "numero",
         "Preço sobre Valor Patrimonial: compara a cotação da cota com o valor "
         "patrimonial por cota. Abaixo de 1 sugere cota negociada abaixo do valor contábil."),
        ("ffo_yield", "FFO Yield", "percentual",
         "Funds From Operations Yield: geração de caixa operacional do fundo em relação "
         "à cotação atual."),
        ("cap_rate", "Cap Rate", "percentual",
         "Taxa de capitalização: retorno operacional dos imóveis do fundo em relação "
         "ao seu valor de mercado. Costuma ser 0 (indisponível) em fundos de papel/CRI."),
        ("vacancia_media", "Vacância", "percentual",
         "Percentual médio de área dos imóveis do fundo sem locação. Costuma ser 0 "
         "(indisponível) em fundos de papel/CRI."),
        ("qtd_imoveis", "Imóveis", "numero",
         "Quantidade de imóveis na carteira do fundo. Costuma ser 0 em fundos de papel/CRI."),
        ("liquidez", "Liquidez", "compacto", "Volume médio negociado por dia, em reais."),
        ("valor_mercado", "Valor merc.", "compacto", "Valor de mercado total do fundo."),
    ],
}

# Colunas exibidas apenas quando o preset calcula ranking.
COLUNAS_RANK = [
    ("rank_dy", "Rank DY", "inteiro", "Posição no ranking por Dividend Yield (1 = melhor)."),
    ("rank_pvp", "Rank P/VP", "inteiro", "Posição no ranking por P/VP (1 = melhor)."),
    ("nota", "Nota", "inteiro", "Nota final combinando os rankings usados no preset."),
]


class Manipulador(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (nome exigido pelo BaseHTTPRequestHandler)
        rota = urlparse(self.path)
        parametros = parse_qs(rota.query)

        try:
            if rota.path in ("/", "/index.html"):
                return self._enviar_html(PAGINA.read_text(encoding="utf-8"))
            if rota.path == "/api/config":
                return self._enviar_json({
                    "colunas": {t: [{"chave": c, "titulo": r, "formato": f, "descricao": d}
                                     for c, r, f, d in cols]
                                for t, cols in COLUNAS.items()},
                    "colunas_rank": [{"chave": c, "titulo": r, "formato": f, "descricao": d}
                                      for c, r, f, d in COLUNAS_RANK],
                    "presets": {n: {"descricao": p["descricao"], "tipo": p["tipo"],
                                    "criterios": p["criterios"], "ordenar_por": p["ordenar_por"],
                                    "crescente": p.get("crescente", False),
                                    "ranquear": p.get("ranquear")}
                                for n, p in filtros.PRESETS.items()},
                    "taxa_base": filtros.TAXA_BASE_PADRAO,
                    "spread": filtros.SPREAD_PADRAO,
                    "percentuais": sorted(fundamentus.COLUNAS_PERCENTUAIS),
                    "setores": db.valores_distintos("acoes", "setor"),
                    "status": db.status(),
                })
            if rota.path in ("/api/acoes", "/api/fiis"):
                return self._enviar_json(self._consultar(rota.path.rsplit("/", 1)[1], parametros))
            if rota.path == "/api/sync":
                return self._enviar_json(self._sincronizar())
        except Exception as erro:  # devolve o erro na tela em vez de derrubar o server
            return self._enviar_json({"erro": f"{type(erro).__name__}: {erro}"}, codigo=500)

        self._enviar_json({"erro": "rota nao encontrada"}, codigo=404)

    def _consultar(self, tipo: str, parametros: dict) -> dict:
        criterios = []
        for expressao in parametros.get("f", []):
            if expressao.strip():
                criterios.append(filtros.parse_criterio(expressao))

        preset = (parametros.get("preset") or [""])[0]
        ordenar_por = (parametros.get("ordenar") or [""])[0] or None
        crescente = (parametros.get("crescente") or ["0"])[0] == "1"
        zeros = (parametros.get("zeros") or ["0"])[0] == "1"
        setor = (parametros.get("setor") or [""])[0]
        ranquear_por = None
        descricao = None

        if preset and preset in filtros.PRESETS:
            config = filtros.PRESETS[preset]
            if preset == "fii-aula":
                config = filtros.preset_fii_aula(
                    float((parametros.get("taxa_base") or [filtros.TAXA_BASE_PADRAO])[0]),
                    float((parametros.get("spread") or [filtros.SPREAD_PADRAO])[0]),
                )
            criterios = list(config["criterios"]) + criterios
            ordenar_por = ordenar_por or config["ordenar_por"]
            ranquear_por = config.get("ranquear")
            descricao = config["descricao"]
            if ordenar_por == "nota":
                crescente = True

        # Com ranking, o Mongo devolve tudo e a ordenacao acontece depois de
        # calcular a nota (que so existe dentro do recorte filtrado).
        documentos = db.consultar(
            tipo, criterios,
            None if ranquear_por else ordenar_por,
            crescente, zeros_valem=zeros,
            iguais={"setor": setor} if setor else None,
        )
        if ranquear_por:
            documentos = filtros.ranquear(documentos, ranquear_por)
            documentos = filtros.ordenar(documentos, ordenar_por or "nota", crescente)

        return {
            "tipo": tipo,
            "total": db.banco()[tipo].count_documents({}),
            "encontrados": len(documentos),
            "criterios": criterios,
            "descricao": descricao,
            "ranqueado": bool(ranquear_por),
            "registros": db.serializavel(documentos),
        }

    def _sincronizar(self) -> dict:
        relatorio = []
        for tipo in ("acoes", "fiis"):
            registros, origem = fundamentus.carregar(tipo, forcar=True)
            if tipo == "acoes":
                empresas, origem_emp = fundamentus.carregar_empresas(
                    [r["papel"] for r in registros])
                fundamentus.enriquecer(registros, empresas)
                emp = db.gravar_empresas(empresas)
                emp["origem"] = origem_emp
                relatorio.append(emp)
            resumo = db.gravar(tipo, registros)
            resumo["origem"] = origem
            relatorio.append(resumo)
        return {"sync": relatorio, "status": db.status(),
                "setores": db.valores_distintos("acoes", "setor")}

    def _enviar_json(self, dados, codigo: int = 200):
        corpo = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _enviar_html(self, texto: str):
        corpo = texto.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, formato, *args):  # silencia o log de cada request
        pass


def servir(porta: int = 8000, abrir_navegador: bool = True) -> None:
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Manipulador)
    url = f"http://localhost:{porta}"
    print(f"painel em {url}  (ctrl+c para parar)")
    if abrir_navegador:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrado.")
    finally:
        servidor.server_close()
