# Plano e Relatório de Teste de Desempenho

Equipe: Renato de Paiva Belarmino e Alisson Gabriel   Pacote/Projeto: Pacote B – Desafio B (consulta de minicursos)   Data: 17/11/2026 (plano); 18/11/2026 e 22/11/2026 (execuções)

> Observação: o plano (seção 1) foi escrito em 17/11/2026, antes das execuções, no modelo da disciplina. As execuções seguiram esses parâmetros (operações, proporção, fases, repetições e metas). A exceção foi o critério de parada, que na rodada de 18/11 não foi aplicado (ver abaixo).
>
> Na primeira rodada (18/11) o critério de parada não estava automatizado e o Estresse 2 rodou os 90 s inteiros, acima do limite de falhas. Em 22/11 acrescentamos a parada automática ao script e **refizemos o Estresse 2 e a Recuperação** (3 repetições cada). As execuções originais desses dois patamares foram guardadas em `resultados/pacote-B/desafio/execucao_18-11_sem_parada/`.

## 1. Plano

| Item | Preenchimento |
|---|---|
| Pergunta / hipótese | Com 20 usuários, a consulta de minicursos atende p95 ≤ 500 ms e falhas ≤ 1%. Depois do estresse, volta a essas metas em até 30 s com 20 usuários. |
| Operações testadas e proporção | `GET /api/cursos` com peso 7 (70%) e `GET /api/cursos/1` com peso 3 (30%). |
| Verificações de conteúdo | Lista: HTTP 200, `total = 3` e o curso "Python" presente nos itens. Detalhe: HTTP 200, `id = 1`, `nome = Python` e `vagas = 2`. JSON inválido ou campo ausente também conta como falha. Timeout de 5 s por requisição. |
| Think time (pausa entre ações) | 0,2 a 0,6 s (`between(0.2, 0.6)`) |
| Massa de dados | Não se aplica: as duas operações só leem os 3 cursos fixos do sistema. |
| Perfis (usuários, ritmo, duração) | Verificação: 1 usuário, 15 s. Referência: 5 usuários (r = 1/s), 90 s. Carga: 20 (r = 2/s), 90 s. Estresse 1: 50 (r = 5/s), 90 s. Estresse 2: 100 (r = 10/s), até 90 s. Recuperação: 20 (r = 2/s), 90 s, iniciada logo após o Estresse 2. Pico: não exigido no Desafio B. |
| Repetições | 3 por patamar (r1, r2, r3). A verificação inicial foi feita 1 vez. |
| Metas (SLA) | p95 ≤ 500 ms; falhas ≤ 1%; recuperação às metas em até 30 s com 20 usuários. |
| Critério de parada | Interromper se a máquina ficar instável, se as falhas passarem de 20% por 10 s ou se o p95 passar de 2000 ms por 10 s. Automatizado no script a partir de 22/11: a cada segundo ele calcula a taxa de falhas daquele segundo e o p95 recente; com 10 segundos seguidos acima do limite, encerra o teste e registra `[PARADA]` no log. |

Comando usado (exemplo da carga, repetição 1):

```
python -m locust -f pacote-B/desafio/desafio_locust.py --host http://127.0.0.1:8000 --headless -u 20 -r 2 -t 90s --stop-timeout 5s --csv resultados/pacote-B/desafio/carga20_r1 --html resultados/pacote-B/desafio/carga20_r1.html
```

## 2. Ambiente

| Item | Rodada de 18/11 (verificação, referência, carga, estresse 1) | Rodada de 22/11 (estresse 2 e recuperação) |
|---|---|---|
| Processador / memória | Intel Core i7-13620H / 16 GB (15 GB utilizáveis; GPU RTX 3050, não usada pelo teste) | Intel Core i5-13420H / 8 GB (7,7 GB utilizáveis; GPU RTX 2050 4 GB, não usada pelo teste) |
| Sistema operacional | Ubuntu 24.04.5 LTS | Windows 11 Home |
| Python (versão) | Python 3.12.3 | Python 3.13.14 |
| Ferramenta e versão | Locust 2.47.0, headless | Locust 2.47.0, headless |
| Servidor e gerador de carga na mesma máquina? | Sim (`127.0.0.1`) | Sim (`127.0.0.1`) |

## 3. Resultados

Fonte única: os arquivos `resultados/pacote-B/desafio/*_stats.csv` e `*_stats_history.csv` do Locust. Os totais impressos nos `.log` são um pouco maiores, porque incluem requisições terminadas durante o `--stop-timeout`; por isso não foram usados. Relatórios completos com gráficos em `resultados/pacote-B/desafio/*.html`. Uma linha por execução em `pacote-B/desafio/registro_resultados_desempenho.csv`.

### Exemplo resolvido B (catálogo)

