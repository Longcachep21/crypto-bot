from datetime import datetime
import pytz
from config import COIN_LABELS, TIMEZONE, MAJOR_COINS


def _fmt_price(price: float) -> str:
    if price >= 1000: return f"${price:,.0f}"
    if price >= 1:    return f"${price:,.2f}"
    return f"${price:.5f}"

def _fmt_tvl(tvl: float) -> str:
    if tvl >= 1e9: return f"${tvl/1e9:,.2f}B"
    if tvl >= 1e6: return f"${tvl/1e6:,.1f}M"
    return f"${tvl:,.0f}"

def _pct_emoji(pct: float) -> str:
    if pct >=  5: return "🚀"
    if pct >=  1: return "📈"
    if pct <= -5: return "💥"
    if pct <= -1: return "📉"
    return "↔️"

def _rsi_emoji(rsi: float) -> str:
    if rsi >= 70: return "🔴"   # Overbought – cẩn thận
    if rsi >= 55: return "🟡"   # Trung tính cao
    if rsi >= 45: return "🟢"   # Trung tính
    if rsi >= 30: return "🔵"   # Trung tính thấp
    return "💎"                  # Oversold – cơ hội

def _fg_emoji(val: int) -> str:
    if val >= 75: return "🟠"
    if val >= 55: return "🟡"
    if val >= 45: return "⚪"
    if val >= 25: return "🔵"
    return "🟣"

def _signal_bar(score: int) -> str:
    clamped = max(-100, min(100, score))
    filled  = round((clamped + 100) / 200 * 10)
    return f"[{'🟩'*filled}{'⬜'*(10-filled)}] {score:+d}đ"


