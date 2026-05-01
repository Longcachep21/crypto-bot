import requests
import logging

logger = logging.getLogger(__name__)

BINANCE_SPOT     = "https://api.binance.com"
BINANCE_FUTURES  = "https://fapi.binance.com"
FEAR_GREED_URL   = "https://api.alternative.me/fng/?limit=1"
DEFILLAMA_URL    = "https://api.llama.fi/v2/chains"
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"

# Mapping: Binance symbol -> CoinGecko ID
SYMBOL_TO_CG = {
    "BTCUSDT":"bitcoin","ETHUSDT":"ethereum","BNBUSDT":"binancecoin",
    "SOLUSDT":"solana","XRPUSDT":"ripple","DOGEUSDT":"dogecoin",
    "ADAUSDT":"cardano","AVAXUSDT":"avalanche-2","TONUSDT":"the-open-network",
    "SHIBUSDT":"shiba-inu","DOTUSDT":"polkadot","LINKUSDT":"chainlink",
    "MATICUSDT":"matic-network","UNIUSDT":"uniswap","LTCUSDT":"litecoin",
    "NEARUSDT":"near","TRXUSDT":"tron","ICPUSDT":"internet-computer",
    "ETCUSDT":"ethereum-classic","HBARUSDT":"hedera-hashgraph",
    "APTUSDT":"aptos","SUIUSDT":"sui","OPUSDT":"optimism","ARBUSDT":"arbitrum",
    "STXUSDT":"blockstack","ATOMUSDT":"cosmos","ALGOUSDT":"algorand",
    "VETUSDT":"vechain","EGLDUSDT":"elrond-erd-2","FILUSDT":"filecoin",
    "FLOWUSDT":"flow","XMRUSDT":"monero","ZECUSDT":"zcash",
    "QNTUSDT":"quant-network","DASHUSDT":"dash","AAVEUSDT":"aave",
    "MKRUSDT":"maker","CRVUSDT":"curve-dao-token","LDOUSDT":"lido-dao",
    "RUNEUSDT":"thorchain","DYDXUSDT":"dydx-chain","GMXUSDT":"gmx",
    "SNXUSDT":"havven","COMPUSDT":"compound-governance-token",
    "INJUSDT":"injective-protocol","AXSUSDT":"axie-infinity",
    "SANDUSDT":"the-sandbox","MANAUSDT":"decentraland","GALAUSDT":"gala",
    "CHZUSDT":"chiliz","APEUSDT":"apecoin","ENSUSDT":"ethereum-name-service",
    "GRTUSDT":"the-graph","BATUSDT":"basic-attention-token","ZILUSDT":"zilliqa",
    "PEPEUSDT":"pepe","WIFUSDT":"dogwifcoin","BONKUSDT":"bonk",
    "FLOKIUSDT":"floki","NOTUSDT":"notcoin","WLDUSDT":"worldcoin-wld",
    "TIAUSDT":"celestia","PYTHUSDT":"pyth-network",
    "JUPUSDT":"jupiter-exchange-solana","ENAUSDT":"ethena",
    "STRKUSDT":"starknet","SEIUSDT":"sei-network","IOTAUSDT":"iota",
}


# ─────────────────────────────────────────────────────────────
#  CoinGecko: Giá + 24h + 7d (dùng cho GitHub Actions)
# ─────────────────────────────────────────────────────────────
def get_coingecko_prices(symbols: list) -> dict:
    """Lấy giá từ CoinGecko — hoạt động trên mọi server."""
    cg_ids = [SYMBOL_TO_CG[s] for s in symbols if s in SYMBOL_TO_CG]
    id_to_sym = {v: k for k, v in SYMBOL_TO_CG.items()}
    results = {s: None for s in symbols}
    if not cg_ids:
        return results
    try:
        resp = requests.get(
            COINGECKO_MARKETS,
            params={
                "vs_currency": "usd",
                "ids": ",".join(cg_ids),
                "per_page": 250,
                "page": 1,
                "price_change_percentage": "24h,7d",
                "sparkline": "false",
            },
            timeout=20,
        )
        resp.raise_for_status()
        for coin in resp.json():
            sym = id_to_sym.get(coin["id"])
            if sym and sym in results:
                ch24 = coin.get("price_change_percentage_24h") or 0
                results[sym] = {
                    "price":       coin["current_price"],
                    "change_pct":  ch24,
                    "change_usd":  coin.get("price_change_24h") or 0,
                    "volume_usdt": coin.get("total_volume") or 0,
                    "high_24h":    coin.get("high_24h") or 0,
                    "low_24h":     coin.get("low_24h") or 0,
                    "change_7d":   coin.get("price_change_percentage_7d_in_currency") or 0,
                }
    except Exception as e:
        logger.error(f"[CoinGecko prices]: {e}")
    return results


# ─────────────────────────────────────────────────────────────
#  Binance batch (nhanh, dùng khi chạy local)
# ─────────────────────────────────────────────────────────────
def get_binance_prices(symbols: list) -> dict:
    try:
        resp = requests.get(f"{BINANCE_SPOT}/api/v3/ticker/24hr", timeout=10)
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
                    "change_7d":   None,
                }
            else:
                results[sym] = None
        return results
    except Exception as e:
        logger.error(f"[Binance batch]: {e}")
        return {s: None for s in symbols}


def get_prices(symbols: list) -> dict:
    """Thử Binance trước, nếu bị chặn dùng CoinGecko."""
    results = get_binance_prices(symbols)
    valid = sum(1 for v in results.values() if v is not None)
    if valid < len(symbols) * 0.3:  # <30% thành công → dùng CoinGecko
        logger.warning(f"Binance trả về {valid}/{len(symbols)} coin, chuyển sang CoinGecko...")
        results = get_coingecko_prices(symbols)
    return results


# ─────────────────────────────────────────────────────────────
#  Funding Rate (Binance Futures)
# ─────────────────────────────────────────────────────────────
def get_funding_rates(symbols: list) -> dict:
    try:
        resp = requests.get(f"{BINANCE_FUTURES}/fapi/v1/premiumIndex", timeout=10)
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
        logger.error(f"[Funding Rate]: {e}")
        return {s: None for s in symbols}


# ─────────────────────────────────────────────────────────────
#  RSI từ Binance klines
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
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 1)


def get_extended_data(symbols: list) -> dict:
    """RSI + volume spike từ Binance klines."""
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
            vol_avg_7d = sum(quote_vols[-8:-1]) / 7
            results[sym] = {
                "rsi":       _calculate_rsi(closes),
                "change_7d": round((closes[-1] - closes[-8]) / closes[-8] * 100, 2),
                "vol_ratio": round(quote_vols[-1] / vol_avg_7d, 2) if vol_avg_7d else 1.0,
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
#  BTC Dominance
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
    prices = get_prices(coins)
    return {
        "prices":        prices,
        "funding_rates": get_funding_rates(coins),
        "extended":      get_extended_data(MAJOR_COINS),
        "fear_greed":    get_fear_greed(),
        "defi_tvl":      get_defillama_tvl(),
        "btc_dominance": get_btc_dominance(),
    }
