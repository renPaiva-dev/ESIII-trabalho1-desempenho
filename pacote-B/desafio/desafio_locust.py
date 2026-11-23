"""Novo desafio: complete as tarefas e as verificações conforme o roteiro.
Mistura exigida: 70% de listagem e 30% de detalhe em expectativa.
O peso define probabilidade, não uma proporção exata por execução.
"""
import logging

import gevent
from locust import HttpUser, task, between, events

# Critério de parada do guia (p.7): parar o teste se as falhas passarem de 20%
# por 10 s seguidos ou se o p95 passar de 2000 ms por 10 s seguidos.
# A função vigiar roda junto com o teste (gevent.spawn, como no exemplo da
# documentação do Locust) e confere os números a cada 1 segundo.


def vigiar(environment):
    requisicoes_antes = 0
    falhas_antes = 0
    segundos_com_falhas = 0
    segundos_com_p95_alto = 0

    while True:
        gevent.sleep(1)
        total = environment.runner.stats.total

        # requisições e falhas só do último segundo
        requisicoes = total.num_requests - requisicoes_antes
        falhas = total.num_failures - falhas_antes
        requisicoes_antes = total.num_requests
        falhas_antes = total.num_failures

        if requisicoes > 0 and falhas / requisicoes > 0.20:
            segundos_com_falhas += 1
        else:
            segundos_com_falhas = 0

        p95 = total.get_current_response_time_percentile(0.95) or 0
        if p95 > 2000:
            segundos_com_p95_alto += 1
        else:
            segundos_com_p95_alto = 0

        if segundos_com_falhas >= 10:
            logging.warning("[PARADA] falhas acima de 20% por 10 s seguidos: teste interrompido (criterio de parada do plano)")
            environment.runner.quit()
            return
        if segundos_com_p95_alto >= 10:
            logging.warning("[PARADA] p95 acima de 2000 ms por 10 s seguidos: teste interrompido (criterio de parada do plano)")
            environment.runner.quit()
            return


@events.init.add_listener
def iniciar_vigia(environment, **kwargs):
    gevent.spawn(vigiar, environment)


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
