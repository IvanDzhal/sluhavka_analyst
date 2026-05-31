# services/analytics.py
from datetime import date
from config.shops import EFFICIENCY_THRESHOLDS, KPI_BONUS_3OF4, KPI_BONUS_4OF4, SHOP_NAMES


def emoji_pct(pct: float) -> str:
    if pct >= 100: return "✅"
    elif pct >= 80: return "🟡"
    elif pct >= 50: return "🟠"
    else: return "🔴"


def emoji_eff_service(pct: float) -> str:
    t = EFFICIENCY_THRESHOLDS["services"]
    if pct <= t["alarm"]: return "🚨"
    elif pct <= t["medium"]: return "🟡"
    elif pct <= t["good"]: return "✅"
    else: return "🌟"


def emoji_eff_guarantee(pct: float) -> str:
    t = EFFICIENCY_THRESHOLDS["guarantee"]
    if pct < t["critical_alarm"]: return "🚨"
    elif pct < t["alarm"]: return "🔴"
    else: return "✅"


def progress_bar(pct: float, length: int = 10) -> str:
    filled = min(int(pct / 100 * length), length)
    return "█" * filled + "░" * (length - filled)


def fmt_delta(delta: float) -> str:
    if delta > 0:
        return f"+{delta}%"
    elif delta < 0:
        return f"{delta}%"
    return "0%"


def shop_name(code: str) -> str:
    return SHOP_NAMES.get(code, code)


# ── Вечірній звіт за день ─────────────────────────────────────────────────────

def format_evening_report(all_data: dict, show_focus: bool = True) -> str:
    today = date.today().strftime("%d.%m.%Y")
    lines = [f"📊 *ПІДСУМКИ ДНЯ | {today}*", ""]

    for code, d in sorted(all_data.items()):
        name = shop_name(code)
        lines.append(f"🏪 *{name} ({code})*")
        lines.append(
            f"*Продажі за день:*\n"
            f"  ТО: +{int(d['day_to']):,} грн  "
            f"МТ: +{int(d['day_mt']):,} грн  Акс: +{int(d['day_aks']):,} грн\n"
            f"  Послуги: +{int(d['day_service']):,} грн  "
            f"Гарантія: +{int(d['day_guarantee']):,} грн"
        )
        lines.append(
            f"*Виконання плану:*\n"
            f"  ТО: {d['pct_to']}% ({fmt_delta(d['delta_to'])})  "
            f"МТ: {d['pct_mt']}% ({fmt_delta(d['delta_mt'])})\n"
            f"  Акс: {d['pct_aks']}% ({fmt_delta(d['delta_aks'])})  "
            f"Послуги: {d['pct_service']}% ({fmt_delta(d['delta_service'])})\n"
            f"  Гарантія: {d['pct_guarantee']}% ({fmt_delta(d['delta_guarantee'])})"
        )
        srv_e = emoji_eff_service(d['eff_service'])
        gar_e = emoji_eff_guarantee(d['eff_guarantee'])
        lines.append(
            f"*Ефективність:*\n"
            f"  Послуги/МТ: {srv_e}{d['eff_service']}%  "
            f"Гарантія/МТ: {gar_e}{d['eff_guarantee']}%"
        )
        lines.append("━━━━━━━━━━━━━━━")

    if show_focus:
        lines.append("")
        lines += _focus_lines(all_data)

    return "\n".join(lines)


def format_focus(all_data: dict) -> str:
    lines = _focus_lines(all_data)
    return "\n".join(lines)


