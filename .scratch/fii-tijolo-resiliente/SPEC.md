# Preset `fii-tijolo` — triagem de fundos de tijolo resilientes

Status: ready-for-agent

## Problem Statement

Hoje o painel tem `fii-aula`, `fii-renda` e `fii-tijolo-desconto`, todos puramente
quantitativos sobre o snapshot do Fundamentus. Nenhum deles responde à pergunta
que eu realmente faço quando vou montar carteira de tijolo: *quais fundos são
grandes, antigos, baratos de manter e estão em segmento que aguenta ciclo ruim?*

Para chegar nesses fundos hoje eu preciso:

1. filtrar tipo "Fundo de Tijolo" na tela e olhar segmento fundo a fundo — e o
   Fundamentus classifica HGLG11 e KNRI11 como `Multicategoria` e HGRU11 como
   `Outros`, então o recorte por segmento sozinho *derruba* justamente os fundos
   que eu quero;
2. calcular patrimônio na mão (`valor de mercado ÷ P/VP`), porque a tabela de
   FIIs do Fundamentus não traz patrimônio líquido;
3. sair do sistema para descobrir taxa de administração, ano de IPO e quem é a
   gestora — três critérios que o Fundamentus simplesmente não fornece.

E, depois de tudo isso, ainda preciso lembrar sozinho dos cuidados de leitura:
DY alto pode ser cota que caiu, e rendimento de venda de imóvel não é recorrente.

## Solution

Um preset novo, **`fii-tijolo`**, na aba FIIs, que:

- classifica cada FII em um **segmento resiliente** próprio (Logística, Shopping,
  Lajes corporativas AAA, Renda urbana), independente do rótulo do Fundamentus,
  usando uma tabela curada com fallback heurístico;
- mantém só os segmentos resilientes e descarta Hotel, Hospital, Residencial,
  Desenvolvimento e Fundo de Fundos;
- exige patrimônio acima de R$ 1 bilhão, derivado de `valor_mercado ÷ pvp`;
- exige mais de 5 anos de bolsa e taxa de administração de até 1,1% a.a., a
  partir de uma tabela de curadoria mantida por mim — **fundo sem esse dado não
  é eliminado**, passa marcado como "a verificar";
- **ordena por taxa de administração** (menor primeiro), com desempate pelos
  critérios de análise final;
- mostra colunas de desempate (vacância, P/VP, segmento resiliente) e um
  **painel de avisos** que diz, explicitamente, quais critérios não puderam ser
  validados dentro do sistema e precisam de verificação minha por fora — em
  especial a qualidade da gestora, que o projeto não tem como aferir;
- sinaliza DY suspeito: fundo cujo DY está muito acima da mediana do recorte
  ganha um alerta pedindo para olhar a evolução da cota antes de comemorar.

## User Stories

