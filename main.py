"""
╔══════════════════════════════════════════╗
║   CRYPTO TELEGRAM BOT – Entry Point      ║
║   Chạy: python main.py                   ║
║   Test ngay: python main.py --test       ║
╚══════════════════════════════════════════╝
"""

import sys
import logging
import asyncio

# Fix emoji/UTF-8 trên Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# ── Cấu hình logging ────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt= "%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


from config           import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, COINS
from data.fetcher     import fetch_all
from data.analyzer    import analyze_market
from bot.formatter    import build_report
from bot.telegram_bot import send_message, send_startup_message
from scheduler        import start_scheduler


def check_config():
    """Kiểm tra cấu hình trước khi khởi động."""
    ok = True
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ Thiếu TELEGRAM_BOT_TOKEN trong file .env")
        ok = False
    if not TELEGRAM_CHAT_ID:
        logger.error("❌ Thiếu TELEGRAM_CHAT_ID trong file .env")
        ok = False
    return ok


def run_test():
    """Chạy thử ngay lập tức — không cần đợi 14:00."""
    logger.info("🧪 Chế độ TEST – Đang chạy báo cáo ngay...")
    data     = fetch_all(COINS)
    analysis = analyze_market(data)
    report   = build_report(data, analysis)

    # In ra màn hình để kiểm tra
    print("\n" + "="*50)
    print("📋 NỘI DUNG BÁO CÁO (preview):")
    print("="*50)
    # Bỏ HTML tags để đọc dễ hơn trên terminal
    import re
    clean = re.sub(r"<[^>]+>", "", report)
    print(clean)
    print("="*50 + "\n")

    # Gửi lên Telegram
    ok = send_message(report)
    if ok:
        logger.info("✅ Gửi thành công lên Telegram!")
    else:
        logger.error("❌ Gửi Telegram thất bại – kiểm tra token và chat_id.")


def main():
    logger.info("🚀 Khởi động Crypto Telegram Bot...")

    if not check_config():
        logger.error("⛔ Vui lòng cấu hình file .env trước khi chạy.")
        logger.info("   Hướng dẫn: copy .env.example → .env rồi điền token.")
        sys.exit(1)

    # python main.py --test  →  chạy thử ngay, không dùng scheduler
    if "--test" in sys.argv:
        run_test()
        return

    # Gửi thông báo bot khởi động
    asyncio.run(send_startup_message())

    # Chạy scheduler (blocking – bot sẽ chạy mãi cho đến khi Ctrl+C)
    start_scheduler()


if __name__ == "__main__":
    main()
