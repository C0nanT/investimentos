Lives: [https://drive.google.com/drive/folders/1F5VqMXGUT0344gHOrBvuk66-6bduGGi4?hl=pt-br](https://drive.google.com/drive/folders/1F5VqMXGUT0344gHOrBvuk66-6bduGGi4?hl=pt-br)

# Fase 2:

## Quais são os indicadores que você precisa analisar antes de comprar qualquer ação ou fundo imobiliário?
- Erro comum:
  1. Comprar ou vender olhando apenas para a cotação do ativo.
    - "Se caiu, ta barato", nem tudo que caiu é oportunidade.
    - "Se subiu, ta caro", nem tudo que subiu deixou de ser oportunidade.

## O que os grandes investidores fazem diferente?
- Análise quantitativa e qualitativa.
  - Quantitativa é para filtragem pois olha o passado/presente.
  - Qualitativa é para decisão pois olha o futuro.

---

## Fundos imobiliários:

### Principais indicadores:

#### Dividend Yield (DY):
- O que é dividend yield?
  - É o rendimento dos dividendos (12 meses) em relação ao preço da ação. `(dividendos (12 meses) / preço da ação) * 100% = DY`
  - Exemplo: Se a ação custa R$ 100 e paga R$ 10 de dividendos, o DY é de 10%.
- Tem 2 formas dele subir:
  - Subir por conta do lucro = BOM.
  - Cair a cotação = RUIM.
- Métricas de porcentagem:
  - Abaixo e 7% não é interessante.
  - 7% a 10% é bom.
  - 10% é o ideal.
  - 15% é cuidado.
- Spread (diferença):
  1. Primeiro é necessário ver o IPCA mais curto do Tesouro Direto: [https://www.tesourodireto.com.br/produtos/dados-sobre-titulos/rendimento-dos-titulos](https://www.tesourodireto.com.br/produtos/dados-sobre-titulos/rendimento-dos-titulos), hoje é IPCA + 8,17% a.a.
    - Bons fundos imobiliários repassão inflação, portanto o DY mínimo aceitável deve ser 8,17% a.a.
    - Portanto se o fundo imobiliário está pagando 10% o spread é de 1,83% a.a.
    - Para fundos de ancoragem, exigir spread mínimo de 1% até 2% a.a.
    - Para fundos de crescimento, exigir spread mínimo de 3%
    - Para fundos com risco, exigir spread mínimo de 5%

---

#### Preço/Valor Patrimonial (P/VP):
- Não levar P/VP = 1 como regra rígida.
- Papel pós-fixado (ex: KNCR11): retorno vem quase só dos juros; pouco upside de NAV além do yield.
  - Prêmio alto (P/VP bem > 1) é difícil de justificar → preferir ~1 ou desconto moderado.
  - Desconto pode ser oportunidade **ou** risco (crédito/liquidez).
- Tijolo (ex: BTLG11): aluguel + possível valorização do imóvel/NAV.
  - P/VP > 1 pode fazer sentido se qualidade justifica, mas prêmio alto demais dilui DY.
- Papel IPCA+: nuance à parte (principal reajusta inflação) — não misturar com regra do pós CDI.

---

#### Vacância:
- Física e Financeira:
  - Física é o imóvel vazio.
  - Financeira é o imóvel com inquilino.
- Vacância física:
  - Vacância física é a porcentagem de imóveis vazios em relação ao total de imóveis.
  - Exemplo: Se o fundo imobiliário tem 100 imóveis e 10 estão vazios, a vacância física é de 10%.
- Vacância financeira:
  - Vacância financeira é a porcentagem de imóveis com inquilino em relação ao total de imóveis.
  - Exemplo: Se o fundo imobiliário tem 100 imóveis e 10 estão com inquilino, a vacância financeira é de 10%.
- Vacância total:
  - Vacância total é a porcentagem de imóveis vazios e com inquilino em relação ao total de imóveis.
- Preferir vacância *menor que 10%*.
- Exemplo de possível compra:
  - Fundo imobiliário X com vacância física 0%, vacância financeira 0%, DY 10% e P/VP 1.
  - Fundo imobiliário Y com vacância física 5%, vacância financeira 10%, DY 10% e P/VP 1.
  - Nesse caso, comprar o fundo imobiliário Y, pois ele com vacância ainda tem o mesmo DY, portanto quando a vacância cair, o DY vai subir.

---

#### Alavancagem bruta:

- Passivos (obrigações) / Ativos (imóveis) = Alavancagem bruta.
- Preferir menos alavancados, usar como último critério de desempate pois é complexo de entender.

---

#### Triagem quantitativa:
  - Usar o site: [https://www.fundamentus.com.br/fii_resultado.php](https://www.fundamentus.com.br/fii_resultado.php) para puxar os fundos e tabelar eles no google sheets.
1. Liquidez, remover fundos com menos de 2 milhões.
2. Dividend Yield, remover fundos com mais de 18%, e com menos de 1% de spread.
3. Tirar fundos com P/VP abaixo de 0.8, e com mais de 1.2.
4. Criar rank de DY, rank de P/VP e coluna de notas.
  - Rank de DY deve ser do maior para o menor.
  - Rank de P/VP deve ser do menor para o maior.
  - Notas é a soma dos ranks de DY e P/VP, usar ele como rank final.


## Ações:
### Principais indicadores:
#### Segue as mesmas regras do DY e P/VP do fundo imobiliário.
  - ...

#### Preço sobre lucro (P/L):
  - Preferir P/L baixo, porém P/L menor que 3 é suspeito, tomar cuidado.
  - P/L de 3 até 12 é o normal no brasil, porém se for maior que 12 é suspeito, tomar cuidado.

#### Margem líquida:
  - Preferir margem líquida alta, 15% para cima.
  - Comparar com os pares equivalentes, exemplo: Sanepar é uma empresa de energia, então seu P/L deve ser comparado com as outras empresas de energia.
  - Demonstra a competitividade da empresa.

#### ROE (Return on Equity):
  - Lucro líquido / Patrimônio líquido = ROE.
  - Quanto maior melhor, preferir ROE acima de 12%, mas ainda é necessário ver o setor e suas concorrentes, se todas tiverem ROE baixo, é pq o setor é pouco competitivo.
  - Necessário análise qualitativa para entender o ROE, portanto usar só como último critério de desempate.

#### Divida líquida/EBITDA:
  - Indicador de endividamento da empresa.
  - Revisar o grau de endividamento da empresa, geralmente fica em 50% até 80%.
  - Preferir valores baixos, menores que 3, pois quanto mais baixo, menos endividada a empresa está, maior que 3 é suspeito, tomar cuidado, as empresas de energia são exceções e podem ficar entre 3 e 5, pois tem fluxo de caixa previsível.
> OBS: nas seguradoras ela pode ficar negativa, e isso *NÃO* é ruim.

#### Triagem quantitativa:
  - (Não mostrou na aula, necessário criar)
  
---

#### Valuation pelo fluxo de caixa descontado:
> O valor de uma empresa é a soma dos seus fluxos de caixas futuros corrigido a valor presente atravez de uma taxa, chegando ao seu valor presente líquido, que é o valor real da empresa hoje.
> Fluxo de Caixa aos Acionistas (FCA) = Lucro Líquido (LL)
> Preço teto é importante para saber se a empresa está cara ou barata.

``` revisar isso aqui
- Valor Presente Teto = Lucro Líquido / (1 + taxa de desconto(SELIC))^1 + Lucro Líquido / (1 + taxa de desconto(SELIC, CDI, etc))^2 + ... + Lucro Líquido / (1 + taxa de desconto(SELIC, CDI, etc))^t
- Fazer n = 10 anos para prever os 10 anos futuros.

Formulas de preço teto:
VPL = VF / (1 + r)^t
VPL = (ultVF * (1+g)) / (r-g)

Como calcular algo que ainda não explicou na aula:
1. Pegar os últimos 6 meses de Lucro Líquido, multiplicar por 2 para ter o Lucro Líquido anual de forma conservadora.
2. Pegar o payout médio, exemplo 80%.
3. Pegar o ROE médio, exemplo 20%.
4. Fazer a conta de (1 - payout) * ROE para ter o resultado da taxa esperada de crescimento, exemplo 4% 

Para calcular o preço teto:
1. Pegar o Lucro Líquido anual mais recente, se só tiver de 6 meses, multiplicar por 2 para ter o Lucro Líquido anual.
2. Crescimento esperado, 3% a.a. ou da empresa específica.
3. 
```

