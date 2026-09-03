# 04: Anos de bolsa, taxa de administração e ordenação por custo

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Suggestion only, use whatever model you have to hand.

**What to build:** os dois critérios que dependem só da minha curadoria entram no preset. Fundo precisa ter mais de 5 anos de bolsa, para eu ver que já atravessou pelo menos um ciclo, e taxa de administração de até 1,1% ao ano, para eu não pagar caro por gestão de tijolo. O resultado passa a vir **ordenado pela taxa de administração, da menor para a maior** — custo é o critério que eu mais uso para decidir entre dois fundos parecidos. A tabela ganha as colunas **Anos de bolsa**, **Taxa de adm.** e **Gestora**.

A regra que inverte o padrão do projeto e merece atenção: **dado de curadoria ausente não elimina o fundo**. Sem taxa cadastrada, sem ano de IPO ou sem gestora, o fundo passa e acumula uma pendência ("a verificar") que a fatia 05 transforma em selo e aviso. Motivo: a curadoria começa incompleta e um filtro estrito esconderia candidatos que eu ainda não cataloguei. A regra geral do projeto ("campo com filtro não pode valer 0") continua valendo para os campos vindos do Fundamentus.

Anos de bolsa saem de `ano corrente menos ano de IPO`. Fundo sem taxa cadastrada vai para o fim da ordenação por custo, para não parecer barato só por falta de dado.

**Blocked by:** 02 (Preset `fii-tijolo`).

**Status:** ready-for-agent

- [ ] O preset descarta fundo com 5 anos de bolsa ou menos, quando o ano de IPO está cadastrado
- [ ] O preset descarta fundo com taxa de administração acima de 1,1% ao ano, quando a taxa está cadastrada
- [ ] Fundo sem taxa de administração cadastrada **passa** no preset e chega com a pendência correspondente — teste próprio, por inverter o padrão do projeto
- [ ] Fundo sem ano de IPO cadastrado passa e acumula a pendência de anos de bolsa
- [ ] O resultado vem ordenado por taxa de administração crescente, com os fundos sem taxa no fim
- [ ] As colunas **Anos de bolsa**, **Taxa de adm.** e **Gestora** aparecem na tabela quando o preset está ativo
- [ ] Cada fundo carrega a lista de pendências acumuladas, pronta para a fatia seguinte consumir
- [ ] Os limites de 5 anos e 1,1% aparecem nos campos mín/máx e podem ser ajustados e salvos
- [ ] `make test` passa
