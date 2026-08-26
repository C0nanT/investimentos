# 05: Ranking e ordenação por nota sob teste

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Sugestão apenas, use o modelo que tiver à mão.

**What to build:** o investidor roda o preset da aula e confia na nota: o rank de DY e o rank de P/VP são calculados só entre os fundos que passaram na triagem, empates recebem a mesma posição, quem não tem dado fica sem nota, e o primeiro da lista é o melhor colocado.

**Blocked by:** 03 (módulo de triagem)

**Status:** ready-for-human

- [x] Teste: a nota é calculada apenas dentro do recorte filtrado, não sobre o mercado inteiro
- [x] Teste: papéis com o mesmo valor num campo ranqueado recebem a mesma posição
- [x] Teste: papel sem valor num campo ranqueado fica sem nota
- [x] Teste: ordenar por nota é crescente, independentemente do sentido pedido
- [x] Teste: trocar a coluna de ordenação preserva os ranks já calculados
- [x] Teste: o resultado sinaliza que foi ranqueado, para o painel decidir se mostra as colunas de rank e nota
- [x] Teste: pedido sem ranking delega a ordenação ao banco e respeita o sentido pedido
- [x] `make test` verde
