# Módulo de Triagem

Status: ready-for-agent

## Problem Statement

A triagem — pegar um preset, aplicar os critérios sobre o snapshot de ações ou FIIs,
calcular ranking e devolver os papéis ordenados — é a razão de existir do painel.
Hoje ela só existe dentro de um método do handler HTTP.

Consequências que o usuário sente:

- Não dá para conferir se um preset devolve o que deveria sem subir o servidor,
  abrir o navegador e olhar a tabela.
- Quando o resultado sai errado (a nota do `fii-aula` fora de ordem, um critério de
  taxa que não foi aplicado, o `setor` ignorado), não há teste que aponte onde.
  A composição — merge do preset, override de taxa/spread, decisão de ranquear,
  ordenação pós-ranking — é exatamente onde os erros moram, e é a parte sem cobertura.
- A mesma triagem não pode ser executada pela linha de comando: `python3 -m invest.cli`
  só sabe `sync`, `web` e `status`.

## Solution

Um módulo `triagem` com uma única interface:

    executar(pedido: Pedido) -> Resultado

`web.py` passa a fazer só duas coisas na rota `/api/acoes` e `/api/fiis`: decodificar a
query string em um `Pedido` e serializar o `Resultado` em JSON. Toda a decisão de
triagem fica atrás dessa interface, e é ali que os testes entram.

O usuário ganha: o mesmo comportamento no painel, com a triagem testável, e um lugar
óbvio para pendurar a triagem por linha de comando depois.

## User Stories

1. Como investidor, quero que a triagem que vejo no painel seja a mesma que os testes exercitam, para confiar que o resultado na tela é o resultado especificado.
2. Como investidor, quero escolher um preset e ver os papéis que passam nos critérios dele, para partir de uma triagem pronta em vez de lembrar cada critério.
3. Como investidor, quero somar critérios avulsos (`dy>=6`, `pvp<=1.2`, `pl=5:15`) aos critérios do preset, para apertar uma triagem sem editar o preset.
4. Como investidor, quero que meus critérios avulsos venham depois dos do preset, para que a ordem de aplicação seja previsível.
5. Como investidor, quero ajustar taxa base e spread na tela e ver o DY mínimo do `fii-aula` recalculado, para acompanhar o IPCA+ do Tesouro sem editar código.
6. Como investidor, quero que o override de taxa só afete presets que declaram `taxa_base`, para não mudar silenciosamente presets que não dependem dela.
7. Como investidor, quero que o preset `fii-aula` calcule rank de DY e rank de P/VP e some numa nota, para ordenar por qualidade combinada e não por um indicador só.
8. Como investidor, quero que a nota seja calculada apenas dentro do recorte já filtrado, para que o rank reflita os candidatos reais e não o mercado inteiro.
9. Como investidor, quero que a ordenação por `nota` seja crescente por padrão, para que o primeiro da lista seja o melhor colocado.
10. Como investidor, quero poder trocar a coluna de ordenação sem perder os ranks calculados, para inspecionar o mesmo recorte por outro ângulo.
11. Como investidor, quero que papéis com o mesmo valor recebam o mesmo rank, para não ser enganado por uma diferença que não existe.
12. Como investidor, quero que papéis sem valor num campo ranqueado fiquem sem nota, para não competir com quem tem dado.
13. Como investidor, quero que um campo com critério não aceite o valor 0 por padrão, porque no Fundamentus zero quase sempre significa dado ausente.
14. Como investidor, quero poder ligar "zeros valem" quando o zero for informação de verdade, para triar fundos de papel sem vacância nem cap rate.
15. Como investidor, quero filtrar ações por setor, para comparar múltiplos com os pares e não com o mercado inteiro.
16. Como investidor, quero ver quantos papéis existem no total e quantos passaram na triagem, para saber o quanto o filtro apertou.
17. Como investidor, quero ver a descrição do preset aplicado junto do resultado, para lembrar que critérios estão em vigor.
18. Como investidor, quero ver a lista de critérios efetivamente aplicados, incluindo os do preset e os avulsos já resolvidos, para conferir o que o painel entendeu.
19. Como investidor, quero saber se o resultado foi ranqueado, para o painel decidir se mostra as colunas de rank e nota.
20. Como investidor, quero que um preset inexistente não derrube a triagem, para um link antigo continuar devolvendo uma triagem sem preset em vez de erro.
21. Como investidor, quero que um critério mal escrito me diga o formato aceito, para corrigir a expressão em vez de adivinhar.
22. Como investidor, quero que datas venham serializadas no JSON, para o painel exibir a data de atualização sem tratar tipos do Mongo.
23. Como desenvolvedor, quero uma interface única para a triagem, para ter um só lugar onde procurar quando o resultado sai errado.
24. Como desenvolvedor, quero montar um `Pedido` diretamente no teste, para exercitar a triagem sem subir servidor nem abrir socket.
25. Como desenvolvedor, quero que o handler HTTP não toque no Mongo, para que a decodificação da query e o acesso ao banco parem de se misturar.
26. Como desenvolvedor, quero que `filtros.ranquear` e `filtros.ordenar` passem a ter um chamador de produção coberto por teste, para que mudanças neles quebrem um teste em vez de o painel.
27. Como desenvolvedor, quero um `Resultado` com forma explícita, para o contrato com o painel ficar declarado em vez de implícito no `dict` de retorno.
28. Como desenvolvedor, quero que a triagem sirva depois a um comando de CLI, para rodar uma triagem no terminal sem duplicar a composição.

## Implementation Decisions

**Módulo novo: `triagem`.** Uma interface pública, `executar(pedido) -> resultado`.
Tudo o que hoje está em `Manipulador._consultar` passa para dentro dele.

