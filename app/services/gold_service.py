from app.repository.gold_repo import GoldPriceRepository
from app.schemas.gold import (
    GoldPriceResponse, GoldPriceListResponse, GoldChartResponse,
    GoldChartItem, ImportRange
)
from app.models.gold import GoldType, Unit, Location, GoldPrice
from typing import List, Dict, Any
from datetime import date, timedelta

class GoldPriceService:
    def __init__(self, repo: GoldPriceRepository):
        self.repo = repo

    def get_current_gold_price(self, gold_type: str, location: str, unit: str):
        gt = self.repo.get_gold_type_by_code(gold_type)
        loc = self.repo.get_location_by_code(location)
        un = self.repo.get_unit_by_code(unit)
        if not gt or not loc or not un:
            raise ValueError("Not found: gold_type, location, or unit.")

        gold_price = self.repo.get_latest(gt.id, loc.id, un.id)
        prev_price = self.repo.get_latest_before(gt.id, loc.id, un.id, gold_price.timestamp) if gold_price else None

        delta_buy = delta_sell = delta_buy_percent = delta_sell_percent = None
        if gold_price and prev_price:
            delta_buy = float(gold_price.buy_price) - float(prev_price.buy_price)
            delta_sell = float(gold_price.sell_price) - float(prev_price.sell_price)
            if prev_price.buy_price and float(prev_price.buy_price) != 0:
                delta_buy_percent = (delta_buy / float(prev_price.buy_price)) * 100
            if prev_price.sell_price and float(prev_price.sell_price) != 0:
                delta_sell_percent = (delta_sell / float(prev_price.sell_price)) * 100

        response = GoldPriceResponse(
            timestamp=gold_price.timestamp,
            buy_price=float(gold_price.buy_price),
            sell_price=float(gold_price.sell_price),
            gold_type=gt.code,
            unit=un.code,
            location=loc.code,
            delta_buy=delta_buy,
            delta_sell=delta_sell,
            delta_buy_percent=delta_buy_percent,
            delta_sell_percent=delta_sell_percent,
        ) if gold_price else None

        return {"status": "success", "data": [response] if response else []}

    def get_gold_chart(self, gold_types: List[str], locations: List[str], days: int):
        data = {}
        today = date.today()
        start = today - timedelta(days=days-1)
        for gt_code in gold_types:
            gt = self.repo.get_gold_type_by_code(gt_code)
            if not gt: continue
            for loc_code in locations:
                loc = self.repo.get_location_by_code(loc_code)
                if not loc: continue
                # mặc định unit là tael
                un = self.repo.get_unit_by_code("tael")
                if not un: continue
                series = self.repo.get_range(gt.id, loc.id, un.id, start, today)
                daily_latest = {}
                for p in series:
                    d = p.timestamp.date()
                    if d not in daily_latest or p.timestamp > daily_latest[d].timestamp:
                        daily_latest[d] = p
                key = f"{gt_code}-{loc_code}"
                data[key] = [GoldChartItem(date=day, price=float(p.sell_price)) for day, p in sorted(daily_latest.items())]
        return GoldChartResponse(status="success", data=data)

    def get_gold_table(self, selected_date: date):
        current_data = self.repo.get_latest_group_by_key(selected_date)
        previous_data = self.repo.get_latest_group_by_key(selected_date - timedelta(days=1))
        prev_map = {(p.gold_type_id, p.unit_id, p.location_id): p for p in previous_data}
        result = []
        for cur in current_data:
            prev = prev_map.get((cur.gold_type_id, cur.unit_id, cur.location_id))
            delta_buy = delta_sell = None
            if prev:
                delta_buy = float(cur.buy_price) - float(prev.buy_price)
                delta_sell = float(cur.sell_price) - float(prev.sell_price)
            gt = cur.gold_type
            un = cur.unit
            loc = cur.location
            result.append(GoldPriceResponse(
                timestamp=cur.timestamp,
                buy_price=float(cur.buy_price),
                sell_price=float(cur.sell_price),
                gold_type=gt.code,
                unit=un.code,
                location=loc.code,
                delta_buy=delta_buy,
                delta_sell=delta_sell
            ))
        return GoldPriceListResponse(status="success", data=result)


    def import_gold_data_from_json(self, items: List[dict]):
        inserted, skipped = 0, 0
        for entry in items:
            gt = self.repo.get_gold_type_by_code(entry["gold_type"]["code"])
            if not gt:
                gt = GoldType(**entry["gold_type"])
                self.repo.db.add(gt)
                self.repo.db.flush()
            un = self.repo.get_unit_by_code(entry["unit"]["code"])
            if not un:
                un = Unit(**entry["unit"])
                self.repo.db.add(un)
                self.repo.db.flush()
            loc = self.repo.get_location_by_code(entry["location"]["code"])
            if not loc:
                loc = Location(**entry["location"])
                self.repo.db.add(loc)
                self.repo.db.flush()
            timestamp = entry["timestamp"]
            exists = self.repo.db.query(GoldPrice).filter_by(
                timestamp=timestamp,
                gold_type_id=gt.id,
                unit_id=un.id,
                location_id=loc.id
            ).first()
            if exists:
                skipped += 1
                continue
            gold_price = GoldPrice(
                timestamp=timestamp,
                buy_price=entry["buy_price"],
                sell_price=entry["sell_price"],
                gold_type_id=gt.id,
                unit_id=un.id,
                location_id=loc.id
            )
            self.repo.db.add(gold_price)
            inserted += 1
        self.repo.db.commit()
        return {"inserted": inserted, "skipped": skipped}

    def import_pnj_range(self, start: date, end: date, scraper):
        total_days = (end - start).days + 1
        report = []
        inserted, skipped = 0, 0
        for n in range(total_days):
            day = start + timedelta(days=n)
            try:
                items = scraper.fetch(day.strftime("%Y%m%d"))
                count = 0
                for item in items:
                    gt = self.repo.get_gold_type_by_code(item["gold_type_code"])
                    if not gt:
                        gt = GoldType(code=item["gold_type_code"], name=item["gold_type_code"], source="pnj")
                        self.repo.db.add(gt)
                        self.repo.db.flush()
                    un = self.repo.get_unit_by_code(item["unit_code"])
                    if not un:
                        un = Unit(code=item["unit_code"], name=item["unit_code"])
                        self.repo.db.add(un)
                        self.repo.db.flush()
                    loc = self.repo.get_location_by_code(item["location_code"])
                    if not loc:
                        loc = Location(code=item["location_code"], name=item["location_code"])
                        self.repo.db.add(loc)
                        self.repo.db.flush()
                    exists = self.repo.db.query(GoldPrice).filter_by(
                        timestamp=item["timestamp"],
                        gold_type_id=gt.id,
                        unit_id=un.id,
                        location_id=loc.id
                    ).first()
                    if exists:
                        skipped += 1
                        continue
                    gold_price = GoldPrice(
                        timestamp=item["timestamp"],
                        buy_price=item["buy_price"],
                        sell_price=item["sell_price"],
                        gold_type_id=gt.id,
                        unit_id=un.id,
                        location_id=loc.id
                    )
                    self.repo.db.add(gold_price)
                    inserted += 1
                    count += 1
                self.repo.db.commit()
                report.append({"date": str(day), "status": "success", "inserted": count})
            except Exception as e:
                self.repo.db.rollback()
                report.append({"date": str(day), "status": "error", "error": str(e)})
        return {"inserted": inserted, "skipped": skipped, "report": report}