1. Como investidor de FIIs, quero um preset `fii-tijolo` no menu de presets da aba FIIs, para não ter que reconstruir esses filtros toda vez que abro o painel.
2. Como investidor, quero que o preset já venha com todos os limites preenchidos nos campos mín/máx, para poder afrouxar ou apertar cada um sem editar código.
3. Como investidor, quero poder salvar meus ajustes com **Salvar preset**, como já faço nos outros presets, para que o preset passe a refletir meu critério.
4. Como investidor, quero abrir o painel direto no preset por link (`/?tipo=fiis&preset=fii-tijolo`), para guardar o atalho no navegador.
5. Como investidor, quero que o preset mantenha apenas fundos de segmento Logística, para ter exposição a galpões, que sofrem menos em ciclo ruim.
6. Como investidor, quero que o preset mantenha fundos de Shopping, para capturar renda de varejo consolidado.
7. Como investidor, quero que o preset mantenha fundos de Lajes corporativas AAA, para ficar só com escritório de padrão alto, não com laje B/C.
8. Como investidor, quero que o preset mantenha fundos de Renda urbana, para incluir varejo de rua e ativos urbanos de contrato longo.
9. Como investidor, quero que o preset descarte fundos de Hotel, porque a receita é cíclica demais.
10. Como investidor, quero que o preset descarte fundos de Hospital, porque a concentração em poucos locatários me incomoda.
11. Como investidor, quero que o preset descarte fundos Residenciais, porque o modelo ainda é imaturo no Brasil.
12. Como investidor, quero que o preset descarte fundos de Desenvolvimento, porque quero renda pronta, não obra.
13. Como investidor, quero que o preset descarte Fundos de Fundos, porque não quero taxa sobre taxa.
14. Como investidor, quero que HGLG11, KNRI11 e HGRU11 apareçam no resultado mesmo o Fundamentus rotulando-os como `Multicategoria`/`Outros`, para que a classificação da fonte não elimine bons fundos.
15. Como investidor, quero ver na tabela a coluna **Segmento resiliente**, separada do segmento cru do Fundamentus, para saber em qual bucket cada fundo caiu.
16. Como investidor, quero que o segmento resiliente indique se veio de curadoria ou de inferência, para saber quanto confiar nele.
17. Como investidor, quero poder corrigir a classificação de um fundo editando um arquivo de curadoria, para não depender de mudança de código a cada fundo novo.
18. Como investidor, quero que o preset exija patrimônio acima de R$ 1 bilhão, para ficar com fundos grandes o bastante para diluir custo e ter liquidez.
19. Como investidor, quero ver a coluna **Patrimônio** na tabela de FIIs, para conferir o número que está sendo filtrado.
20. Como investidor, quero saber que o patrimônio é derivado de `valor de mercado ÷ P/VP`, e não um dado direto da fonte, para interpretar o valor com a devida margem.
21. Como investidor, quero que fundos sem P/VP ou sem valor de mercado não travem a triagem, para que dado faltante vire "a verificar", não um erro.
22. Como investidor, quero que o preset exija mais de 5 anos de bolsa, para ver o fundo já ter atravessado pelo menos um ciclo.
23. Como investidor, quero informar o ano de IPO de cada fundo num arquivo de curadoria, já que o Fundamentus não traz essa data.
24. Como investidor, quero ver a coluna **Anos de bolsa** calculada a partir do ano de IPO, para não fazer a conta de cabeça.
25. Como investidor, quero que fundo sem ano de IPO cadastrado apareça marcado como "a verificar" em vez de sumir do resultado, para não perder candidato por falta de cadastro.
26. Como investidor, quero que o preset exija taxa de administração de até 1,1% ao ano, para não pagar caro por gestão de tijolo.
27. Como investidor, quero **ordenar** o resultado pela taxa de administração, do menor para o maior, porque custo é o critério que eu mais uso para decidir entre dois fundos parecidos.
28. Como investidor, quero ver a coluna **Taxa de adm.** na tabela, para comparar custo lado a lado.
29. Como investidor, quero informar a taxa de administração de cada fundo no arquivo de curadoria, já que a fonte não fornece.
30. Como investidor, quero que fundo sem taxa cadastrada apareça marcado como "a verificar" e vá para o fim da ordenação por custo, para não parecer barato só por falta de dado.
31. Como investidor, quero ver a coluna **Gestora** quando ela estiver cadastrada na curadoria, para reconhecer o nome antes de investigar.
32. Como investidor, quero um aviso explícito de que a qualidade da gestora (histórico do time, transparência dos relatórios, governança) **não é validada pelo sistema**, para lembrar de checar isso por fora antes de comprar.
33. Como investidor, quero que esse aviso liste nominalmente os critérios não validados, para saber exatamente o que ainda me falta olhar.
34. Como investidor, quero ver quantos fundos do resultado têm pendência de curadoria, para saber o tamanho do trabalho manual restante.
35. Como investidor, quero um selo visual na linha de cada fundo com dado pendente, para localizar as pendências sem ler o painel de avisos inteiro.
36. Como investidor, quero ver a **vacância média** na tabela do preset, para usar como critério de desempate.
37. Como investidor, quero ver o **P/VP** na tabela e identificar rapidamente quem está abaixo de 1, para priorizar quem está descontado.
38. Como investidor, quero que P/VP abaixo de 1 seja destacado visualmente, para bater o olho e ver os descontados.
39. Como investidor, quero ver o **cap rate** junto com o DY, para checar se o rendimento se sustenta no aluguel e não em venda de ativo.
40. Como investidor, quero um alerta no fundo cujo DY está muito acima da mediana do próprio recorte, para investigar antes de tratar como oportunidade.
41. Como investidor, quero que esse alerta explique o motivo — cota pode ter caído, ou o rendimento pode ter vindo de venda de imóvel — para lembrar do raciocínio no momento em que olho a linha.
42. Como investidor, quero que o alerta de DY seja informativo e não elimine o fundo, porque DY alto sozinho não significa fundo ruim.
43. Como investidor, quero ver quantos fundos há por segmento resiliente no resultado, para não concentrar a carteira em vários FIIs do mesmo segmento.
44. Como investidor, quero um resumo por segmento no topo do resultado, para escolher conscientemente um fundo por segmento.
45. Como investidor, quero baixar o resultado do preset em CSV com as colunas derivadas (segmento resiliente, patrimônio, anos de bolsa, taxa de adm., pendências), para continuar a análise na planilha.
46. Como investidor, quero levar os fundos do resultado para o modo **Comparar** já existente, para colocar meus finalistas lado a lado.
47. Como investidor, quero que a caixa "considerar zeros" continue funcionando neste preset, para inspecionar o dado cru quando desconfiar de um campo zerado.
48. Como investidor, quero que o `make sync` continue não descartando nada na coleta, para que o preset siga sendo um recorte reversível sobre o mercado inteiro.
49. Como investidor, quero que o arquivo de curadoria seja versionado no git, para acompanhar minhas próprias correções ao longo do tempo.
50. Como investidor, quero que um erro no arquivo de curadoria (JSON inválido, ticker desconhecido) apareça como aviso na tela e não derrube o painel, para não perder a triagem inteira por um erro de digitação.
51. Como investidor, quero que o README descreva o preset `fii-tijolo` junto dos demais, para lembrar do critério meses depois.
52. Como investidor, quero que o README explique quais critérios ficam fora do sistema e por quê, na mesma linha do que já é feito para vacância física e alavancagem no preset `fii-aula`.

