# services/sheets.py
import gspread
from google.oauth2.service_account import Credentials
from config.shops import SHOPS, DEFAULT_CELLS, SHOP_CELLS_OVERRIDES
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

_client = None

def get_client():
    global _client
    if _client is None:
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client


def get_cells_for_shop(shop_code: str) -> dict:
    """Повертає фінальний маппінг комірок для магазину (базові + override)."""
    cells = dict(DEFAULT_CELLS)
    overrides = SHOP_CELLS_OVERRIDES.get(shop_code, {})
    cells.update(overrides)
    return cells


def _parse_num(val) -> float:
    if val is None or val == "":
        return 0.0
    s = str(val).replace(" ", "").replace("\xa0", "").replace(",", ".").replace("грн", "").replace("%", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def get_shop_data(shop_code: str) -> dict | None:
    shop = SHOPS.get(shop_code)
    if not shop or shop["sheet_id"] == "YOUR_SHEET_ID":
        return None

    try:
        gc = get_client()
        sh = gc.open_by_key(shop["sheet_id"])
        ws = sh.worksheet(shop["sheet_name"]) if shop["sheet_name"] else sh.get_worksheet(0)
        all_values = ws.get_all_values()

        cells = get_cells_for_shop(shop_code)

        def cell(row, col):
            try:
                return all_values[row - 1][col - 1]
            except IndexError:
                return ""

        data = {
            "shop":           shop_code,
            "days_left":      _parse_num(cell(*cells["days_left"])),
            "days_passed":    _parse_num(cell(*cells["days_passed"])),

            "plan_to":        _parse_num(cell(*cells["plan_to"])),
            "plan_mt":        _parse_num(cell(*cells["plan_mt"])),
            "plan_aks":       _parse_num(cell(*cells["plan_aks"])),
            "plan_service":   _parse_num(cell(*cells["plan_service"])),
            "plan_guarantee": _parse_num(cell(*cells["plan_guarantee"])),

            "fact_to":        _parse_num(cell(*cells["fact_to"])),
            "fact_mt":        _parse_num(cell(*cells["fact_mt"])),
            "fact_aks":       _parse_num(cell(*cells["fact_aks"])),
            "fact_service":   _parse_num(cell(*cells["fact_service"])),
            "fact_guarantee": _parse_num(cell(*cells["fact_guarantee"])),

            "day_to":         _parse_num(cell(*cells["day_to"])),
            "day_mt":         _parse_num(cell(*cells["day_mt"])),
            "day_aks":        _parse_num(cell(*cells["day_aks"])),
            "day_service":    _parse_num(cell(*cells["day_service"])),
            "day_guarantee":  _parse_num(cell(*cells["day_guarantee"])),
        }

        def pct(fact, plan):
            return round(fact / plan * 100, 1) if plan > 0 else 0.0

        # Загальне виконання плану (накопичувально)
        data["pct_to"]        = pct(data["fact_to"],        data["plan_to"])
        data["pct_mt"]        = pct(data["fact_mt"],        data["plan_mt"])
        data["pct_aks"]       = pct(data["fact_aks"],       data["plan_aks"])
        data["pct_service"]   = pct(data["fact_service"],   data["plan_service"])
        data["pct_guarantee"] = pct(data["fact_guarantee"], data["plan_guarantee"])

        # Вчорашнє виконання = (факт - звіт за день) / план
        data["pct_to_yday"]        = pct(data["fact_to"]        - data["day_to"],        data["plan_to"])
        data["pct_mt_yday"]        = pct(data["fact_mt"]        - data["day_mt"],        data["plan_mt"])
        data["pct_aks_yday"]       = pct(data["fact_aks"]       - data["day_aks"],       data["plan_aks"])
        data["pct_service_yday"]   = pct(data["fact_service"]   - data["day_service"],   data["plan_service"])
        data["pct_guarantee_yday"] = pct(data["fact_guarantee"] - data["day_guarantee"], data["plan_guarantee"])

        # Приріст за день
        data["delta_to"]        = round(data["pct_to"]        - data["pct_to_yday"],        1)
        data["delta_mt"]        = round(data["pct_mt"]        - data["pct_mt_yday"],        1)
        data["delta_aks"]       = round(data["pct_aks"]       - data["pct_aks_yday"],       1)
        data["delta_service"]   = round(data["pct_service"]   - data["pct_service_yday"],   1)
        data["delta_guarantee"] = round(data["pct_guarantee"] - data["pct_guarantee_yday"], 1)

        # Залишилось до плану
        data["left_to"]        = max(0, data["plan_to"]        - data["fact_to"])
        data["left_mt"]        = max(0, data["plan_mt"]        - data["fact_mt"])
        data["left_aks"]       = max(0, data["plan_aks"]       - data["fact_aks"])
        data["left_service"]   = max(0, data["plan_service"]   - data["fact_service"])
        data["left_guarantee"] = max(0, data["plan_guarantee"] - data["fact_guarantee"])

        # Ефективність
        data["eff_service"]   = pct(data["fact_service"],   data["fact_mt"])
        data["eff_guarantee"] = pct(data["fact_guarantee"], data["fact_mt"])
        data["eff_aks"]       = pct(data["fact_aks"],       data["fact_mt"])

        # Прогноз до кінця місяця
        days_total = data["days_passed"] + data["days_left"]
        def forecast(fact, plan):
            if data["days_passed"] == 0 or plan == 0:
                return 0.0
            return round(fact / data["days_passed"] * days_total / plan * 100, 1)

        data["forecast_to"]        = forecast(data["fact_to"],        data["plan_to"])
        data["forecast_mt"]        = forecast(data["fact_mt"],        data["plan_mt"])
        data["forecast_aks"]       = forecast(data["fact_aks"],       data["plan_aks"])
        data["forecast_service"]   = forecast(data["fact_service"],   data["plan_service"])
        data["forecast_guarantee"] = forecast(data["fact_guarantee"], data["plan_guarantee"])

        return data

    except Exception as e:
        print(f"[ERROR] {shop_code}: {e}")
        return None


def get_all_shops_data() -> dict:
    result = {}
    for code in SHOPS:
        data = get_shop_data(code)
        if data:
            result[code] = data
    return result
