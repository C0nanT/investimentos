"""CLI de triagem: filtra acoes e FIIs por indicadores fundamentalistas.

Exemplos:
    python3 -m invest.cli sync                 # baixa e grava no MongoDB
    python3 -m invest.cli web                  # abre o painel no navegador
    python3 -m invest.cli presets
    python3 -m invest.cli acoes --preset dividendos
    python3 -m invest.cli acoes -f "dy>=6" -f "pvp<=2" -f "roe>=15" --ordenar dy
    python3 -m invest.cli fiis --preset fii-renda --csv data/selecao-fiis.csv
"""

from __future__ import annotations

import argparse
import csv
import sys

from . import filtros, fundamentus

COLUNAS_PADRAO = {
    "acoes": ["papel", "cotacao", "dy", "pl", "pvp", "roe", "roic",
              "margem_liquida", "div_liq_patrim", "cagr_receita_5a", "liquidez_2meses"],
    "fiis": ["papel", "segmento", "cotacao", "dy", "pvp", "cap_rate",
             "vacancia_media", "qtd_imoveis", "liquidez"],
}

PERCENTUAIS = fundamentus.COLUNAS_PERCENTUAIS


def formatar(chave: str, valor) -> str:
    if valor is None:
        return "-"
    if isinstance(valor, str):
        return valor[:22]
    if chave in PERCENTUAIS:
        return f"{valor:.1f}%"
    if abs(valor) >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M"
    if abs(valor) >= 1_000:
        return f"{valor / 1_000:.1f}k"
    return f"{valor:.2f}"


def imprimir_tabela(registros: list[dict], colunas: list[str]) -> None:
    linhas = [[formatar(c, r.get(c)) for c in colunas] for r in registros]
    larguras = [max(len(c), *(len(l[i]) for l in linhas)) if linhas else len(c)
                for i, c in enumerate(colunas)]
    print("  ".join(c.upper().ljust(w) for c, w in zip(colunas, larguras)))
    print("  ".join("-" * w for w in larguras))
    for linha in linhas:
        print("  ".join(v.ljust(w) for v, w in zip(linha, larguras)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="invest", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("presets", help="lista os presets disponiveis")
    sub.add_parser("status", help="mostra o estado do banco")

    p_sync = sub.add_parser("sync", help="baixa do Fundamentus e grava no MongoDB")
    p_sync.add_argument("--cache", action="store_true",
                        help="usa o cache local em vez de rebaixar")

    p_web = sub.add_parser("web", help="sobe o painel HTML em localhost")
    p_web.add_argument("-p", "--porta", type=int, default=8000)
    p_web.add_argument("--sem-navegador", action="store_true")

    for tipo in ("acoes", "fiis"):
        p = sub.add_parser(tipo, help=f"filtra {tipo}")
        p.add_argument("--preset", choices=[k for k, v in filtros.PRESETS.items() if v["tipo"] == tipo])
        p.add_argument("-f", "--filtro", action="append", default=[], metavar="EXPR",
                       help='criterio extra, ex: "dy>=6", "pvp<=1.2", "pl=5:15"')
        p.add_argument("--ordenar", metavar="CAMPO", help="campo de ordenacao")
        p.add_argument("--crescente", action="store_true", help="ordena do menor para o maior")
        p.add_argument("-n", "--limite", type=int, default=30, help="quantas linhas mostrar (0 = todas)")
        p.add_argument("--colunas", help="lista separada por virgula")
        p.add_argument("--csv", metavar="ARQUIVO", help="salva o resultado em CSV")
        p.add_argument("--atualizar", action="store_true", help="ignora o cache e rebaixa do Fundamentus")
        p.add_argument("--campos", action="store_true", help="so lista os campos disponiveis e sai")

    for p in (sub.choices["acoes"], sub.choices["fiis"]):
        p.add_argument("--banco", action="store_true",
                       help="consulta o MongoDB em vez do cache local")

    args = parser.parse_args(argv)

    if args.comando == "sync":
        from . import db
        for tipo in ("acoes", "fiis"):
            registros, origem = fundamentus.carregar(tipo, forcar=not args.cache)
            resumo = db.gravar(tipo, registros)
            print(f"{tipo}: {resumo['total']} papeis gravados "
                  f"({resumo['novos']} novos, {resumo['existentes']} ja conhecidos) — {origem}")
        print(f"historico acumulado: {db.status()['historico']['dias']} dia(s)")
        return 0

    if args.comando == "status":
        from . import db
        info = db.status()
        print(f"mongo: {info['uri']} / banco {info['banco']}")
        for tipo, dados in info["colecoes"].items():
            print(f"  {tipo}: {dados['documentos']} documentos, atualizado em {dados['atualizado_em']}")
        print(f"  historico: {info['historico']['documentos']} documentos "
              f"em {info['historico']['dias']} dia(s)")
        return 0

    if args.comando == "web":
        from . import web
        web.servir(args.porta, abrir_navegador=not args.sem_navegador)
        return 0

    if args.comando == "presets":
        for nome, preset in filtros.PRESETS.items():
            criterios = " ".join(
                f"{c}{'>=' + str(mi) if mi is not None else ''}{'<=' + str(ma) if ma is not None else ''}"
                for c, mi, ma in preset["criterios"])
            print(f"{nome:22} [{preset['tipo']}] {preset['descricao']}\n{'':22} {criterios}\n")
        return 0

    tipo = args.comando
    if args.banco:
        from . import db
        registros = db.consultar(tipo)
        info = db.status()["colecoes"][tipo]
        origem = f"MongoDB, atualizado em {info['atualizado_em']}"
    else:
        registros, origem = fundamentus.carregar(tipo, forcar=args.atualizar)

    if args.campos:
        print(f"campos de {tipo}:")
        for chave in registros[0]:
            print(f"  {chave}")
        return 0

    criterios = []
    ordenar_por, crescente = args.ordenar, args.crescente
    if args.preset:
        preset = filtros.PRESETS[args.preset]
        criterios += preset["criterios"]
        ordenar_por = ordenar_por or preset["ordenar_por"]
        crescente = crescente or preset.get("crescente", False)
    try:
        criterios += [filtros.parse_criterio(e) for e in args.filtro]
    except ValueError as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2

    selecao = filtros.aplicar(registros, criterios)
    if ordenar_por:
        selecao = filtros.ordenar(selecao, ordenar_por, crescente)

    colunas = args.colunas.split(",") if args.colunas else COLUNAS_PADRAO[tipo]
    recorte = selecao if args.limite == 0 else selecao[:args.limite]

    print(f"# {tipo}: {len(selecao)} de {len(registros)} passaram no filtro ({origem})")
    if criterios:
        print("# criterios: " + ", ".join(
            f"{c} em [{mi if mi is not None else '-inf'}, {ma if ma is not None else '+inf'}]"
            for c, mi, ma in criterios))
    print()
    if not recorte:
        print("nenhum papel passou. afrouxe algum criterio.")
        return 0
    imprimir_tabela(recorte, colunas)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as saida:
            escritor = csv.DictWriter(saida, fieldnames=list(selecao[0].keys()))
            escritor.writeheader()
            escritor.writerows(selecao)
        print(f"\n{len(selecao)} linhas salvas em {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