## Implementation Decisions

### Módulo novo: curadoria de FIIs

- Novo módulo `invest/curadoria.py` e novo arquivo de dados versionado
  `data/fiis-curadoria.json`, mantido à mão. É a única fonte para o que o
  Fundamentus não fornece.
- Formato: objeto no topo, chave = ticker, valor = objeto com campos opcionais.
  Todos os campos são opcionais; um ticker pode estar presente com um campo só.

  ```json
  {
    "HGLG11": { "segmento_resiliente": "Logística", "ano_ipo": 2010, "taxa_adm": 0.60, "gestora": "Credit Suisse / Pátria" },
    "XPML11": { "segmento_resiliente": "Shopping", "ano_ipo": 2017, "taxa_adm": 0.95, "gestora": "XP Asset" },
    "KNRI11": { "segmento_resiliente": "Logística", "ano_ipo": 2010, "taxa_adm": 1.05, "gestora": "Kinea" },
    "HGRU11": { "segmento_resiliente": "Renda urbana", "ano_ipo": 2018, "taxa_adm": 0.85, "gestora": "Credit Suisse / Pátria" },
    "PVBI11": { "segmento_resiliente": "Lajes corporativas AAA", "ano_ipo": 2020, "taxa_adm": 0.90, "gestora": "VBI Real Estate" }
  }
  ```

  Os valores acima são a semente inicial do arquivo; taxas e anos devem ser
  conferidos pelo mantenedor — o sistema não os valida.
