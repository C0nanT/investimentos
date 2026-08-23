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

Toda a consulta acontece no painel web. O terminal serve só para operar o
serviço. `make` sozinho lista os comandos:

| Comando | O que faz |
|---|---|
| `make start` | tudo de uma vez: banco + sync + painel |
| `make up` | só sobe o MongoDB (espera ele aceitar conexão) |
| `make sync` | baixa do Fundamentus e grava no banco |
| `make web` | painel em http://localhost:8000 (`make web PORTA=9000`) |
| `make status` | estado do container e do banco |
| `make mongosh` | shell do MongoDB |
| `make parar` | para o container (dados preservados) |
| `make limpar-cache` | apaga o cache local |
| `make reset` | apaga banco e volume (pede confirmação) |

Sem Make, os comandos equivalentes:

```bash
docker compose up -d
python3 -m venv .venv && .venv/bin/pip install pymongo
.venv/bin/python -m invest.cli sync      # atualiza os dados
.venv/bin/python -m invest.cli web       # sobe o painel
.venv/bin/python -m invest.cli status    # estado do banco
```

Esses três são os únicos comandos que existem: filtrar, ordenar e exportar é
tudo pelo painel.

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

1. **Download** — a tabela de ações, a de FIIs, a listagem de empresas e a ficha
   de cada papel (nome, setor, subsetor), gravadas em `data/*.json`.
2. **Upsert nas coleções `acoes`/`fiis`** — um documento por papel, sempre
   sobrescrito com o dado mais recente. A coleção nunca cresce, só se atualiza.
3. **Carimbo no `historico`** — um documento por papel **por dia**
   (`{papel, data}` é chave única). Rodar o sync cinco vezes no mesmo dia
   sobrescreve o registro daquele dia; rodar amanhã cria uma nova camada.
   É daí que sai, com o tempo, a resposta para "esse DY se repete ou foi um
   ano fora da curva?".

O cache de 12h em `data/{acoes,fiis}.json` guarda o último download bruto e serve de
rede de segurança (`sync --cache` regrava sem internet). Nome, setor e subsetor das
empresas ficam em `data/empresas.json` por **30 dias** (a classificação quase não
muda). Na primeira vez o sync baixa a ficha de cada papel — leva cerca de um ou dois
minutos. `sync --empresas` força essa atualização.
O `sync` normal e o botão do painel sempre ignoram o cache de indicadores e buscam
dados novos; empresas só rebaixam se o cache estiver velho, incompleto ou sem setor.
Use `make limpar-cache` para descartá-los.

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
| `acoes` | 1 documento por ação, sempre o dado mais recente (chave única `papel`), com nome da empresa e setor |
| `fiis` | 1 documento por FII |
| `empresas` | 1 documento por papel: nome comercial, razão social, setor e subsetor (atualiza no máximo a cada 30 dias) |
| `historico` | 1 documento por papel por dia — permite ver depois se o DY se repete ou foi evento isolado |
| `presets` | filtros predefinidos do painel (semente do código; edição na página sobrescreve) |

Consultas diretas, se quiser:

```bash
docker exec -it investimentos-mongo mongosh investimentos
> db.acoes.find({ dy: { $gte: 6 }, pvp: { $lte: 2 }, roe: { $gte: 15 } }).sort({ dy: -1 }).limit(10)
> db.historico.find({ papel: "TAEE11" }).sort({ data: -1 })
```

Configurável por `MONGO_URI` e `MONGO_DB`.

## O painel

Tudo acontece em http://localhost:8000:

- abas **Ações** e **FIIs**;
- menu de **presets** (os limites do preset aparecem nos campos, prontos para
  afrouxar ou apertar; **Salvar preset** grava esses limites no banco e passa a
  ser o novo original daquele preset);
- filtro por **setor** (ações), para comparar um papel com os pares; clicar no
  setor na tabela aplica o mesmo recorte;
- campos de **mín/máx** para cada indicador;
- **ordenação** clicando no título da coluna;
- caixa **considerar zeros** (veja abaixo);
- **Baixar CSV** com o resultado atual — todos os campos do documento, não só
  as colunas visíveis, prontos para o LibreOffice/Excel;
