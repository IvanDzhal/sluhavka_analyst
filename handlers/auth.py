# handlers/auth.py
import os
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes


def get_allowed_users() -> set[int]:
    raw = os.getenv("ALLOWED_USERS", "")
    result = set()
    for uid in raw.split(","):
        uid = uid.strip()
        if uid.isdigit():
            result.add(int(uid))
    return result


def restricted(func):
    """Декоратор — блокує доступ якщо user не в whitelist."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in get_allowed_users():
            if update.message:
                await update.message.reply_text("⛔ Доступ заборонено.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Доступ заборонено.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
