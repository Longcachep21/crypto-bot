# ============================================================
#  CẤU HÌNH BOT - BẠN CHỈ CẦN SỬA FILE NÀY
# ============================================================

# --- 1. Thông tin Telegram (xem hướng dẫn lấy trong README) ---
TELEGRAM_TOKEN = "8886739251:AAHUaQP9kYe2v5Rue2DYylHuzjD4XYqiFUk"     # Token bot lấy từ @BotFather
TELEGRAM_CHAT_ID = "8111145571"     # ID chat của bạn

# --- 2. Coin theo dõi ---
# Bot tự lấy top coin theo vốn hóa, từ hạng THEO_DOI_TU đến THEO_DOI_DEN.
THEO_DOI_TU = 50      # bắt đầu từ hạng (vốn hóa) thứ mấy
THEO_DOI_DEN = 100 # đến hạng thứ mấy

# Nếu muốn theo dõi THÊM vài coin cụ thể (id CoinGecko, chữ thường), điền vào đây.
# Để trống [] cũng được. Ví dụ: ["bitcoin", "ethereum"]
COIN_THEM = ["bitcoin", "ethereum"]

# --- 3. Giờ gửi bản tin hằng ngày (giờ Việt Nam, dạng 24h) ---
GIO_GUI_BAN_TIN = ["08:00", "14:00"]

# --- 4. Ngưỡng cảnh báo biến động realtime ---
NGUONG_BIEN_DONG = 5.0      # cảnh báo khi giá đổi +/- bao nhiêu % trong 1 giờ
PHUT_KIEM_TRA = 5           # cứ bao nhiêu phút kiểm tra giá một lần
