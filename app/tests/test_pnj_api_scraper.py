import sys
import os
from decimal import Decimal
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.pnj_api_scraper import fetch_pnj_history


def test_fetch_pnj_history():
    sample_date = "20250710"
    results = fetch_pnj_history(sample_date)

    assert isinstance(results, list)
    assert len(results) > 0

    sample = results[0]
    assert "timestamp" in sample
    assert "date" in sample
    assert "buy_price" in sample
    assert "sell_price" in sample
    assert "gold_type" in sample
    assert "unit" in sample
    assert "location" in sample

    assert sample["unit"] == "tael"
    assert isinstance(sample["buy_price"], Decimal)
    assert isinstance(sample["sell_price"], Decimal)

    print("✅ Test passed with", len(results), "records.")
    print("🟡 Sample records:")
    for i, record in enumerate(results, 1):
        print(f"{i:02d}. {record}")


