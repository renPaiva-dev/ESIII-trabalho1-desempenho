# Plano e Relatório de Teste de Desempenho

Equipe: Renato de Paiva Belarmino e Alisson Gabriel   Pacote/Projeto: Pacote A – Desafio A (abertura da matrícula)   Data: 18/11/2026

## 1. Plano

| Item | Preenchimento |
|---|---|
| Pergunta / hipótese | Com 100 alunos por 2 minutos, o portal de matrícula atende p95 geral ≤ 800 ms, p95 do comprovante ≤ 1,5 s e erros técnicos < 1%, sem nenhuma disciplina com vagas negativas. |
| Operações testadas e proporção | Pesos 5 : 2 : 1 – consultar a oferta (`GET /api/disciplinas`), matricular (`POST /api/matriculas`) e baixar o comprovante (`GET /api/matriculas/[id]/comprovante`). |
| Verificações de conteúdo | Oferta: status 200 e nenhuma disciplina com `vagas < 0`. Matrícula: 201 guarda o `id`; 409 e 422 são marcados como sucesso (regra de negócio) e contados à parte; qualquer outro status é falha. Comprovante: status 200 e `id`/`aluno` iguais aos da matrícula do usuário. |
| Think time (pausa entre ações) | 1 a 4 s (`between(1, 4)`) |
| Massa de dados | Um aluno diferente por usuário virtual (20260001 a 20260200). Disciplinas sorteadas de 7 combinações sem choque de horário. |
| Perfis (usuários, ritmo, duração) | Carga: 100 alunos, 10/s, 2 min. Pico: 0 → 200 alunos em 1 s (200/s), mantém 60 s. Recuperação: volta para 20 alunos e observa por 60 s. Estresse: degraus de +25 alunos a cada 30 s, até 400 (8 min). |
| Repetições | 1 execução por tipo (ver Limitações) |
| Metas (SLA) | p95 geral ≤ 800 ms; erros técnicos (5xx, timeout) < 1%; outras: p95 do comprovante ≤ 1500 ms e vagas nunca negativas. |
| Critério de parada | Interromper se as falhas técnicas passarem de 20% por 10 s. No estresse não interrompemos por tempo de resposta, porque o objetivo era subir até 400 alunos. |

### Justificativa da proporção

Na abertura da matrícula o aluno consulta a oferta várias vezes antes de decidir (confere horário e vagas), por isso consultar tem o maior peso. A matrícula acontece uma vez por aluno: depois de receber 201 o usuário não tenta de novo. O comprovante tem o menor peso porque só quem teve a matrícula aceita pode baixá-lo; quem recebe 409 ou 422 não tem comprovante.

Como cada aluno se matricula no máximo uma vez, a proporção real de requisições fica mais concentrada nas consultas do que os pesos sugerem. Na carga, por exemplo, foram 81% consultas, 6% matrículas e 12% comprovantes.

### Combinações de disciplinas

ES3 e RED são no mesmo horário (SEG-19h) e nunca aparecem juntas; nenhuma combinação passa de 5 disciplinas. As combinações misturam 2 e 3 disciplinas para espalhar a procura e incluem a MOB (só 5 vagas) para forçar disputa pela última vaga e testar a integridade das vagas.

`ES3+BD2`, `ES3+PW2+IHC`, `RED+BD2`, `RED+EMP`, `BD2+PW2+EMP`, `IHC+EMP`, `ES3+MOB`

## 2. Ambiente

| Item | Valor |
|---|---|
| Processador / memória | Intel Core i7-13620H (16 threads) / 15 GB |
| Sistema operacional | Ubuntu 24.04.5 LTS (kernel 7.0.0-43) |
| Python ou JDK (versão) | Python 3.12.3, Flask 3.1.3 |
| Ferramenta e versão (Locust/Gatling) | Locust 2.47.0 (modo headless) |
| Servidor e gerador de carga na mesma máquina? | Sim, os dois em `localhost` |

## 3. Resultados

Relatórios completos (com gráficos de req/s, tempo de resposta e usuários) em `resultados/pacote-A/desafio/carga.html`, `resultados/pacote-A/desafio/pico.html` e `resultados/pacote-A/desafio/estresse.html`. Registro por execução em `registro_resultados.csv`.

### Resumo por teste

| Teste | Requisições | req/s | p50 geral | p95 geral | p95 comprovante | Falhas técnicas | SLA |
|---|---|---|---|---|---|---|---|
| Carga | 3445 | 28,6 | 26 ms | 1500 ms | 2900 ms | 0% | não atendido |
| Pico | 4299 | 35,7 | 26 ms | 720 ms | 3400 ms | 0% | não atendido |
| Estresse | 32386 | 67,4 | 25 ms | 260 ms | 5300 ms | 0% | não atendido |

### Por endpoint (p95 / máximo)

