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
        "Giá vàng nữ trang": "tq"
    }.get(name.strip(), name.strip().lower().replace(" ", "_"))


def normalize_gold_type(name: str) -> str:
    return name.strip().lower()\
        .replace(" ", "_")\
        .replace(".", "")\
        .replace("(", "")\
        .replace(")", "")\
        .replace("-", "_")


def fetch_pnj_history(date: str) -> list[dict]:
    """
    Gọi API PNJ và chuẩn hóa dữ liệu về dạng phù hợp với model gold_prices:
    Không chứa id, không chứa date, chỉ còn:
        - timestamp
        - buy_price, sell_price
        - gold_type_code, gold_type_name
        - unit_code, location_code
    :param date: 'YYYYMMDD'
    :return: List[Dict] đã chuẩn hóa
    """
    if not PNJ_API_URL:
        raise ValueError("PNJ_API_URL not set in .env")

    try:
        response = httpx.get(PNJ_API_URL, params={"date": date}, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"❌ Failed to fetch data for {date}: {e}")
        return []

    try:
        data = response.json()
    except Exception as e:
        logger.error(f"❌ Failed to parse JSON response for {date}: {e}")
        return []

    results = []
    errors = 0

    for location in data.get("locations", []):
        loc_code = normalize_location(location.get("name", "").strip())

        for gold_item in location.get("gold_type", []):
            raw_name = gold_item.get("name", "").strip()
            gold_code = normalize_gold_type(raw_name)

            for entry in gold_item.get("data", []):
                try:
                    ts = datetime.strptime(entry["updated_at"], "%d/%m/%Y %H:%M:%S")
                    results.append({
                        "timestamp": ts,
                        "buy_price": Decimal(entry["gia_mua"].replace(".", "")),
                        "sell_price": Decimal(entry["gia_ban"].replace(".", "")),
                        "gold_type_code": gold_code,
                        "gold_type_name": raw_name,
                        "unit_code": "tael",
                        "location_code": loc_code
                    })
                except Exception as e:
                    errors += 1
                    logger.warning(f"⚠️ Skipped malformed entry: {entry} ⚠ {e}")

    logger.info(f"✅ Parsed {len(results)} records for {date} ({errors} skipped)")
    return results
