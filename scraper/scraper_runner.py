"""
scraper_runner.py
------------------
Orquestrador principal do scraper BetRadar.

Recebe uma match_query do bot Telegram, dispara todos os extractors
em paralelo via asyncio.gather, valida as odds coletadas e publica
cada uma no Kafka (tópico: raw-odds).

Uso:
    import asyncio
    from scraper_runner import run
    count = asyncio.run(run("Flamengo x Vasco"))
"""

import asyncio
import logging
import os

from extractors import ALL_EXTRACTORS
from kafka_client.producer import get_producer, publish_odd

logger = logging.getLogger(__name__)

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "raw-odds")
KAFKA_SERVERS = [s.strip() for s in os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092").split(",")]

# Campos obrigatórios no schema RawOddDTO
_REQUIRED_FIELDS = {"bookmaker", "match_id", "team_home", "team_away", "odds", "timestamp"}


def _validate_odd(odd: dict) -> bool:
    """
    Valida que um dict de odd possui todos os campos obrigatórios e valores válidos.
    Espelha a lógica de OddProcessorService.validateInput() do backend Java.

    Returns:
        True se a odd é válida para publicação no Kafka.
    """
    if not isinstance(odd, dict):
        return False

    # Verifica campos de nível raiz
    missing = _REQUIRED_FIELDS - odd.keys()
    if missing:
        logger.debug(f"Odd descartada — campos faltando: {missing}")
        return False

    # Verifica campos string não-vazios
    for field in ("bookmaker", "match_id", "team_home", "team_away", "timestamp"):
        val = odd.get(field, "")
        if not isinstance(val, str) or not val.strip():
            logger.debug(f"Odd descartada — campo '{field}' vazio ou inválido")
            return False

    # Valida odds numéricas
    odds_dict = odd.get("odds", {})
    if not isinstance(odds_dict, dict):
        return False

    for key in ("home_win", "draw", "away_win"):
        val = odds_dict.get(key)
        try:
            if float(val) <= 0:
                logger.debug(f"Odd descartada — {key}={val} deve ser > 0")
                return False
        except (TypeError, ValueError):
            logger.debug(f"Odd descartada — {key}={val} não é numérico")
            return False

    return True


async def run(match_query: str) -> int:
    """
    Ponto de entrada principal do scraper.

    Executa todos os extractors em paralelo para a partida informada,
    valida cada odd coletada e publica as válidas no Kafka.

    Args:
        match_query: String fornecida pelo usuário (ex: "Flamengo x Vasco").

    Returns:
        Número de odds publicadas com sucesso no Kafka.
        Retorna 0 se nenhuma casa retornou dados ou todos falharam.
    """
    logger.info(f"[Runner] Iniciando scraping para: '{match_query}'")
    logger.info(f"[Runner] Extractors ativos: {[e.BOOKMAKER_NAME for e in ALL_EXTRACTORS]}")

    # Dispara todos os extractors em paralelo — falhas individuais não bloqueiam os outros
    tasks = [extractor.extract(match_query) for extractor in ALL_EXTRACTORS]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    producer = get_producer(KAFKA_SERVERS)
    published_count = 0
    total_collected = 0

    for extractor, result in zip(ALL_EXTRACTORS, raw_results):
        name = extractor.BOOKMAKER_NAME

        # asyncio.gather captura exceções como valores quando return_exceptions=True
        if isinstance(result, Exception):
            logger.error(f"[Runner] [{name}] Exceção não capturada: {result}")
            continue

        if not isinstance(result, list):
            logger.warning(f"[Runner] [{name}] Retorno inesperado (não é lista): {type(result)}")
            continue

        logger.info(f"[Runner] [{name}] {len(result)} odd(s) coletada(s)")
        total_collected += len(result)

        for odd in result:
            if not _validate_odd(odd):
                logger.warning(f"[Runner] [{name}] Odd inválida descartada: {odd}")
                continue

            if publish_odd(producer, KAFKA_TOPIC, odd):
                published_count += 1
            else:
                logger.warning(f"[Runner] [{name}] Falha ao publicar odd no Kafka")

    logger.info(
        f"[Runner] Scraping concluído. "
        f"Coletadas: {total_collected} | Publicadas: {published_count}"
    )
    return published_count
