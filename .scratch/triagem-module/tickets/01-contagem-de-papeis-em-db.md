# 01: Contagem de papéis sai do handler e vira interface de `db`

> **Difficulty:** Light: **suggested model:** Haiku (Claude Code) / Composer ou outro modelo rápido e barato (Cursor). Sugestão apenas, use o modelo que tiver à mão.

**What to build:** o painel continua mostrando "X de Y papéis" exatamente como hoje, mas a contagem passa a ser pedida ao módulo de persistência em vez de o handler HTTP abrir o cliente Mongo por conta própria. Nada muda na tela.

Prefactor do ticket 03: enquanto o handler souber acessar o banco direto, a triagem não tem como levar essa responsabilidade junto.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] O módulo de persistência expõe uma contagem de documentos por tipo (`acoes`, `fiis`)
- [x] O handler das rotas de consulta não referencia mais o cliente Mongo diretamente
- [x] O campo `total` do JSON continua com o mesmo valor de antes
- [x] `make test` verde