- **Atualizar do Fundamentus**, que refaz o sync sem sair da tela;
- o papel é um link para a ficha completa no Fundamentus.

Dá para salvar um link direto do preset:
`http://localhost:8000/?tipo=fiis&preset=fii-aula`.

## Triagem da aula (FIIs)

Preset `fii-aula`, seguindo `notes/aula-live-geracao-dividendos.md`:

1. liquidez acima de R$ 2 milhões;
2. DY no máximo 18% e com pelo menos 1% de spread sobre o IPCA+ mais curto do
   Tesouro (padrão 8,17% → DY mínimo 9,17%);
3. P/VP entre 0,8 e 1,2;
4. rank de DY (maior primeiro) + rank de P/VP (menor primeiro) = **nota**, e a
   nota ordena o resultado (menor = melhor colocação combinada). Empates
   recebem o mesmo rank.

Escolha o preset **fii-aula** na aba FIIs. Ele mostra dois campos extras,
**IPCA+** e **spread**, que recalculam o DY mínimo na hora — 1% para fundos de
ancoragem, 3% para crescimento, 5% para os com risco, como a aula orienta.
Confira a taxa atual em [tesourodireto.com.br](https://www.tesourodireto.com.br/produtos/dados-sobre-titulos/rendimento-dos-titulos)
— o valor 8,17% é o que estava na anotação, não é atualizado sozinho.

O que a aula pede e o Fundamentus **não** fornece: vacância física e financeira
separadas (só há vacância média) e alavancagem bruta (passivos/ativos). Esses
dois ficam para a análise individual, no relatório gerencial do fundo.

## Presets

| Preset | Tipo | Ideia |
|---|---|---|
| `dividendos` | ações | DY 6–20%, P/L ≤ 15, ROE ≥ 10%, dív.líq/PL ≤ 2, liquidez ≥ R$1M |
| `valor` | ações | P/VP ≤ 1,5, P/L ≤ 10, EV/EBIT ≤ 8, ROIC ≥ 10% |
| `qualidade` | ações | ROE ≥ 15%, ROIC ≥ 12%, margem líq. ≥ 8%, baixa alavancagem |
| `fii-renda` | FIIs | DY 8–20%, P/VP 0,5–1,05, liquidez ≥ R$500k, vacância ≤ 15% |
| `fii-tijolo-desconto` | FIIs | P/VP ≤ 0,95, cap rate ≥ 6%, com imóveis |
| `fii-aula` | FIIs | a triagem descrita acima, com rank e nota |

Os valores iniciais vêm de `invest/filtros.py` e são gravados na coleção `presets`
na primeira vez. Depois disso o banco manda: ajuste os mín/máx na página e clique
**Salvar preset** para sobrescrever aquele preset. Um preset já salvo nunca é
restaurado pelo código.

## O que é filtrado (e o que não é)

**Nada é descartado na coleta.** As 994 ações e os 560 FIIs do Fundamentus
entram no MongoDB com todas as colunas, e a página sem preset mostra os 994 e
os 560. Todo filtro acontece na consulta, é seu e é reversível.

A única regra automática: **um campo com filtro não pode valer 0**, porque no
Fundamentus zero quase sempre significa dado ausente — filtrar
`vacância ≤ 10%` sem essa regra traria 486 FIIs, sendo 412 deles fundos de
papel que simplesmente não têm vacância. A caixa **"considerar zeros"** no
painel desliga a regra quando você quiser o dado cru.

## Cuidados de leitura

- O teto de DY nos presets existe de propósito: yield acima de ~20% quase
  sempre é dividendo extraordinário não recorrente.
- No Fundamentus, `0` normalmente significa **dado indisponível**, não zero
  real. Bancos aparecem com ROIC e margens zeradas.
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
invest/cli.py           comandos de operação (sync, web, status)
docker-compose.yml      MongoDB 7
notes/                  anotações de estudo
```

O cache em `data/*.json` guarda o último download bruto; o painel sempre lê do
MongoDB.
