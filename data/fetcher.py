"""
fetcher.py – Thu thập dữ liệu thị trường crypto
Chiến lược: CoinGecko Markets (sparkline=true) → 1 request duy nhất
            lấy được: giá, 24h, 7d, VÀ dữ liệu sparkline để tính RSI
Không dùng Binance (bị chặn 451 trên GitHub Actions)
"""

import time
import logging
import requests

logger = logging.getLogger(__name__)

FEAR_GREED_URL    = "https://api.alternative.me/fng/?limit=1"
DEFILLAMA_URL     = "https://api.llama.fi/v2/chains"
COINGECKO_GLOBAL  = "https://api.coingecko.com/api/v3/global"
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"

# ─────────────────────────────────────────────────────────────
#  Mapping symbol → CoinGecko ID
# ─────────────────────────────────────────────────────────────
SYMBOL_TO_CG = {
    "BTCUSDT":   "bitcoin",
    "ETHUSDT":   "ethereum",
    "BNBUSDT":   "binancecoin",
    "SOLUSDT":   "solana",
    "XRPUSDT":   "ripple",
    "DOGEUSDT":  "dogecoin",
    "ADAUSDT":   "cardano",
    "AVAXUSDT":  "avalanche-2",
    "TONUSDT":   "the-open-network",
    "SHIBUSDT":  "shiba-inu",
    "DOTUSDT":   "polkadot",
    "LINKUSDT":  "chainlink",
    "MATICUSDT": "matic-network",
    "UNIUSDT":   "uniswap",
    "LTCUSDT":   "litecoin",
    "NEARUSDT":  "near",
    "TRXUSDT":   "tron",
    "ICPUSDT":   "internet-computer",
    "ETCUSDT":   "ethereum-classic",
    "HBARUSDT":  "hedera-hashgraph",
    "APTUSDT":   "aptos",
    "SUIUSDT":   "sui",
    "OPUSDT":    "optimism",
    "ARBUSDT":   "arbitrum",
    "STXUSDT":   "blockstack",
    "ATOMUSDT":  "cosmos",
    "ALGOUSDT":  "algorand",
    "VETUSDT":   "vechain",
    "FILUSDT":   "filecoin",
    "FLOWUSDT":  "flow",
    "XMRUSDT":   "monero",
    "ZECUSDT":   "zcash",
    "AAVEUSDT":  "aave",
    "MKRUSDT":   "maker",
    "LDOUSDT":   "lido-dao",
    "INJUSDT":   "injective-protocol",
    "AXSUSDT":   "axie-infinity",
    "SANDUSDT":  "the-sandbox",
    "MANAUSDT":  "decentraland",
    "GALAUSDT":  "gala",
    "CHZUSDT":   "chiliz",
    "APEUSDT":   "apecoin",
    "ENSUSDT":   "ethereum-name-service",
    "GRTUSDT":   "the-graph",
    "PEPEUSDT":  "pepe",
    "WIFUSDT":   "dogwifcoin",
    "BONKUSDT":  "bonk",
    "FLOKIUSDT": "floki",
    "WLDUSDT":   "worldcoin-wld",
    "TIAUSDT":   "celestia",
    "JUPUSDT":   "jupiter-exchange-solana",
    "ENAUSDT":   "ethena",
    "SEIUSDT":   "sei-network",
    "IOTAUSDT":  "iota",
    "NOTUSDT":   "notcoin",
    "FETUSDT":   "fetch-ai",
    "RENDERUSDT":"render-token",
    "RUNEUSDT":  "thorchain",
    "COMPUSDT":  "compound-governance-token",
    "SNXUSDT":   "havven",
    "BATUSDT":   "basic-attention-token",
}

CG_ID_TO_SYM = {v: k for k, v in SYMBOL_TO_CG.items()}


