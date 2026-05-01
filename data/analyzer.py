def analyze_market(data: dict) -> dict:
    analysis = {"signal": "TRUNG TÍNH", "score": 0, "summary": [], "warnings": [], "emoji": "⚪"}
    score = 0
    summary  = []
    warnings = []

    prices   = data.get("prices", {})   or {}
    funding  = data.get("funding_rates", {}) or {}
    extended = data.get("extended", {}) or {}
    fg       = data.get("fear_greed")   or {}
    defi     = data.get("defi_tvl")     or {}
    btc_dom  = data.get("btc_dominance")

    # ── 1. BTC (trọng số cao nhất) ───────────────────────────────
    btc = prices.get("BTCUSDT")
    if btc:
        pct = btc["change_pct"]
        if   pct >=  7: score += 35; summary.append(f"🚀 BTC tăng rất mạnh +{pct:.1f}% trong 24h")
        elif pct >=  3: score += 20; summary.append(f"📈 BTC tăng tích cực +{pct:.1f}% trong 24h")
        elif pct >=  1: score +=  8; summary.append(f"📈 BTC tăng nhẹ +{pct:.1f}% trong 24h")
        elif pct <= -7: score -= 35; summary.append(f"🔴 BTC giảm rất mạnh {pct:.1f}%"); warnings.append("⚠️ BTC giảm >7% – rủi ro lan sang altcoin cao")
        elif pct <= -3: score -= 20; summary.append(f"📉 BTC giảm {pct:.1f}% trong 24h")
        elif pct <= -1: score -=  8; summary.append(f"📉 BTC giảm nhẹ {pct:.1f}% trong 24h")
        else:                        summary.append(f"↔️ BTC đi ngang ({pct:+.1f}%) trong 24h")

    # ── 2. RSI BTC ───────────────────────────────────────────────
    btc_ext = extended.get("BTCUSDT")
    if btc_ext:
        rsi = btc_ext.get("rsi")
        ch7 = btc_ext.get("change_7d")
        vr  = btc_ext.get("vol_ratio", 1)

        if rsi is not None:
            if rsi >= 75:
                score -= 10
                warnings.append(f"⚠️ RSI BTC = {rsi} – vùng overbought, thận trọng khi mua")
            elif rsi <= 30:
                score += 10
                summary.append(f"💡 RSI BTC = {rsi} – vùng oversold, có thể là cơ hội")
            else:
                summary.append(f"📊 RSI BTC = {rsi} – trung tính")

        if ch7 is not None:
            sign = "+" if ch7 >= 0 else ""
            summary.append(f"📅 BTC 7 ngày: {sign}{ch7:.1f}%")

        if vr >= 2.0:
            score += 8
            summary.append(f"🔥 Volume BTC đột biến gấp {vr:.1f}x bình thường – tín hiệu mạnh")
        elif vr >= 1.5:
            score += 4
            summary.append(f"📢 Volume BTC cao gấp {vr:.1f}x – chú ý xu hướng")

    # ── 3. ETH ───────────────────────────────────────────────────
    eth = prices.get("ETHUSDT")
    if eth:
        pct = eth["change_pct"]
        if   pct >=  3: score += 10; summary.append(f"📈 ETH tăng {pct:+.1f}%")
        elif pct <= -3: score -= 10; summary.append(f"📉 ETH giảm {pct:.1f}%")

    eth_ext = extended.get("ETHUSDT")
    if eth_ext and eth_ext.get("rsi"):
        rsi = eth_ext["rsi"]
        if rsi >= 75:
            warnings.append(f"⚠️ RSI ETH = {rsi} – overbought")
        elif rsi <= 30:
            summary.append(f"💡 RSI ETH = {rsi} – oversold, xem xét tích lũy")

    # ── 4. Fear & Greed ──────────────────────────────────────────
    if fg:
        val = fg["value"]
        if   val >= 80: score += 10; warnings.append(f"⚠️ Fear&Greed cực kỳ tham lam ({val}/100) – nguy cơ điều chỉnh")
        elif val >= 60: score += 12; summary.append(f"😏 Tâm lý tham lam ({val}/100) – xu hướng tích cực")
        elif val >= 45:              summary.append(f"😐 Tâm lý trung tính ({val}/100)")
        elif val >= 25: score -= 10; summary.append(f"😨 Thị trường đang sợ hãi ({val}/100)")
        else:           score -=  5; summary.append(f"😱 Cực kỳ sợ hãi ({val}/100) – có thể là cơ hội tích lũy")

    # ── 5. Funding Rate BTC ──────────────────────────────────────
    btc_fr = funding.get("BTCUSDT")
    if btc_fr is not None:
        if   btc_fr >  0.15: score += 5; warnings.append(f"⚠️ Funding Rate BTC rất cao ({btc_fr:+.4f}%) – Long đang nóng")
        elif btc_fr >  0.05: score += 5; summary.append(f"📊 Funding Rate BTC dương ({btc_fr:+.4f}%) – Long chiếm ưu thế")
        elif btc_fr < -0.05: score -= 5; summary.append(f"📊 Funding Rate BTC âm ({btc_fr:+.4f}%) – Short chiếm ưu thế")
        else:                            summary.append(f"📊 Funding Rate BTC cân bằng ({btc_fr:+.4f}%)")

    # ── 6. BTC Dominance ─────────────────────────────────────────
    if btc_dom is not None:
        if btc_dom >= 60:
            score -= 8
            warnings.append(f"👑 BTC Dominance = {btc_dom}% – tiền đang tập trung vào BTC, altcoin bất lợi")
        elif btc_dom <= 45:
            score += 8
            summary.append(f"🌈 BTC Dominance thấp ({btc_dom}%) – altcoin season có thể đang đến")
        else:
            summary.append(f"👑 BTC Dominance = {btc_dom}% – cân bằng")

    # ── 7. Altcoin Breadth ───────────────────────────────────────
    alt_prices = {s: p for s, p in prices.items() if s != "BTCUSDT" and p}
    total_alt  = len(alt_prices)
    if total_alt > 0:
        up_count   = sum(1 for p in alt_prices.values() if p["change_pct"] >  1)
        down_count = sum(1 for p in alt_prices.values() if p["change_pct"] < -1)
        up_pct = up_count / total_alt * 100
        if   up_pct >= 65: score += 10; summary.append(f"🟢 Altcoin mạnh – {up_count}/{total_alt} coin tăng >1%")
        elif up_pct <= 25: score -= 10; summary.append(f"🔴 Altcoin yếu – {down_count}/{total_alt} coin giảm >1%")

    # ── 8. DeFi TVL ──────────────────────────────────────────────
    if defi:
        tvl_b = defi["total_tvl"] / 1e9
        summary.append(f"🏦 Tổng TVL DeFi: ${tvl_b:,.1f}B")

    # ── Tín hiệu tổng thể ────────────────────────────────────────
    if   score >= 40: analysis["signal"] = "BULLISH MẠNH";  analysis["emoji"] = "🟢"
    elif score >= 15: analysis["signal"] = "BULLISH";       analysis["emoji"] = "🟩"
    elif score <= -40:analysis["signal"] = "BEARISH MẠNH";  analysis["emoji"] = "🔴"
    elif score <= -15:analysis["signal"] = "BEARISH";       analysis["emoji"] = "🟥"
    else:             analysis["signal"] = "TRUNG TÍNH";    analysis["emoji"] = "⚪"

    analysis["score"]    = score
    analysis["summary"]  = summary
    analysis["warnings"] = warnings
    return analysis
