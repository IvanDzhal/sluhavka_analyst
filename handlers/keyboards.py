# handlers/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.shops import SHOPS


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Зведений звіт",     callback_data="report"),
            InlineKeyboardButton("⚠️ Алярми",            callback_data="alerts"),
        ],
        [
            InlineKeyboardButton("💰 Мій KPI",           callback_data="kpi"),
            InlineKeyboardButton("📅 Місячна аналітика", callback_data="month"),
        ],
        [
            InlineKeyboardButton("🏆 Рейтинг",           callback_data="rating"),
            InlineKeyboardButton("☀️ Брифінг",           callback_data="morning"),
        ],
        [
            InlineKeyboardButton("🏪 Магазини",          callback_data="shops_list"),
        ],
    ])


def shops_list_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    codes = list(SHOPS.keys())
    per_page = 10
    start = page * per_page
    chunk = codes[start:start + per_page]

    rows = []
    for i in range(0, len(chunk), 5):
        row = [
            InlineKeyboardButton(code, callback_data=f"shop_menu:{code}")
            for code in chunk[i:i + 5]
        ]
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Назад", callback_data=f"shops_page:{page-1}"))
    if start + per_page < len(codes):
        nav.append(InlineKeyboardButton("▶️ Далі", callback_data=f"shops_page:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def shop_menu(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Деталі",    callback_data=f"shop_detail:{code}"),
            InlineKeyboardButton("🤖 AI Аналіз", callback_data=f"shop_ai:{code}"),
        ],
        [
            InlineKeyboardButton("◀️ До списку магазинів", callback_data="shops_list"),
        ],
        [
            InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu"),
        ],
    ])


def back_to_shop(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ До магазину", callback_data=f"shop_menu:{code}")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")],
    ])


def back_to_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")],
    ])
