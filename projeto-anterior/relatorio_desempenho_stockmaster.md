# Plano e Relatório de Teste de Desempenho – Projeto anterior (StockMaster)

Equipe: Renato de Paiva Belarmino, Alisson Gabriel · Projeto: StockMaster (ES II) · Data: 22/11/2026

O StockMaster é o sistema de estoque e vendas da equipe: uma API REST em Java/Spring Boot
com banco H2 em memória. Ele já tem interface HTTP, então não foi preciso criar adaptador:
o Locust chama a API original. No código Java, a única mudança foi corrigir o erro que impedia a
compilação (DEF-04 do relatório funcional). As páginas `produtos.html` e `venda.html` em
`src/main/resources/static/` foram criadas para os testes funcionais (Trabalho 2) e não são usadas aqui.

## 1. Plano (definido antes de executar)

| Item | Preenchimento |
|---|---|
| Pergunta / hipótese | Com 20 operadores simultâneos, o StockMaster consulta o estoque, registra vendas e mostra o resumo dentro das metas, sem falhas e **sem perder baixas de estoque**. Hipótese de risco: como a venda lê o produto, subtrai e grava sem nenhuma trava, vendas simultâneas podem sobrescrever a baixa uma da outra |
| Operações e proporção | `GET /produtos` 60% (peso 6) · `POST /vendas` 30% (peso 3), uma venda de 2 produtos · `GET /relatorios/vendas/resumo` 10% (peso 1) |
| Verificações de conteúdo | **Lista:** HTTP 200 e os 2 produtos da massa presentes. **Venda:** HTTP 201, `valorTotal` = 22.50 (1 × 2,50 + 2 × 10,00, sem desconto) e 2 itens. **Resumo:** HTTP 200, `totalVendas` ≥ 0 e `valorTotalAcumulado` ≥ 0. **Ao final de cada execução:** vendas gravadas pelo servidor comparadas com a baixa no estoque de cada produto |
| Think time | 0,5 a 1,5 s (operador entre uma ação e outra no balcão) |
| Massa de dados | No início de cada execução, 2 produtos novos com estoque de 10.000.000 (a venda nunca falha por falta de estoque, então qualquer diferença no estoque é defeito). O StockMaster é reiniciado antes de cada repetição, e o banco volta a zero |
| Perfis | Verificação: 1 usuário (-r 1) por 15 s · Referência: 5 (-r 1) · Carga: 20 (-r 2) · Estresse: 50 (-r 5) e 100 (-r 10) · Recuperação: 20 (-r 2), logo após o estresse 100. Todos com 90 s |
| Repetições | 3 por patamar (r1, r2, r3); verificação só 1 vez |
| Metas (SLA) | **p95 de `GET /produtos` ≤ 300 ms**, **p95 de `POST /vendas` ≤ 500 ms**, **p95 do resumo ≤ 1000 ms**, **falhas ≤ 1%**, **0 baixas de estoque perdidas**, **recuperação**: voltar às metas em até 30 s com 20 usuários |
| Critério de parada | Falhas > 20% por 10 s ou p95 > 2000 ms por 10 s (parada automática no próprio locustfile, igual ao Pacote B) |

### Justificativa das metas

As metas foram pensadas para uma loja pequena ou média que usa o StockMaster no balcão:

- **20 usuários:** é mais do que o número de caixas e estoquistas usando ao mesmo tempo nessa loja. É uma carga nominal com folga.
- **Consulta de estoque (300 ms):** o operador consulta enquanto atende o cliente, então a resposta precisa parecer imediata.
- **Registrar a venda (500 ms):** pode ser um pouco mais lento, porque grava dados, mas não pode segurar a fila do caixa.
- **Resumo (1 s):** é usado pelo gerente, de vez em quando, então aceita mais tempo.
- **Falhas (1%):** é o mesmo nível de tolerância dos pacotes, porque uma venda que falha obriga a repetir o atendimento.
- **Estoque (0 baixas perdidas):** é a regra que mais importa num sistema de estoque. Um estoque errado gera venda de produto que não existe, então a tolerância é zero.

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i5-13420H · 8 GB (7,7 GB utilizáveis) · GPU RTX 2050 4 GB (não usada pelo teste) |
| Sistema operacional | Windows 11 Home (10.0.26200) |
| Servidor | StockMaster (Spring Boot 3.5.15, Tomcat embutido), empacotado com `mvn package` e executado com `java -jar` · JDK: OpenJDK 21.0.6 (Zulu) · configuração original (`show-sql=true`) |
| Banco | H2 2.x em memória (`jdbc:h2:mem:stockmaster`), no mesmo processo da aplicação |
| Ferramenta | Locust 2.47.0 · Python 3.13.14 |
| Servidor e gerador na mesma máquina? | Sim (`127.0.0.1:8080`) |
| Como reproduzir | ver o README (seção Projeto anterior): gerar o `.jar` com `mvn package` e rodar `executar_series.sh` no Git Bash |

