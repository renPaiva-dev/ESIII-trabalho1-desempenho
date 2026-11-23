# Exemplo resolvido A – Semana do Cliente (registro da execução)

O guia (p.4) pede: rodar o teste de carga e o de estresse, comparar com `resultados-exemplo/` (relatórios de referência que vêm no kit do professor, em `solucao-professor/python/`) e descobrir qual endpoint é o gargalo.

## Execuções

| Teste | Arquivos | Data / hora (UTC) | Ambiente |
|---|---|---|---|
| Carga (50 usuários, 2 min) | `resultados/pacote-A/exemplo/carga.*` | 18/11/2026, 12:12–12:14 | Intel Core i7-13620H, 16 GB (15 GB utilizáveis), Ubuntu 24.04.5 LTS, Python 3.12.3, Flask 3.1.3, Locust 2.47.0; servidor e Locust na mesma máquina |
| Estresse (+25 usuários a cada 30 s, até 250) | `resultados/pacote-A/exemplo/estresse.*` | 22/11/2026, 17:29–17:34 | Intel Core i5-13420H, 8 GB (7,7 GB utilizáveis), Windows 11 Home, Python 3.13.14, Flask 3.1.3, Locust 2.47.0; servidor e Locust na mesma máquina |

Comando do estresse (com os dados zerados antes por `POST /api/admin/reset`):

```
TIPO_TESTE=estresse locust -f locustfile.py --host http://127.0.0.1:5000 --headless --csv ../../resultados/pacote-A/exemplo/estresse --html ../../resultados/pacote-A/exemplo/estresse.html
```

**Atenção no Windows:** a primeira tentativa usou `--host http://localhost:5000` e foi descartada. No Windows, `localhost` é resolvido primeiro para o endereço IPv6 (`::1`), mas o Flask só escuta em IPv4; cada conexão perdia cerca de 2 s antes de cair no IPv4. Todas as requisições, até as mais leves, levaram no mínimo 2017 ms. Com `127.0.0.1` o problema some (o cardápio voltou a ~16 ms).

## Comparação com os relatórios de referência (`resultados-exemplo/`)

p95 por endpoint, em ms:

| Endpoint | Carga – referência | Carga – nossa | Estresse – referência | Estresse – nosso |
|---|---|---|---|---|
| `GET /api/cardapio` | 16 | 17 | 16 | 29 |
| `GET /api/pedidos/[id]` | 4 | 6 | 5 | 16 |
| `POST /api/pedidos` | 36 | 37 | 36 | 49 |
| `GET /api/relatorio/vendas` | 190 | 170 | **13000** | **13000** |
| Agregado | 70 | 72 | 36 | 47 |
| Requisições / req/s | 2805 / 23,3 | 2740 / 22,8 | 18917 / 62,9 | 18822 / 62,6 |
| Falhas | 0 | 0 | 0 | 0 |

O p95 por janela do estresse (`resultados/pacote-A/exemplo/estresse_stats_history.csv`) ficou entre 49 e 110 ms em todos os degraus, e a vazão subiu em linha reta de 11,9 req/s (25 usuários) a 112,4 req/s (250 usuários).

## Conclusão

- **Medido:** os resultados ficaram muito próximos da referência. Na carga, todas as metas foram atendidas (p95 geral 72 ms ≤ 500; relatório 170 ms ≤ 2000; 0% de erro). No estresse, o teste foi reprovado só pelo relatório de vendas: p95 de 13 s, contra a meta de 2 s. Os outros endpoints ficaram abaixo de 50 ms.
- **Gargalo:** `GET /api/relatorio/vendas`. No código (`app/app.py` do kit do Pacote A, linhas 301–302) ele roda dentro de uma trava global (um gerente por vez) e o tempo cresce com o número de pedidos gravados (`0,05 s + 0,0002 s × pedidos`). Quanto mais o teste dura, mais pedidos existem e mais lento o relatório fica.
- **Lição para o desafio:** o p95 agregado do estresse (47 ms) parece ótimo, porque o relatório é só ~3% das requisições. Um endpoint ruim fica escondido no agregado; por isso o professor definiu uma meta própria para ele. Usamos a mesma ideia no Desafio A, com a meta do comprovante.