- `curadoria.carregar()` lê e cacheia o arquivo em memória; arquivo ausente
  equivale a curadoria vazia (nada quebra). JSON inválido, ticker fora do
  formato ou campo com tipo errado não levantam exceção para o painel: são
  coletados numa lista de problemas devolvida junto, para virar aviso na tela.
- A curadoria **não vai para o Mongo**. É lida a cada triagem, do arquivo. Isso
  mantém o ciclo de edição curto: editar o JSON e recarregar a página basta.

### Classificação em segmento resiliente

- Nova constante em `invest/filtros.py`: `SEGMENTOS_RESILIENTES = ["Logística",
  "Shopping", "Lajes corporativas AAA", "Renda urbana"]` — os quatro buckets
  mantidos. Fora deles, tudo é "Outro".
- Nova função pura `filtros.classificar_segmento_resiliente(registro, curado)`
  devolve `(segmento, origem)`, com `origem` em `{"curadoria", "inferido"}`:
  1. se o ticker tem `segmento_resiliente` na curadoria, é esse, origem
     `curadoria` — a curadoria sempre vence;
  2. senão, o tipo inferido por `classificar_tipo_fii` precisa ser
     `Fundo de Tijolo`; qualquer outro tipo (Papel, FOF, Desenvolvimento,
     Misto, Outro) vira "Outro" e é descartado pelo preset;
  3. senão, mapeia o segmento do Fundamentus: `Logística` → Logística;
     `Shoppings` → Shopping; `Lajes Corporativas`/`Escritórios` → Lajes
     corporativas AAA; `Varejo` → Renda urbana; `Hotel`, `Hospital`,
     `Residencial` → "Outro" (descarte explícito);
  4. `Multicategoria`/`Outros` sem curadoria: fica "Outro", origem `inferido`.
     Ou seja, um fundo bom não catalogado *não* entra sozinho — a curadoria é o
     mecanismo de resgate, e é por isso que os cinco fundos da lista já entram
     na semente.
- O rótulo **AAA** para lajes é assumido, não medido: o Fundamentus não
  qualifica o padrão do edifício. Isso entra no painel de avisos como critério
  não validado.

### Campos derivados

Calculados na triagem, sobre o documento vindo do Mongo — não são gravados na
coleção, para não misturar dado da fonte com dado derivado:

- `patrimonio`: `valor_mercado / pvp`, `None` quando `pvp` é 0/ausente.
- `anos_bolsa`: `ano_corrente - ano_ipo`, `None` sem `ano_ipo` na curadoria.
- `taxa_adm`, `gestora`: cópia direta da curadoria, `None` quando ausente.
- `segmento_resiliente` e `segmento_origem`: da classificação acima.
- `pendencias`: lista de rótulos de critérios que não puderam ser avaliados
  para aquele fundo (`"taxa de administração"`, `"anos de bolsa"`, `"gestora"`,
  `"padrão AAA"`), usada pelo selo "a verificar" na linha.
- `dy_suspeito`: booleano. Verdadeiro quando o DY do fundo é maior que
  `1,5 × mediana do DY do recorte já filtrado`. O múltiplo vive como constante
  nomeada em `filtros.py`, não espalhado pelo código.

### Regra de dado ausente

O preset **não elimina por dado ausente** nos critérios de curadoria
(taxa de adm., anos de bolsa, gestora): o fundo passa e ganha uma pendência.
Isso é uma exceção deliberada à regra geral do projeto, em que "campo com filtro
não pode valer 0/ausente". A regra geral continua valendo para os campos vindos
do Fundamentus (patrimônio, P/VP, vacância). Motivo: a curadoria começa
incompleta e um filtro estrito esconderia candidatos que ainda não catalogei.

### Preset

- `filtros.PRESETS["fii-tijolo"]`, tipo `fiis`, com os critérios numéricos que o
  mecanismo existente já sabe aplicar (`patrimonio >= 1_000_000_000`,
  `taxa_adm <= 1.1`, `anos_bolsa >= 5`) e `ordenar_por: "taxa_adm"`,
  `crescente: True`.
