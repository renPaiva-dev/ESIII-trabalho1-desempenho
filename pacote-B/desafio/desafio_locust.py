"""Novo desafio: complete as tarefas e as verificações conforme o roteiro.
Mistura exigida: 70% de listagem e 30% de detalhe em expectativa.
O peso define probabilidade, não uma proporção exata por execução.
"""
import logging

import gevent
from locust import HttpUser, task, between, events
from locust.runners import WorkerRunner

# Critério de parada do guia (p.7): interromper se as falhas passarem de 20%
# por 10 s ou se o p95 passar de 2000 ms por 10 s.
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


class Visitante(HttpUser):
    wait_time = between(0.2, 0.6)

    @task(7)
    def listar_cursos(self):
        with self.client.get('/api/cursos', name='cursos', catch_response=True, timeout=5) as r:
            if r.status_code != 200:
                r.failure(f'HTTP {r.status_code}')
                return
            try:
                d = r.json()
                nomes = [curso['nome'] for curso in d['itens']]
                if d['total'] != 3 or 'Python' not in nomes:
                    r.failure('Lista de cursos incorreta')
            except (ValueError, KeyError, TypeError):
                r.failure('Resposta inválida')

    @task(3)
    def detalhar_curso(self):
        with self.client.get('/api/cursos/1', name='curso 1', catch_response=True, timeout=5) as r:
            if r.status_code != 200:
                r.failure(f'HTTP {r.status_code}')
                return
            try:
                d = r.json()
                if d['id'] != 1 or d['nome'] != 'Python' or d['vagas'] != 2:
                    r.failure('Detalhe do curso incorreto')
            except (ValueError, KeyError, TypeError):
                r.failure('Resposta inválida')
