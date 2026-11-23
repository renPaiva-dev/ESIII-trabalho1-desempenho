# Trabalho 1 – Testes de desempenho (ES III)

**Equipe:** Renato de Paiva Belarmino · Alisson Gabriel

Testes de desempenho com **Locust** nos dois pacotes de prática e no projeto anterior da equipe:

- **Pacote A:** Sabor Express e Matrícula.
- **Pacote B:** Biblioteca e Minicursos.
- **Projeto anterior:** StockMaster, o sistema de estoque e vendas de ES II.

## Estrutura

```
trabalho1-desempenho/
  README.md                      este arquivo
  pacote-A/
    exemplo/                     exemplo resolvido A (Semana do Cliente): locustfile do professor + nosso registro
    desafio/                     desafio A (abertura da matrícula): locustfile, relatório e registro de resultados
  pacote-B/
    exemplo/                     exemplo resolvido B (catálogo da biblioteca)
    desafio/                     desafio B (consulta de minicursos): locustfile, relatório e registro de resultados
  projeto-anterior/              StockMaster: código do sistema, locustfile, script da bateria, relatório e registro
  resultados/                    resultados brutos de cada execução (HTML, CSV e log do Locust)
    pacote-A/exemplo/  pacote-A/desafio/  pacote-B/exemplo/  pacote-B/desafio/  projeto-anterior/
  relatorio.pdf
  slides.pdf
```

Cada relatório (`.md`) fica junto do teste correspondente. O `relatorio.pdf` reúne tudo.

## Versões usadas

| Item | Versão |
|---|---|
| Python | 3.13.14 (Windows 11) e 3.12.3 (Ubuntu 24.04), conforme a máquina de cada execução (ver relatórios) |
| Locust | 2.47.0 |
| Flask (sistema do Pacote A) | 3.1.3 |
| Java / Maven (StockMaster) | JDK 21.0.6 (o projeto exige 17 ou superior) · Maven 3.9.11 · Spring Boot 3.5.15 · banco H2 em memória |

## Preparação (uma vez)

Os sistemas dos pacotes A e B vêm no **kit do professor** (`ESIII_Testes_Funcionais_v2`). Abaixo, `KIT` é a pasta
onde o kit foi descompactado.

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    |   Linux/macOS: source .venv/bin/activate
pip install "locust==2.47.0" "flask>=3.0"
```

> **Windows:** use sempre `http://127.0.0.1:...` em vez de `localhost`. No Windows, `localhost` tenta IPv6 primeiro e
> cada conexão perde cerca de 2 s, o que invalida as medições (ver `pacote-A/exemplo/resultado_exemplo_A.md`).

Os comandos abaixo são para bash. No PowerShell, troque `VAR=valor comando` por `$env:VAR="valor"; comando`.

---

## Pacote A (sistema em `KIT/02_Pacote_A_SaborExpress_Matricula/app/app.py`, porta 5000)

Num terminal separado, deixe o sistema rodando:

```bash
python KIT/02_Pacote_A_SaborExpress_Matricula/app/app.py
```

Antes de **cada** execução, zere os dados: `curl -X POST http://127.0.0.1:5000/api/admin/reset`

### Exemplo resolvido A – Semana do Cliente

```bash
cd pacote-A/exemplo
TIPO_TESTE=carga    locust -f locustfile.py --host http://127.0.0.1:5000 --headless --csv ../../resultados/pacote-A/exemplo/carga    --html ../../resultados/pacote-A/exemplo/carga.html
TIPO_TESTE=estresse locust -f locustfile.py --host http://127.0.0.1:5000 --headless --csv ../../resultados/pacote-A/exemplo/estresse --html ../../resultados/pacote-A/exemplo/estresse.html
```

Registro e comparação com os relatórios de referência: `pacote-A/exemplo/resultado_exemplo_A.md`.

### Desafio A – Abertura da matrícula

O perfil de carga é escolhido por `TIPO_TESTE`: `carga` (100 alunos, 2 min), `pico` (0 → 200 em até 10 s) ou
`estresse` (degraus até 400). Zere os dados antes de cada um.

