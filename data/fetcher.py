import requests
import logging

logger = logging.getLogger(__name__)

BINANCE_SPOT     = "https://api.binance.com"
BINANCE_FUTURES  = "https://fapi.binance.com"
FEAR_GREED_URL   = "https://api.alternative.me/fng/?limit=1"
DEFILLAMA_URL    = "https://api.llama.fi/v2/chains"
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"


# ─────────────────────────────────────────────────────────────
#  BATCH: Giá 24h tất cả coin (1 request thay vì 70)
# ─────────────────────────────────────────────────────────────
def get_binance_prices(symbols: list) -> dict:
    try:
        resp = requests.get(f"{BINANCE_SPOT}/api/v3/ticker/24hr", timeout=15)
        resp.raise_for_status()
        all_tickers = {t["symbol"]: t for t in resp.json()}
        results = {}
        for sym in symbols:
            d = all_tickers.get(sym)
            if d:
                results[sym] = {
                    "price":       float(d["lastPrice"]),
                    "change_pct":  float(d["priceChangePercent"]),
                    "change_usd":  float(d["priceChange"]),
                    "volume_usdt": float(d["quoteVolume"]),
                    "high_24h":    float(d["highPrice"]),
                    "low_24h":     float(d["lowPrice"]),
                }
            else:
                results[sym] = None
        return results
    except Exception as e:
        logger.error(f"[Batch giá]: {e}")
        return {s: None for s in symbols}


# ─────────────────────────────────────────────────────────────
#  BATCH: Funding Rate tất cả coin (1 request)
# ─────────────────────────────────────────────────────────────
def get_funding_rates(symbols: list) -> dict:
    try:
        resp = requests.get(f"{BINANCE_FUTURES}/fapi/v1/premiumIndex", timeout=15)
        resp.raise_for_status()
        all_rates = {item["symbol"]: item for item in resp.json()}
        results = {}
        for sym in symbols:
            item = all_rates.get(sym)
            if item and item.get("lastFundingRate"):
                results[sym] = round(float(item["lastFundingRate"]) * 100, 4)
            else:
                results[sym] = None
        return results
    except Exception as e:
        logger.error(f"[Batch FR]: {e}")
        return {s: None for s in symbols}


# ─────────────────────────────────────────────────────────────
#  RSI Calculation
# ─────────────────────────────────────────────────────────────
def _calculate_rsi(closes: list, period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


# ─────────────────────────────────────────────────────────────
#  Extended: RSI + 7d Change + Volume Spike (chỉ major coins)
# ─────────────────────────────────────────────────────────────
def get_extended_data(symbols: list) -> dict:
    results = {}
    for sym in symbols:
        try:
            url  = f"{BINANCE_SPOT}/api/v3/klines?symbol={sym}&interval=1d&limit=16"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            klines = resp.json()
            if len(klines) < 8:
                results[sym] = None
                continue
            closes     = [float(k[4]) for k in klines]
            quote_vols = [float(k[7]) for k in klines]
            rsi        = _calculate_rsi(closes)
            change_7d  = round((closes[-1] - closes[-8]) / closes[-8] * 100, 2)
            vol_today  = quote_vols[-1]
            vol_avg_7d = sum(quote_vols[-8:-1]) / 7
            vol_ratio  = round(vol_today / vol_avg_7d, 2) if vol_avg_7d > 0 else 1.0
            results[sym] = {
                "rsi":       rsi,
                "change_7d": change_7d,
                "vol_ratio": vol_ratio,
            }
        except Exception as e:
            logger.error(f"[Extended] {sym}: {e}")
            results[sym] = None
    return results


# ─────────────────────────────────────────────────────────────
#  Fear & Greed
# ─────────────────────────────────────────────────────────────
def get_fear_greed() -> dict | None:
    try:
        resp = requests.get(FEAR_GREED_URL, timeout=10)
        resp.raise_for_status()
        item = resp.json()["data"][0]
        return {"value": int(item["value"]), "label": item["value_classification"]}
    except Exception as e:
        logger.error(f"[Fear&Greed]: {e}")
        return None


# ─────────────────────────────────────────────────────────────
#  DeFiLlama TVL
# ─────────────────────────────────────────────────────────────
def get_defillama_tvl() -> dict | None:
    try:
        resp = requests.get(DEFILLAMA_URL, timeout=15)
        resp.raise_for_status()
        chains = sorted(resp.json(), key=lambda x: x.get("tvl", 0), reverse=True)
        return {
            "total_tvl": sum(c.get("tvl", 0) for c in chains),
            "top_chains": [
                {"name": c["name"], "tvl": c.get("tvl", 0), "change_1d": c.get("change_1d", 0) or 0}
                for c in chains[:3]
            ],
        }
    except Exception as e:
        logger.error(f"[DeFiLlama]: {e}")
        return None


# ─────────────────────────────────────────────────────────────
#  BTC Dominance (CoinGecko free)
# ─────────────────────────────────────────────────────────────
def get_btc_dominance() -> float | None:
    try:
        resp = requests.get(COINGECKO_GLOBAL, timeout=10)
        resp.raise_for_status()
        return round(resp.json()["data"]["market_cap_percentage"]["btc"], 1)
    except Exception as e:
        logger.error(f"[BTC Dominance]: {e}")
        return None


# ─────────────────────────────────────────────────────────────
#  FETCH ALL
# ─────────────────────────────────────────────────────────────
def fetch_all(coins: list) -> dict:
    from config import MAJOR_COINS
    logger.info("📡 Đang thu thập dữ liệu thị trường...")
    return {
        "prices":        get_binance_prices(coins),
        "funding_rates": get_funding_rates(coins),
        "extended":      get_extended_data(MAJOR_COINS),   # RSI + 7d + Volume
        "fear_greed":    get_fear_greed(),
        "defi_tvl":      get_defillama_tvl(),
        "btc_dominance": get_btc_dominance(),
    }
