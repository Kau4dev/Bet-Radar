"""
e2e_validate.py
----------------
Script de validacao end-to-end do pipeline BetRadar.

Testa o fluxo completo:
  1. Publica uma odd sintetica no Kafka (topico raw-odds)
  2. Aguarda o backend processar e gerar o alerta
  3. Consulta a API REST /api/v1/opportunities para confirmar o alerta

Uso:
    python e2e_validate.py [--match "Flamengo x Vasco"] [--timeout 30]

Requisitos:
  - Backend Spring Boot rodando em http://localhost:8080
  - Kafka acessivel em localhost:29092
  - Variaveis de ambiente: JWT_E2E_TOKEN (ou SEED_USERNAME + SEED_PASSWORD)

O script retorna exit code 0 em sucesso, 1 em falha.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("e2e")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "raw-odds")


# ---------------------------------------------------------------------------
# Autenticacao
# ---------------------------------------------------------------------------

def get_jwt_token(username: str, password: str) -> str:
    """Autentica no backend e retorna o JWT."""
    url = f"{BACKEND_URL}/api/v1/auth/login"
    try:
        resp = httpx.post(url, json={"username": username, "password": password}, timeout=10)
        resp.raise_for_status()
        token = resp.json().get("token") or resp.json().get("accessToken")
        if not token:
            raise ValueError(f"Token nao encontrado na resposta: {resp.json()}")
        logger.info("Autenticacao no backend OK.")
        return token
    except Exception as e:
        logger.error(f"Falha ao autenticar no backend: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Publicacao no Kafka
# ---------------------------------------------------------------------------

def publish_synthetic_odd(match_query: str) -> dict:
    """
    Publica uma odd sintetica no Kafka para simular o scraper.
    Retorna o payload publicado.
    """
    try:
        from kafka import KafkaProducer
    except ImportError:
        logger.error("kafka-python nao instalado. Rode: pip install kafka-python")
        sys.exit(1)

    parts = None
    for sep in [" x ", " vs ", " X ", " VS ", " versus "]:
        if sep in match_query:
            parts = match_query.split(sep, 1)
            break

    if not parts or len(parts) < 2:
        logger.error(f"Nao foi possivel separar os times de: '{match_query}'")
        sys.exit(1)

    home, away = parts[0].strip(), parts[1].strip()

    # Odd com EV+ intencional: home_win muito acima da media esperada
    payload = {
        "matchId": f"{home.lower().replace(' ', '_')}_v_{away.lower().replace(' ', '_')}_e2e",
        "bookmaker": "E2E-TestBookmaker",
        "teamHome": home,
        "teamAway": away,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "odds": {
            "homeWin": 5.00,   # Odd artificialmente alta para garantir EV+
            "draw": 3.20,
            "awayWin": 2.50,
        },
    }

    # Segunda odd de outra "casa" para a media do mercado ser calculada
    payload_ref = {
        "matchId": payload["matchId"],
        "bookmaker": "E2E-ReferenceBookmaker",
        "teamHome": home,
        "teamAway": away,
        "timestamp": payload["timestamp"],
        "odds": {
            "homeWin": 2.00,
            "draw": 3.20,
            "awayWin": 2.50,
        },
    }

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            api_version=(2, 8, 1),
            retries=3,
            acks="all",
        )
        for p in [payload_ref, payload]:
            future = producer.send(KAFKA_TOPIC, value=p)
            future.get(timeout=10)
            logger.info(f"Publicado no Kafka: {p['bookmaker']} | {p['matchId']}")

        producer.flush()
        producer.close()
        return payload

    except Exception as e:
        logger.error(f"Falha ao publicar no Kafka: {e}")
        logger.error("Verifique se o Kafka esta rodando: docker-compose up -d")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Polling da API REST
# ---------------------------------------------------------------------------

def wait_for_alert(token: str, match_id: str, timeout_s: int) -> bool:
    """
    Faz polling em GET /api/v1/opportunities ate encontrar um alerta
    para o match_id publicado ou esgotar o timeout.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BACKEND_URL}/api/v1/opportunities"
    deadline = time.time() + timeout_s
    attempt = 0

    logger.info(f"Aguardando alerta para match_id='{match_id}' (timeout={timeout_s}s)...")

    while time.time() < deadline:
        attempt += 1
        try:
            resp = httpx.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                alerts = resp.json()
                if isinstance(alerts, list):
                    for alert in alerts:
                        # Aceita match por matchId ou por nome do bookmaker de teste
                        mid = alert.get("matchId", "") or alert.get("match", {}).get("id", "")
                        bk = alert.get("bookmakerName", "") or ""
                        if match_id in mid or "E2E-TestBookmaker" in bk:
                            logger.info(f"Alerta encontrado na tentativa {attempt}: {alert}")
                            return True
            else:
                logger.debug(f"[tentativa {attempt}] HTTP {resp.status_code}")
        except Exception as e:
            logger.debug(f"[tentativa {attempt}] Erro na requisicao: {e}")

        time.sleep(3)

    return False


