#!/usr/bin/env bash
# Roda a bateria de desempenho do StockMaster (Git Bash no Windows).
#
# Uso:  JAR=/caminho/stockMaster-0.0.1-SNAPSHOT.jar PY=/caminho/python.exe [LOGS=pasta] ./executar_series.sh [repeticoes...]
#       ex.: ./executar_series.sh 1 2 3
#
# Para cada repetição: reinicia o StockMaster (banco H2 em memória volta a zero),
# roda referência, carga, estresse 50, estresse 100 e, logo em seguida, a
# recuperação com 20 usuários. Os resultados vão para ../resultados/projeto-anterior/.
set -u
cd "$(dirname "$0")"
HOST=http://127.0.0.1:8080
: "${JAR:?defina JAR com o caminho do .jar do StockMaster}"
: "${PY:?defina PY com o python que tem o locust}"
LOGS="${LOGS:-/tmp/stockmaster_logs}"
RES=../resultados/projeto-anterior

parar_stockmaster() {
  pid=$(netstat -ano | grep ':8080 ' | grep LISTENING | awk '{print $5}' | head -1)
  [ -n "$pid" ] && taskkill //PID "$pid" //F > /dev/null
  while netstat -ano | grep ':8080 ' | grep -q LISTENING; do read -t 1 < /dev/zero 2>/dev/null; done
}

subir_stockmaster() {
  # show-sql=true do projeto gera um log muito grande: ele fica fora do repositório (LOGS)
  java -jar "$JAR" > "$LOGS/stockmaster_$1.log" 2>&1 &
  until [ "$(curl -s -o /dev/null -w '%{http_code}' $HOST/produtos)" = "200" ]; do
    read -t 1 < /dev/zero 2>/dev/null
  done
}

fase() {  # nome usuarios ritmo duracao
  echo "$(date '+%H:%M:%S') $1 (-u $2 -r $3 -t $4)"
  "$PY" -m locust -f locust_stockmaster.py --host "$HOST" --headless -u "$2" -r "$3" -t "$4" \
    --stop-timeout 5s --csv "$RES/$1" --html "$RES/$1.html" --logfile "$RES/$1.log" --only-summary
  grep -h "\[PARADA\]\|\[CONSISTENCIA\]" "$RES/$1.log" | sed 's/^.*\] /    /'
}

mkdir -p "$RES" "$LOGS"
[ $# -eq 0 ] && set -- 1 2 3
for r in "$@"; do
  parar_stockmaster
  subir_stockmaster "r$r"
  [ "$r" = "1" ] && fase verificacao1_r1 1 1 15s
  fase referencia5_r$r     5   1 90s
  fase carga20_r$r         20  2 90s
  fase estresse50_r$r      50  5 90s
  fase estresse100_r$r     100 10 90s
  fase recuperacao20_r$r   20  2 90s
done
parar_stockmaster