def _focus_lines(all_data: dict) -> list:
    lines = ["📌 *Фокус уваги*"]

    best_delta = max(all_data.items(), key=lambda x: x[1]["delta_to"])
    lines.append(f"🔥 Найбільший приріст ТО: {shop_name(best_delta[0])} ({fmt_delta(best_delta[1]['delta_to'])})")

    best_to = max(all_data.items(), key=lambda x: x[1]["pct_to"])
    lines.append(f"🏆 Найкраще виконання ТО: {shop_name(best_to[0])} ({best_to[1]['pct_to']}%)")

    worst_srv = min(all_data.items(), key=lambda x: x[1]["eff_service"])
    if worst_srv[1]["eff_service"] < EFFICIENCY_THRESHOLDS["services"]["medium"]:
        lines.append(f"⚠️ Найнижча ефективність послуг: {shop_name(worst_srv[0])} ({worst_srv[1]['eff_service']}%)")

    worst_gar = min(all_data.items(), key=lambda x: x[1]["eff_guarantee"])
    if worst_gar[1]["eff_guarantee"] < EFFICIENCY_THRESHOLDS["guarantee"]["alarm"]:
        lines.append(f"⚠️ Найнижча гарантія/МТ: {shop_name(worst_gar[0])} ({worst_gar[1]['eff_guarantee']}%)")

    worst_to = min(all_data.items(), key=lambda x: x[1]["pct_to"])
    lines.append(f"⚠️ Найнижче виконання ТО: {shop_name(worst_to[0])} ({worst_to[1]['pct_to']}%)")

    return lines


# ── Зведений звіт (по кнопці) ────────────────────────────────────────────────

