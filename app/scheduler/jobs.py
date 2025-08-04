from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.database import SessionLocal
from app.repository.gold_repo import GoldPriceRepository
from app.services.gold_service import GoldPriceService
from app.scrapers.pnj_scraper import PNJScraper
from app.scrapers.xau_usd_scraper import scrape_xau_usd_price
from app.services.import_xau_usd import insert_xau_usd_price

def crawl_gold_pnj_job():
    db = SessionLocal()
    try:
        repo = GoldPriceRepository(db)
        service = GoldPriceService(repo)
        scraper = PNJScraper()
        today = datetime.today().date()
        today_str = today.strftime("%Y%m%d")
        print(f"[Scheduler] Crawling PNJ gold for {today_str}")
        result = service.import_pnj_range(
            start=today,
            end=today,
            scraper=scraper
        )
        print(f"[Scheduler] PNJ gold: Inserted: {result['inserted']}, Skipped: {result['skipped']}")
    except Exception as e:
        print(f"[Scheduler] PNJ gold error: {e}")
    finally:
        db.close()

def crawl_xau_usd_job():
    db = SessionLocal()
    try:
        print(f"[Scheduler] Crawling XAU/USD gold at {datetime.now()}")
        data = scrape_xau_usd_price()
        result = insert_xau_usd_price(data, db)
        print(f"[Scheduler] XAU/USD: Inserted: {result['inserted']}, Skipped: {result['skipped']}")
    except Exception as e:
        print(f"[Scheduler] XAU/USD error: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")
    # Giá vàng PNJ mỗi 1 giờ
    scheduler.add_job(crawl_gold_pnj_job, "interval", hours=1, id="crawl_gold_pnj_hourly")
    # Giá vàng thế giới XAU/USD mỗi 1 giờ
    scheduler.add_job(crawl_xau_usd_job, "interval", hours=1, id="crawl_xau_usd_hourly")
    scheduler.start()
    print("[Scheduler] All jobs started.")

# Gọi start_scheduler() ở main.py khi app khởi động
