"""
kafka/producer.py
-----------------
KafkaProducer singleton com retry e publicação de odds.

O producer é criado uma única vez e reutilizado durante todo o ciclo de vida
do processo. Conexão com retry exponencial de até 20 tentativas.
"""

import json
import logging
import os
import time

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaError

logger = logging.getLogger(__name__)

# Singleton do producer — compartilhado entre todos os módulos
_producer_instance: KafkaProducer | None = None


def get_producer(
    bootstrap_servers: list[str] | None = None,
    max_attempts: int = 20,
    retry_interval_seconds: float = 3.0,
) -> KafkaProducer:
    """
    Retorna o KafkaProducer singleton, criando-o se ainda não existir.

    Tenta conectar ao Kafka até `max_attempts` vezes antes de lançar RuntimeError.
    Útil quando o Kafka ainda está subindo (ex: docker-compose up).

    Args:
        bootstrap_servers: Lista de brokers (ex: ["localhost:29092"]).
                           Se None, usa a variável de ambiente KAFKA_BOOTSTRAP_SERVERS.
        max_attempts: Número máximo de tentativas de conexão. Padrão: 20
        retry_interval_seconds: Pausa entre tentativas em segundos. Padrão: 3.0

    Returns:
        KafkaProducer configurado e conectado.

    Raises:
        RuntimeError: Se não conseguir conectar após todas as tentativas.
    """
    global _producer_instance

    if _producer_instance is not None:
        return _producer_instance

    if bootstrap_servers is None:
        env_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
        bootstrap_servers = [s.strip() for s in env_servers.split(",")]

    logger.info(f"Conectando ao Kafka em: {bootstrap_servers}")

    for attempt in range(1, max_attempts + 1):
        try:
            _producer_instance = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                api_version=(2, 8, 1),
                retries=3,
                acks="all",                    # Aguarda confirmação de todos os réplicas
                request_timeout_ms=30_000,
                max_block_ms=60_000,
            )
            logger.info("✅ Kafka producer conectado com sucesso.")
            return _producer_instance

        except NoBrokersAvailable:
            logger.warning(
                f"Kafka indisponível (tentativa {attempt}/{max_attempts}). "
                f"Aguardando {retry_interval_seconds}s..."
            )
            time.sleep(retry_interval_seconds)

        except Exception as exc:
            logger.error(f"Erro inesperado ao conectar ao Kafka: {exc}")
            time.sleep(retry_interval_seconds)

    raise RuntimeError(
        f"Não foi possível conectar ao Kafka após {max_attempts} tentativas. "
        f"Verifique se o Kafka está rodando em: {bootstrap_servers}"
    )


def publish_odd(producer: KafkaProducer, topic: str, odd: dict) -> bool:
    """
    Publica uma odd no tópico Kafka especificado de forma síncrona.

    Usa future.get(timeout=10) para garantir que a mensagem foi aceita pelo broker
    antes de retornar True. Erros são logados e retornam False sem propagar.

    Args:
        producer: KafkaProducer já conectado (obtido via get_producer())
        topic: Nome do tópico (ex: "raw-odds")
        odd: Dict no schema RawOddDTO

    Returns:
        True se a mensagem foi aceita pelo broker, False em caso de falha.
    """
    try:
        future = producer.send(topic, value=odd)
        record_metadata = future.get(timeout=10)
        logger.debug(
            f"Kafka ✅ | topic={record_metadata.topic} "
            f"partition={record_metadata.partition} "
            f"offset={record_metadata.offset} | "
            f"{odd.get('bookmaker')} | {odd.get('match_id')}"
        )
        return True

    except KafkaError as exc:
        logger.error(
            f"Kafka ❌ | Falha ao publicar odd "
            f"({odd.get('bookmaker')} | {odd.get('match_id')}): {exc}"
        )
        return False

    except Exception as exc:
        logger.error(f"Kafka ❌ | Erro inesperado ao publicar: {exc}")
        return False


def close_producer() -> None:
    """
    Fecha o producer e libera recursos. Deve ser chamado no shutdown da aplicação.
    Faz flush antes de fechar para garantir que mensagens pendentes sejam entregues.
    """
    global _producer_instance
    if _producer_instance is not None:
        try:
            _producer_instance.flush(timeout=10)
            _producer_instance.close()
            logger.info("Kafka producer fechado.")
        except Exception as exc:
            logger.warning(f"Erro ao fechar Kafka producer: {exc}")
        finally:
            _producer_instance = None
