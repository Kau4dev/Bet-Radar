"""
utils/logger.py
---------------
Configura logging estruturado para todo o módulo scraper.
O nível de log é controlado pela variável de ambiente LOG_LEVEL (padrão: INFO).
"""

import logging
import os
import sys


def setup_logging() -> None:
    """
    Configura o logging global da aplicação.
    Deve ser chamado uma única vez no entry point (telegram_bot.py ou scraper_runner.py).

    Variáveis de ambiente:
        LOG_LEVEL: nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL). Padrão: INFO
        LOG_FORMAT: 'simple' ou 'structured'. Padrão: 'simple'
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    log_format = os.getenv("LOG_FORMAT", "simple")

    if log_format == "structured":
        # Formato estruturado — mais fácil de parsear em sistemas de observabilidade
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    else:
        # Formato legível para desenvolvimento local
        fmt = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger()
    root.setLevel(level)

    # Evita adicionar handlers duplicados em ambientes que chamam setup múltiplas vezes
    if not root.handlers:
        root.addHandler(handler)

    # Silencia bibliotecas muito verbosas em nível DEBUG
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("kafka").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger nomeado. Convenção: usar __name__ do módulo.

    Exemplo:
        logger = get_logger(__name__)
        logger.info("Mensagem informativa")
    """
    return logging.getLogger(name)
