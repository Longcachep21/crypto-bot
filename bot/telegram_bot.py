import logging
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


async def send_message_async(text: str) -> bool:
    """Gửi tin nhắn HTML đến Telegram (async)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env")
        return False
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id    = TELEGRAM_CHAT_ID,
            text       = text,
            parse_mode = ParseMode.HTML,
        )
        logger.info("✅ Đã gửi báo cáo lên Telegram thành công!")
        return True
    except Exception as e:
        logger.error(f"❌ Lỗi gửi Telegram: {e}")
        return False


def send_message(text: str) -> bool:
    """Wrapper đồng bộ — gọi từ scheduler."""
    return asyncio.run(send_message_async(text))


async def send_startup_message():
    """Gửi tin nhắn thông báo bot đã khởi động."""
    msg = (
        "🤖 <b>Crypto Bot đã khởi động!</b>\n"
        "📅 Báo cáo hàng ngày sẽ gửi lúc <b>14:00 giờ VN</b>.\n"
        "✅ Nguồn: Binance · Fear&amp;Greed · DeFiLlama"
    )
    await send_message_async(msg)