# ─────────────────────────────────────────────────────────────
#  Helper: HTTP GET với retry
# ─────────────────────────────────────────────────────────────
def _get(url: str, params: dict = None, retries: int = 3, timeout: int = 30) -> requests.Response | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 429:
                wait = 35 * (attempt + 1)
                logger.warning(f"Rate limit 429 – chờ {wait}s (lần {attempt+1}/{retries})...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            logger.error(f"HTTP {code}: {url}")
            if code in (429, 503):
                time.sleep(30 * (attempt + 1))
            else:
                return None
        except Exception as e:
            logger.error(f"Request error ({attempt+1}/{retries}): {e}")
            time.sleep(5)
    return None


# ─────────────────────────────────────────────────────────────
#  RSI từ sparkline (168 giờ = 7 ngày)
# ─────────────────────────────────────────────────────────────
def _calc_rsi(prices: list, period: int = 14) -> float | None:
    if not prices or len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains  = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_g  = sum(gains[-period:]) / period
    avg_l  = sum(losses[-period:]) / period
    if avg_l == 0:
        return 100.0
    return round(100 - 100 / (1 + avg_g / avg_l), 1)


# ─────────────────────────────────────────────────────────────
#  CoinGecko Markets: giá + 24h + 7d + sparkline (RSI)
#  Chỉ CẦN 1-2 REQUEST cho toàn bộ danh sách coin
# ─────────────────────────────────────────────────────────────
def get_all_data(symbols: list) -> tuple[dict, dict]:
    """
    Trả về (prices, extended) cho tất cả symbols.
    Chỉ gọi CoinGecko 1-2 lần, không gọi riêng lẻ.
    """
    cg_ids  = [SYMBOL_TO_CG[s] for s in symbols if s in SYMBOL_TO_CG]
    prices  = {s: None for s in symbols}
    extended = {s: None for s in symbols}

    if not cg_ids:
        return prices, extended

    # CoinGecko cho phép ~250 IDs/request, chia batch nếu vượt
    batch_size = 200
    for i in range(0, len(cg_ids), batch_size):
        batch = cg_ids[i : i + batch_size]
        resp = _get(
            COINGECKO_MARKETS,
            params={
                "vs_currency":             "usd",
                "ids":                     ",".join(batch),
                "per_page":                250,
                "page":                    1,
                "price_change_percentage": "24h,7d",
                "sparkline":               "true",   # ← lấy 168h giá để tính RSI
            },
            retries=4,
            timeout=30,
        )

        if resp is None:
            logger.error("[CoinGecko] Không lấy được dữ liệu.")
            continue

        data = resp.json()
        if not isinstance(data, list):
            logger.error(f"[CoinGecko] Phản hồi lạ: {str(data)[:200]}")
            continue

        for coin in data:
            sym = CG_ID_TO_SYM.get(coin.get("id"))
            if not sym or sym not in prices:
                continue

            ch24 = coin.get("price_change_percentage_24h") or 0.0
            ch7  = coin.get("price_change_percentage_7d_in_currency") or 0.0
            vol  = coin.get("total_volume") or 0.0

            prices[sym] = {
                "price":       coin.get("current_price") or 0.0,
                "change_pct":  ch24,
                "change_usd":  coin.get("price_change_24h") or 0.0,
                "volume_usdt": vol,
                "high_24h":    coin.get("high_24h") or 0.0,
                "low_24h":     coin.get("low_24h") or 0.0,
                "change_7d":   ch7,
            }

            # Tính RSI từ sparkline (không cần thêm API call)
            spark = coin.get("sparkline_in_7d", {}) or {}
            spark_prices = spark.get("price", [])
            rsi = _calc_rsi(spark_prices) if spark_prices else None

            # Volume ratio: so sánh vol hôm nay với avg 7 ngày
            # (sparkline không có vol, dùng vol mCap ratio thay thế)
            extended[sym] = {
                "rsi":       rsi,
                "change_7d": ch7,
                "vol_ratio": 1.0,  # không có dữ liệu vol lịch sử từ endpoint này
            }

        # Nếu còn batch tiếp theo, nghỉ 8 giây
        if i + batch_size < len(cg_ids):
            logger.info("Chờ 8s trước batch tiếp theo...")
            time.sleep(8)

    ok_p = sum(1 for v in prices.values()   if v is not None)
    ok_e = sum(1 for v in extended.values() if v is not None)
    logger.info(f"[CoinGecko] Giá: {ok_p}/{len(symbols)} | RSI: {ok_e}/{len(symbols)}")
    return prices, extended


# ─────────────────────────────────────────────────────────────
#  Public wrapper (giữ interface cũ)
# ─────────────────────────────────────────────────────────────
def get_prices(symbols: list) -> dict:
    prices, _ = get_all_data(symbols)
    return prices


def get_extended_data(symbols: list) -> dict:
    _, extended = get_all_data(symbols)
    return extended


def get_funding_rates(symbols: list) -> dict:
    """Funding rate không khả dụng (Binance bị chặn 451). Trả về None."""
    return {s: None for s in symbols}


# ─────────────────────────────────────────────────────────────
#  Fear & Greed
# ─────────────────────────────────────────────────────────────
def get_fear_greed() -> dict | None:
    try:
        resp = _get(FEAR_GREED_URL, retries=3, timeout=15)
        if resp is None:
            return None
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
        resp = _get(DEFILLAMA_URL, retries=3, timeout=20)
        if resp is None:
            return None
        chains = sorted(resp.json(), key=lambda x: x.get("tvl", 0), reverse=True)
        return {
            "total_tvl": sum(c.get("tvl", 0) for c in chains),
            "top_chains": [
                {
                    "name":      c["name"],
                    "tvl":       c.get("tvl", 0),
                    "change_1d": c.get("change_1d", 0) or 0,
                }
                for c in chains[:3]
            ],
        }
    except Exception as e:
        logger.error(f"[DeFiLlama]: {e}")
        return None


# ─────────────────────────────────────────────────────────────
#  BTC Dominance
# ─────────────────────────────────────────────────────────────
def get_btc_dominance() -> float | None:
    try:
        resp = _get(COINGECKO_GLOBAL, retries=3, timeout=15)
        if resp is None:
            return None
        return round(resp.json()["data"]["market_cap_percentage"]["btc"], 1)
    except Exception as e:
        logger.error(f"[BTC Dominance]: {e}")
        return None


# ─────────────────────────────────────────────────────────────
#  FETCH ALL – gọi hàm duy nhất
# ─────────────────────────────────────────────────────────────
def fetch_all(coins: list) -> dict:
    from config import MAJOR_COINS
    logger.info("📡 Đang thu thập dữ liệu thị trường (CoinGecko)...")

    # 1 lần gọi duy nhất cho cả prices + RSI
    prices, extended = get_all_data(coins)

    return {
        "prices":        prices,
        "funding_rates": get_funding_rates(coins),
        "extended":      extended,
        "fear_greed":    get_fear_greed(),
        "defi_tvl":      get_defillama_tvl(),
        "btc_dominance": get_btc_dominance(),
    }