## 3. Resultados

Os dados brutos estão em `resultados/projeto-anterior/` (`.html`, `.log` e CSVs de cada execução). Há uma linha por execução em
`projeto-anterior/registro_resultados_desempenho_stockmaster.csv`. Os gráficos de p95, req/s e usuários ao
longo do tempo estão no HTML de cada execução.

### Tempo de resposta, vazão e falhas (medido)

| Patamar | Rep. | Requisições | req/s | p95 produtos (ms) | p95 venda (ms) | p95 resumo (ms) | Máx. (ms) | Falhas |
|---|---|---|---|---|---|---|---|---|
| Verificação 1 | r1 | 15 | 1,0 | 7 | 140 ¹ | – | 137 | 0% |
| Referência 5 | r1 | 434 | 4,8 | 6 | 11 | 9 | 19 | 0% |
| | r2 | 442 | 4,9 | 6 | 10 | 7 | 86 | 0% |
| | r3 | 430 | 4,8 | 6 | 12 | 8 | 101 | 0% |
| Carga 20 | r1 | 1687 | 18,8 | 4 | 6 | 4 | 8 | 0% |
| | r2 | 1680 | 18,7 | 4 | 8 | 6 | 15 | 0% |
| | r3 | 1702 | 19,0 | 5 | 8 | 6 | 16 | 0% |
| Estresse 50 | r1 | 4204 | 46,9 | 4 | 5 | 5 | 8 | 0% |
| | r2 | 4242 | 47,3 | 4 | 5 | 6 | 11 | 0% |
| | r3 | 4236 | 47,3 | 4 | 5 | 7 | 31 | 0% |
| Estresse 100 | r1 | 8493 | 94,7 | 3 | 4 | 7 | 96 | 0% |
| | r2 | 8543 | 95,1 | 5 | 6 | 11 | 24 | 0% |
| | r3 | 8506 | 94,6 | 5 | 6 | 10 | 24 | 0% |
| Recuperação 20 | r1 | 1703 | 19,0 | 2 | 3 | 8 | 9 | 0% |
| | r2 | 1699 | 18,9 | 3 | 3 | 12 | 13 | 0% |
| | r3 | 1701 | 19,0 | 3 | 4 | 11 | 13 | 0% |

¹ A primeira venda depois que a aplicação sobe leva cerca de 140 ms (aquecimento da JVM).
Com só 15 requisições, ela sozinha define o p95 da verificação.

### Consistência do estoque (medido)

A conferência compara as vendas gravadas pelo servidor com a baixa no estoque. Cada venda
deveria baixar 1 unidade do produto A e 2 do produto B. A tabela mostra o produto A. O B
perdeu cerca do dobro em unidades (por exemplo, 722 no estresse 100 da r1), porque cada
venda baixa 2 unidades dele. As linhas `[CONSISTENCIA]` dos `.log` têm os números exatos.

| Patamar | Vendas gravadas (r1 / r2 / r3) | Vendas sem baixa (r1 / r2 / r3) | % perdido |
|---|---|---|---|
| Verificação 1 | 6 | 0 | 0% |
| Referência 5 | 136 / 137 / 121 | 1 / 4 / 3 | 0,7% a 2,9% |
| Carga 20 | 521 / 473 / 496 | 20 / 28 / 18 | 3,6% a 5,9% |
| Estresse 50 | 1239 / 1274 / 1347 | 127 / 126 / 125 | 9,3% a 10,3% |
| Estresse 100 | 2540 / 2598 / 2558 | 370 / 298 / 289 | 11,3% a 14,6% |
| Recuperação 20 | 509 / 533 / 486 | 24 / 25 / 18 | 3,7% a 4,7% |

## 4. Análise (interpretação)

**Tempo de resposta e falhas: metas atendidas em todos os patamares.**
- **Tempo:** mesmo com 100 usuários, o maior p95 por operação foi 11 ms (resumo), muito abaixo das metas de 300, 500 e 1000 ms. Não houve nenhuma falha HTTP nem de conteúdo, e a parada automática nunca foi acionada.
- **Limite de tempo não atingido:** o primeiro patamar que viola a meta de tempo não existe até 100 usuários.
- **Vazão:** cresceu na mesma proporção dos usuários: cerca de 4,8, 19, 47 e 95 req/s. Cada usuário faz em média uma requisição por segundo (pausa média de 1 s), então a vazão não parou de crescer. Isso indica que o servidor não saturou. O limite de vazão do sistema está acima do que foi testado.

