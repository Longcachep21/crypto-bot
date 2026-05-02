# 🤖 Crypto Telegram Bot – Tài Liệu Dự Án

> **Workspace:** `l:\posches 911 tuboS\crypto-bot`  
> **GitHub:** https://github.com/Longcachep21/crypto-bot  
> **Chạy tự động:** GitHub Actions – 10:00 sáng mỗi ngày (giờ VN)

---

## ✅ Trạng thái hiện tại (01/05/2026)

Bot hoạt động ổn định, gửi báo cáo Telegram tự động hàng ngày.

### Kết quả test thực tế:
```
📊 5 COIN LỚN NHẤT
  BTC: $78,325 (+2.66%)📈 | 7d:+0.1% | RSI:78.5🔴
  ETH: $2,310 (+2.09%)📈  | 7d:-0.8% | RSI:74.1🔴
  BNB: $621.05 (+0.98%)   | 7d:-2.7% | RSI:59.7🟡
  SOL: $84.52 (+1.66%)📈  | 7d:-1.9% | RSI:73.2🔴
  XRP: $1.39 (+1.45%)📈   | 7d:-3.4% | RSI:65.8🟡

🟢 TOP 5 TĂNG | 🔴 TOP 5 GIẢM
📈 BREADTH: 41 tăng | 12 giảm | 54 coin
👑 BTC Dominance: 58.4%
😱 Fear&Greed: 26/100 – Sợ hãi
🏦 DeFi TVL: $84.48B
```

---

## 🏗️ Kiến trúc dự án

```
crypto-bot/
├── main.py              # Entry point: python main.py --test
├── config.py            # Danh sách coin, timezone, labels
├── scheduler.py         # Lên lịch tự động hàng ngày
├── .env                 # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (bí mật, không push)
├── requirements.txt     # Thư viện cần cài
├── README.md            # File này
├── data/
│   ├── fetcher.py       # ⭐ Thu thập dữ liệu từ API
│   └── analyzer.py      # Phân tích thị trường, tính điểm tín hiệu
├── bot/
│   ├── formatter.py     # Định dạng báo cáo HTML gửi Telegram
│   └── telegram_bot.py  # Gửi tin nhắn qua Telegram API
└── .github/workflows/
    └── daily_report.yml # GitHub Actions – tự động lúc 03:00 UTC (10:00 VN)
```

---

## 📡 Nguồn dữ liệu

| Dữ liệu | API | Ghi chú |
|---|---|---|
| Giá + 24h + 7d + RSI | **CoinGecko** `/coins/markets?sparkline=true` | 1 request, miễn phí |
| Fear & Greed Index | **alternative.me** | Miễn phí |
| DeFi TVL | **DeFiLlama** `/v2/chains` | Miễn phí |
| BTC Dominance | **CoinGecko** `/global` | Miễn phí |
| Funding Rate | ~~Binance~~ | ❌ Bị chặn 451 trên GitHub Actions (server Mỹ) |

> ⚠️ **Lý do bỏ Binance:** GitHub Actions chạy server Mỹ/EU → Binance trả lỗi **451 Unavailable For Legal Reasons**

---

## 🔧 Kỹ thuật quan trọng

### RSI tính từ Sparkline (không cần gọi thêm API)
```python
# sparkline_in_7d.price = 168 điểm giá mỗi giờ trong 7 ngày
spark_prices = coin["sparkline_in_7d"]["price"]
rsi = _calc_rsi(spark_prices, period=14)
```

### Retry thông minh khi bị rate-limit 429
```python
if resp.status_code == 429:
    time.sleep(35 * (attempt + 1))  # chờ 35s, 70s, 105s...
```

### GitHub Secrets cần có
Vào **GitHub repo → Settings → Secrets → Actions**:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

---

## 🚀 Cách chạy

```bash
# Chạy test ngay lập tức (gửi Telegram luôn)
python main.py --test

# Chạy GitHub Actions thủ công
# GitHub repo → Actions → "Crypto Daily Report" → Run workflow
```

---

## 💡 Ý tưởng nâng cấp trong tương lai

### Tính năng mới
- [ ] **CoinGecko Pro API key** – tăng rate limit, 100% coin có dữ liệu
- [ ] **Báo cáo tuần** (thứ Hai) và **báo cáo tháng** (đầu tháng)
- [ ] **Cảnh báo giá** – khi BTC vượt/dưới ngưỡng (VD: BTC < $70,000)
- [ ] **Lịch sử báo cáo** – lưu vào file JSON hoặc SQLite
- [ ] **Lệnh Telegram** – `/price BTC`, `/rsi ETH`, `/report`
- [ ] **Funding rate** từ Bybit hoặc OKX API (thay Binance)
- [ ] **On-chain data** – Whale alerts, dòng tiền vào/ra sàn
- [ ] **Tin tức crypto** – CryptoPanic API
- [ ] **Biểu đồ** – gửi ảnh chart giá kèm báo cáo

### Cải thiện hiện có
- [ ] **Volume ratio** – lấy vol lịch sử từ CoinGecko (cần API key)
- [ ] **Thêm coin** – ONDO, STRK, JUP, ENA, SEI...
- [ ] **Cảnh báo RSI** – thông báo riêng khi RSI < 30 (oversold) cho coin bất kỳ
- [ ] **Đa ngôn ngữ** – thêm bản tiếng Anh

---

## 📦 Dependencies

```
requests
python-telegram-bot
apscheduler
pytz
python-dotenv
```

Cài đặt: `pip install -r requirements.txt`
