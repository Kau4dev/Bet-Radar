"""
bot/states.py
--------------
Define os estados da máquina de estados do bot Telegram (ConversationHandler).
"""

from enum import IntEnum


class BotState(IntEnum):
    """
    Estados do ConversationHandler do bot BetRadar.

    Fluxo:
        IDLE          → usuário não iniciou nenhuma conversa
        WAITING_MATCH → bot aguarda o usuário informar a partida
        SCRAPING      → bot está executando o scraper em background
                        (estado interno — não mapeado no ConversationHandler)

    Uso no ConversationHandler:
        entry_points=[CommandHandler("start", start_handler)]
        states={BotState.WAITING_MATCH: [MessageHandler(...)]}
    """

    WAITING_MATCH = 0
    """Aguardando o usuário informar o nome da partida."""