```bash
cd pacote-A/desafio
TIPO_TESTE=carga    locust -f locustfile_matricula.py --host http://127.0.0.1:5000 --headless --csv ../../resultados/pacote-A/desafio/carga    --html ../../resultados/pacote-A/desafio/carga.html
TIPO_TESTE=pico     locust -f locustfile_matricula.py --host http://127.0.0.1:5000 --headless --csv ../../resultados/pacote-A/desafio/pico     --html ../../resultados/pacote-A/desafio/pico.html
TIPO_TESTE=estresse locust -f locustfile_matricula.py --host http://127.0.0.1:5000 --headless --csv ../../resultados/pacote-A/desafio/estresse --html ../../resultados/pacote-A/desafio/estresse.html
```

Ao final, o script confere o SLA e as vagas negativas. Ele sai com código 1 quando o SLA não é atendido, o que é um
resultado do teste e não um erro do script. Relatório: `pacote-A/desafio/relatorio.md`; registro: `pacote-A/desafio/registro_resultados.csv`.

---

## Pacote B (sistema em `KIT/03_Pacote_B_Biblioteca_Minicursos/app.py`, porta 8000)

```bash
python KIT/03_Pacote_B_Biblioteca_Minicursos/app.py
```

### Exemplo resolvido B – Catálogo

```bash
python -m locust -f pacote-B/exemplo/locustfile.py --host http://127.0.0.1:8000 --headless -u 20 -r 2 -t 90s --stop-timeout 5s --csv resultados/pacote-B/exemplo/carga20_r1 --html resultados/pacote-B/exemplo/carga20_r1.html
```

### Desafio B – Consulta de minicursos

Um comando por patamar e repetição (`N` = 1, 2, 3), a partir da raiz deste repositório:

```bash
python -m locust -f pacote-B/desafio/desafio_locust.py --host http://127.0.0.1:8000 --headless -u U -r R -t T --stop-timeout 5s \
  --csv resultados/pacote-B/desafio/NOME_rN --html resultados/pacote-B/desafio/NOME_rN.html --logfile resultados/pacote-B/desafio/NOME_rN.log
```

| NOME | U (usuários) | R (por segundo) | T (duração) | Repetições |
|---|---|---|---|---|
| verificacao | 1 | 1 | 15s | 1 |
| ref5 | 5 | 1 | 90s | 3 |
| carga20 | 20 | 2 | 90s | 3 |
| estresse50 | 50 | 5 | 90s | 3 |
| estresse100 | 100 | 10 | 90s | 3 |
| recuperacao20 (logo após o estresse100) | 20 | 2 | 90s | 3 |

O script interrompe sozinho a execução se as falhas passarem de 20% ou o p95 passar de 2000 ms por 10 s seguidos.
Quando isso acontece, ele registra `[PARADA]` no log. Relatório: `pacote-B/desafio/relatorio_desempenho.md`; registro:
`pacote-B/desafio/registro_resultados_desempenho.csv`.

---

## Projeto anterior – StockMaster (porta 8080)

Requer JDK 17 ou superior e Maven instalado. O `mvnw` do projeto não funciona, porque a pasta `.mvn/` não existe no
repositório original. Use `mvn`.

```bash
cd projeto-anterior/StockMaster
mvn package -DskipTests          # gera target/stockMaster-0.0.1-SNAPSHOT.jar
cd ..
```

A bateria completa (Git Bash no Windows, ou bash no Linux) reinicia o StockMaster antes de cada repetição, porque o banco
H2 em memória volta a zero. Ela roda referência (5), carga (20), estresse (50 e 100) e recuperação (20), com 90 s cada,
e grava os resultados em `resultados/projeto-anterior/`. Leva cerca de 25 minutos.

```bash
JAR="$PWD/StockMaster/target/stockMaster-0.0.1-SNAPSHOT.jar" PY="$(which python)" ./executar_series.sh 1 2 3
```

No fim de cada execução, o locustfile confere a consistência do estoque e grava a linha `[CONSISTENCIA]` no `.log`.
Relatório: `projeto-anterior/relatorio_desempenho_stockmaster.md`; registro:
`projeto-anterior/registro_resultados_desempenho_stockmaster.csv`.

---

## Observações

- Nenhum teste foi apontado para sistema de terceiros: tudo roda em `127.0.0.1`.
- Os logs da aplicação StockMaster não foram incluídos, porque ficam muito grandes com `show-sql=true`. Os logs do
  Locust estão em `resultados/`.
