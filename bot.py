"""
Bot Telegram tổng hợp tin & giá crypto.
- Tự gửi bản tin vào giờ đã đặt (mặc định 8h, 14h).
- Cảnh báo realtime khi giá biến động mạnh.
- Trả lời lệnh bạn gõ trong Telegram: /gia /tin /thitruong /bantin
Chạy bằng: python bot.py
"""
import time
import datetime
import requests
import schedule

import config

CG = "https://api.coingecko.com/api/v3"
NEWS_URL = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
API = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"

gia_truoc = {}      # lưu giá lần trước để so biến động
_danh_sach = []     # cache danh sách coin theo dõi


# ============ Gửi / lấy dữ liệu ============

def gui_telegram(text, chat_id=None):
    try:
        requests.post(f"{API}/sendMessage", data={
            "chat_id": chat_id or config.TELEGRAM_CHAT_ID,
            "text": text, "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)
    except Exception as e:
        print("Lỗi gửi Telegram:", e)


def lay_danh_sach_coin():
    global _danh_sach
    try:
        r = requests.get(f"{CG}/coins/markets", params={
            "vs_currency": "usd", "order": "market_cap_desc",
            "per_page": config.THEO_DOI_DEN, "page": 1,
        }, timeout=15).json()
        ids = [c["id"] for c in r][config.THEO_DOI_TU - 1:config.THEO_DOI_DEN]
        for c in config.COIN_THEM:
            if c not in ids:
                ids.append(c)
        if ids:
            _danh_sach = ids
    except Exception as e:
        print("Lỗi lấy danh sách coin:", e)
    return _danh_sach


def lay_gia(ids):
    try:
        r = requests.get(f"{CG}/simple/price", params={
            "ids": ",".join(ids), "vs_currencies": "usd",
            "include_24hr_change": "true",
        }, timeout=15)
        return r.json()
    except Exception as e:
        print("Lỗi lấy giá:", e)
        return {}


def lay_top_thi_truong():
    try:
        glob = requests.get(f"{CG}/global", timeout=15).json()["data"]
        markets = requests.get(f"{CG}/coins/markets", params={
            "vs_currency": "usd", "order": "market_cap_desc",
            "per_page": 50, "page": 1, "price_change_percentage": "24h",
        }, timeout=15).json()
        return glob, markets
    except Exception as e:
        print("Lỗi lấy thị trường:", e)
        return None, []


def lay_tin(gioi_han=5):
    try:
        data = requests.get(NEWS_URL, timeout=15).json()["Data"]
        cutoff = time.time() - 2 * 86400
        tins = [n for n in data if n.get("published_on", 0) >= cutoff]
        if not tins:
            tins = data
        return tins[:gioi_han]
    except Exception as e:
        print("Lỗi lấy tin:", e)
        return []


def dinh_dang_gia(p):
    return f"{p:,.2f}" if p >= 1 else f"{p:,.6f}"


# ============ Soạn nội dung ============

def soan_thitruong():
    glob, markets = lay_top_thi_truong()
    if not glob:
        return "Không lấy được dữ liệu thị trường lúc này."
    dong = ["<b>📊 TỔNG QUAN THỊ TRƯỜNG</b>", ""]
    cap = glob["total_market_cap"]["usd"]
    chg = glob.get("market_cap_change_percentage_24h_usd", 0)
    dau = "🟢" if chg >= 0 else "🔴"
    dong.append(f"{dau} Tổng vốn hóa: ${cap/1e12:.2f}T ({chg:+.2f}% / 24h)")
    dong.append(f"₿ BTC thống trị: {glob['market_cap_percentage']['btc']:.1f}%")
    if markets:
        sap = sorted([m for m in markets if m.get("price_change_percentage_24h") is not None],
                     key=lambda x: x["price_change_percentage_24h"], reverse=True)
        dong.append("")
        dong.append("🚀 Tăng: " + ", ".join(f"{m['symbol'].upper()} {m['price_change_percentage_24h']:+.1f}%" for m in sap[:3]))
        dong.append("📉 Giảm: " + ", ".join(f"{m['symbol'].upper()} {m['price_change_percentage_24h']:+.1f}%" for m in sap[-3:][::-1]))
    return "\n".join(dong)


def soan_gia():
    ds = lay_danh_sach_coin()
    gia = lay_gia(ds)
    if not gia:
        return "Không lấy được giá lúc này."
    dong = [f"<b>💰 GIÁ NHÓM COIN (hạng {config.THEO_DOI_TU}-{config.THEO_DOI_DEN})</b>", ""]
    for cid in ds:
        p = gia.get(cid)
        if not p:
            continue
        c = p.get("usd_24h_change", 0)
        dau = "🟢" if c >= 0 else "🔴"
        dong.append(f"{dau} {cid.upper()}: ${dinh_dang_gia(p['usd'])} ({c:+.2f}%)")
    return "\n".join(dong)


def soan_tin():
    tins = lay_tin(6)
    if not tins:
        return "Không lấy được tin lúc này."
    dong = ["<b>📰 TIN MỚI (2 ngày)</b>", ""]
    for n in tins:
        src = (n.get("source_info") or {}).get("name", n.get("source", ""))
        dong.append(f"• {n['title']} <i>({src})</i>\n{n['url']}")
    return "\n".join(dong)


def soan_ban_tin():
    now = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")
    parts = [f"<b>📊 BẢN TIN CRYPTO — {now}</b>", "",
             soan_thitruong(), "", soan_gia(), "", soan_tin(), "",
             "⚠️ Thông tin tham khảo, không phải lời khuyên đầu tư."]
    return "\n".join(parts)


# ============ Hành động định kỳ ============

def ban_tin():
    gui_telegram(soan_ban_tin())
    print("Đã gửi bản tin lúc", datetime.datetime.now().strftime("%H:%M"))


def kiem_tra_bien_dong():
    ds = lay_danh_sach_coin()
    gia = lay_gia(ds)
    for cid in ds:
        p = gia.get(cid)
        if not p:
            continue
        gia_moi = p["usd"]
        if cid in gia_truoc:
            cu = gia_truoc[cid]
            thay_doi = (gia_moi - cu) / cu * 100
            if abs(thay_doi) >= config.NGUONG_BIEN_DONG:
                dau = "🟢📈" if thay_doi > 0 else "🔴📉"
                gui_telegram(
                    f"{dau} <b>CẢNH BÁO BIẾN ĐỘNG</b>\n"
                    f"{cid.upper()} vừa đổi {thay_doi:+.2f}% trong ~{config.PHUT_KIEM_TRA} phút.\n"
                    f"Giá hiện tại: ${dinh_dang_gia(gia_moi)}"
                )
                print(f"Cảnh báo {cid}: {thay_doi:+.2f}%")
        gia_truoc[cid] = gia_moi


# ============ Xử lý lệnh trong Telegram ============

MENU = (
    "<b>🤖 Bot Crypto của bạn</b>\n\n"
    "Gõ các lệnh sau để xem ngay:\n"
    "/gia — giá nhóm coin đang theo dõi\n"
    "/tin — tin mới nhất (2 ngày)\n"
    "/thitruong — tổng quan thị trường\n"
    "/bantin — bản tin đầy đủ\n\n"
    "Bot cũng tự gửi bản tin lúc " + " & ".join(config.GIO_GUI_BAN_TIN) +
    " và cảnh báo khi giá biến động mạnh."
)


def xu_ly_lenh(text, chat_id):
    t = text.lower().strip()
    if t.startswith("/start") or t.startswith("/help"):
        gui_telegram(MENU, chat_id)
    elif t.startswith("/gia"):
        gui_telegram(soan_gia(), chat_id)
    elif t.startswith("/tin"):
        gui_telegram(soan_tin(), chat_id)
    elif t.startswith("/thitruong"):
        gui_telegram(soan_thitruong(), chat_id)
    elif t.startswith("/bantin"):
        gui_telegram(soan_ban_tin(), chat_id)
    else:
        gui_telegram("Mình chưa hiểu lệnh đó. Gõ /help để xem các lệnh.", chat_id)


def doc_lenh(offset):
    try:
        r = requests.get(f"{API}/getUpdates",
                         params={"offset": offset, "timeout": 10}, timeout=20).json()
        return r.get("result", [])
    except Exception as e:
        print("Lỗi đọc lệnh:", e)
        return []


# ============ Vòng lặp chính ============

def main():
    print("Bot đang chạy... (Ctrl+C để dừng)")
    gui_telegram("✅ Bot crypto đã khởi động. Gõ /help để xem các lệnh.")

    for gio in config.GIO_GUI_BAN_TIN:
        schedule.every().day.at(gio).do(ban_tin)
    schedule.every(config.PHUT_KIEM_TRA).minutes.do(kiem_tra_bien_dong)
    kiem_tra_bien_dong()

    offset = None
    while True:
        schedule.run_pending()
        updates = doc_lenh(offset)
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message") or u.get("edited_message")
            if not msg:
                continue
            text = msg.get("text", "")
            chat_id = msg["chat"]["id"]
            if text:
                xu_ly_lenh(text, chat_id)


if __name__ == "__main__":
    main()
