# services/ai_analysis.py
from groq import Groq
import os

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def _ask(prompt: str) -> str:
    try:
        response = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ AI недоступний: {e}"


def analyze_shop(d: dict) -> str:
    prompt = f"""Ти — жорсткий бізнес-аналітик роздрібної мережі магазинів електроніки.
Дай аналіз магазину {d['shop']} СТРОГО в такому форматі (без відступів від формату, без вступів):

🔴 ПРОБЛЕМИ:
- [конкретна проблема з цифрою]
- [конкретна проблема з цифрою]

👥 ДІЇ З ПРОДАВЦЯМИ:
- [конкретна дія, що саме сказати або зробити]
- [конкретна дія]

📈 РЕКОМЕНДАЦІЇ:
- [конкретний крок для підйому показника]
- [конкретний крок]

Дані магазину (% від місячного плану, лишилось {int(d['days_left'])} днів):
ТО: {d['pct_to']}% (ліміт: {int(d['left_to']):,} грн)
МТ: {d['pct_mt']}%
Аксесуари: {d['pct_aks']}%
Послуги: {d['pct_service']}%
Гарантія: {d['pct_guarantee']}%
Ефективність послуги/МТ: {d['eff_service']}% (норма 10%)
Ефективність гарантія/МТ: {d['eff_guarantee']}% (норма 7.5%)
Аксесуари/МТ: {d['eff_aks']}%

Тільки факти і конкретні дії. Жодної води. Відповідай українською."""
    return _ask(prompt)


def analyze_month(all_data: dict) -> str:
    rows = "\n".join(
        f"{code}: ТО {d['pct_to']}%, МТ {d['pct_mt']}%, Акс {d['pct_aks']}%, "
        f"Пос {d['pct_service']}%, Гар {d['pct_guarantee']}%, "
        f"ефПос {d['eff_service']}%, ефГар {d['eff_guarantee']}%"
        for code, d in sorted(all_data.items())
    )

    prompt = f"""Ти — жорсткий бізнес-аналітик роздрібної мережі магазинів електроніки.
Дай місячний аналіз мережі СТРОГО в такому форматі (без відступів від формату):

🏆 ЛІДЕРИ: [перелік магазинів і чому]

🔴 АУТСАЙДЕРИ: [перелік магазинів і головна проблема кожного]

⚠️ ГОЛОВНІ ПРОБЛЕМИ МЕРЕЖІ:
- [проблема 1 з цифрами]
- [проблема 2 з цифрами]

📋 ДІЇ НА НАСТУПНИЙ МІСЯЦЬ:
1. [конкретна дія]
2. [конкретна дія]
3. [конкретна дія]

Дані магазинів:
{rows}

Тільки факти і конкретні дії. Жодної води. Відповідай українською."""
    return _ask(prompt)
