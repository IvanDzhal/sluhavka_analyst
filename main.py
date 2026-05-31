# main.py
import os
import logging
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from handlers.auth import restricted
from handlers.keyboards import main_menu
from handlers.callbacks import handle_callback
from services.sheets import get_all_shops_data
from services.analytics import (
    format_evening_report, format_morning_briefing,
    get_alerts, format_focus
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOKEN   = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))


@restricted
async def cmd_start(update, context):
    await update.message.reply_text(
        "👋 *Слухавка — Аналітика*\nОбери розділ:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu(),
    )


async def send_morning_briefing(bot: Bot):
    logger.info("Відправляю ранковий брифінг...")
    try:
        all_data = get_all_shops_data()
        if not all_data:
            await bot.send_message(CHAT_ID, "❌ Не вдалося зібрати брифінг.")
            return
        text = format_morning_briefing(all_data)
        await bot.send_message(CHAT_ID, text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Помилка ранкового брифінгу: {e}")
        await bot.send_message(CHAT_ID, f"❌ Помилка брифінгу: {e}")


async def send_evening_report(bot: Bot):
    logger.info("Відправляю вечірній звіт...")
    try:
        all_data = get_all_shops_data()
        if not all_data:
            await bot.send_message(CHAT_ID, "❌ Не вдалося зібрати вечірній звіт.")
            return

        # Магазини без фокусу уваги
        shops_list = list(all_data.items())
        for i in range(0, len(shops_list), 5):
            chunk = dict(shops_list[i:i + 5])
            text = format_evening_report(chunk, show_focus=False)
            await bot.send_message(CHAT_ID, text, parse_mode=ParseMode.MARKDOWN)

        # Фокус уваги окремо — по всіх магазинах
        focus = format_focus(all_data)
        await bot.send_message(CHAT_ID, focus, parse_mode=ParseMode.MARKDOWN)

        # Алярми
        alerts = get_alerts(all_data)
        if alerts:
            await bot.send_message(
                CHAT_ID,
                "⚠️ *АЛЯРМИ:*\n\n" + "\n".join(alerts),
                parse_mode=ParseMode.MARKDOWN,
            )

        await bot.send_message(CHAT_ID, "✅ Звіт готово", reply_markup=main_menu())

    except Exception as e:
        logger.error(f"Помилка вечірнього звіту: {e}")
        await bot.send_message(CHAT_ID, f"❌ Помилка звіту: {e}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    scheduler = AsyncIOScheduler(timezone="Europe/Kiev")

    # Ранковий брифінг о 9:00
    scheduler.add_job(
        send_morning_briefing,
        trigger="cron", hour=9, minute=0,
        args=[app.bot],
    )

    # Вечірній звіт о 21:00
    scheduler.add_job(
        send_evening_report,
        trigger="cron", hour=21, minute=0,
        args=[app.bot],
    )

    scheduler.start()
    logger.info("✅ Бот запущено! Брифінг о 9:00, звіт о 21:00.")
    app.run_polling()


if __name__ == "__main__":
    main()
