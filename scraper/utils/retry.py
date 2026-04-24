"""
utils/retry.py
--------------
Decorator @async_retry com backoff exponencial para funções async.

Uso:
    @async_retry(max_attempts=3, base_delay=1.0, exceptions=(httpx.HTTPError,))
    async def fetch_data(url: str) -> dict:
        ...
"""

import asyncio
import functools
import logging
from typing import Type

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator que adiciona retry com backoff exponencial a coroutines.

    Fórmula do delay: base_delay * (2 ** (attempt - 1))
        attempt 1 → base_delay * 1  (imediato na falha)
        attempt 2 → base_delay * 2
        attempt 3 → base_delay * 4
        ...

    Comportamento:
        - Se a função retornar normalmente em qualquer tentativa, retorna o valor.
        - Se esgotar todas as tentativas, loga o erro e retorna [] (convenção de extractor).
        - Apenas exceções listadas em `exceptions` disparam retry. Outros erros propagam.

    Args:
        max_attempts: Número máximo de tentativas (incluindo a primeira). Padrão: 3
        base_delay: Delay base em segundos para backoff. Padrão: 1.0
        exceptions: Tupla de tipos de exceção que devem disparar retry. Padrão: (Exception,)

    Returns:
        Decorator aplicável a coroutines async.

    Exemplo:
        @async_retry(max_attempts=3, base_delay=1.5, exceptions=(httpx.HTTPError,))
        async def fetch(url: str) -> dict:
            async with httpx.AsyncClient() as client:
                return (await client.get(url)).json()
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = f"{func.__qualname__}"

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            f"[retry] {func_name} falhou após {max_attempts} tentativas. "
                            f"Último erro: {type(exc).__name__}: {exc}"
                        )
                        # Convenção: extractors retornam [] em falha, nunca propagam
                        return []

                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"[retry] {func_name} — tentativa {attempt}/{max_attempts} falhou "
                        f"({type(exc).__name__}: {exc}). Retry em {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
