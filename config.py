import os
from dotenv import load_dotenv

load_dotenv()

# ===== TELEGRAM =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ===== API KEYS =====
COINGECKO_API_KEY     = os.getenv("COINGECKO_API_KEY", "")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
ETHERSCAN_API_KEY     = os.getenv("ETHERSCAN_API_KEY", "")
CRYPTOPANIC_API_KEY   = os.getenv("CRYPTOPANIC_API_KEY", "")

# ===== COIN THEO DÕI (70 coin) =====
COINS = [
    # 👑 Mega Cap
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    # 🔵 Large Cap
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "TONUSDT", "SHIBUSDT",
    "DOTUSDT", "LINKUSDT", "MATICUSDT", "UNIUSDT", "LTCUSDT",
    "NEARUSDT", "TRXUSDT", "ICPUSDT", "ETCUSDT", "HBARUSDT",
    # ⚡ Layer 1 & Layer 2
    "APTUSDT", "SUIUSDT", "OPUSDT", "ARBUSDT", "STXUSDT",
    "ATOMUSDT", "ALGOUSDT", "VETUSDT", "EGLDUSDT", "FILUSDT",
    "FLOWUSDT", "XMRUSDT", "ZECUSDT", "DASHUSDT", "QNTUSDT",
    # 🏦 DeFi
    "AAVEUSDT", "UNIUSDT", "MKRUSDT", "CRVUSDT", "LDOUSDT",
    "DYDXUSDT", "GMXUSDT", "RUNEUSDT", "SNXUSDT", "COMPUSDT",
    # 🎮 Gaming & NFT & Metaverse
    "AXSUSDT", "SANDUSDT", "MANAUSDT", "GALAUSDT", "CHZUSDT",
    "APEUSDT", "INJUSDT", "ENSUSDT", "GRTUSDT", "BATUSDT",
    # 🔥 Trending & Meme
    "PEPEUSDT", "WIFUSDT", "BONKUSDT", "FLOKIUSDT", "SHIBUSDT",
    "NOTUSDT", "WLDUSDT", "BLURUS DT", "TIAUSDT", "PYTHUSDT",
    # 🌐 Infrastructure & Oracle
    "JUPUSDT", "ENAUSDT", "STRKUSDT", "SEIUS DT", "ZILUSDT",
]

# Loại bỏ trùng lặp và giữ thứ tự
seen = set()
COINS = [
    c for c in [
        # 👑 Mega Cap
        "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
        # 🔵 Large Cap
        "DOGEUSDT","ADAUSDT","AVAXUSDT","TONUSDT","SHIBUSDT",
        "DOTUSDT","LINKUSDT","MATICUSDT","UNIUSDT","LTCUSDT",
        "NEARUSDT","TRXUSDT","ICPUSDT","ETCUSDT","HBARUSDT",
        # ⚡ Layer 1 & Layer 2
        "APTUSDT","SUIUSDT","OPUSDT","ARBUSDT","STXUSDT",
        "ATOMUSDT","ALGOUSDT","VETUSDT","EGLDUSDT","FILUSDT",
        "FLOWUSDT","XMRUSDT","ZECUSDT","QNTUSDT","DASHUSDT",
        # 🏦 DeFi
        "AAVEUSDT","MKRUSDT","CRVUSDT","LDOUSDT","RUNEUSDT",
        "DYDXUSDT","GMXUSDT","SNXUSDT","COMPUSDT","INJUSDT",
        # 🎮 Gaming & NFT
        "AXSUSDT","SANDUSDT","MANAUSDT","GALAUSDT","CHZUSDT",
        "APEUSDT","ENSUSDT","GRTUSDT","BATUSDT","ZILUSDT",
        # 🔥 Trending & Meme
        "PEPEUSDT","WIFUSDT","BONKUSDT","FLOKIUSDT","NOTUSDT",
        "WLDUSDT","TIAUSDT","PYTHUSDT","JUPUSDT","ENAUSDT",
        # 🌐 Khác
        "STRKUSDT","SEIUSDT","BLRUSDT","HFTUSDT","IOTAUSDT",
    ]
    if c not in seen and not seen.add(c)
]

COIN_LABELS = {c: c.replace("USDT", "") for c in COINS}

# Coin luôn hiển thị đầy đủ trong báo cáo
MAJOR_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# ===== LỊCH GỬI BÁO CÁO =====
TIMEZONE       = "Asia/Ho_Chi_Minh"
REPORT_HOUR    = 13   # 13:00 giờ Việt Nam
REPORT_MINUTE  = 0
