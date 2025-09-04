import streamlit as st
import pandas as pd
import alpaca_trade_api as tradeapi
import config, strategy

st.set_page_config(page_title="BTC Momentum Bot", layout="wide")

api = tradeapi.REST(
    key_id=config.API_KEY,
    secret_key=config.API_SECRET,
    base_url=config.API_BASE_URL
)

st.title("BTC/USD Momentum Bot – Dashboard")

# Konto
account = api.get_account()
col1, col2, col3 = st.columns(3)
col1.metric("Equity", f"{float(account.equity):,.2f} {account.currency}")
col2.metric("Cash", f"{float(account.cash):,.2f} USD")
col3.metric("Buying Power", f"{float(account.buying_power):,.2f} USD")

# Position
try:
    pos = api.get_position(config.SYMBOL)
    st.subheader("Offene Position")
    st.write(f"{pos.qty} {pos.symbol} @ {float(pos.avg_entry_price):.2f} USD")
except Exception:
    st.subheader("Offene Position")
    st.write("Keine")

# Letzte Orders
orders = api.list_orders(status="closed", limit=5)
st.subheader("Letzte Trades")
if orders:
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
    st.write("Keine abgeschlossenen Orders.")

# Aktuelles Signal
df = api.get_crypto_bars([config.SYMBOL], config.TIMEFRAME, limit=config.EMA_SLOW + 3).df
signal = strategy.generate_signal(df)
st.subheader("Aktuelles Signal")
st.write(signal)

# Mini-Chart (Close + EMAs)
sym = config.SYMBOL
if isinstance(df.index, pd.MultiIndex):
    df = df.loc[(sym, ), :]

closes = df["close"].astype(float)
ema_fast = closes.ewm(span=config.EMA_FAST, adjust=False).mean()
ema_slow = closes.ewm(span=config.EMA_SLOW, adjust=False).mean()
plot_df = pd.DataFrame({"Close": closes, f"EMA{config.EMA_FAST}": ema_fast, f"EMA{config.EMA_SLOW}": ema_slow})
st.line_chart(plot_df.tail(200))
