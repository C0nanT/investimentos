# 03: Módulo de triagem com a interface `Pedido` → `Resultado`

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Sugestão apenas, use o modelo que tiver à mão.

**What to build:** o investidor abre o painel, escolhe um preset, soma critérios avulsos, filtra por setor, liga ou desliga "zeros valem" — e vê exatamente o mesmo resultado de hoje. A diferença é que agora essa triagem existe como um módulo próprio, com uma interface só, e um desenvolvedor consegue exercitá-la montando um pedido direto no teste, sem subir servidor.

O seam é o `Pedido`: um objeto de valor já decodificado, sem lista de strings nem flag `"1"`/`"0"` na interface. Ele carrega tipo, preset, critérios avulsos já convertidos, coluna de ordenação, sentido, "zeros valem", setor e os overrides de taxa e spread. O handler HTTP passa a fazer duas coisas: decodificar a query string em um `Pedido` e serializar o `Resultado` em JSON.

A composição não é redesenhada, é movida. A ordem de decisão continua a mesma: resolver preset → aplicar taxa quando o preset declara taxa base → concatenar critérios do preset com os avulsos → ordenar no banco apenas quando não há ranking → consultar → ranquear e ordenar em memória quando há ranking → montar o resultado.

O contrato HTTP não muda: mesmas rotas, mesmos parâmetros, mesma forma de JSON. `painel.html` não é tocado.

**Blocked by:** 01 (contagem em `db`), 02 (substituto do Mongo)

**Status:** ready-for-human

- [x] Existe um módulo de triagem com uma única interface pública que recebe um pedido e devolve um resultado
- [x] O resultado carrega tipo, total, encontrados, critérios aplicados, descrição, se foi ranqueado, e os registros
- [x] As datas já vêm serializadas como texto no resultado
- [x] O handler HTTP não conhece mais preset, taxa, ranking nem persistência
- [x] O JSON devolvido pelas rotas de consulta é idêntico ao de antes
- [x] Teste: preset aplicado sozinho devolve os papéis esperados
- [x] Teste: critérios avulsos entram depois dos critérios do preset
- [x] Teste: filtro por setor recorta o resultado
- [x] Teste: "zeros valem" ligado e desligado mudam o recorte
- [x] Teste: `total` e `encontrados` são coerentes com o snapshot e com o recorte
- [x] Teste: a descrição do preset aplicado volta no resultado
- [x] Os testes montam o pedido direto, sem HTTP
- [x] `make test` verde