def build_report(data: dict, analysis: dict) -> str:
    tz  = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    timestamp = now.strftime("%H:%M – %d/%m/%Y (%A)")
    # Dịch thứ sang tiếng Việt
    days_vi = {"Monday":"Thứ Hai","Tuesday":"Thứ Ba","Wednesday":"Thứ Tư",
               "Thursday":"Thứ Năm","Friday":"Thứ Sáu","Saturday":"Thứ Bảy","Sunday":"Chủ Nhật"}
    for en, vi in days_vi.items():
        timestamp = timestamp.replace(en, vi)

    prices   = data.get("prices", {})       or {}
    funding  = data.get("funding_rates", {}) or {}
    extended = data.get("extended", {})      or {}
    fg       = data.get("fear_greed")        or {}
    defi     = data.get("defi_tvl")          or {}
    btc_dom  = data.get("btc_dominance")

    lines = []

    # ── HEADER ──────────────────────────────────────────────────────────
    lines.append("🤖 <b>BÁO CÁO CRYPTO HÀNG NGÀY</b>")
    lines.append(f"🕙 {timestamp}\n")

    # ── 1. 5 COIN LỚN với RSI + 7 ngày ─────────────────────────────────
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📊 <b>5 COIN LỚN NHẤT</b>")
    for sym in MAJOR_COINS:
        label = COIN_LABELS.get(sym, sym.replace("USDT", ""))
        p     = prices.get(sym)
        if not p:
            lines.append(f"  • {label}: ─")
            continue
        pct     = p["change_pct"]
        sign    = "+" if pct >= 0 else ""
        pemoji  = _pct_emoji(pct)
        fr      = funding.get(sym)
        fr_str  = f" | FR:<code>{fr:+.4f}%</code>" if fr is not None else ""

        ext = extended.get(sym)
        rsi_str = ""
        ch7_str = ""
        if ext:
            rsi = ext.get("rsi")
            ch7 = ext.get("change_7d")
            vr  = ext.get("vol_ratio", 1)
            rsi_str = f" | RSI:{rsi}{_rsi_emoji(rsi)}" if rsi else ""
            if ch7 is not None:
                s7 = "+" if ch7 >= 0 else ""
                ch7_str = f" | 7d:<b>{s7}{ch7:.1f}%</b>"
            if vr >= 1.5:
                ch7_str += f" ⚡{vr:.1f}x"

        lines.append(
            f"  <b>{label}</b>: {_fmt_price(p['price'])} "
            f"(<b>{sign}{pct:.2f}%</b>){pemoji}{ch7_str}{rsi_str}{fr_str}"
        )

    # ── 2. TOP 5 TĂNG & GIẢM ────────────────────────────────────────────
    valid = [(s, p) for s, p in prices.items() if p and s not in MAJOR_COINS]
    sorted_gain = sorted(valid, key=lambda x: x[1]["change_pct"], reverse=True)
    top_up   = sorted_gain[:5]
    top_down = sorted_gain[-5:][::-1]

    lines.append("")
    lines.append("🟢 <b>TOP 5 TĂNG MẠNH</b>")
    for sym, p in top_up:
        label = COIN_LABELS.get(sym, sym.replace("USDT",""))
        lines.append(f"  🚀 <b>{label}</b>: {_fmt_price(p['price'])} (+{p['change_pct']:.2f}%)")

    lines.append("")
    lines.append("🔴 <b>TOP 5 GIẢM MẠNH</b>")
    for sym, p in top_down:
        label = COIN_LABELS.get(sym, sym.replace("USDT",""))
        lines.append(f"  💥 <b>{label}</b>: {_fmt_price(p['price'])} ({p['change_pct']:.2f}%)")

    # ── 3. BREADTH + BTC DOMINANCE ──────────────────────────────────────
    total   = len(valid)
    up_n    = sum(1 for _, p in valid if p["change_pct"] > 0)
    down_n  = sum(1 for _, p in valid if p["change_pct"] < 0)
    up_pct  = round(up_n / total * 100) if total else 0
    bar_f   = round(up_pct / 10)
    bar     = "🟩"*bar_f + "⬜"*(10-bar_f)

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📈 <b>BREADTH</b>: 🟢{up_n} tăng | 🔴{down_n} giảm | {total} coin")
    lines.append(f"  [{bar}] {up_pct}% coin xanh")
    if btc_dom is not None:
        dom_note = "⚡ Alt season" if btc_dom <= 45 else ("⚠️ BTC thống trị" if btc_dom >= 60 else "")
        lines.append(f"👑 <b>BTC Dominance</b>: {btc_dom}% {dom_note}")

    # ── 4. TÂM LÝ ───────────────────────────────────────────────────────
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("😱 <b>TÂM LÝ THỊ TRƯỜNG</b>")
    if fg:
        val = fg["value"]
        vi_label = {
            "Extreme Fear": "Cực kỳ sợ hãi",
            "Fear":         "Sợ hãi",
            "Neutral":      "Trung tính",
            "Greed":        "Tham lam",
            "Extreme Greed":"Cực kỳ tham lam",
        }.get(fg["label"], fg["label"])
        lines.append(f"  Fear&Greed: <b>{val}/100</b> – {vi_label} {_fg_emoji(val)}")

    # ── 5. DEFI TVL ─────────────────────────────────────────────────────
    if defi:
        lines.append(f"🏦 <b>DeFi TVL</b>: {_fmt_tvl(defi['total_tvl'])}")
        for c in defi.get("top_chains", []):
            chg = c.get("change_1d", 0) or 0
            e   = "📈" if chg >= 0 else "📉"
            lines.append(f"    ↳ {c['name']}: {_fmt_tvl(c['tvl'])} ({chg:+.1f}%) {e}")

    # ── 6. NHẬN ĐỊNH & CẢNH BÁO ─────────────────────────────────────────
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🧠 <b>NHẬN ĐỊNH HÔM NAY</b>: {analysis['emoji']} <b>{analysis['signal']}</b>")
    lines.append(f"  Điểm: {_signal_bar(analysis['score'])}")
    for s in analysis.get("summary", []):
        lines.append(f"  — {s}")

    if analysis.get("warnings"):
        lines.append("")
        lines.append("🚨 <b>CẢNH BÁO ĐẦU TƯ</b>")
        for w in analysis["warnings"]:
            lines.append(f"  {w}")

    # ── FOOTER ──────────────────────────────────────────────────────────
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📌 <i>Binance • Fear&Greed • DeFiLlama • CoinGecko</i>")
    lines.append("⚠️ <i>Tham khảo, không phải lời khuyên đầu tư.</i>")

    return "\n".join(lines)
