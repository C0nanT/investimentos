# Investimentos — triagem de ações e FIIs

Ferramenta de linha de comando para puxar indicadores fundamentalistas da B3 e
filtrar uma lista curta de papéis para analisar com calma.

Dados do Fundamentus -> MongoDB -> painel HTML local.

## Fonte dos dados

[Fundamentus](https://www.fundamentus.com.br) — uma requisição traz a tabela
inteira do mercado, já com os múltiplos calculados:

- **Ações** (~990 papéis): cotação, P/L, P/VP, PSR, DY, P/EBIT, EV/EBIT,
  EV/EBITDA, margens (bruta, EBIT, líquida), liquidez corrente, ROIC, ROE,
  liquidez 2 meses, patrimônio líquido, dívida líquida/patrimônio, CAGR de
  receita 5 anos.
- **FIIs** (~560 fundos): cotação, FFO yield, DY, P/VP, valor de mercado,
  liquidez, qtd de imóveis, preço/m², aluguel/m², cap rate, vacância média.

Os dados ficam em cache em `data/{acoes,fiis}.json` por 12h; `--atualizar`
força novo download.

Alternativas avaliadas: [brapi.dev](https://brapi.dev/docs) (API JSON oficial,
mas fundamentos completos e FIIs só nos planos pagos), yfinance (cotação boa,
fundamento BR fraco), B3/CVM dados abertos (bruto, exige calcular os
indicadores). O brapi é o complemento natural quando for preciso histórico de
cotação ou série de dividendos por papel.

## Como rodar

```bash
make start        # cria o venv, sobe o Mongo, atualiza os dados e abre o painel
```

`make` sozinho lista todos os comandos:

| Comando | O que faz |
|---|---|
| `make start` | tudo de uma vez: banco + sync + painel |
| `make up` | só sobe o MongoDB (espera ele aceitar conexão) |
| `make sync` | baixa do Fundamentus e grava no banco |
| `make web` | painel em http://localhost:8000 (`make web PORTA=9000`) |
| `make status` | estado do container e do banco |
| `make acoes` / `make fiis` | lista no terminal (`make acoes PRESET=valor`) |
| `make csv` | exporta a seleção para `data/*.csv` |
| `make mongosh` | shell do MongoDB |
| `make parar` | para o container (dados preservados) |
| `make limpar-cache` | apaga o cache local |
| `make reset` | apaga banco e volume (pede confirmação) |

Sem Make, os comandos equivalentes:

```bash
docker compose up -d
python3 -m venv .venv && .venv/bin/pip install pymongo
.venv/bin/python -m invest.cli sync
.venv/bin/python -m invest.cli web
```

O painel tem abas Ações/FIIs, os presets em um menu, campos de mín/máx para
cada indicador, ordenação clicando na coluna, link para a página do papel no
Fundamentus e um botão "Atualizar do Fundamentus" que refaz o sync.

## Como os dados são atualizados

Nada atualiza sozinho — **todo sync é disparado por você**. O caminho é sempre:

```
Fundamentus  →  cache local (data/*.json, 12h)  →  MongoDB  →  painel
```

Três formas de disparar:

| Forma | O que faz |
|---|---|
| `make sync` | força download novo do Fundamentus e grava no Mongo |
| Botão **"Atualizar do Fundamentus"** no painel | o mesmo, sem sair da tela |
| `invest.cli sync --cache` | regrava no Mongo a partir do cache, sem acessar a internet |

O que acontece em cada sync:

1. **Download** — duas requisições (ações e FIIs) que trazem o mercado inteiro,
   e o resultado é gravado em `data/*.json`.
2. **Upsert nas coleções `acoes`/`fiis`** — um documento por papel, sempre
   sobrescrito com o dado mais recente. A coleção nunca cresce, só se atualiza.
3. **Carimbo no `historico`** — um documento por papel **por dia**
   (`{papel, data}` é chave única). Rodar o sync cinco vezes no mesmo dia
   sobrescreve o registro daquele dia; rodar amanhã cria uma nova camada.
   É daí que sai, com o tempo, a resposta para "esse DY se repete ou foi um
   ano fora da curva?".

Sobre o cache de 12h: ele só vale para a CLI lendo sem `--banco`
(`invest.cli acoes`). O `sync` e o botão do painel sempre ignoram o cache e
buscam dados novos. Use `make limpar-cache` para descartá-lo.

Frequência que faz sentido: o Fundamentus recalcula os múltiplos com o preço
do fechamento, então **uma vez por dia, depois do pregão, é suficiente** —
balanços só mudam a cada trimestre. Rodar de hora em hora não traz dado novo.

Se quiser automatizar depois, um cron diário resolve:

```cron
0 20 * * 1-5 make sync >> data/sync.log 2>&1
```

## Banco de dados

MongoDB 7 em container (`docker-compose.yml`), banco `investimentos`:

| Coleção | Conteúdo |
|---|---|
| `acoes` | 1 documento por ação, sempre o dado mais recente (chave única `papel`) |
| `fiis` | 1 documento por FII |
| `historico` | 1 documento por papel por dia — permite ver depois se o DY se repete ou foi evento isolado |

Consultas diretas, se quiser:

```bash
docker exec -it investimentos-mongo mongosh investimentos
> db.acoes.find({ dy: { $gte: 6 }, pvp: { $lte: 2 }, roe: { $gte: 15 } }).sort({ dy: -1 }).limit(10)
> db.historico.find({ papel: "TAEE11" }).sort({ data: -1 })
```

Configurável por `MONGO_URI` e `MONGO_DB`.

## Uso pela linha de comando

```bash
.venv/bin/python -m invest.cli status         # estado do banco
.venv/bin/python -m invest.cli acoes --banco --preset dividendos   # lê do Mongo
python3 -m invest.cli presets                  # lista os presets prontos
python3 -m invest.cli acoes --preset dividendos
python3 -m invest.cli fiis  --preset fii-renda
python3 -m invest.cli acoes --campos           # todos os campos filtráveis

# critérios livres
python3 -m invest.cli acoes -f "dy>=6" -f "pvp<=2" -f "roe>=15" --ordenar roe
python3 -m invest.cli acoes -f "pl=5:15" -f "div_liq_patrim<=1" -n 0

# preset + ajuste + exportação
python3 -m invest.cli fiis --preset fii-renda -f "pvp<=0.9" --csv data/selecao.csv
```

Sintaxe de filtro: `campo>=valor`, `campo<=valor`, `campo=min:max`.
Percentuais são o número em si (`dy>=6` = 6%).

## Presets

| Preset | Tipo | Ideia |
|---|---|---|
| `dividendos` | ações | DY 6–20%, P/L ≤ 15, ROE ≥ 10%, dív.líq/PL ≤ 2, liquidez ≥ R$1M |
| `valor` | ações | P/VP ≤ 1,5, P/L ≤ 10, EV/EBIT ≤ 8, ROIC ≥ 10% |
| `qualidade` | ações | ROE ≥ 15%, ROIC ≥ 12%, margem líq. ≥ 8%, baixa alavancagem |
| `fii-renda` | FIIs | DY 8–20%, P/VP 0,5–1,05, liquidez ≥ R$500k, vacância ≤ 15% |
| `fii-tijolo-desconto` | FIIs | P/VP ≤ 0,95, cap rate ≥ 6%, com imóveis |

Editar os presets: `invest/filtros.py`.

## Cuidados de leitura

- O teto de DY nos presets existe de propósito: yield acima de ~20% quase
  sempre é dividendo extraordinário não recorrente.
- No Fundamentus, `0` normalmente significa **dado indisponível**, não zero
  real — por isso um campo zerado reprova critérios de mínimo. Bancos, por
  exemplo, aparecem com ROIC e margens zeradas.
- FIIs de papel (CRI) aparecem com cap rate, vacância e qtd de imóveis em zero:
  eles não têm imóvel.
- A triagem é ponto de partida, não recomendação. Múltiplo baixo com frequência
  é armadilha de valor.

## Estrutura

```
invest/fundamentus.py   download, parsing e cache local
invest/db.py            MongoDB: gravação, índices, consultas e histórico
invest/web.py           servidor local + API JSON
invest/painel.html      página do painel
invest/filtros.py       critérios, presets e ordenação
invest/cli.py           interface de linha de comando
docker-compose.yml      MongoDB 7
notes/                  anotações de estudo
```

Sem `--banco`, a CLI lê o cache em `data/*.json` e funciona mesmo com o
container desligado.