- Os três critérios acima operam sobre campos derivados, então a filtragem do
  preset acontece **em memória, depois** da consulta ao Mongo — diferente dos
  outros presets, que empurram tudo para a query. A consulta ao banco traz o
  universo de FIIs e a composição derivada + filtro + ordenação roda em
  `triagem.triar`.
- Ordenação por `taxa_adm` coloca `None` no fim, na mesma lógica que
  `filtros.ordenar` já usa para valor não numérico.
- Semente no código, gravada em `presets` no primeiro insert, editável pela
  tela e sobrescrevível por **Salvar preset** — o comportamento já existente de
  `db.garantir_presets` vale sem mudança.

### Triagem

- `triagem.Pedido` ganha nada de novo: o preset é identificado pelo nome, como
  hoje. `triagem.triar` passa a, quando o preset é `fii-tijolo`, enriquecer os
  documentos com os campos derivados antes de aplicar critérios e ordenar.
- `triagem.Resultado` ganha um campo `avisos`: lista de mensagens estruturadas
  (`{"tipo": ..., "texto": ...}`) para a tela, cobrindo (a) critérios não
  validáveis pelo sistema, (b) contagem de fundos com pendência, (c) problemas
  de leitura do arquivo de curadoria, (d) distribuição por segmento resiliente.
  Presets que não geram avisos devolvem lista vazia — o campo é sempre presente,
  para a tela não precisar de condicional.

### API e painel

- `/api/fiis` passa a devolver `avisos` no corpo da resposta, junto de
  `registros`. Contrato aditivo: nenhum campo existente muda de nome ou tipo.
- `/api/config` ganha `segmentos_resilientes` (a lista) para a tela poder montar
  o resumo por segmento sem hardcode.
- `web.COLUNAS["fiis"]` ganha as colunas derivadas
  (`segmento_resiliente`, `patrimonio`, `anos_bolsa`, `taxa_adm`, `gestora`),
  cada uma com título, formato e descrição, como as demais. Elas só aparecem na
  tabela quando o preset ativo é `fii-tijolo` — mesmo mecanismo já usado por
  `COLUNAS_RANK` com o `fii-aula`.
- No `painel.html`: um bloco de avisos acima da tabela, no mesmo lugar e estilo
  da `#descricao` do preset; selo "a verificar" na linha do fundo com
  pendências, com o detalhe no `title`; destaque no P/VP abaixo de 1; ícone de
  alerta na célula de DY quando `dy_suspeito`.
- O CSV existente já exporta todos os campos do documento, então as colunas
  derivadas entram nele sem trabalho extra.

### Fora do banco de propósito

Nada disso muda o schema das coleções `fiis` ou `historico`, nem o `sync`. O
snapshot do Fundamentus continua sendo gravado cru; tudo que é opinião do preset
vive em `filtros.py` + `curadoria.py` + o JSON de curadoria.

## Testing Decisions

O que faz um bom teste aqui: exercitar a **decisão** (este fundo entra? em que
bucket? que pendência ele acumula?) através da menor interface pública possível,
com o snapshot do Fundamentus como entrada — nunca inspecionando estado interno
ou ordem de chamadas.

**Seam principal: `triagem.triar(Pedido(tipo="fiis", preset="fii-tijolo"))`.**
É onde preset, curadoria, campos derivados, filtro, ordenação e avisos se
encontram, e é exatamente o que o handler HTTP chama. Prior art direta:
`tests/test_triagem.py`, que já monta `Pedido` e inspeciona `Resultado`, com o
Mongo substituído pelo dublê em memória de `tests/apoio_mongo.py`.

Casos a cobrir nessa seam:

- HGLG11, XPML11, KNRI11, HGRU11 e PVBI11, com a curadoria semente, sobrevivem
  ao preset — este é o teste de regressão que protege o achado de que o
  Fundamentus os classifica como `Multicategoria`/`Outros`;
- fundo de Hotel, Hospital, Residencial, Desenvolvimento e FOF são descartados,
  um caso por tipo;
