# 04: Override de taxa e spread sob teste

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Sugestão apenas, use o modelo que tiver à mão.

**What to build:** o investidor ajusta a taxa base e o spread na tela e o DY mínimo do preset da aula é recalculado; presets que não declaram taxa base seguem intocados. Hoje isso funciona mas nada garante que continue funcionando.

**Blocked by:** 03 (módulo de triagem)

**Status:** ready-for-agent

- [ ] Teste: taxa base e spread no pedido recalculam o DY mínimo do preset da aula, deixando os demais critérios como estavam
- [ ] Teste: o máximo do DY não é alterado pelo recálculo
- [ ] Teste: preset sem taxa base declarada ignora o override
- [ ] Teste: sem override no pedido, valem a taxa e o spread guardados no preset
- [ ] Teste: os critérios que voltam no resultado refletem o DY mínimo já recalculado
- [ ] `make test` verde
