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
        ("papel", "Papel", "texto"),
        ("cotacao", "Cotação", "reais"),
        ("dy", "DY", "percentual"),
        ("pl", "P/L", "numero"),
        ("pvp", "P/VP", "numero"),
        ("roe", "ROE", "percentual"),
        ("roic", "ROIC", "percentual"),
        ("margem_liquida", "Mrg. Líq.", "percentual"),
        ("ev_ebit", "EV/EBIT", "numero"),
        ("div_liq_patrim", "Dív.Líq/PL", "numero"),
        ("cagr_receita_5a", "CAGR Rec. 5a", "percentual"),
        ("liquidez_2meses", "Liquidez 2m", "compacto"),
        ("patrimonio_liquido", "Patrimônio", "compacto"),
    ],
    "fiis": [
        ("papel", "Papel", "texto"),
        ("segmento", "Segmento", "texto"),
        ("cotacao", "Cotação", "reais"),
        ("dy", "DY", "percentual"),
        ("pvp", "P/VP", "numero"),
        ("ffo_yield", "FFO Yield", "percentual"),
        ("cap_rate", "Cap Rate", "percentual"),
        ("vacancia_media", "Vacância", "percentual"),
        ("qtd_imoveis", "Imóveis", "numero"),
        ("liquidez", "Liquidez", "compacto"),
        ("valor_mercado", "Valor merc.", "compacto"),
    ],
}


class Manipulador(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (nome exigido pelo BaseHTTPRequestHandler)
        rota = urlparse(self.path)
        parametros = parse_qs(rota.query)

        try:
            if rota.path in ("/", "/index.html"):
                return self._enviar_html(PAGINA.read_text(encoding="utf-8"))
            if rota.path == "/api/config":
                return self._enviar_json({
                    "colunas": {t: [{"chave": c, "titulo": r, "formato": f} for c, r, f in cols]
                                for t, cols in COLUNAS.items()},
                    "presets": {n: {"descricao": p["descricao"], "tipo": p["tipo"],
                                    "criterios": p["criterios"], "ordenar_por": p["ordenar_por"],
                                    "crescente": p.get("crescente", False)}
                                for n, p in filtros.PRESETS.items()},
                    "percentuais": sorted(fundamentus.COLUNAS_PERCENTUAIS),
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
        if preset and preset in filtros.PRESETS:
            config = filtros.PRESETS[preset]
            criterios = list(config["criterios"]) + criterios
            ordenar_por = ordenar_por or config["ordenar_por"]

        documentos = db.consultar(tipo, criterios, ordenar_por, crescente)
        return {
            "tipo": tipo,
            "total": db.banco()[tipo].count_documents({}),
            "encontrados": len(documentos),
            "criterios": criterios,
            "registros": db.serializavel(documentos),
        }

    def _sincronizar(self) -> dict:
        relatorio = []
        for tipo in ("acoes", "fiis"):
            registros, origem = fundamentus.carregar(tipo, forcar=True)
            resumo = db.gravar(tipo, registros)
            resumo["origem"] = origem
            relatorio.append(resumo)
        return {"sync": relatorio, "status": db.status()}

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
