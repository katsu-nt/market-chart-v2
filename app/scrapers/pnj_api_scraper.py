import httpx
import os
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal
from app.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

PNJ_API_URL = os.getenv("PNJ_API_URL")

def normalize_location(name: str) -> str:
    return {
        "TPHCM": "hcm",
        "Hà Nội": "hn",
        "Đà Nẵng": "dn",
        "Miền Tây": "mt",
        "Tây Nguyên": "tn",
        "Đông Nam Bộ": "dnb",
        "Giá vàng nữ trang": "nu_trang"
    }.get(name.strip(), name.lower().replace(" ", "_"))

def normalize_gold_type(name: str) -> str:
    name = name.lower()
    if name == "pnj":
        return "pnj"
    elif name == "sjc":
        return "sjc"
    elif "nhẫn" in name:
        return "pnj_nhan"
    elif "nữ trang" in name:
        return "pnj_nutrang"
    return name.replace(" ", "_").replace(".", "").lower()

def fetch_pnj_history(date: str) -> list[dict]:
    """
    :param date: 'YYYYMMDD'
    :return: list of dicts with normalized gold price records
    """
    if not PNJ_API_URL:
        raise ValueError("PNJ_API_URL not set in .env")

    response = httpx.get(PNJ_API_URL, params={"date": date}, timeout=15)
    response.raise_for_status()

    data = response.json()
    results = []

    for location in data.get("locations", []):
        loc_code = normalize_location(location["name"])

        for gold_item in location.get("gold_type", []):
            gold_code = normalize_gold_type(gold_item["name"])

            for entry in gold_item.get("data", []):
                try:
                    ts = datetime.strptime(entry["updated_at"], "%d/%m/%Y %H:%M:%S")
                    results.append({
                        "timestamp": ts.isoformat(),
                        "date": ts.date().isoformat(),
                        "buy_price": Decimal(entry["gia_mua"].replace(".", "")),
                        "sell_price": Decimal(entry["gia_ban"].replace(".", "")),
                        "gold_type": gold_code,
                        "unit": "tael",
                        "location": loc_code
                    })
                except Exception as e:
                    logger.error("❌ Error parsing entry:", entry, "⚠", e)

    return results