`GET /api/livros?q=software`, 20 usuários, 90 s (arquivos em `resultados/pacote-B/exemplo/carga20_r1.*`, 18/11 às 13:22): 3897 requisições, 0 falhas, p50 34 ms, p95 37 ms, 43,7 req/s. Meta atendida. Serviu de modelo para a estrutura do script do desafio.

### Resumo por patamar (agregado de cada execução)

| Patamar | Usuários | Requisições (r1 / r2 / r3) | p50 | p95 | req/s (média) | Falhas | Meta |
|---|---|---|---|---|---|---|---|
| Verificação | 1 | 33 | 36 ms | 37 ms | 2,4 | 0% | atende |
| Referência | 5 | 1001 / 992 / 1007 | 35 ms | 36–37 ms | 11,2 | 0% | atende |
| Carga | 20 | 3880 / 3918 / 3887 | 35 ms | 37 ms | 43,7 | 0% | atende |
| Estresse 1 | 50 | 9490 / 9534 / 9520 | 40 ms | 71–75 ms | 106,6 | 0,00–0,02% | atende |
| Estresse 2 (interrompido aos 18–19 s) | 100 | 2717 / 2698 / 2706 | 110–120 ms | 140 ms | 148,0 | 23,5–24,0% | **não atende** |
| Recuperação | 20 | 3903 / 3869 / 3876 | 33–34 ms | 38–44 ms | 43,5 | 0% | atende |

No Estresse 2, o agregado inclui a rampa de 0 a 100 usuários (os primeiros ~9 s), por isso a vazão e a taxa de falhas ficam abaixo dos valores do patamar.

### Patamar estável (janelas do `stats_history` depois que todos os usuários entraram)

| Patamar | p95 por janela | req/s | Falhas |
|---|---|---|---|
| Carga 20 | 37–38 ms | 44,1–44,5 | 0% |
| Estresse 50 | 71–81 ms | 108,1–108,3 | ≈ 0% |
| Estresse 100 (cerca de 10 s, até a parada) | 140 ms | 191–193 (sucesso: 132) | 31% |
| Recuperação 20 | 37–46 ms | 44,8–45,5 | 0% |

### Estresse 2: início das falhas e parada automática

| Repetição | Primeira falha | Falhas > 20% (por segundo) | Parada | Com 100 usuários: total / com sucesso |
|---|---|---|---|---|
| r1 | t = 6 s, 70 usuários (129 req/s) | t = 9 a 18 s | 18 s | 193 / 132 req/s |
| r2 | t = 5 s, 60 usuários (113 req/s) | t = 9 a 18 s | 18 s | 191 / 132 req/s |
| r3 | t = 6 s, 70 usuários (130 req/s) | t = 9 a 19 s | 19 s | 193 / 132 req/s |

### Falhas

Todas as falhas registradas foram `HTTP 503` ("Capacidade didática ocupada"). Nenhuma falha de conteúdo (lista ou detalhe incorreto) em nenhuma execução.

| Execução | Total de falhas (r1 / r2 / r3) |
|---|---|
| Estresse 1 (50 usuários) | 2 / 0 / 1 |
| Estresse 2 (100 usuários) | 652 / 635 / 644 |

### Proporção real das operações

70/30 configurado; nas execuções de 90 s de 18/11, `GET /api/cursos` ficou entre 68,8% e 71,7% do total (na verificação, com só 33 requisições, foi 66,7%). Os pesos definem probabilidade, não proporção exata.

### Recuperação

| Execução | Intervalo entre o fim do Estresse 2 e o início da recuperação | Primeiras janelas com 20 usuários |
|---|---|---|
| r1 | 1 s (19:10:17 → 19:10:18) | p95 37 ms, 0 falhas |
| r2 | 2 s (19:12:07 → 19:12:09) | p95 46 ms, 0 falhas |
| r3 | 2 s (19:13:59 → 19:14:01) | p95 37 ms, 0 falhas |

Em todas, o p95 ficou entre 37 e 46 ms e não houve falhas desde a primeira janela.

## 4. Análise

**A meta foi atendida em cada teste? Em qual patamar deixou de ser?**
Medido: com 5, 20 e 50 usuários as metas foram atendidas nas 3 repetições. O primeiro patamar que viola a meta é o de **100 usuários**, pelo critério de falhas: com todos os usuários ativos, cerca de 31% das requisições receberam HTTP 503, contra o limite de 1%. O teste foi interrompido pelo critério de parada aos 18–19 s nas 3 repetições. O p95 continuou dentro da meta (140 ms ≤ 500 ms).

Interpretação: o p95 baixo no estresse de 100 não significa que o sistema estava bem. As respostas 503 voltam rápido (o servidor desiste depois de esperar 100 ms por uma vaga), então elas puxam o tempo para baixo. Olhar só o p95 esconderia o problema; por isso a meta tem dois critérios.

