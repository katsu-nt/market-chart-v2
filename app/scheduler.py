from apscheduler.schedulers.background import BackgroundScheduler
from app.services.import_pnj_to_db import insert_gold_prices_for_date
from app.scrapers.xau_usd_scraper import scrape_xau_usd_price
from app.services.import_xau_usd import insert_xau_usd_price
from app.database import SessionLocal
from datetime import datetime, date
from app.utils.logger import get_logger

logger = get_logger(__name__)

def run_hourly_job():
    today_str = date.today().strftime("%Y%m%d")
    logger.info(f"🟡 [PNJ] Scheduler running at {datetime.now().strftime('%H:%M:%S')} for {today_str}")
    try:
        insert_gold_prices_for_date(today_str)
    except Exception as e:
        logger.error(f"❌ [PNJ] Scheduler error: {e}")

def run_xau_usd_job():
    logger.info(f"🟠 [XAU] Scraper running at {datetime.now().strftime('%H:%M:%S')}")
    db = SessionLocal()
    try:
        data = scrape_xau_usd_price()
        result = insert_xau_usd_price(data, db)
        logger.info(f"✅ [XAU] Scraped + inserted: {result}")
    except Exception as e:
        logger.error(f"❌ [XAU] Scraper error: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")

    scheduler.add_job(run_hourly_job, "cron", minute="1")


    scheduler.add_job(run_xau_usd_job, "cron", minute="1")  

    scheduler.start()
    logger.info("✅ Scheduler started")
