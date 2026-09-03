# 03: Patrimônio derivado acima de R$ 1 bilhão

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Suggestion only, use whatever model you have to hand.

**What to build:** o preset passa a manter só fundos com patrimônio acima de R$ 1 bilhão, para eu ficar com fundos grandes o bastante para diluir custo e ter liquidez. A tabela de FIIs ganha a coluna **Patrimônio**, e o limite aparece preenchido nos campos mín/máx como em qualquer outro preset, pronto para eu afrouxar ou apertar.

A tabela de FIIs do Fundamentus não traz patrimônio líquido, então o valor é derivado de `valor de mercado ÷ P/VP`. Isso precisa estar claro na descrição da coluna: é número derivado, não dado direto da fonte, e merece margem na interpretação.

Como o critério opera sobre um campo derivado, a filtragem acontece em memória depois da consulta ao Mongo, diferente dos outros presets que empurram tudo para a query.

**Blocked by:** 02 (Preset `fii-tijolo`).

**Status:** ready-for-agent

- [ ] O preset descarta fundo com patrimônio derivado abaixo de R$ 1 bilhão e mantém fundo logo acima
- [ ] A coluna **Patrimônio** aparece na tabela quando o preset está ativo
- [ ] A descrição da coluna deixa explícito que o valor é derivado de valor de mercado dividido por P/VP
- [ ] Fundo sem P/VP ou sem valor de mercado não trava a triagem: o patrimônio fica ausente, não zero
- [ ] O limite de R$ 1 bilhão aparece preenchido nos campos mín/máx e pode ser ajustado na tela
- [ ] **Salvar preset** grava o limite ajustado, como nos demais presets
- [ ] A caixa "considerar zeros" continua funcionando com o preset ativo
- [ ] `make test` passa
