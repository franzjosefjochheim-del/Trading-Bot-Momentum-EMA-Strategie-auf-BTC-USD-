import math
import config

def should_enter(position):
    # Einfach: nur kaufen, wenn keine Position offen ist
    return position is None

def should_exit(position):
    # Einfach: verkaufen, wenn Position existiert
    return position is not None

def calc_qty(api):
    """
    Kaufmenge simpel auf Basis von ~95% des verfügbaren Cash-Betrags.
    Crypto erlaubt Bruchteile, auf 6 Dezimalstellen runden.
    """
    account = api.get_account()
    cash = float(account.cash)
    if cash <= 0:
        return 0.0

    # Letzten Kurs holen (aus den letzten Bars)
    bars = api.get_crypto_bars([config.SYMBOL], config.TIMEFRAME, limit=1).df
    price = float(bars["close"].iloc[-1])

    usd_to_use = cash * 0.95
    qty = usd_to_use / price
    return round(qty, 6)
