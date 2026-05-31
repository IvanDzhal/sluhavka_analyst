# handlers/callbacks.py
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from handlers.auth import restricted
from handlers.keyboards import (
    main_menu, shops_list_keyboard, shop_menu, back_to_shop, back_to_main
)
from services.sheets import get_shop_data, get_all_shops_data
from services.analytics import (
    format_shop_detail, format_daily_summary, format_evening_report,
    get_alerts, calculate_kpi, format_kpi_report, format_morning_briefing,
    shop_name, emoji_pct, emoji_eff_service, emoji_eff_guarantee, fmt_delta
)
from services.ai_analysis import analyze_shop, analyze_month


async def _edit(query, text: str, markup=None):
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup,
    )


@restricted
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Головне меню ──────────────────────────────────────────
    if data == "main_menu":
        await _edit(query, "🏠 *Слухавка — Аналітика*\nОбери розділ:", main_menu())

    # ── Зведений звіт ─────────────────────────────────────────
    elif data == "report":
        await _edit(query, "⏳ Збираю дані по всіх магазинах...")
        all_data = get_all_shops_data()
        if not all_data:
            await _edit(query, "❌ Не вдалося отримати дані.", back_to_main())
            return
        text = format_daily_summary(all_data)
        await _edit(query, text, back_to_main())

    # ── Алярми ────────────────────────────────────────────────
    elif data == "alerts":
        await _edit(query, "⏳ Перевіряю...")
        all_data = get_all_shops_data()
        alerts = get_alerts(all_data)
        if alerts:
            text = "⚠️ *АЛЯРМИ:*\n\n" + "\n".join(alerts)
        else:
            text = "✅ Алярмів немає — всі показники в нормі!"
        await _edit(query, text, back_to_main())

    # ── KPI ───────────────────────────────────────────────────
    elif data == "kpi":
        await _edit(query, "⏳ Рахую KPI...")
        all_data = get_all_shops_data()
        if not all_data:
            await _edit(query, "❌ Не вдалося отримати дані.", back_to_main())
            return
        kpi = calculate_kpi(all_data)
        text = format_kpi_report(kpi)
        await _edit(query, text, back_to_main())

    # ── Місячна аналітика ─────────────────────────────────────
    elif data == "month":
        await _edit(query, "⏳ Збираю дані для місячної аналітики...")
        all_data = get_all_shops_data()
        if not all_data:
            await _edit(query, "❌ Не вдалося отримати дані.", back_to_main())
            return
        analysis = analyze_month(all_data)
        text = f"📅 *Місячна аналітика мережі*\n\n{analysis}"
        await _edit(query, text, back_to_main())

    # ── Рейтинг ───────────────────────────────────────────────
    elif data == "rating":
        await _edit(query, "⏳ Будую рейтинг...")
        all_data = get_all_shops_data()
        if not all_data:
            await _edit(query, "❌ Не вдалося отримати дані.", back_to_main())
            return
        text = format_rating(all_data)
        await _edit(query, text, back_to_main())

    # ── Ранковий брифінг ──────────────────────────────────────
    elif data == "morning":
        await _edit(query, "⏳ Готую брифінг...")
        all_data = get_all_shops_data()
        if not all_data:
            await _edit(query, "❌ Не вдалося отримати дані.", back_to_main())
            return
        text = format_morning_briefing(all_data)
        await _edit(query, text, back_to_main())

    # ── Список магазинів ──────────────────────────────────────
    elif data == "shops_list":
        await _edit(query, "🏪 *Оберіть магазин:*", shops_list_keyboard(0))

    elif data.startswith("shops_page:"):
        page = int(data.split(":")[1])
        await _edit(query, "🏪 *Оберіть магазин:*", shops_list_keyboard(page))

    # ── Меню магазину ─────────────────────────────────────────
    elif data.startswith("shop_menu:"):
        code = data.split(":")[1]
        await _edit(query, f"🏪 *Магазин {code}*\nОбери дію:", shop_menu(code))

    # ── Деталі магазину ───────────────────────────────────────
    elif data.startswith("shop_detail:"):
        code = data.split(":")[1]
        await _edit(query, f"⏳ Читаю дані {code}...")
        d = get_shop_data(code)
        if not d:
            await _edit(query, f"❌ Немає даних для {code}.", back_to_shop(code))
            return
        text = format_shop_detail(d)
        await _edit(query, text, back_to_shop(code))

    # ── AI Аналіз магазину ────────────────────────────────────
    elif data.startswith("shop_ai:"):
        code = data.split(":")[1]
        await _edit(query, f"🤖 Аналізую {code}...")
        d = get_shop_data(code)
        if not d:
            await _edit(query, f"❌ Немає даних для {code}.", back_to_shop(code))
            return
        analysis = analyze_shop(d)
        text = f"🤖 *AI Аналіз — {code}*\n\n{analysis}"
        await _edit(query, text, back_to_shop(code))


def format_rating(all_data: dict) -> str:
    """Рейтинг магазинів по ключових показниках."""
    lines = ["🏆 *РЕЙТИНГ МАГАЗИНІВ*", "━━━━━━━━━━━━━━━━━━━━", ""]

    def ranked(key, label, reverse=True):
        sorted_shops = sorted(all_data.items(), key=lambda x: x[1].get(key, 0), reverse=reverse)
        result = [f"📊 *{label}*"]
        medals = ["🥇", "🥈", "🥉"]
        for i, (code, d) in enumerate(sorted_shops[:5]):
            medal = medals[i] if i < 3 else f"  {i+1}."
            val = d.get(key, 0)
            result.append(f"  {medal} {shop_name(code)} — {val}%")
        # Аутсайдер
        worst_code, worst_d = sorted_shops[-1]
        result.append(f"  🔴 Аутсайдер: {shop_name(worst_code)} — {worst_d.get(key, 0)}%")
        return result

    lines += ranked("pct_to", "Товарооборот")
    lines.append("")
    lines += ranked("eff_service", "Ефективність послуг")
    lines.append("")
    lines += ranked("eff_guarantee", "Ефективність гарантії")
    lines.append("")
    lines += ranked("pct_aks", "Аксесуари")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
