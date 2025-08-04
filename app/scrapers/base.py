from abc import ABC, abstractmethod
from typing import List, Dict

class GoldScraperBase(ABC):
    @abstractmethod
    def fetch(self, date: str) -> List[Dict]:
        """Fetch gold price data for a given date. Must return a list of dict:
        {
            "timestamp": datetime,
            "buy_price": Decimal,
            "sell_price": Decimal,
            "gold_type_code": str,
            "unit_code": str,
            "location_code": str
        }
        """
        pass
