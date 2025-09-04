import pandas as pd
import config

def _close_series_from_df(df):
    # df: Multiindex (symbol, timestamp) von alpaca_trade_api.get_crypto_bars(...).df
    sym = config.SYMBOL
    if isinstance(df.index, pd.MultiIndex):
        df = df.loc[(sym, ), :]
    # Sicherstellen, dass 'close' existiert
    closes = df["close"].astype(float).dropna()
    return closes

def generate_signal(df_bars):
    """
    df_bars: Pandas-DataFrame aus api.get_crypto_bars([...]).df
    Rückgabe: "BUY" | "SELL" | "HOLD"
    """
    closes = _close_series_from_df(df_bars)
    if len(closes) < max(config.EMA_FAST, config.EMA_SLOW) + 2:
        return "HOLD"

    ema_fast = closes.ewm(span=config.EMA_FAST, adjust=False).mean()
    ema_slow = closes.ewm(span=config.EMA_SLOW, adjust=False).mean()

    last_fast, prev_fast = ema_fast.iloc[-1], ema_fast.iloc[-2]
    last_slow, prev_slow = ema_slow.iloc[-1], ema_slow.iloc[-2]

    if last_fast > last_slow and prev_fast <= prev_slow:
        return "BUY"
    elif last_fast < last_slow and prev_fast >= prev_slow:
        return "SELL"
    else:
        return "HOLD"
