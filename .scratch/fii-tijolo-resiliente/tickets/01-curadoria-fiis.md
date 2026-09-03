# 01: Curadoria de FIIs: arquivo de dados e leitura tolerante a erro

> **Difficulty:** Light: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Suggestion only, use whatever model you have to hand.

**What to build:** o lugar onde eu registro à mão o que o Fundamentus não fornece — segmento resiliente, ano de IPO, taxa de administração e gestora de cada FII — e a leitura desse arquivo pelo sistema. Eu edito o JSON, recarrego a página e o painel enxerga a mudança, sem sync e sem mexer no Mongo. Um erro de digitação meu nunca derruba o painel: vira um problema reportado que as fatias seguintes transformam em aviso na tela.

Esta é a fundação das fatias 02 e 04, por isso vem antes de qualquer comportamento visível.

Formato do arquivo (semente inicial; as taxas e anos precisam ser conferidos pelo mantenedor, o sistema não os valida):

```json
{
  "HGLG11": { "segmento_resiliente": "Logística", "ano_ipo": 2010, "taxa_adm": 0.60, "gestora": "Credit Suisse / Pátria" },
  "XPML11": { "segmento_resiliente": "Shopping", "ano_ipo": 2017, "taxa_adm": 0.95, "gestora": "XP Asset" },
  "KNRI11": { "segmento_resiliente": "Logística", "ano_ipo": 2010, "taxa_adm": 1.05, "gestora": "Kinea" },
  "HGRU11": { "segmento_resiliente": "Renda urbana", "ano_ipo": 2018, "taxa_adm": 0.85, "gestora": "Credit Suisse / Pátria" },
  "PVBI11": { "segmento_resiliente": "Lajes corporativas AAA", "ano_ipo": 2020, "taxa_adm": 0.90, "gestora": "VBI Real Estate" }
}
```

Todos os campos são opcionais: um ticker pode estar presente com um campo só.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] `data/fiis-curadoria.json` existe, versionado no git, com os cinco fundos da semente
- [ ] Um módulo novo de curadoria lê o arquivo e devolve, junto dos dados, a lista de problemas encontrados
- [ ] Arquivo ausente equivale a curadoria vazia: nenhuma exceção, nenhum aviso de erro
- [ ] JSON inválido devolve dados vazios mais um problema descrevendo a falha, sem levantar exceção
- [ ] Ticker em minúsculo no arquivo é aceito e normalizado para maiúsculo
- [ ] Campo com tipo errado (ex.: `ano_ipo` como texto) vira problema reportado e o resto daquele ticker continua utilizável
- [ ] O caminho do arquivo é injetável, para os testes apontarem para um diretório temporário
- [ ] Testes cobrem: arquivo ausente, JSON quebrado, campo com tipo errado, ticker minúsculo
- [ ] `make test` passa