| Teste | Oferta | Matrícula | Comprovante | Vazão do comprovante |
|---|---|---|---|---|
| Carga | 28 / 54 ms | 60 / 82 ms | 2900 / 3316 ms | 3,5 req/s |
| Pico | 29 / 1054 ms | 120 / 1083 ms | 3400 / 3975 ms | 2,2 req/s |
| Estresse | 28 / 60 ms | 58 / 89 ms | 5300 / 6411 ms | 3,6 req/s |

### Respostas de regra de negócio (contadas à parte)

| Teste | Matrículas aceitas (201) | 409 | 422 |
|---|---|---|---|
| Carga | 89 | 125 | 0 |
| Pico | 92 | 683 | 0 |
| Estresse | 92 | 6014 | 0 |

Os números de 201/409/422 vieram da saída do terminal. No estresse, a soma (92 + 6014 = 6106) difere em 1 das 6105 requisições `POST /api/matriculas` do `estresse_stats.csv`; provavelmente uma requisição terminou durante o encerramento do teste.

Nenhum 422 em nenhum teste: as combinações sem choque de horário funcionaram. As vagas (230 no total) acabaram com cerca de 90 matrículas, porque cada aluno pega 2 ou 3 disciplinas. Por isso o número de aceitas fica perto de 90 nos três testes, e o restante dos alunos recebe 409 por vagas esgotadas. No pico, 200 alunos disputaram as vagas e só 92 conseguiram matrícula. No estresse, o número alto de 409 vem principalmente dos usuários acima de 200, que repetem alunos já matriculados (ver Limitações).

Integridade das vagas: nenhuma falha registrada nos três testes. Como toda consulta da oferta verifica `vagas < 0` e marca falha, isso mostra que nenhuma disciplina ficou com vaga negativa em nenhum momento.

### Estresse por degrau

p95 geral medido nos últimos segundos de cada degrau (janela do relatório HTML) e vazão total no fim do degrau.

Fonte: o histórico embutido em `resultados/pacote-A/desafio/estresse.html` (um ponto a cada 5 s), que é o que aparece nos gráficos. Cada ponto é o p95 dos últimos ~10 s. O arquivo `resultados/pacote-A/desafio/estresse_stats_history.csv`, gerado na mesma execução, traz valores menores (por exemplo, 520 ms com 100 alunos) porque mede outra coisa: sem a opção `--csv-full-history`, o Locust grava nele o p95 acumulado desde o início do teste, que inclui os primeiros degraus, quando ainda não havia fila. Por isso usamos o HTML para ver cada degrau. Os valores agregados (tabelas acima) são iguais nas duas fontes.

| Alunos | p95 geral (maior valor no degrau) | req/s |
|---|---|---|
| 25 | 260 ms | 8 |
| 50 | 670 ms | 14 |
| 75 | 450 ms | 21 |
| 100 | 1900 ms | 28 |
| 125 | 1900 ms | 38 |
| 150 | 1900 ms | 44 |
| 175 | 2000 ms | 55 |
| 200 | 4300 ms | 60 |
| 225 | 4400 ms | 71 |
| 250 | 4000 ms | 76 |
| 275 | 4900 ms na 1ª janela (fila do degrau anterior); 57 a 66 ms nas demais | 85 |
| 300 a 400 | 57 a 63 ms | 95 a 130 |

### Pico e recuperação

| Momento | Alunos | p95 geral (janela) | req/s |
|---|---|---|---|
| 5 a 60 s | 200 | 480 a 2800 ms | 62 a 78 |
| 65 s (logo após a descida) | 20 | 1400 ms | 53 |
| 70 a 120 s | 20 | 250 a 260 ms | 6 a 7 |

## 4. Análise

**A meta foi atendida em cada teste?** Não. Os três testes reprovaram, e o motivo é o mesmo nos três: o p95 do comprovante passou de 1,5 s (2900, 3400 e 5300 ms). Na carga o p95 geral também passou de 800 ms (1500 ms). Taxa de erro técnico e integridade das vagas foram atendidas em todos.

Na carga a piora acontece com o tempo: o p95 geral fica abaixo de 100 ms nos primeiros 10 s e passa de 800 ms por volta de 40 a 45 s, chegando a 2100–2800 ms no fim. Isso indica uma fila que vai crescendo enquanto os alunos se matriculam e começam a pedir comprovante.

**Qual endpoint piora primeiro? A vazão parou de crescer?** O comprovante. Consultar a oferta e matricular ficaram com p95 entre 28 e 120 ms em todos os testes. A vazão total cresceu quase em linha reta no estresse (de 8 para 130 req/s), então o servidor como um todo não chegou ao limite. Já a vazão do comprovante ficou parada entre 2 e 4 req/s em todos os testes, independente do número de alunos. O comprovante leva cerca de 250 ms e é gerado um de cada vez, o que dá um teto de 4 por segundo; acima disso os pedidos esperam na fila.

