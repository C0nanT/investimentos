# 07: README e verificação do CSV

> **Difficulty:** Light: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Suggestion only, use whatever model you have to hand.

**What to build:** o registro do critério, para eu lembrar meses depois por que o preset é assim, e a confirmação de que consigo levar o resultado para a planilha e para o comparador.

O README ganha o preset `fii-tijolo` na tabela de presets e uma seção descrevendo: os quatro segmentos resilientes e os cinco descartados, o patrimônio mínimo e o fato de ser derivado, os dois critérios de curadoria, a ordenação por custo, e — na mesma linha do que já é feito hoje para vacância física e alavancagem no preset `fii-aula` — **o que fica fora do sistema e por quê**: qualidade da gestora, padrão AAA das lajes, estabilidade da vacância ao longo do tempo, origem do dividendo (aluguel versus venda de ativo) e evolução do preço da cota.

Documentar também o arquivo de curadoria: onde fica, que formato tem, que é mantido à mão e que os valores da semente precisam ser conferidos.

O CSV já exporta todos os campos do documento, então as colunas derivadas devem sair sem trabalho extra — esta fatia confirma isso na prática em vez de assumir.

**Blocked by:** 05 (Painel de avisos), 06 (Cuidados de leitura).

**Status:** ready-for-agent

- [ ] O README lista `fii-tijolo` na tabela de presets, junto dos demais
- [ ] O README descreve os critérios do preset e a ordenação por custo
- [ ] O README explica quais critérios ficam fora do sistema e por quê
- [ ] O README documenta o arquivo de curadoria: localização, formato e manutenção manual
- [ ] O CSV baixado com o preset ativo contém as colunas derivadas: segmento resiliente, patrimônio, anos de bolsa, taxa de adm. e pendências
- [ ] Os fundos do resultado podem ser levados para o modo Comparar existente
- [ ] `make test` passa
