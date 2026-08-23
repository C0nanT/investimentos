# 02: Substituto do Mongo em memória, com a regra do zero sob teste

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Sugestão apenas, use o modelo que tiver à mão.

**What to build:** um desenvolvedor consegue rodar uma consulta ao snapshot de ações ou FIIs sem Mongo nenhum, com um conjunto pequeno e fixo de papéis, e verificar que a consulta se comporta como no banco de verdade.

Isso fecha a lacuna que já existe hoje: a regra "campo com critério não pode valer 0, porque no Fundamentus zero quase sempre significa dado ausente" nunca foi exercitada por teste.

Arte prévia: `tests/test_presets.py` já substitui uma coleção do Mongo por uma coleção em memória via `unittest.mock.patch`. Seguir o mesmo padrão, generalizando o suficiente para as coleções `acoes` e `fiis`.

Prefactor do ticket 03: é o substituto que permite testar a triagem sem socket e sem container.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Existe um substituto em memória reutilizável pelos testes, com registros fixos de ações e de FIIs
- [x] Os registros de exemplo incluem casos com campo em 0 e campo ausente
- [x] Teste: critério de faixa (mínimo, máximo, os dois) devolve só os papéis dentro da faixa
- [x] Teste: com a regra padrão, papel com 0 no campo filtrado fica de fora
- [x] Teste: com "zeros valem" ligado, o mesmo papel entra
- [x] Teste: filtro por igualdade (setor) recorta corretamente
- [x] Teste: ordenação crescente e decrescente
- [x] Os testes rodam sem rede e sem Mongo, por `make test`