def format_daily_summary(all_data: dict) -> str:
    today = date.today().strftime("%d.%m.%Y")
    lines = [
        f"📋 *ЗВЕДЕНИЙ ЗВІТ | {today}*",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for code, d in sorted(all_data.items()):
        days_total = int(d["days_passed"] + d["days_left"])
        to_e = emoji_pct(d['pct_to'])
        srv_e = emoji_eff_service(d['eff_service'])
        gar_e = emoji_eff_guarantee(d['eff_guarantee'])

        lines.append(f"{to_e} *{code}* | День {int(d['days_passed'])}/{days_total}")
        lines.append(
            f"ТО {d['pct_to']}% · МТ {d['pct_mt']}% · "
            f"Акс {d['pct_aks']}% · Пос {d['pct_service']}% · Гар {d['pct_guarantee']}%"
        )
        lines.append(
            f"⚡ Пос/МТ {srv_e}{d['eff_service']}% · Гар/МТ {gar_e}{d['eff_guarantee']}%"
        )
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


# ── Деталі магазину ───────────────────────────────────────────────────────────

def format_shop_detail(d: dict) -> str:
    days_total = int(d["days_passed"] + d["days_left"])
    lines = [
        f"🏪 *{shop_name(d['shop'])} ({d['shop']})*",
        f"📅 День {int(d['days_passed'])} з {days_total} | Лишилось: {int(d['days_left'])} дн.",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "📦 *ВИКОНАННЯ ПЛАНУ*",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"{emoji_pct(d['pct_to'])} *Товарооборот*",
        f"  {progress_bar(d['pct_to'])} {d['pct_to']}% (сьогодні {fmt_delta(d['delta_to'])})",
        f"  Факт: {int(d['fact_to']):,} грн | План: {int(d['plan_to']):,} грн",
        f"  Залишилось: {int(d['left_to']):,} грн | Прогноз: {d['forecast_to']}%",
        "",
        f"{emoji_pct(d['pct_mt'])} *Мобільні телефони*",
        f"  {progress_bar(d['pct_mt'])} {d['pct_mt']}% (сьогодні {fmt_delta(d['delta_mt'])})",
        f"  Факт: {int(d['fact_mt']):,} грн | План: {int(d['plan_mt']):,} грн",
        f"  Залишилось: {int(d['left_mt']):,} грн | Прогноз: {d['forecast_mt']}%",
        "",
        f"{emoji_pct(d['pct_aks'])} *Аксесуари*",
        f"  {progress_bar(d['pct_aks'])} {d['pct_aks']}% (сьогодні {fmt_delta(d['delta_aks'])})",
        f"  Факт: {int(d['fact_aks']):,} грн | План: {int(d['plan_aks']):,} грн",
        f"  Залишилось: {int(d['left_aks']):,} грн | Прогноз: {d['forecast_aks']}%",
        "",
        f"{emoji_pct(d['pct_service'])} *Послуги*",
        f"  {progress_bar(d['pct_service'])} {d['pct_service']}% (сьогодні {fmt_delta(d['delta_service'])})",
        f"  Факт: {int(d['fact_service']):,} грн | План: {int(d['plan_service']):,} грн",
        f"  Залишилось: {int(d['left_service']):,} грн | Прогноз: {d['forecast_service']}%",
        "",
        f"{emoji_pct(d['pct_guarantee'])} *Гарантія*",
        f"  {progress_bar(d['pct_guarantee'])} {d['pct_guarantee']}% (сьогодні {fmt_delta(d['delta_guarantee'])})",
        f"  Факт: {int(d['fact_guarantee']):,} грн | План: {int(d['plan_guarantee']):,} грн",
        f"  Залишилось: {int(d['left_guarantee']):,} грн | Прогноз: {d['forecast_guarantee']}%",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "📊 *ЕФЕКТИВНІСТЬ*",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"{emoji_eff_service(d['eff_service'])} Послуги/МТ: *{d['eff_service']}%* (норма ≥10%)",
        f"{emoji_eff_guarantee(d['eff_guarantee'])} Гарантія/МТ: *{d['eff_guarantee']}%* (норма ≥7.5%)",
        f"📦 Аксесуари/МТ: *{d['eff_aks']}%*",
    ]
    return "\n".join(lines)


# ── Алярми ────────────────────────────────────────────────────────────────────

def get_alerts(all_data: dict) -> list[str]:
    alerts = []
    t_srv = EFFICIENCY_THRESHOLDS["services"]
    t_gar = EFFICIENCY_THRESHOLDS["guarantee"]

    for code, d in all_data.items():
        name = shop_name(code)
        if d["eff_service"] <= t_srv["alarm"]:
            alerts.append(f"🚨 *{name}* — погана ефективність послуг: {d['eff_service']}% (норма >8%)")
        if d["eff_guarantee"] < t_gar["critical_alarm"]:
            alerts.append(f"🚨 *{name}* — критично низька гарантія: {d['eff_guarantee']}% (норма >7.5%)")
        elif d["eff_guarantee"] < t_gar["alarm"]:
            alerts.append(f"⚠️ *{name}* — низька гарантія: {d['eff_guarantee']}%")

    return alerts


# ── KPI ───────────────────────────────────────────────────────────────────────

def calculate_kpi(all_data: dict) -> dict:
    results = {}
    total_bonus = 0

    for code, d in all_data.items():
        # Використовуємо прогноз до кінця місяця
        metrics = {
            "ТО":       d["forecast_to"],
            "Акс":      d["forecast_aks"],
            "Послуги":  d["forecast_service"],
            "Гарантія": d["forecast_guarantee"],
        }

        closed = sum(1 for v in metrics.values() if v >= 100)
        bonus = KPI_BONUS_4OF4 if closed == 4 else (KPI_BONUS_3OF4 if closed == 3 else 0)

        results[code] = {"metrics": metrics, "closed": closed, "bonus": bonus}
        total_bonus += bonus

    return {"shops": results, "total": total_bonus}


def format_kpi_report(kpi: dict) -> str:
    lines = [
        "💰 *МІЙ KPI — ПРОГНОЗ ДО КІНЦЯ МІСЯЦЯ*",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    shops_4    = [(c, r) for c, r in kpi["shops"].items() if r["closed"] == 4]
    shops_3    = [(c, r) for c, r in kpi["shops"].items() if r["closed"] == 3]
    shops_less = [(c, r) for c, r in kpi["shops"].items() if r["closed"] < 3]

    if shops_4:
        lines.append("🌟 *4/4 показники* (+1600 грн)")
        for code, _ in sorted(shops_4):
            lines.append(f"  ✅ {shop_name(code)} ({code})")
        lines.append("")

    if shops_3:
        lines.append("✅ *3/4 показники* (+800 грн)")
        for code, r in sorted(shops_3):
            miss = [f"{k} {v}%" for k, v in r["metrics"].items() if v < 100]
            lines.append(f"  🟡 {shop_name(code)} — не вистачає: {', '.join(miss)}")
        lines.append("")

    if shops_less:
        lines.append("❌ *Менше 3/4 — без бонусу*")
        for code, r in sorted(shops_less):
            miss = [f"{k} {v}%" for k, v in r["metrics"].items() if v < 100]
            lines.append(f"  🔴 {shop_name(code)} — не вистачає: {', '.join(miss)}")
        lines.append("")

    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        f"💵 *Прогноз виплати: {kpi['total']:,} грн*",
        "_(на основі поточного темпу продажів)_",
    ]
    return "\n".join(lines)


# ── Ранковий брифінг ──────────────────────────────────────────────────────────

def format_morning_briefing(all_data: dict) -> str:
    from datetime import date
    today = date.today().strftime("%d.%m.%Y")

    lines = [
        f"☀️ *РАНКОВИЙ БРИФІНГ | {today}*",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # Хто не виконав план вчора (delta_to < 0 або дуже малий)
    problem_shops = [
        (code, d) for code, d in all_data.items()
        if d.get("delta_to", 0) < 2.0  # менше 2% приросту за день
    ]

    if problem_shops:
        lines.append("⚠️ *Вчора слабкий день:*")
        for code, d in sorted(problem_shops, key=lambda x: x[1].get("delta_to", 0)):
            lines.append(f"  • {shop_name(code)} — приріст ТО: {fmt_delta(d.get('delta_to', 0))}")
        lines.append("")

    # Скільки потрібно продавати на день щоб закрити місяць
    lines.append("📋 *Денна норма для закриття плану:*")
    lines.append("")

    urgent = []  # магазини де норма дуже висока відносно середньої

    for code, d in sorted(all_data.items()):
        days_left = d["days_left"]
        if days_left <= 0:
            continue

        need_to = d["left_to"] / days_left if d["left_to"] > 0 else 0
        need_mt = d["left_mt"] / days_left if d["left_mt"] > 0 else 0
        need_srv = d["left_service"] / days_left if d["left_service"] > 0 else 0
        need_gar = d["left_guarantee"] / days_left if d["left_guarantee"] > 0 else 0

        # Середньоденний факт
        avg_to = d["fact_to"] / d["days_passed"] if d["days_passed"] > 0 else 0

        to_icon = "🔴" if need_to > avg_to * 1.3 else ("🟡" if need_to > avg_to else "✅")

        if need_to > avg_to * 1.3:
            urgent.append(code)

        lines.append(
            f"{to_icon} *{code}* ({int(days_left)} дн.) — "
            f"ТО: {int(need_to):,} грн/день"
        )
        if need_srv > 0 or need_gar > 0:
            lines.append(
                f"   Пос: {int(need_srv):,} · Гар: {int(need_gar):,} грн/день"
            )

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")

    # Фокус уваги
    if urgent:
        lines.append("🎯 *Фокус уваги сьогодні:*")
        for code in urgent:
            d = all_data[code]
            avg = d["fact_to"] / d["days_passed"] if d["days_passed"] > 0 else 0
            need = d["left_to"] / d["days_left"] if d["days_left"] > 0 else 0
            lines.append(
                f"  🔴 {shop_name(code)} — потрібно {int(need):,} грн/день "
                f"(середнє {int(avg):,} грн/день)"
            )
    else:
        lines.append("✅ *Всі магазини в нормальному темпі*")

    return "\n".join(lines)
