# 06: Bordas da triagem sob teste

> **Difficulty:** Light: **suggested model:** Haiku (Claude Code) / Composer ou outro modelo rápido e barato (Cursor). Sugestão apenas, use o modelo que tiver à mão.

**What to build:** um link antigo com um preset que não existe mais continua devolvendo uma triagem em vez de erro, um critério mal escrito diz qual é o formato aceito, e a data de atualização chega ao painel como texto.

Testes que espelham a montagem já criada no ticket 03.

**Blocked by:** 03 (módulo de triagem)

**Status:** ready-for-human

- [x] Teste: preset inexistente no pedido cai para triagem sem preset, sem erro e sem descrição
- [x] Teste: critério avulso mal escrito falha com mensagem que mostra o formato aceito
- [x] Teste: campos de data nos registros voltam como texto no resultado
- [x] Teste: pedido sem preset e sem critérios devolve o snapshot inteiro
- [x] `make test` verde
