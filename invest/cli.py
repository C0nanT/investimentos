"""Comandos de operação do painel.

    python3 -m invest.cli sync     baixa do Fundamentus e grava no MongoDB
    python3 -m invest.cli web      sobe o painel em http://localhost:8000
    python3 -m invest.cli status   estado do banco

A consulta aos dados é feita no painel web (invest/web.py + invest/painel.html).
"""

from __future__ import annotations

import argparse

from . import db, fundamentus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="invest", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p_sync = sub.add_parser("sync", help="baixa do Fundamentus e grava no MongoDB")
    p_sync.add_argument("--cache", action="store_true",
                        help="usa o cache local em vez de baixar de novo")
    p_sync.add_argument("--empresas", action="store_true",
                        help="força novo download de nome e setor das empresas")

    p_web = sub.add_parser("web", help="sobe o painel em localhost")
    p_web.add_argument("-p", "--porta", type=int, default=8234)
    p_web.add_argument("--sem-navegador", action="store_true")

    sub.add_parser("status", help="mostra o estado do banco")

    args = parser.parse_args(argv)

    if args.comando == "sync":
        for tipo in ("acoes", "fiis"):
            registros, origem = fundamentus.carregar(tipo, forcar=not args.cache)
            if tipo == "acoes":
                empresas, origem_emp = fundamentus.carregar_empresas(
                    [r["papel"] for r in registros],
                    forcar=args.empresas,
                )
                fundamentus.enriquecer(registros, empresas)
                emp = db.gravar_empresas(empresas)
                print(f"empresas: {emp['total']} fichas "
                      f"({emp['com_setor']} com setor, {emp['novos']} novas) — {origem_emp}")
            resumo = db.gravar(tipo, registros)
            print(f"{tipo}: {resumo['total']} papeis gravados "
                  f"({resumo['novos']} novos, {resumo['existentes']} ja conhecidos) — {origem}")
        print(f"historico acumulado: {db.status()['historico']['dias']} dia(s)")
        return 0

    if args.comando == "status":
        info = db.status()
        print(f"mongo: {info['uri']} / banco {info['banco']}")
        for tipo, dados in info["colecoes"].items():
            print(f"  {tipo}: {dados['documentos']} documentos, atualizado em {dados['atualizado_em']}")
        print(f"  historico: {info['historico']['documentos']} documentos "
              f"em {info['historico']['dias']} dia(s)")
        emp = info["empresas"]
        print(f"  empresas: {emp['documentos']} fichas, {emp['setores']} setores, "
              f"atualizado em {emp['atualizado_em']}")
        return 0

    if args.comando == "web":
        from . import web
        web.servir(args.porta, abrir_navegador=not args.sem_navegador)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
