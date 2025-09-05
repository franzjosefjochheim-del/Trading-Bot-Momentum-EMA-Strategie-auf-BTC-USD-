# streamlit_app.py
import time
import pandas as pd
import streamlit as st
import alpaca_trade_api as tradeapi

import config
import strategy
import control  # <<— Start/Pause Buttons

st.set_page_config(page_title="BTC Momentum Bot", layout="wide")
st.title("BTC/USD Momentum Bot – Dashboard")

# Sidebar: Steuerung
with st.sidebar:
    st.markdown("### Steuerung")
    paused = control.is_paused()
    st.write(f"Status: **{'PAUSIERT' if paused else 'AKTIV'}**")

    colA, colB = st.columns(2)
    if colA.button("Aktualisieren"):
        st.rerun()

    if not paused:
        if colB.button("Pause"):
            control.set_paused(True); st.success("Bot pausiert."); st.rerun()
    else:
        if colB.button("Start"):
            control.set_paused(False); st.success("Bot gestartet."); st.rerun()

@st.cache_resource(show_spinner=False)
def get_api():
    return tradeapi.REST(
        key_id=config.API_KEY,
        secret_key=config.API_SECRET,
        base_url=config.API_BASE_URL
    )

api = get_api()

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
        return [o for o in orders if o.symbol == symbol], None
    except Exception as e:
        return [], str(e)

def load_bars(symbol: str, limit: int):
    df = api.get_crypto_bars([symbol], config.TIMEFRAME, limit=limit).df
    if isinstance(df.index, pd.MultiIndex):
        df = df.loc[(symbol,), :]
    for c in ("open", "high", "low", "close", "volume", "vwap"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["close"])

# Konto
acct, acct_err = load_account()
c1, c2, c3 = st.columns(3)
if acct_err:
    c1.error(f"Konto-Fehler: {acct_err}")
else:
    c1.metric("Equity", f"{float(acct.equity):,.2f} {acct.currency}")
    c2.metric("Cash", f"{float(acct.cash):,.2f} USD")
    c3.metric("Buying Power", f"{float(acct.buying_power):,.2f} USD")

# Position
pos, _ = load_position(config.SYMBOL)
st.subheader("Offene Position")
if pos:
    st.write(f"{pos.qty} {pos.symbol} @ {float(pos.avg_entry_price):.2f} USD")
else:
    st.write("Keine")

# Trades
st.subheader("Letzte Trades")
orders, oerr = load_orders(config.SYMBOL, limit=50)
if oerr:
    st.error(f"Orders-Fehler: {oerr}")
elif orders:
    data = [{
        "Zeit": str(o.filled_at) if o.filled_at else str(o.submitted_at),
        "Side": o.side.upper(),
        "Symbol": o.symbol,
        "Menge": o.qty,
        "Preis": o.filled_avg_price or o.limit_price
    } for o in orders]
    st.table(pd.DataFrame(data))
else:
    st.write("Keine abgeschlossenen Orders für BTC/USD.")

# Signal & Chart
st.subheader("Aktuelles Signal")
bars = load_bars(config.SYMBOL, limit=config.EMA_SLOW + 3)
if bars.empty:
    st.warning("Keine Marktdaten empfangen.")
else:
    sig = strategy.generate_signal(bars)
    st.write(sig)

    closes = bars["close"].astype(float)
    ema_fast = closes.ewm(span=config.EMA_FAST, adjust=False).mean()
    ema_slow = closes.ewm(span=config.EMA_SLOW, adjust=False).mean()
    plot_df = pd.DataFrame({
        "Close": closes,
        f"EMA{config.EMA_FAST}": ema_fast,
        f"EMA{config.EMA_SLOW}": ema_slow
    })
    st.line_chart(plot_df.tail(200))

st.caption(
    f"Symbol: {config.SYMBOL} • Timeframe: 1h • EMA: {config.EMA_FAST}/{config.EMA_SLOW} • "
    f"Letzte Aktualisierung: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
)
