import sys
import os
from datetime import date, timedelta

# Đảm bảo import được từ app/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.import_pnj_to_db import insert_gold_prices_for_date


def bulk_import_pnj(start_date: date, end_date: date):
    for n in range((end_date - start_date).days + 1):
        day = start_date + timedelta(days=n)
        day_str = day.strftime("%Y%m%d")
        print(f"📅 Inserting for {day_str}...")
        try:
            insert_gold_prices_for_date(day_str)
        except Exception as e:
            print(f"❌ Error inserting {day_str}: {e}")


def test_bulk_import_pnj():
    # test đơn giản: 3 ngày đầu năm 2016
    start = date(2016, 1, 1)
    end = date(2016, 1, 3)
    bulk_import_pnj(start, end)


if __name__ == "__main__":
    # chạy thật: cả năm 2016
    bulk_import_pnj(date(2021, 1, 1), date(2025, 7, 24))
