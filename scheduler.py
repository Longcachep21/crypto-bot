import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import TIMEZONE, REPORT_HOUR, REPORT_MINUTE
from data.fetcher   import fetch_all
from data.analyzer  import analyze_market
from bot.formatter  import build_report
from bot.telegram_bot import send_message
from config import COINS

logger = logging.getLogger(__name__)


def run_report():
    """Hàm chính: lấy dữ liệu → phân tích → format → gửi Telegram."""
    logger.info("⏰ Bắt đầu thu thập và gửi báo cáo...")
    try:
        data     = fetch_all(COINS)
        analysis = analyze_market(data)
        report   = build_report(data, analysis)
        send_message(report)
    except Exception as e:
        logger.error(f"❌ Lỗi khi chạy báo cáo: {e}")
        send_message(f"❌ <b>Bot gặp lỗi khi chạy báo cáo:</b>\n<code>{e}</code>")


def start_scheduler():
    """Khởi động scheduler — chạy run_report() mỗi ngày lúc 14:00 VN."""
    tz        = pytz.timezone(TIMEZONE)
    scheduler = BlockingScheduler(timezone=tz)

    scheduler.add_job(
        func    = run_report,
        trigger = CronTrigger(hour=REPORT_HOUR, minute=REPORT_MINUTE, timezone=tz),
        id      = "daily_crypto_report",
        name    = "Báo cáo crypto 14:00",
        replace_existing = True,
    )

    logger.info(f"📅 Scheduler đã cài đặt: mỗi ngày {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} ({TIMEZONE})")
    logger.info("🔁 Bot đang chạy... Nhấn Ctrl+C để dừng.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot đã dừng.")