**Qual endpoint piora primeiro? A vazão parou de crescer em algum ponto?**
Medido: os dois endpoints pioram juntos. O p95 de `cursos` e de `curso 1` foi igual ou quase igual em todos os patamares (37/37 ms na carga, 71–75/72–74 ms no estresse de 50, 140/140 ms no de 100). A vazão total subiu de 43,7 (20 usuários) para 106,6 req/s (50 usuários). Durante a rampa do Estresse 2, as primeiras falhas apareceram com 60–70 usuários (113–130 req/s). Com 100 usuários, as respostas **com sucesso** ficaram paradas em 132 req/s nas 3 repetições, mesmo com 191–193 req/s chegando ao servidor. A vazão útil parou de crescer aí.

Interpretação: os dois endpoints passam pelo mesmo limite do servidor, que aceita só 4 consultas ao mesmo tempo, cada uma com cerca de 30 ms de atraso artificial (`app.py`, linhas 10 e 29–32). Isso dá um teto teórico de 4 / 0,03 s ≈ 133 respostas por segundo, praticamente o valor medido (132). Com 50 usuários a demanda (≈ 107 req/s) ainda cabia nesse teto; a partir de 60–70 usuários passou dele, e o excedente virou 503.

**O sistema se recuperou após o estresse? Em quanto tempo?**
Medido: sim. Nas 3 repetições a recuperação começou 1 a 2 s depois da parada do estresse, e desde a primeira janela o p95 ficou entre 37 e 46 ms, sem falhas. A meta de voltar em até 30 s foi atendida. Os valores da recuperação (43,5 req/s em média) ficaram iguais aos da carga de 20 (43,7 req/s).

Interpretação: a recuperação é imediata porque o servidor não acumula fila nem estado com a sobrecarga: quem não consegue vaga recebe 503 na hora.

**As repetições deram resultados parecidos? O que explica as diferenças?**
Medido: sim, muito parecidos. A vazão variou menos de 1% entre r1, r2 e r3 em quase todos os patamares (1,5% na referência, que tem poucas requisições). O p95 variou no máximo 4 ms no estresse de 50 (71 a 75 ms) e ficou igual (140 ms) nas 3 repetições do estresse de 100. A vazão com sucesso no estresse de 100 foi 132 req/s nas três. A diferença mais visível foi o número de 503 no estresse de 50 (2, 0 e 1 em cerca de 9500 requisições) e o momento da primeira falha no estresse de 100 (60 ou 70 usuários).

Interpretação: o sistema tem atraso fixo e não usa banco nem disco, por isso varia pouco. Os poucos 503 com 50 usuários são momentos em que, por acaso, mais de 4 requisições chegaram juntas e uma esperou mais de 100 ms.

## 5. Limitações e recomendações

### Limitações

- **Duas máquinas.** O Estresse 2 e a Recuperação foram refeitos em 22/11 em outra máquina (ver Ambiente): em 18/11 um notebook com Ubuntu, i7-13620H e 16 GB; em 22/11 um com Windows 11, i5 e 8 GB. A comparação entre esses patamares e os de 18/11 deve ser feita com cuidado. Mesmo assim, os números que importam bateram: a recuperação deu os mesmos valores da carga de 18/11 (43,5 contra 43,7 req/s) e as execuções originais do Estresse 2 tiveram a mesma taxa de falhas no patamar (≈ 31%) e vazão parecida (186–187 req/s em 18/11, contra 191–193 req/s em 22/11). Isso é esperado, porque o limite do sistema é artificial e não depende do processador.
- As execuções originais do Estresse 2 (18/11, em `resultados/pacote-B/desafio/execucao_18-11_sem_parada/`) não respeitaram o critério de parada: rodaram os 90 s com ≈ 31% de falhas. Foram substituídas pelas de 22/11 e mantidas só como registro.
- Servidor e Locust rodaram na mesma máquina, disputando o mesmo processador.
- O limite de 4 consultas simultâneas e o atraso de 30 ms são artificiais (o próprio README do pacote avisa). Os números servem para estudar as métricas, não para estimar a capacidade de um sistema real.
- A verificação inicial foi feita uma vez e não tem arquivo `.log`.

### Recomendações

- Para o teste: a parada automática deve ficar no script para as próximas execuções. Um patamar fixo de 60 ou 75 usuários mediria a saturação com mais precisão do que a rampa.
- Para o sistema: o gargalo é o limite de 4 consultas simultâneas. Como a lista de cursos muda pouco, guardar a resposta em cache, ou aumentar o limite, eliminaria os 503 nesse volume. Se o limite for mantido de propósito, o cliente deveria receber um aviso de "tente novamente em instantes" em vez de um erro.
