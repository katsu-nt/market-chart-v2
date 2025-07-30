import requests
from bs4 import BeautifulSoup
from datetime import datetime
from decimal import Decimal
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pytz import timezone



def get_session():
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

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

    session = get_session()
    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Lấy giá vàng
    price_tag = soup.select_one('div[data-test="instrument-price-last"]')
    if not price_tag:
        raise ValueError("❌ Không tìm thấy giá vàng XAU/USD trên trang")

    raw_price = price_tag.text.strip().replace(",", "")
    sell_price = Decimal(raw_price)

    # Lấy thời gian hiện tại theo giờ TP.HCM
    tz = timezone("Asia/Ho_Chi_Minh")
    now_hcm = datetime.now(tz)
    timestamp_iso = now_hcm.isoformat()

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
