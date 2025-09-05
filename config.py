# config.py
import os
import logging
from dotenv import load_dotenv
from alpaca_trade_api.rest import TimeFrame

# .env Variablen laden
load_dotenv()

# --- API Keys ---
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
API_BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

# --- Strategie-Parameter ---
SYMBOL = "BTC/USD"          # Alpaca Crypto-Symbol (mit Slash)
TIMEFRAME = TimeFrame.Hour  # 1h-Candles
EMA_FAST = 20
EMA_SLOW = 50

# --- Bot-Loop-Intervall (Sekunden) ---
LOOP_SECONDS = 15 * 60      # alle 15 Minuten

# --- Risiko/Trade-Parameter ---
MAX_TRADE_USD = 2000.0      # max. USD pro Kauf
STOP_LOSS_PCT = 0.03        # 3% Stop-Loss
TAKE_PROFIT_PCT = 0.06      # 6% Take-Profit

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
