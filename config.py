import os
import logging
from dotenv import load_dotenv
from alpaca_trade_api.rest import TimeFrame

load_dotenv()

API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
API_BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

# --- Strategie-Parameter (simpel & anpassbar) ---
SYMBOL = "BTC/USD"       # Alpaca Crypto-Symbol mit Slash
TIMEFRAME = TimeFrame.Hour  # 1h-Candles
EMA_FAST = 20
EMA_SLOW = 50

# Bot-Loop-Intervall (Sekunden)
LOOP_SECONDS = 15 * 60   # alle 15 Minuten

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
