# 02: Preset `fii-tijolo` com recorte por segmento resiliente

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Suggestion only, use whatever model you have to hand.

**What to build:** escolher `fii-tijolo` no menu de presets da aba FIIs e ver só fundos de tijolo em segmento que aguenta ciclo ruim: Logística, Shopping, Lajes corporativas AAA e Renda urbana. Hotel, Hospital, Residencial, Desenvolvimento e Fundo de Fundos somem do resultado. Uma coluna **Segmento resiliente**, separada do segmento cru do Fundamentus, mostra em qual bucket cada fundo caiu e se essa classificação veio da curadoria ou de inferência.

O ponto crítico: o Fundamentus classifica HGLG11 e KNRI11 como `Multicategoria` e HGRU11 como `Outros`. Tratar o campo `segmento` como verdade derruba justamente os fundos que eu quero. Por isso a curadoria tem precedência sobre a inferência.

Ordem de decisão da classificação:

1. ticker com `segmento_resiliente` na curadoria: usa esse, origem `curadoria` — a curadoria sempre vence;
2. senão, o tipo inferido precisa ser `Fundo de Tijolo`; Papel, FOF, Desenvolvimento, Misto e Outro viram "Outro" e são descartados;
3. senão, mapeia o segmento do Fundamentus: `Logística` → Logística; `Shoppings` → Shopping; `Lajes Corporativas` e `Escritórios` → Lajes corporativas AAA; `Varejo` → Renda urbana; `Hotel`, `Hospital`, `Residencial` → "Outro";
4. `Multicategoria` e `Outros` sem curadoria: "Outro", origem `inferido`. Fundo bom não catalogado não entra sozinho — a curadoria é o mecanismo de resgate.

A classificação é uma função pura sobre o registro mais a curadoria, testável sem banco. Os campos derivados não são gravados na coleção: o snapshot do Fundamentus continua cru.

**Blocked by:** 01 (Curadoria de FIIs).

**Status:** ready-for-agent

- [ ] O preset `fii-tijolo` aparece no menu de presets da aba FIIs e filtra ao ser escolhido
- [ ] O link direto `/?tipo=fiis&preset=fii-tijolo` abre o painel já no preset
- [ ] HGLG11, XPML11, KNRI11, HGRU11 e PVBI11 sobrevivem ao preset — teste de regressão explícito
- [ ] Fundo de Hotel, Hospital, Residencial, Desenvolvimento e FOF são descartados, um caso de teste por tipo
- [ ] A coluna **Segmento resiliente** aparece na tabela apenas quando este preset está ativo
- [ ] A tela distingue classificação vinda de curadoria de classificação inferida
- [ ] Corrigir o segmento de um fundo editando o arquivo de curadoria muda o resultado sem alteração de código
- [ ] A classificação é uma função pura, testada com dicionários literais, cobrindo a precedência dos quatro passos
- [ ] Nenhum campo derivado é gravado nas coleções `fiis` ou `historico`; o `sync` não muda
- [ ] Um teste exercita a triagem completa do preset com o dublê de Mongo em memória
- [ ] `make test` passa
