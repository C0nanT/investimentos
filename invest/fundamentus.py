"""Coleta de indicadores fundamentalistas do Fundamentus.

Uma requisicao traz a tabela inteira do mercado (acoes ou FIIs), ja com os
multiplos calculados. Sem dependencias externas: urllib + html.parser.
"""

from __future__ import annotations

import gzip
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

URL_ACOES = "https://www.fundamentus.com.br/resultado.php"
URL_FIIS = "https://www.fundamentus.com.br/fii_resultado.php"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

DIR_DADOS = Path(__file__).resolve().parent.parent / "data"

# Nome bonito do site -> chave usada no codigo/filtros.
CAMPOS_ACOES = {
    "Papel": "papel",
    "Cotação": "cotacao",
    "P/L": "pl",
    "P/VP": "pvp",
    "PSR": "psr",
    "Div.Yield": "dy",
    "P/Ativo": "p_ativo",
    "P/Cap.Giro": "p_cap_giro",
    "P/EBIT": "p_ebit",
    "P/Ativ Circ.Liq": "p_acl",
    "EV/EBIT": "ev_ebit",
    "EV/EBITDA": "ev_ebitda",
    "Mrg Bruta": "margem_bruta",
    "Mrg Ebit": "margem_ebit",
    "Mrg. Líq.": "margem_liquida",
    "Liq. Corr.": "liquidez_corrente",
    "ROIC": "roic",
    "ROE": "roe",
    "Liq.2meses": "liquidez_2meses",
    "Patrim. Líq": "patrimonio_liquido",
    "Dív.Líq/ Patrim.": "div_liq_patrim",
    "Cresc. Rec.5a": "cagr_receita_5a",
}

CAMPOS_FIIS = {
    "Papel": "papel",
    "Segmento": "segmento",
    "Cotação": "cotacao",
    "FFO Yield": "ffo_yield",
    "Dividend Yield": "dy",
    "P/VP": "pvp",
    "Valor de Mercado": "valor_mercado",
    "Liquidez": "liquidez",
    "Qtd de imóveis": "qtd_imoveis",
    "Preço do m2": "preco_m2",
    "Aluguel por m2": "aluguel_m2",
    "Cap Rate": "cap_rate",
    "Vacância Média": "vacancia_media",
    "Endereço": "endereco",
}

# Colunas em percentual: o site manda "12,34%" -> guardamos 12.34
COLUNAS_PERCENTUAIS = {
    "dy", "margem_bruta", "margem_ebit", "margem_liquida", "roic", "roe",
    "cagr_receita_5a", "ffo_yield", "cap_rate", "vacancia_media",
}

COLUNAS_TEXTO = {"papel", "segmento", "endereco"}


class _ParserTabela(HTMLParser):
    """Extrai <thead> e <tbody> da primeira tabela da pagina."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cabecalho: list[str] = []
        self.linhas: list[list[str]] = []
        self._linha: list[str] | None = None
        self._celula: list[str] | None = None
        self._na_tabela = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._na_tabela = not self.linhas and not self.cabecalho
        elif not self._na_tabela:
            return
        elif tag == "tr":
            self._linha = []
        elif tag in ("td", "th"):
            self._celula = []

    def handle_endtag(self, tag):
        if not self._na_tabela:
            return
        if tag in ("td", "th") and self._celula is not None:
            texto = " ".join("".join(self._celula).split())
            if self._linha is not None:
                self._linha.append(texto)
            self._celula = None
        elif tag == "tr" and self._linha is not None:
            if self._linha:
                if self.cabecalho:
                    self.linhas.append(self._linha)
                else:
                    self.cabecalho = self._linha
            self._linha = None
        elif tag == "table":
            self._na_tabela = False

    def handle_data(self, data):
        if self._celula is not None:
            self._celula.append(data)


def _baixar(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        bruto = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            bruto = gzip.decompress(bruto)
    return bruto.decode("latin-1")


def _para_numero(texto: str) -> float | None:
    """Converte o formato brasileiro do site ("1.234,56", "12,34%") em float.

    Percentuais viram o numero em si: "12,34%" -> 12.34.
    """
    texto = texto.strip().replace("%", "").replace(".", "").replace(",", ".")
    if not texto or texto == "-":
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _montar_registros(html: str, campos: dict[str, str]) -> list[dict]:
    parser = _ParserTabela()
    parser.feed(html)

    # O cabecalho do site tem acentos em latin-1 ja decodificados; casamos por
    # nome normalizado para nao depender de detalhe de acento/espaco.
    def normalizar(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower()
                      .replace("ã", "a").replace("á", "a").replace("â", "a")
                      .replace("é", "e").replace("ê", "e").replace("í", "i")
                      .replace("ó", "o").replace("õ", "o").replace("ú", "u")
                      .replace("ç", "c"))

    mapa = {normalizar(k): v for k, v in campos.items()}
    chaves = [mapa.get(normalizar(c), normalizar(c)) for c in parser.cabecalho]

    registros = []
    for linha in parser.linhas:
        if len(linha) != len(chaves):
            continue
        registro: dict = {}
        for chave, valor in zip(chaves, linha):
            if chave in COLUNAS_TEXTO:
                registro[chave] = valor
            else:
                registro[chave] = _para_numero(valor)
        if registro.get("papel"):
            registros.append(registro)
    return registros


def _caminho_cache(tipo: str) -> Path:
    return DIR_DADOS / f"{tipo}.json"


def carregar(tipo: str, max_idade_horas: float = 12.0, forcar: bool = False) -> tuple[list[dict], str]:
    """Retorna (registros, origem) para tipo em {"acoes", "fiis"}.

    Usa o cache em data/<tipo>.json enquanto ele for mais novo que
    max_idade_horas; caso contrario rebaixa do Fundamentus e regrava.
    """
    if tipo not in ("acoes", "fiis"):
        raise ValueError(f"tipo invalido: {tipo}")

    cache = _caminho_cache(tipo)
    if cache.exists() and not forcar:
        conteudo = json.loads(cache.read_text(encoding="utf-8"))
        idade = time.time() - conteudo["baixado_em_epoch"]
        if idade < max_idade_horas * 3600:
            return conteudo["registros"], f"cache de {conteudo['baixado_em']}"

    url = URL_ACOES if tipo == "acoes" else URL_FIIS
    campos = CAMPOS_ACOES if tipo == "acoes" else CAMPOS_FIIS
    registros = _montar_registros(_baixar(url), campos)
    if not registros:
        raise RuntimeError(f"nenhum registro extraido de {url} (layout do site pode ter mudado)")

    agora = datetime.now(timezone.utc).astimezone()
    DIR_DADOS.mkdir(exist_ok=True)
    cache.write_text(
        json.dumps(
            {
                "fonte": url,
                "baixado_em": agora.strftime("%d/%m/%Y %H:%M"),
                "baixado_em_epoch": time.time(),
                "registros": registros,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return registros, "download novo"
