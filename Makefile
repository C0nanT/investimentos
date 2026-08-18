# Painel de investimentos — atalhos de operação.
# Uso rápido:  make start   (sobe tudo e abre o painel)

PY      := .venv/bin/python
PORTA   ?= 8000

.DEFAULT_GOAL := ajuda

.PHONY: ajuda venv up sync web start status parar reiniciar logs mongosh limpar-cache reset

ajuda:  ## mostra esta lista de comandos
	@echo "Painel de investimentos — comandos disponíveis:"
	@echo
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-14s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Variável: PORTA=$(PORTA)"

$(PY):
	python3 -m venv .venv
	.venv/bin/pip install --quiet --upgrade pip pymongo

venv: $(PY)  ## cria o ambiente virtual e instala o pymongo

up: $(PY)  ## sobe o container do MongoDB
	docker compose up -d
	@echo "aguardando o MongoDB aceitar conexão…"
	@until docker exec investimentos-mongo mongosh --quiet --eval 'db.runCommand({ping:1}).ok' >/dev/null 2>&1; do sleep 1; done
	@echo "MongoDB pronto."

sync: up  ## baixa os dados do Fundamentus e grava no MongoDB
	$(PY) -m invest.cli sync

web: up  ## sobe o painel no navegador (use PORTA=xxxx)
	$(PY) -m invest.cli web --porta $(PORTA)

start: sync web  ## sobe o banco, atualiza os dados e abre o painel

status: $(PY)  ## estado do container e do banco
	@docker compose ps
	@echo
	@$(PY) -m invest.cli status

parar:  ## para o container (os dados ficam salvos no volume)
	docker compose stop

reiniciar: parar up  ## para e sobe o container de novo

logs:  ## acompanha o log do MongoDB
	docker compose logs -f mongo

mongosh: up  ## abre o shell do MongoDB no banco investimentos
	docker exec -it investimentos-mongo mongosh investimentos

limpar-cache:  ## apaga o cache local (força novo download no próximo sync)
	rm -f data/acoes.json data/fiis.json
	@echo "cache local removido."

reset:  ## APAGA o banco e o volume do Docker (irreversível)
	@printf 'Isso apaga o banco e todo o histórico acumulado. Digite "sim" para confirmar: '; \
	read resposta; [ "$$resposta" = "sim" ] || { echo "cancelado."; exit 1; }
	docker compose down -v
	@echo "volume removido. rode 'make sync' para recriar."
