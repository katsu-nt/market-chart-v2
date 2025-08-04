from app.scrapers.base import GoldScraperBase
import httpx
from datetime import datetime
from decimal import Decimal
from typing import List, Dict
import os

def normalize_location(name: str) -> str:
    """Chuẩn hóa tên địa điểm"""
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
    return name.strip().lower().replace(" ", "_").replace(".", "").replace("(", "").replace(")", "").replace("-", "_")

class PNJScraper(GoldScraperBase):
    def __init__(self):
        # Bạn có thể lấy từ biến môi trường hoặc hardcode cho test nhanh
        self.api_url = os.getenv("PNJ_API_URL", "https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price-history")

    def fetch(self, date: str) -> List[Dict]:
        """
        Lấy dữ liệu từ PNJ cho 1 ngày, trả về list dict chuẩn hóa cho insert DB.
        date: YYYYMMDD
        """
        try:
            response = httpx.get(self.api_url, params={"date": date}, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"❌ Failed to fetch PNJ API: {e}")
            return []

        results = []
        for location in data.get("locations", []):
            loc_code = normalize_location(location.get("name", ""))
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
                            "unit_code": "tael",  # Nếu bạn có nhiều unit thì sửa ở đây
                            "location_code": loc_code
                        })
                    except Exception as e:
                        print(f"⚠️ Skipped malformed entry: {entry} ({e})")
        return results
