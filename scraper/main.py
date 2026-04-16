import json
import time
import random
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP_SERVERS = ["localhost:29092"]
TOPIC = "raw-odds"


def criar_produtor_com_retry(max_tentativas=20, intervalo_segundos=3):
    tentativa = 1
    while tentativa <= max_tentativas:
        try:
            producer = KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                api_version=(2, 8, 1)
            )
            print("Conectado ao Kafka com sucesso.")
            return producer
            
        except NoBrokersAvailable:
            print(f"Tentativa {tentativa}/{max_tentativas}: Kafka indisponível. Aguardando {intervalo_segundos}s...")
            time.sleep(intervalo_segundos)
            tentativa += 1

    raise RuntimeError("Não foi possível conectar ao Kafka após várias tentativas.")


def extrair_odds_simuladas():
    return {
        "bookmaker": random.choice(["Bet365", "Betano", "Pinnacle"]),
        "match_id": "REAL_x_BARCA_1001",
        "team_home": "Real Madrid",
        "team_away": "Barcelona",
        "odds": {
            "home_win": round(random.uniform(2.10, 2.50), 2),
            "draw": round(random.uniform(3.10, 3.50), 2),
            "away_win": round(random.uniform(2.80, 3.20), 2)
        },
        "timestamp": int(time.time())
    }


def iniciar_bot():
    print("Iniciando scraper...")
    producer = criar_produtor_com_retry()

    try:
        while True:
            dados = extrair_odds_simuladas()

            future = producer.send(TOPIC, value=dados)
            future.get(timeout=10)
            print(f"Odd enviada: {dados['bookmaker']} - Casa: {dados['odds']['home_win']}")

            time.sleep(3)
    except KeyboardInterrupt:
        print("\nBot parado pelo usuário.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    iniciar_bot()