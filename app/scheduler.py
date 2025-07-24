from apscheduler.schedulers.background import BackgroundScheduler
from app.services.import_pnj_to_db import insert_gold_prices_for_date
from datetime import datetime, date
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_hourly_job():
    today_str = date.today().strftime("%Y%m%d")
    logger.info(f"⏰ Scheduler running at {datetime.now().strftime('%H:%M:%S')} for {today_str}")
    try:
        insert_gold_prices_for_date(today_str)
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(run_hourly_job, "cron", minute=59)
    scheduler.start()
    logger.info("✅ Scheduler started")
