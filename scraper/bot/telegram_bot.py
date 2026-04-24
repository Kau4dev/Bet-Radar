"""
bot/telegram_bot.py
--------------------
Entry point principal do bot BetRadar no Telegram.

Implementa o fluxo completo via ConversationHandler:
    /start → WAITING_MATCH → scraping → resultado

Comandos disponíveis:
    /start  → inicia o fluxo (pode ser usado em qualquer estado)
    /cancel → cancela a operação atual e volta ao estado inicial
    /status → mostra o estado atual do bot e a última partida consultada

O scraper é executado de forma não-bloqueante usando asyncio,
garantindo que o bot continue responsivo durante o scraping.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from telegram import Update, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import scraper_runner
from bot.states import BotState
from utils.logger import setup_logging

logger = logging.getLogger(__name__)

# Chave para armazenar contexto do usuário no chat_data
_CTX_LAST_MATCH = "last_match"
_CTX_IS_SCRAPING = "is_scraping"


# ---------------------------------------------------------------------------
# Handlers de comando
# ---------------------------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler para /start — inicia o fluxo e pede o nome da partida.
    Pode ser invocado de qualquer estado (allow_reentry=True no ConversationHandler).
    """
    context.chat_data[_CTX_IS_SCRAPING] = False

    await update.message.reply_text(
        "🎯 *BetRadar — Monitor de Odds Esportivas*\n\n"
        "Qual partida deseja monitorar?\n"
        "Informe no formato: `Time A x Time B`\n\n"
        "_Exemplos:_\n"
        "• `Real Madrid x Barcelona`\n"
        "• `Flamengo x Vasco`\n"
        "• `Manchester City vs Arsenal`\n\n"
        "Use /cancel para cancelar a qualquer momento.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return BotState.WAITING_MATCH


async def receive_match_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler para a mensagem com o nome da partida.
    Valida a entrada, inicia o scraper de forma assíncrona e reporta o resultado.
    """
    match_query = update.message.text.strip()

    # Validação básica da entrada
    if len(match_query) < 5:
        await update.message.reply_text(
            "❌ Nome da partida muito curto.\n"
            "Informe no formato: `Time A x Time B`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return BotState.WAITING_MATCH

    # Verifica se há um separador válido
    separators = [" x ", " vs ", " X ", " VS ", " versus ", " - "]
    has_separator = any(sep in match_query for sep in separators)
    if not has_separator:
        await update.message.reply_text(
            "❌ Não reconheci o formato. Use:\n"
            "`Flamengo x Vasco` ou `Flamengo vs Vasco`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return BotState.WAITING_MATCH

    # Salva no contexto para /status
    context.chat_data[_CTX_LAST_MATCH] = match_query
    context.chat_data[_CTX_IS_SCRAPING] = True

    # Confirma recebimento e informa que o scraping está em andamento
    await update.message.reply_text(
        f"🔍 Buscando odds para: *{match_query}*\n\n"
        "⏳ Consultando casas de apostas...\n"
        "_Isso pode levar até 30 segundos._",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        # Executa o scraper — run() é uma coroutine, pode ser aguardada diretamente
        published = await scraper_runner.run(match_query)
        context.chat_data[_CTX_IS_SCRAPING] = False

        if published > 0:
            await update.message.reply_text(
                f"✅ *{published} odds* enviadas ao sistema de análise!\n\n"
                "📊 O backend está calculando EV+ e Surebets...\n"
                "Você receberá um alerta automático caso haja oportunidades.\n\n"
                "Use /start para monitorar outra partida.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.message.reply_text(
                "⚠️ *Nenhuma odd encontrada* para essa partida.\n\n"
                "Possíveis causas:\n"
                "• A partida ainda não está disponível nas casas\n"
                "• O nome foi digitado de forma diferente do padrão\n"
                "• As casas estão temporariamente indisponíveis\n\n"
                "Tente novamente com /start ou verifique o nome da partida.",
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as exc:
        context.chat_data[_CTX_IS_SCRAPING] = False
        logger.error(f"[Bot] Erro durante scraping de '{match_query}': {exc}")
        await update.message.reply_text(
            "💥 Ocorreu um erro interno durante o scraping.\n"
            "Tente novamente com /start.",
        )

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler para /cancel — cancela operação atual e volta ao estado inicial."""
    context.chat_data[_CTX_IS_SCRAPING] = False
    await update.message.reply_text(
        "❌ Operação cancelada.\n\nUse /start para recomeçar."
    )
    return ConversationHandler.END


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para /status — mostra o estado atual do bot.
    Não interfere no ConversationHandler (é um CommandHandler independente).
    """
    is_scraping = context.chat_data.get(_CTX_IS_SCRAPING, False)
    last_match = context.chat_data.get(_CTX_LAST_MATCH, "Nenhuma partida consultada ainda")

    status_icon = "🔄 Scraping em andamento" if is_scraping else "✅ Aguardando comando"

    await update.message.reply_text(
        f"📡 *Status do BetRadar*\n\n"
        f"Estado: {status_icon}\n"
        f"Última partida: `{last_match}`\n\n"
        f"Use /start para iniciar uma nova consulta.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler de fallback para mensagens não reconhecidas no ConversationHandler."""
    await update.message.reply_text(
        "Não entendi. Use /start para iniciar ou /cancel para cancelar."
    )
    return BotState.WAITING_MATCH


# ---------------------------------------------------------------------------
# Setup e inicialização
# ---------------------------------------------------------------------------

async def post_init(application: Application) -> None:
    """
    Configura os comandos disponíveis no menu do Telegram.
    Chamado automaticamente após a inicialização da Application.
    """
    commands = [
        BotCommand("start", "Iniciar monitoramento de uma partida"),
        BotCommand("cancel", "Cancelar operação atual"),
        BotCommand("status", "Ver status atual do bot"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("[Bot] Comandos do Telegram configurados.")


def main() -> None:
    """
    Inicializa e executa o bot Telegram com polling.
    Entry point do módulo scraper.
    """
    setup_logging()
    load_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Variável de ambiente TELEGRAM_BOT_TOKEN não definida. "
            "Configure no arquivo .env."
        )

    logger.info("[Bot] Inicializando BetRadar Telegram Bot...")

    app = Application.builder().token(token).post_init(post_init).build()

    # ConversationHandler: gerencia o fluxo /start → partida → resultado
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            BotState.WAITING_MATCH: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_match_handler,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            MessageHandler(filters.COMMAND, fallback_handler),
        ],
        allow_reentry=True,  # /start pode reiniciar o fluxo em qualquer estado
    )

    app.add_handler(conv_handler)

    # /status funciona independentemente do ConversationHandler
    app.add_handler(CommandHandler("status", status_handler))

    logger.info("[Bot] ✅ Bot iniciado. Aguardando mensagens (polling)...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,  # Ignora mensagens acumuladas durante downtime
    )


if __name__ == "__main__":
    main()
