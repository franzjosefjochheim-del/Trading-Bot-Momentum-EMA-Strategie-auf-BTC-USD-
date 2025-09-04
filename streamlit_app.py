# streamlit_app.py
import time
import pandas as pd
import streamlit as st
import alpaca_trade_api as tradeapi

import config
import strategy

# ---------------------------
# Seiten-Setup
# ---------------------------
st.set_page_config(page_title="BTC Momentum Bot", layout="wide")
st.title("BTC/USD Momentum Bot – Dashboard")

# Auto-Refresh (optional)
with st.sidebar:
    st.markdown("### Ansicht")
    refresh_sec = st.slider("Auto-Refresh (Sek.)", 0, 120, 30, help="0 = kein Auto-Refresh")
    if refresh_sec > 0:
        st.autorefresh(interval=refresh_sec * 1000, key="autorefresh")

# ---------------------------
# Alpaca API-Client
# ---------------------------
@st.cache_resource(show_spinner=False)
def get_api():
    return tradeapi.REST(
        key_id=config.API_KEY,
        secret_key=config.API_SECRET,
        base_url=config.API_BASE_URL
    )

api = get_api()

# ---------------------------
# Hilfsfunktionen
# ---------------------------
def load_account():
    try:
        return api.get_account(), None
    except Exception as e:
        return None, str(e)

def load_position(symbol: str):
    try:
        return api.get_position(symbol), None
    except Exception:
        return None, None

def load_orders(symbol: str, limit: int = 50):
    try:
        orders = api.list_orders(status="closed", limit=limit)
        # Nur BTC/USD anzeigen
        return [o for o in orders if o.symbol == symbol], None
    except Exception as e:
        return [], str(e)

def load_bars(symbol: str, limit: int):
    # get_crypto_bars liefert MultiIndex-DF (symbol, timestamp)
    df = api.get_crypto_bars([symbol], config.TIMEFRAME, limit=limit).df
    if isinstance(df.index, pd.MultiIndex):
        df = df.loc[(symbol, ), :]
    # Sicherheit: numerische Spalten
    for c in ("open", "high", "low", "close", "volume", "vwap"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["close"])
    return df

# ---------------------------
# Konto-Metriken
# ---------------------------
acct, acct_err = load_account()
col1, col2, col3 = st.columns(3)
if acct_err:
    col1.error(f"Konto konnte nicht geladen werden: {acct_err}")
else:
    col1.metric("Equity", f"{float(acct.equity):,.2f} {acct.currency}")
    col2.metric("Cash", f"{float(acct.cash):,.2f} USD")
    col3.metric("Buying Power", f"{float(acct.buying_power):,.2f} USD")

# ---------------------------
# Offene Position
# ---------------------------
pos, _ = load_position(config.SYMBOL)
st.subheader("Offene Position")
if pos:
    st.write(f"{pos.qty} {pos.symbol} @ {float(pos.avg_entry_price):.2f} USD")
else:
    st.write("Keine")

# ---------------------------
# Letzte Trades (nur BTC/USD)
# ---------------------------
st.subheader("Letzte Trades")
orders, ord_err = load_orders(config.SYMBOL, limit=50)
if ord_err:
    st.error(f"Orders konnten nicht geladen werden: {ord_err}")
elif orders:
    data = []
    for o in orders:
        data.append({
            "Zeit": str(o.filled_at) if o.filled_at else str(o.submitted_at),
            "Side": o.side.upper(),
            "Symbol": o.symbol,
            "Menge": o.qty,
            "Preis": o.filled_avg_price or o.limit_price
        })
    st.table(pd.DataFrame(data))
else:
    st.write("Keine abgeschlossenen Orders für BTC/USD.")

# ---------------------------
# Aktuelles Signal + Chart
# ---------------------------
st.subheader("Aktuelles Signal")

# Bars für Signal + Chart laden
df = load_bars(config.SYMBOL, limit=config.EMA_SLOW + 3)
if df.empty:
    st.warning("Keine Marktdaten empfangen.")
else:
    # Signal berechnen
    # Für strategy.generate_signal erwartet: DataFrame mit 'close'
    # Wir reichen hier das MultiIndex-bereinigte df direkt weiter.
    # strategy.generate_signal greift intern auf config.SYMBOL zurück.
    # Falls deine strategy.generate_signal eine Bars-Liste erwartet:
    # passe ggf. dort an; aktuell verarbeitet sie DataFrames.
    sig = strategy.generate_signal(df)
    st.write(sig)

    # Mini-Chart: Close + EMA20/EMA50
    closes = df["close"].astype(float)
    ema_fast = closes.ewm(span=config.EMA_FAST, adjust=False).mean()
    ema_slow = closes.ewm(span=config.EMA_SLOW, adjust=False).mean()
    plot_df = pd.DataFrame({
        "Close": closes,
        f"EMA{config.EMA_FAST}": ema_fast,
        f"EMA{config.EMA_SLOW}": ema_slow
    })
    st.line_chart(plot_df.tail(200))

# ---------------------------
# Fußzeile
# ---------------------------
st.caption(
    f"Symbol: {config.SYMBOL} • Timeframe: 1h • EMA: {config.EMA_FAST}/{config.EMA_SLOW} • "
    f"Letzte Aktualisierung: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
)