# ---------------------------------------------------------------------------
# Checagem de saude dos servicos
# ---------------------------------------------------------------------------

def check_backend_health() -> bool:
    """Verifica se o backend esta respondendo."""
    try:
        resp = httpx.get(f"{BACKEND_URL}/actuator/health", timeout=5)
        return resp.status_code in (200, 404)  # 404 = sem actuator mas esta de pe
    except Exception:
        return False


def check_kafka_connectivity() -> bool:
    """Verifica se o Kafka esta acessivel."""
    try:
        from kafka import KafkaAdminClient
        admin = KafkaAdminClient(
            bootstrap_servers=KAFKA_SERVERS.split(","),
            client_id="e2e-health-check",
            request_timeout_ms=5000,
        )
        admin.close()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validacao end-to-end BetRadar")
    parser.add_argument("--match", default="E2E Flamengo x E2E Vasco",
                        help="Partida a simular (ex: 'Flamengo x Vasco')")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Segundos maximos esperando o alerta aparecer na API")
    parser.add_argument("--username", default=os.getenv("SEED_USERNAME", "admin"),
                        help="Usuario admin do backend")
    parser.add_argument("--password", default=os.getenv("SEED_PASSWORD", "admin123"),
                        help="Senha do admin do backend")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  BetRadar — Validacao End-to-End")
    print("=" * 60)

    # 1. Saude dos servicos
    logger.info("Verificando saude dos servicos...")

    if not check_backend_health():
        logger.error(f"Backend nao acessivel em {BACKEND_URL}")
        logger.error("Execute: cd backend && .\\mvnw.cmd spring-boot:run")
        sys.exit(1)
    logger.info("Backend OK.")

    if not check_kafka_connectivity():
        logger.error(f"Kafka nao acessivel em {KAFKA_SERVERS}")
        logger.error("Execute: docker-compose up -d")
        sys.exit(1)
    logger.info("Kafka OK.")

    # 2. Autenticacao
    token = os.getenv("JWT_E2E_TOKEN") or get_jwt_token(args.username, args.password)

    # 3. Publica odd sintetica no Kafka
    payload = publish_synthetic_odd(args.match)
    match_id = payload["matchId"]

    # 4. Aguarda alerta aparecer na API
    found = wait_for_alert(token, match_id, args.timeout)

    # 5. Resultado
    print()
    print("=" * 60)
    if found:
        print("  RESULTADO: SUCESSO ✅")
        print(f"  Pipeline completo: Kafka -> Backend -> Alerta detectado")
        print(f"  Partida: {args.match}")
        print("=" * 60)
        sys.exit(0)
    else:
        print("  RESULTADO: FALHA ❌")
        print(f"  Nenhum alerta encontrado em {args.timeout}s para: {args.match}")
        print()
        print("  Possiveis causas:")
        print("  - EV threshold nao atingido (verifique OddProcessorService)")
        print("  - Backend ainda processando (tente --timeout maior)")
        print("  - Consumer Kafka nao conectado ao topico 'raw-odds'")
        print("  - Verifique logs: cd backend && .\\mvnw.cmd spring-boot:run")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
