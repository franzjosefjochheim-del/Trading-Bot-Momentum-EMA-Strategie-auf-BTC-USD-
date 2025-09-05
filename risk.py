# risk.py
import config

def should_enter(position):
    """Nur kaufen, wenn keine offene Position."""
    return position is None

def should_exit(position):
    """Verkaufen nur, wenn Position existiert."""
    return position is not None

def calc_qty(api):
    """
    Kaufe bis zu MAX_TRADE_USD (aber nicht mehr als verfügbares Cash).
    """
    account = api.get_account()
    cash = float(account.cash)
    if cash <= 1:
        return 0.0

    bars = api.get_crypto_bars([config.SYMBOL], config.TIMEFRAME, limit=1).df
    sym = config.SYMBOL
    if hasattr(bars.index, "levels"):
        bars = bars.loc[(sym,), :]
    price = float(bars["close"].iloc[-1])

    usd_to_use = min(cash * 0.95, config.MAX_TRADE_USD)
    qty = usd_to_use / price
    return round(qty, 6)

def hit_stop_or_takeprofit(position, last_price: float) -> bool:
    """
    Prüft SL/TP relativ zum Entry-Preis (Long-only).
    """
    if not position:
        return False
    entry = float(position.avg_entry_price or 0)
    if entry <= 0:
        return False

    # Stop-Loss
    if last_price <= entry * (1 - config.STOP_LOSS_PCT):
        return True

    # Take-Profit
    if last_price >= entry * (1 + config.TAKE_PROFIT_PCT):
        return True

    return False
