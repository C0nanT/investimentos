# 05: Painel de avisos e selo "a verificar"

> **Difficulty:** Standard: **suggested model:** Sonnet (Claude Code) / Sonnet (Cursor). Suggestion only, use whatever model you have to hand.

**What to build:** um bloco de avisos acima da tabela que me diz, sem eu ter que lembrar, o que o sistema **não** conseguiu validar e eu preciso checar por fora antes de comprar. É o pedido explícito do escopo: alguns critérios não são aferíveis aqui e a tela tem que avisar.

O bloco cobre quatro coisas:

1. **Critérios não validados pelo sistema**, nominalmente: a qualidade da gestora (histórico público do time, transparência dos relatórios, governança) e o padrão AAA das lajes — o Fundamentus não diz o padrão do edifício, então o "AAA" é premissa, não medida. O campo Gestora é rótulo, não nota.
2. **Contagem de fundos com pendência de curadoria** no resultado, para eu saber o tamanho do trabalho manual restante.
3. **Problemas de leitura do arquivo de curadoria** vindos da fatia 01: JSON inválido ou campo com tipo errado aparecem como aviso, e a triagem continua funcionando.
4. **Distribuição por segmento resiliente**: quantos fundos há em cada bucket, para eu não concentrar a carteira em vários FIIs do mesmo segmento e conseguir escolher um por segmento. É contagem informativa — o sistema não escolhe por mim.

Cada linha de fundo com pendência ganha um selo "a verificar", com o detalhe do que falta acessível sem sair da tabela.

Presets que não geram avisos devolvem lista vazia, para a tela não precisar de condicional.

**Blocked by:** 03 (Patrimônio derivado), 04 (Anos de bolsa e taxa de administração).

**Status:** ready-for-agent

- [ ] O bloco de avisos aparece acima da tabela quando o preset `fii-tijolo` está ativo
- [ ] O aviso lista nominalmente os critérios não validados pelo sistema: qualidade da gestora e padrão AAA das lajes
- [ ] O aviso mostra quantos fundos do resultado têm pendência de curadoria
- [ ] Problema no arquivo de curadoria vira aviso na tela e a triagem continua devolvendo resultado
- [ ] O resumo por segmento resiliente mostra a contagem de fundos em cada bucket
- [ ] Fundo com pendência exibe um selo "a verificar" na sua linha, com o detalhe do que falta
- [ ] Preset sem avisos devolve lista vazia, nunca ausente
- [ ] O contrato da API é aditivo: nenhum campo existente muda de nome ou tipo
- [ ] Testes cobrem os quatro tipos de aviso através da triagem
- [ ] `make test` passa