**Seam: o `Pedido`.** Confirmado com o desenvolvedor. O `Pedido` é um objeto de valor
já decodificado — nada de listas de strings nem de flags `"1"`/`"0"` na interface:

- `tipo`: `"acoes"` ou `"fiis"`
- `preset`: nome do preset ou ausente
- `criterios`: critérios avulsos já convertidos em `(campo, minimo, maximo)`
- `ordenar_por`, `crescente`
- `zeros_valem`
- `setor`
- `taxa_base`, `spread` (overrides, ausentes quando o usuário não mexeu)

`web.py` é quem traduz query string em `Pedido`, incluindo chamar `filtros.parse_criterio`
para cada `f=` recebido. A tradução fica na borda; a triagem não conhece HTTP.

**O `Resultado`** carrega os campos que o painel já consome hoje: `tipo`, `total`,
`encontrados`, `criterios`, `descricao`, `ranqueado`, `registros`. A serialização de
datas acontece dentro do `triagem`, para que o handler só chame `json.dumps`.

**Contagem do total.** `web` hoje chama `db.banco()[tipo].count_documents({})` direto.
Passa a haver uma função de contagem em `db`, chamada pelo `triagem`. O handler perde
o acesso ao cliente Mongo.

**Composição preservada, não redesenhada.** A ordem de decisão continua a de hoje:
resolver preset → aplicar taxa quando o preset declara `taxa_base` → concatenar critérios
do preset com os avulsos → ordenar no Mongo *apenas quando não há ranking* → consultar →
ranquear e ordenar em memória quando há ranking → montar `Resultado`. Ordenar por `nota`
força `crescente`.

**Contrato HTTP inalterado.** `painel.html` não muda. Mesmas rotas, mesmos parâmetros,
mesma forma de JSON.

**`db` e `filtros` mantêm as interfaces atuais.** Este spec não mexe em `db.consultar`,
`db.obter_preset`, `filtros.aplicar_taxa`, `filtros.ranquear` nem `filtros.ordenar`.

**Preset desconhecido.** Comportamento de hoje mantido: `db.obter_preset` devolve nada e
a triagem segue com os critérios avulsos. Sem erro.

## Testing Decisions

**O que faz um bom teste aqui.** O teste monta um `Pedido`, chama `executar` e afirma
sobre o `Resultado` — quais papéis vieram, em que ordem, com que nota, com que descrição.
Nada de afirmar que `filtros.ranquear` foi chamado, nem em que ordem as funções internas
rodaram: isso é implementação e vai mudar quando os candidatos 2 e 3 forem executados.

**Módulo sob teste: `triagem`, pela interface `executar`.** É o único ponto de entrada
dos testes deste spec.

**Substituição do Mongo.** Os testes substituem o acesso ao banco por dados em memória.
Arte prévia: `tests/test_presets.py` já faz isso com `ColecaoMemoria` e `unittest.mock.patch`;
seguir o mesmo padrão, com um conjunto pequeno de registros de ações e FIIs fixos.
(A substituição fica mais limpa quando o candidato 3 introduzir o adapter de Presets;
até lá, o `patch` basta.)

**Casos que precisam existir:**

- preset aplicado sozinho; preset somado a critérios avulsos
- override de taxa/spread recalcula o DY mínimo do `fii-aula`; preset sem `taxa_base` ignora o override
- caminho com ranking: nota calculada dentro do recorte, empates com mesmo rank, papel sem valor sem nota, ordem crescente por nota
- caminho sem ranking: ordenação delegada ao Mongo, `crescente` respeitado
- `zeros_valem` ligado e desligado
- filtro por setor
- preset inexistente cai para triagem sem preset
- `total` e `encontrados` coerentes
- datas serializadas como texto no `Resultado`

**Arte prévia de estilo:** `tests/test_empresas.py` e `tests/test_presets.py` —
`unittest`, sem rede, rodando por `make test`.

**Sem teste novo de HTTP.** O handler fica fino o bastante para não merecer teste próprio.

## Out of Scope

- Candidato 2 (módulo `Criterio` com as duas compilações). A duplicação da regra do zero
  entre `db.consultar` e `filtros._passa` continua existindo depois deste spec.
- Candidato 3 (seam de Presets com adapter Mongo e adapter em memória).
- Candidato 4 (módulo de sincronização). O `forcar` perdido em `web._sincronizar`
  continua perdido; é um bug real, mas de outro spec.
- Candidato 5 (seam de coleta) e candidato 6 (catálogo de indicadores).
- Comando de triagem na CLI. A interface é desenhada para suportá-lo; construí-lo não
  faz parte deste spec.
- Qualquer mudança em `painel.html`, no contrato das rotas ou no schema do Mongo.
- Novos critérios, novos presets, novos indicadores.

## Further Notes

- O repositório não tem `CONTEXT.md` nem `docs/adr/`. O vocabulário de domínio usado aqui
  vem do próprio código: papel, preset, triagem, critério, snapshot, histórico, ficha, coleta.
  Se `CONTEXT.md` for criado, "Triagem", "Pedido" e "Resultado" são os termos a registrar.
- Este é o candidato 1 da revisão de arquitetura de 2026-08-23, e o primeiro por um motivo:
  os candidatos 2, 3 e 4 ganham um chamador testado no momento em que `triagem` existe.
- `filtros.aplicar` continua sem chamador de produção depois deste spec. Ele volta a ter
  sentido no candidato 2; se o candidato 2 for descartado, `aplicar` e `_passa` falham no
  teste da deleção e devem sair.
