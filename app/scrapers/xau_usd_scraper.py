import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from decimal import Decimal
from pytz import timezone

def scrape_xau_usd_price() -> dict:
    url = "https://vn.investing.com/currencies/xau-usd"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Referer": "https://www.google.com/"
    }

    resp = httpx.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    price_tag = soup.select_one('div[data-test="instrument-price-last"]')
    if not price_tag:
        raise ValueError("❌ Không tìm thấy giá vàng XAU/USD trên trang")
    raw_price = price_tag.text.strip().replace(",", "")
    sell_price = Decimal(raw_price)

    tz = timezone("Asia/Ho_Chi_Minh")
    now_hcm = datetime.now(tz)
    timestamp_iso = now_hcm.replace(tzinfo=None)

    return {
        "timestamp": timestamp_iso,
        "buy_price": 0,
        "sell_price": sell_price,
        "gold_type": {
            "code": "xau_usd",
            "name": "Giá vàng thế giới (XAU/USD)",
            "source": "investing.com"
        },
        "unit": {
            "code": "ounce",
            "name": "Ounce (1 oz)"
        },
        "location": {
            "code": "global",
            "name": "Thị trường thế giới"
        }
    }
