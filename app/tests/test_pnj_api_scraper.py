import sys
import os
from decimal import Decimal

# Đảm bảo thêm thư mục gốc để import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.pnj_api_scraper import fetch_pnj_history


def test_fetch_pnj_history():
    sample_date = "20250710"  # <- chỉnh ngày theo dữ liệu bạn muốn test
    results = fetch_pnj_history(sample_date)

    assert isinstance(results, list), "Expected result to be a list"
    assert len(results) > 0, "No records returned"

    sample = results[0]
    expected_keys = {
        "timestamp",
        "buy_price",
        "sell_price",
        "gold_type_code",
        "unit_code",
        "location_code"
    }

    missing = expected_keys - sample.keys()
    assert not missing, f"Missing keys: {missing}"

    assert sample["unit_code"] == "tael", f"Unexpected unit_code: {sample['unit_code']}"
    assert isinstance(sample["buy_price"], Decimal), "buy_price is not Decimal"
    assert isinstance(sample["sell_price"], Decimal), "sell_price is not Decimal"

    print("✅ Test passed with", len(results), "records.")
    print("🟡 All records:")
    for i, record in enumerate(results, 1):
        print(f"{i:03d}. {record}")


if __name__ == "__main__":
    try:
        test_fetch_pnj_history()
    except AssertionError as e:
        print("❌ Test failed:", e)
        sys.exit(1)
    except Exception as e:
        print("❌ Unexpected error:", e)
        sys.exit(2)
