import asyncio
import logging
import os
from contextlib import suppress

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Supply the bot token through the BOT_TOKEN environment variable *or* replace
# the placeholder string below. Keeping secrets in code is discouraged.
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "PASTE-YOUR-BOT-TOKEN-HERE")

# If you want to use a webhook instead of long polling, set the following two
# variables and uncomment the relevant lines in main().
WEBHOOK_URL: str | None = os.getenv("WEBHOOK_URL")  # e.g. "https://your.domain.tld/bot"
WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", 8443))
WEBHOOK_LISTEN: str = os.getenv("WEBHOOK_LISTEN", "0.0.0.0")

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and brief help on /start."""
    user = update.effective_user
    if user:
        name = user.mention_html()
    else:
        name = "there"
    await update.message.reply_html(
        rf"Hi {name}! I'm an example Telegram bot written in <code>bot.py</code>.\n"
        "Send /help to see what I can do.",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message listing available commands."""
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help  - This help text\n"
        "Just send any text and I will echo it back!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo back the received text message."""
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log all errors caused by Updates."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # Notify the user that something went wrong if possible
    if isinstance(update, Update) and update.effective_chat:
        with suppress(Exception):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="An unexpected error occurred. Please try again later.",
            )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "PASTE-YOUR-BOT-TOKEN-HERE":
        raise RuntimeError(
            "❌ Bot token not set. Please set the BOT_TOKEN environment variable or edit bot.py."
        )

    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # Register a non-command text message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Register the error handler (runs last)
    application.add_error_handler(error_handler)

    # Start the bot
    if WEBHOOK_URL:
        # Using webhook (comment out if you prefer polling)
        # Make sure the URL is reachable and you have set the certificate if needed.
        await application.run_webhook(
            listen=WEBHOOK_LISTEN,
            port=WEBHOOK_PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        )
    else:
        # Start using long polling (simpler development setup)
        await application.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")