**Gargalo: não apareceu em tempo de resposta.**
- **Resumo:** é a operação que mais cresce, de 4–7 ms para 7–12 ms. Isso combina com o código: o resumo lê todas as vendas da tabela (`findAll`), e a tabela cresce durante o teste (até cerca de 2.600 vendas por patamar).
- **Projeção (interpretação):** com muitos dados acumulados, o resumo tende a ser o primeiro a degradar. Isso não chegou a afetar as metas neste teste.

**Consistência do estoque: meta violada a partir de 5 usuários.** É o resultado principal.
- **Com 1 usuário, o estoque bate.** Com 5 ou mais usuários simultâneos, uma parte das vendas é gravada sem baixar o estoque.
- **A perda cresce com a concorrência:** cerca de 2% com 5 usuários, 4–6% com 20, cerca de 10% com 50 e 11–15% com 100.
- **Causa provável, pelo código:** `VendaService.registrarVenda` lê o produto, calcula a nova quantidade e salva, sem lock pessimista e sem campo `@Version`. Quando duas vendas leem a mesma quantidade ao mesmo tempo, a segunda gravação sobrescreve a primeira. Isso é uma "atualização perdida".
- **O efeito não depende de o servidor estar lento:** ele acontece com p95 de 5 ms. Por isso o sistema "passa" nas métricas de tempo e mesmo assim não atende a meta de consistência em nenhum patamar com concorrência.
- Esse defeito foi registrado como **DEF-05** no registro de defeitos do Trabalho 2 (`projeto-anterior/registro_defeitos_stockmaster.csv` daquele repositório).

**Recuperação.**
- **Em tempo de resposta, foi imediata.** Logo depois do estresse com 100 usuários, a recuperação com 20 teve p95 de 3 a 8 ms já no 1º segundo, nas três repetições, e terminou com números iguais ou melhores que os da carga nominal. A meta de voltar em até 30 s foi atendida.
- **Na consistência, não houve recuperação.** A perda de baixas com 20 usuários (3,7–4,7%) é do mesmo nível da carga nominal. Isso é esperado: o defeito não é causado pelo estresse, e sim pela concorrência.

**Repetições.**
- **Tempo e vazão:** foram muito parecidos nas três repetições (diferenças de poucos ms).
- **Perda de estoque:** varia mais entre repetições, por exemplo de 3,6% a 5,9% com 20 usuários. Isso é natural, porque depende de duas vendas caírem exatamente no mesmo instante.
- **Picos isolados:** máximos como 86 e 101 ms na referência são casos únicos, provavelmente coleta de lixo da JVM ou outro processo da máquina. Eles não mudam o p95.

## 5. Limitações e recomendações

**Limitações**
- **Mesma máquina:** gerador de carga e servidor dividiram a mesma CPU. Com tempos tão baixos, isso não alterou as conclusões.
- **Banco:** o H2 em memória no mesmo processo é muito mais rápido que um banco real em rede, como o PostgreSQL citado no README. Os tempos absolutos são otimistas. O defeito de concorrência, porém, tende a acontecer também com PostgreSQL, porque a gravação sem trava é do código, não do banco.
- **Configuração original mantida:** o `show-sql=true` imprime cada SQL no console e custa um pouco de desempenho. Os logs da aplicação foram gravados fora do repositório por causa do tamanho.
- **Limite não encontrado:** só foi testado até 100 usuários, então o limite de vazão do sistema não foi encontrado. O critério de parada não foi atingido.
- **Medição da consistência:** ela é feita uma vez no fim de cada execução, pela API. Ela conta quantas baixas faltaram, mas não identifica quais vendas foram afetadas.
- **Escopo:** só um tipo de venda (2 produtos, 3 itens, sem desconto) e os mesmos 2 produtos para todos os usuários. Isso é o pior caso para a concorrência, de propósito.

**Recomendações**
1. **Corrigir a baixa de estoque concorrente** (DEF-05). Há três caminhos:
   - fazer a baixa numa única instrução no banco (`UPDATE produto SET quantidade = quantidade - ? WHERE id = ? AND quantidade >= ?`);
   - usar lock pessimista na leitura do produto;
   - usar lock otimista (`@Version`) com nova tentativa.

   Depois, repetir esta bateria e confirmar 0 baixas perdidas.
2. **Fazer o resumo de vendas no banco** (`SELECT COUNT(*), SUM(valor_total)`) em vez de carregar todas as vendas na memória, antes que o volume de dados cresça.
3. **Repetir o teste com PostgreSQL e com o servidor em outra máquina,** para ter tempos mais realistas.
4. **Desligar `show-sql` fora do ambiente de desenvolvimento.**
