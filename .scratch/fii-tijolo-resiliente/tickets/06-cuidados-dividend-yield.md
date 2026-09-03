# 06: Cuidados de leitura: DY suspeito, P/VP abaixo de 1, cap rate

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Suggestion only, use whatever model you have to hand.

**What to build:** os cuidados de leitura que eu quero ver na tela no momento em que olho a linha, não depois. DY muito acima da média pode ser cota que caiu, e rendimento de venda de imóvel não é recorrente — o fundo com DY destoante ganha um alerta pedindo para eu investigar **por que** o DY está alto antes de tratar como oportunidade.

O alerta é **informativo e nunca elimina o fundo**: DY alto sozinho não significa fundo ruim. O critério é DY maior que 1,5 vez a mediana do DY do recorte já filtrado, com o múltiplo como constante nomeada, não espalhado pelo código.

Junto disso, dois auxílios de desempate: P/VP abaixo de 1 fica destacado visualmente, para eu bater o olho nos descontados, e o cap rate aparece na tabela ao lado do DY, para eu checar se o rendimento se sustenta no aluguel.

Vacância é coluna de desempate, **não** filtro eliminatório — de propósito. XPML11 aparece hoje com vacância de 91,81%, quase certamente erro ou outra unidade na fonte, e um dado sujo assim não pode derrubar um fundo bom.

**Blocked by:** 02 (Preset `fii-tijolo`).

**Status:** ready-for-agent

- [ ] Fundo com DY acima de 1,5 vez a mediana do recorte filtrado recebe um alerta visual na célula de DY
- [ ] O alerta explica o motivo: a cota pode ter caído, ou o rendimento pode ter vindo de venda de imóvel
- [ ] O alerta não remove o fundo do resultado, em nenhuma circunstância
- [ ] O múltiplo do alerta vive como constante nomeada, num único lugar
- [ ] P/VP abaixo de 1 é destacado visualmente na tabela
- [ ] Vacância média e cap rate aparecem na tabela do preset como colunas de desempate
- [ ] Vacância não elimina nenhum fundo; um teste com vacância absurda (padrão XPML11) confirma que o fundo sobrevive
- [ ] `make test` passa