**A partir de quantos alunos?** O histórico do relatório HTML guarda o p95 por janela só para o total, não por endpoint. Mas, no estresse, oferta e matrícula nunca passaram de 89 ms, então qualquer p95 geral acima disso vem do comprovante. Com 25 alunos o p95 ficou em 260 ms (o tempo normal de gerar um comprovante, sem fila). Com 50 alunos chegou a 670 ms, ou seja, a fila começa a se formar. No degrau de 100 alunos ficou entre 570 e 940 ms e só no último ponto do degrau chegou a 1900 ms; no de 125 oscilou entre 400 e 1900 ms. Ou seja, o p95 passa da meta de 1,5 s entre 100 e 125 alunos. Como o p95 geral fica abaixo do p95 do comprovante (os outros endpoints são rápidos), o comprovante pode ter passado da meta um pouco antes. Com 200 alunos chegou a 4300 ms.

A partir da segunda janela do degrau de 275 alunos o p95 geral cai para cerca de 60 ms. Isso não é melhora: os comprovantes continuam travados em ~4 por segundo, mas o total de requisições passa de 85 por segundo e os comprovantes viram menos de 5% do total, saindo do p95. Também contribui que, acima de 200 usuários, os alunos se repetem (ver Limitações) e esses usuários extras só consultam a oferta e tentam matricular. É um exemplo de como o p95 geral pode esconder um endpoint ruim; por isso o comprovante tem meta própria.

**O sistema se recuperou?** O estresse terminou em 400 alunos sem fase de descida, então a recuperação foi medida no pico. Logo após a descida de 200 para 20 alunos o p95 ainda estava em 1400 ms (fila acumulada), e de 5 a 10 s depois já estava em 250–260 ms, o tempo normal do comprovante, ficando estável até o fim. O sistema se recupera em cerca de 10 s depois que a carga diminui. No momento do salto, oferta e matrícula chegaram a um máximo de ~1 s, mas o p95 delas continuou baixo (29 e 120 ms).

**As repetições deram resultados parecidos?** Fizemos uma execução de cada tipo. Uma execução anterior da carga, feita no mesmo dia com uma versão do script que ainda não verificava o conteúdo do comprovante, deu p95 do comprovante de 5400 ms e p95 geral de 2600 ms, contra 2900 ms e 1500 ms desta. A conclusão é a mesma (reprova pelo comprovante), mas os números variam bastante entre execuções, porque dependem de quantos alunos se matriculam cedo e de quando a fila se forma.

## 5. Limitações e recomendações

### Limitações

- O sistema só tem 200 alunos cadastrados. No estresse, do usuário 201 em diante o número do aluno volta para 20260001; esses alunos recebem 409 "já matriculado" (regra de negócio, não erro técnico) e tentam de novo a cada sorteio. Isso aumenta o número de POSTs e de 409 no estresse e muda a mistura de requisições acima de 200 usuários.
- Quem recebe 409 por vagas esgotadas também continua tentando, com outra combinação. Depois que as vagas acabam, isso gera muitos 409.
- Não limitamos quantas vezes cada aluno baixa o comprovante. Na carga foram 425 downloads, cerca de 4 a 5 por aluno matriculado, o que é mais do que um aluno real faria e aumenta a fila do comprovante. É um cenário pessimista.
- A verificação de integridade cobre só vagas negativas. Lendo o código do sistema (não medido), vimos que a checagem "aluno já possui matrícula" (`app/app.py` do kit do Pacote A, linha 321) é feita fora da trava que protege as vagas (linha 330). Duas requisições simultâneas do mesmo aluno podem então ser aceitas e descontar vaga duas vezes. No estresse, acima de 200 usuários os alunos se repetem, então isso pode ter acontecido sem ser detectado: o script não confere se cada aluno tem no máximo uma matrícula.
- Uma execução por tipo de teste. Como os resultados variam, o ideal seriam 3 repetições.
- Servidor e Locust rodaram na mesma máquina, disputando o mesmo processador.
- O histórico por janela só foi salvo para o total. Com `--csv-full-history` daria para ter o p95 do comprovante em cada degrau.
- A contagem de 201/409/422 só foi impressa no terminal e foi copiada de lá para este relatório; nas próximas execuções a saída do terminal deve ser salva em arquivo (`| tee`).

### Recomendações

- Gerar os comprovantes em paralelo (mais de um gerador ao mesmo tempo) em vez de um de cada vez. É o que limita o sistema a ~4 comprovantes por segundo.
- Gerar o comprovante uma vez, no momento da matrícula, e guardar. Os downloads seguintes só devolvem o arquivo pronto, sem passar pelo gerador.
- Oferta e matrícula não precisam de mudança: ficaram rápidas em todos os cenários, com 0% de erro e sem vagas negativas, mesmo com 200 alunos entrando de uma vez.