- fundo com patrimônio derivado abaixo de R$ 1 bi cai; fundo logo acima passa;
- fundo sem taxa de adm. na curadoria **passa** e chega com a pendência
  correspondente — a regra que inverte o padrão do projeto merece teste próprio;
- ordenação por taxa de adm. crescente, com os `None` no fim;
- `avisos` traz o alerta de gestora não validada, a contagem de pendências e a
  distribuição por segmento;
- curadoria com JSON inválido produz aviso e resultado, não exceção.

**Seam secundária: funções puras de `invest/filtros.py`.** Prior art:
`tests/test_tipos_fii.py`, que testa `classificar_tipo_fii` com dicionários
literais. Mesma forma para `classificar_segmento_resiliente`, cobrindo a
precedência curadoria > tipo inferido > mapa de segmento, e o `("Outro",
"inferido")` de Multicategoria sem curadoria.

**Seam de leitura da curadoria: `curadoria.carregar()`**, com o caminho do
arquivo injetável para o teste apontar para um tmp — arquivo ausente, JSON
quebrado, campo com tipo errado, ticker minúsculo. Sem prior art no repo; é
o padrão mais simples com `tempfile`.

Não vamos testar: o HTML do painel, o parser do Fundamentus (já coberto pelo que
existe), nem a formatação das colunas.

Tudo roda por `make test` (`unittest discover`), sem rede e sem Mongo real,
como o resto da suíte.

## Out of Scope

- **Validar a gestora.** Histórico público do time, transparência de relatório e
  governança não são aferíveis com os dados disponíveis. O sistema só avisa que
  a checagem é manual; o campo `gestora` é rótulo, não nota.
- **Classificar padrão AAA de laje.** O Fundamentus não diz o padrão do edifício.
  Lajes corporativas entram no bucket e o painel avisa que o "AAA" é premissa.
- **Vacância estável ao longo do tempo.** Há só a vacância média do dia. A
  coleção `historico` acumula um registro por papel por dia desde que o projeto
  roda, mas ainda não tem série longa o bastante; série de vacância fica para
  depois.
- **Origem do dividendo (aluguel vs. venda de ativo).** Não está em nenhum dado
  que temos. O preset só sinaliza DY suspeito e deixa a investigação comigo, no
  relatório gerencial do fundo.
- **Evolução do preço da cota.** O alerta de DY não plota histórico de cotação;
  isso pediria brapi ou série longa no `historico`.
- **Montar carteira / sugerir alocação.** A diversificação por segmento aparece
  como contagem informativa; o sistema não escolhe um fundo por segmento por mim.
- **Buscar taxa de administração ou data de IPO automaticamente** (CVM, B3,
  relatórios). A curadoria é manual nesta entrega.
- **Aplicar o filtro a ações** ou aos outros presets de FII.

## Further Notes

- O achado que mais moldou esta spec: dos cinco fundos que uso de referência,
  três (HGLG11, KNRI11, HGRU11) não são classificáveis pelo segmento do
  Fundamentus. Qualquer implementação que trate o campo `segmento` como verdade
  vai falhar o teste de regressão desses cinco tickers — foi por isso que a
  curadoria tem precedência sobre a inferência, e não o contrário.
- XPML11 aparece hoje com `vacancia_media: 91.81`, quase certamente erro ou
  outra unidade na fonte. Vacância é critério de desempate visual, não filtro
  eliminatório do preset — de propósito, para um dado sujo assim não derrubar um
  fundo bom. Vale mencionar no painel de cuidados de leitura.
- A regra "campo com filtro não pode valer 0" do projeto existe porque no
  Fundamentus zero significa dado ausente. Os campos derivados desta spec usam
  `None` para ausente, não zero, o que evita o problema na origem.
- O preset ordena por custo porque foi o critério que o usuário destacou como
  servindo tanto para filtrar quanto para ordenar; os demais critérios de
  desempate ficam como colunas visíveis, para leitura, não como ordenação
  composta tipo a `nota` do `fii-aula`.
