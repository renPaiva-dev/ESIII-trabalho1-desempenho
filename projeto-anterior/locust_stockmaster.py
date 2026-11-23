"""Teste de desempenho do projeto anterior (StockMaster) com Locust.

Operações (operador de loja usando o sistema):
  GET  /produtos                 peso 6 (60%)  consultar o estoque
  POST /vendas                   peso 3 (30%)  registrar uma venda de 2 itens
  GET  /relatorios/vendas/resumo peso 1 (10%)  gerente consultando o resumo

Massa de dados: no início de cada execução são criados 2 produtos com estoque
enorme (a venda nunca falha por falta de estoque) e nomes únicos.

Ao final, confere a consistência do estoque: cada venda gravada pelo servidor
baixa 1 unidade do produto A e 2 do produto B. Se o estoque baixou menos do
que isso, houve "atualização perdida" (vendas simultâneas sem trava).
"""
import json
import logging
import time
import urllib.request
from decimal import Decimal

import gevent
from locust import HttpUser, between, events, task
from locust.runners import WorkerRunner

# ---------- critério de parada (igual ao do guia, p.7) ----------
LIMITE_FALHAS = 0.20
LIMITE_P95_MS = 2000
SEGUNDOS_SEGUIDOS = 10


@events.init.add_listener
def criterio_de_parada(environment, **_):
    if isinstance(environment.runner, WorkerRunner):
        return

    def vigiar():
        req_antes = falhas_antes = 0
        seg_falhas = seg_p95 = 0
        while True:
            gevent.sleep(1)
            total = environment.runner.stats.total
            req = total.num_requests - req_antes
            falhas = total.num_failures - falhas_antes
            req_antes, falhas_antes = total.num_requests, total.num_failures
            taxa = falhas / req if req else 0                       # falhas no último segundo
            p95 = total.get_current_response_time_percentile(0.95) or 0
            seg_falhas = seg_falhas + 1 if taxa > LIMITE_FALHAS else 0
            seg_p95 = seg_p95 + 1 if p95 > LIMITE_P95_MS else 0
            if seg_falhas >= SEGUNDOS_SEGUIDOS or seg_p95 >= SEGUNDOS_SEGUIDOS:
                motivo = (f"falhas acima de {LIMITE_FALHAS:.0%}" if seg_falhas >= SEGUNDOS_SEGUIDOS
                          else f"p95 acima de {LIMITE_P95_MS} ms")
                logging.warning("[PARADA] %s por %d s seguidos: teste interrompido "
                                "(criterio de parada do plano)", motivo, SEGUNDOS_SEGUIDOS)
                environment.runner.quit()
                return

    gevent.spawn(vigiar)


# ---------- massa de dados e conferência de consistência ----------
ESTOQUE_INICIAL = 10_000_000
PRECO_A, PRECO_B = Decimal("2.50"), Decimal("10.00")
QTD_A, QTD_B = 1, 2
TOTAL_ESPERADO = PRECO_A * QTD_A + PRECO_B * QTD_B          # R$ 22,50 (3 itens: sem desconto)
massa = {}


def chamar(host, metodo, caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    pedido = urllib.request.Request(host + caminho, data=dados, method=metodo,
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.loads(resposta.read())


@events.test_start.add_listener
def preparar_massa(environment, **_):
    if isinstance(environment.runner, WorkerRunner):
        return
    host, sufixo = environment.host, str(int(time.time()))
    for chave, preco in (("a", PRECO_A), ("b", PRECO_B)):
        produto = chamar(host, "POST", "/produtos", {
            "nome": f"Carga-{chave.upper()}-{sufixo}", "preco": float(preco),
            "quantidade": ESTOQUE_INICIAL, "estoqueMinimo": 0, "descricao": "massa do teste de carga"})
        massa[chave] = produto["id"]
    massa["vendas_antes"] = chamar(host, "GET", "/relatorios/vendas/resumo")["totalVendas"]
    logging.info("[MASSA] produtos A=%s B=%s; vendas ja gravadas=%s", massa["a"], massa["b"], massa["vendas_antes"])


@events.quitting.add_listener
def conferir_consistencia(environment, **_):
    if isinstance(environment.runner, WorkerRunner) or "a" not in massa:
        return
    host = environment.host
    gevent.sleep(2)  # deixa terminar alguma venda que ainda esteja sendo gravada
    vendas = chamar(host, "GET", "/relatorios/vendas/resumo")["totalVendas"] - massa["vendas_antes"]
    baixa_a = ESTOQUE_INICIAL - chamar(host, "GET", f"/produtos/{massa['a']}")["quantidade"]
    baixa_b = ESTOQUE_INICIAL - chamar(host, "GET", f"/produtos/{massa['b']}")["quantidade"]
    perdidas_a, perdidas_b = vendas * QTD_A - baixa_a, vendas * QTD_B - baixa_b
    situacao = "OK" if perdidas_a == 0 and perdidas_b == 0 else "DIVERGENTE"
    logging.warning("[CONSISTENCIA] %s: vendas gravadas=%d; baixa A=%d (esperado %d); baixa B=%d (esperado %d); "
                    "baixas perdidas A=%d B=%d", situacao, vendas, baixa_a, vendas * QTD_A,
                    baixa_b, vendas * QTD_B, perdidas_a, perdidas_b)


# ---------- usuário virtual ----------
class Operador(HttpUser):
    wait_time = between(0.5, 1.5)   # pausa de um operador entre uma ação e outra

    @task(6)
    def listar_produtos(self):
        with self.client.get("/produtos", name="GET /produtos", catch_response=True, timeout=5) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                ids = {p["id"] for p in r.json()}
                if not {massa["a"], massa["b"]} <= ids:
                    r.failure("Produtos da massa ausentes na lista")
            except (ValueError, KeyError, TypeError):
                r.failure("Resposta inválida")

    @task(3)
    def registrar_venda(self):
        corpo = {"itens": [{"produtoId": massa["a"], "quantidade": QTD_A},
                           {"produtoId": massa["b"], "quantidade": QTD_B}]}
        with self.client.post("/vendas", json=corpo, name="POST /vendas", catch_response=True, timeout=5) as r:
            if r.status_code != 201:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                d = r.json()
                if Decimal(str(d["valorTotal"])) != TOTAL_ESPERADO or len(d["itens"]) != 2:
                    r.failure("Venda com total ou itens incorretos")
            except (ValueError, KeyError, TypeError, ArithmeticError):
                r.failure("Resposta inválida")

    @task(1)
    def resumo_vendas(self):
        with self.client.get("/relatorios/vendas/resumo", name="GET /relatorios/vendas/resumo",
                             catch_response=True, timeout=5) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            try:
                d = r.json()
                if int(d["totalVendas"]) < 0 or Decimal(str(d["valorTotalAcumulado"])) < 0:
                    r.failure("Resumo inválido")
            except (ValueError, KeyError, TypeError, ArithmeticError):
                r.failure("Resposta inválida")
