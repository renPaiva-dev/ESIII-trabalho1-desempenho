"""
DESAFIO A - Trabalho 1: abertura da matrícula 2026.2 (Locust / Python)

Complete este arquivo conforme o Guia do Aluno (seção Trabalho 1 > Desafio A).

Sistema: app/app.py do kit do Pacote A   (http://localhost:5000)
Zerar antes de cada execução:  POST http://localhost:5000/api/admin/reset

Executar (exemplo, a partir de pacote-A/desafio/; comandos completos no README):
    $env:TIPO_TESTE="carga"; locust -f locustfile_matricula.py --host http://localhost:5000 --headless --csv ../../resultados/pacote-A/desafio/carga --html ../../resultados/pacote-A/desafio/carga.html
    (Linux/macOS: TIPO_TESTE=carga locust -f ...)

Dicas:
  - Cada usuário virtual deve ser um aluno diferente (20260001 ... 20260200).
  - 409 e 422 são regras de negócio: marque com resp.success() e conte à parte.
  - Verifique que nenhuma disciplina fica com vagas negativas.
  - Use o exemplo resolvido (../../solucao-professor/python/locustfile.py) como modelo de
    LoadTestShape e de verificação de SLA, mas NÃO copie: o cenário é outro.
"""
import os
import random
import itertools
import requests
from locust import HttpUser, LoadTestShape, between,events, task
SLA_P95_MS = 800
SLA_ERRO_MAX = 0.01
SLA_POR_ENDPOINT_MS = {"GET /api/matriculas/[id]/comprovante": 1500}

combinacoes = [
    ["ES3", "BD2"],
    ["ES3", "PW2", "IHC"],
    ["RED", "BD2"],
    ["RED", "EMP"],
    ["BD2", "PW2", "EMP"],
    ["IHC", "EMP"],
    ["ES3", "MOB"],
]

class Aluno(HttpUser):
    wait_time = between(1, 4)
    contador = itertools.count(1)
    aceitas = 0
    recusadas_409 = 0
    recusadas_422 = 0

    def on_start(self):
        # TODO: atribuir uma matrícula única a este usuário virtual
        n = next(Aluno.contador)
        numero = (n - 1) % 200 + 1
        self.matricula = str(20260000 + numero)
        self.id_matricula = None

    @task(5)
    def consultar_oferta(self):
        # TODO: GET /api/disciplinas, validar status e conteúdo (vagas >= 0)
        with self.client.get("/api/disciplinas", name="GET /api/disciplinas", catch_response=True) as r:

          if r.status_code != 200:
              r.failure(f"status {r.status_code}")
              return
          for disciplina in r.json():
              if disciplina["vagas"] < 0:
                r.failure(f"vagas negativas em {disciplina['codigo']}: {disciplina['vagas']}")
                return


    # TODO: tarefa para POST /api/matriculas (tratar 201, 409, 422 e erros técnicos)
    @task(2)
    def efetivar_matricula(self):
        if self.id_matricula is not None:
            return
        corpo = {"aluno": self.matricula, "disciplinas": random.choice(combinacoes)}
         
        with self.client.post("/api/matriculas", json=corpo, name="POST /api/matriculas", catch_response=True) as r:
          if r.status_code == 201:
            self.id_matricula = r.json()["id"]
            Aluno.aceitas += 1
          elif r.status_code == 409:
            r.success()
            Aluno.recusadas_409 += 1
          elif r.status_code == 422:
            r.success()
            Aluno.recusadas_422 += 1
          else:
            r.failure(f"status {r.status_code}")


    # TODO: tarefa para GET /api/matriculas/<id>/comprovante
    @task(1)
    def gerar_comprovante(self):
        if self.id_matricula is None:
            return
        with self.client.get(f"/api/matriculas/{self.id_matricula}/comprovante", name="GET /api/matriculas/[id]/comprovante", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"status {r.status_code}")
                return
            dados = r.json()
            if dados["id"] != self.id_matricula or dados["aluno"] != self.matricula:
                r.failure("comprovante nao corresponde a matricula do aluno")




class Perfil(LoadTestShape):
    tipo = os.getenv("TIPO_TESTE", "carga")

    def tick(self):
        # TODO: carga (100 alunos, 2 min), pico (0 -> 200 em até 10 s), estresse (degraus até 400)
        t = self.get_run_time()
        if self.tipo == "carga":
            return (100, 10) if t < 120 else None
        if self.tipo == "estresse":
            degrau = int(t // 30) + 1          # 1, 2, 3, ...
            usuarios = 25 * degrau
            return (usuarios, 25) if usuarios <= 400 else None
        if self.tipo == "pico":
            if t < 60:
                return (200, 200)   # 200 alunos de uma vez
            if t < 120:
                return (20, 100)    # volta pra 20
            return None
        raise ValueError(f"TIPO_TESTE desconhecido: {self.tipo}")

@events.quitting.add_listener
def verificar_sla(environment, **_):
    total = environment.stats.total
    if total.num_requests == 0:
        return
    reprovado = False
    print(f"\naceitas: {Aluno.aceitas} | 409: {Aluno.recusadas_409} | 422: {Aluno.recusadas_422}")

    for disciplina in requests.get(f"{environment.host}/api/disciplinas").json():
        if disciplina["vagas"] < 0:
            print(f"VAGAS NEGATIVAS em {disciplina['codigo']}")
            reprovado = True
    p95 = total.get_response_time_percentile(0.95)
    taxa_erro = total.fail_ratio
    print(f"\n[SLA] geral: p95 = {p95:.0f} ms (limite {SLA_P95_MS}) | "
          f"erros = {taxa_erro:.2%} (limite {SLA_ERRO_MAX:.0%})")
    if p95 > SLA_P95_MS or taxa_erro > SLA_ERRO_MAX:
        reprovado = True
    for nome, limite in SLA_POR_ENDPOINT_MS.items():
        entrada = environment.stats.entries.get((nome, "GET"))
        if entrada and entrada.num_requests:
            p95_ep = entrada.get_response_time_percentile(0.95)
            print(f"[SLA] {nome}: p95 = {p95_ep:.0f} ms (limite {limite})")
            if p95_ep > limite:
                reprovado = True
    print("[SLA] REPROVADO" if reprovado else "[SLA] APROVADO")
    if reprovado:
        environment.process_exit_code = 1

