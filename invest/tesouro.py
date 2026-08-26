"""Taxa do Tesouro IPCA+ mais curto, para uso como base de spread na triagem de FIIs.

Fonte: dataset publico "Precos e Taxas dos Titulos Publicos" do Tesouro
Transparente (governo federal, sem autenticacao). O endpoint antigo em
tesourodireto.com.br/json/... foi descontinuado (HTTP 410); este CSV e
atualizado diariamente e e a fonte oficial usada pelo proprio site.
"""

from __future__ import annotations

import csv
import io
import urllib.request
from datetime import datetime

URL_PRECO_TAXA = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
)

TITULO_ALVO = "Tesouro IPCA+"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def _baixar_csv() -> str:
    req = urllib.request.Request(URL_PRECO_TAXA, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def _para_numero(texto: str) -> float | None:
    texto = texto.strip().replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _para_data(texto: str) -> datetime | None:
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        return None


def obter_taxa_ipca() -> dict:
    """Baixa o CSV oficial e devolve a taxa de compra do Tesouro IPCA+ de
    vencimento mais curto, na data-base mais recente disponivel.

    Retorna {"taxa": float, "vencimento": "dd/mm/aaaa", "data_base": "dd/mm/aaaa"}.
    Lanca RuntimeError se o titulo nao for encontrado (layout do dataset mudou).
    """
    bruto = _baixar_csv()
    leitor = csv.DictReader(io.StringIO(bruto), delimiter=";")

    linhas = []
    for linha in leitor:
        if linha.get("Tipo Titulo") != TITULO_ALVO:
            continue
        data_base = _para_data(linha.get("Data Base", ""))
        vencimento = _para_data(linha.get("Data Vencimento", ""))
        taxa = _para_numero(linha.get("Taxa Compra Manha", ""))
        if data_base and vencimento and taxa is not None:
            linhas.append((data_base, vencimento, taxa))

    if not linhas:
        raise RuntimeError(f"nenhuma linha de '{TITULO_ALVO}' encontrada no CSV do Tesouro Transparente")

    data_base_mais_recente = max(l[0] for l in linhas)
    do_dia = [l for l in linhas if l[0] == data_base_mais_recente]
    escolhida = min(do_dia, key=lambda l: l[1])

    return {
        "taxa": escolhida[2],
        "vencimento": escolhida[1].strftime("%d/%m/%Y"),
        "data_base": data_base_mais_recente.strftime("%d/%m/%Y"),
    }
