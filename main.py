# main.py
import time
import logging
import traceback
import alpaca_trade_api as tradeapi
import pandas as pd

import config
import strategy
import risk
import control  # <<— Pause/Start

log = logging.getLogger("bot")

def get_api():
    return tradeapi.REST(
        key_id=config.API_KEY,
        secret_key=config.API_SECRET,
        base_url=config.API_BASE_URL
    )

def get_bars(api, symbol: str, limit: int):
    """Holt Crypto-Bars und normalisiert den MultiIndex von Alpaca."""
    df = api.get_crypto_bars([symbol], config.TIMEFRAME, limit=limit).df
    if isinstance(df.index, pd.MultiIndex):
        df = df.loc[(symbol, ), :]
    # Zahlen-Spalten
    for c in ("open", "high", "low", "close", "volume", "vwap"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["close"])

def run():
    api = get_api()
    log.info("Bot gestartet (%s, EMA %d/%d, %s, Long-only).",
             config.SYMBOL, config.EMA_FAST, config.EMA_SLOW, "1h" if str(config.TIMEFRAME) == "TimeFrame.Hour" else str(config.TIMEFRAME))

    while True:
        try:
            # --- Pause? ------------------------------------------------------
            if control.is_paused():
                log.info("PAUSED – kein Trading in diesem Zyklus.")
                time.sleep(config.LOOP_SECONDS)
                continue

            # --- Daten holen -------------------------------------------------
            df = get_bars(api, config.SYMBOL, limit=config.EMA_SLOW + 3)
            if df.empty:
                log.warning("Keine Marktdaten erhalten.")
                time.sleep(config.LOOP_SECONDS)
                continue

            # --- Signal erzeugen --------------------------------------------
            sig = strategy.generate_signal(df)
            log.info("Signal: %s", sig)

            # --- Position lesen ---------------------------------------------
            try:
                pos = api.get_position(config.SYMBOL)
            except Exception:
                pos = None

            # --- Handelslogik ------------------------------------------------
            if sig == "BUY" and risk.should_enter(pos):
                qty = risk.calc_qty(api)  # konservatives USD-Max & Cash
                if qty > 0:
                    api.submit_order(
                        symbol=config.SYMBOL,
                        side="buy",
                        type="market",
                        qty=str(qty),
                        time_in_force="gtc"
                    )
                    log.info("BUY %s qty=%s", config.SYMBOL, qty)
                else:
                    log.info("Kein Kauf: zu wenig Cash oder qty=0.")

            else:
                # Exit wenn SELL-Signal ODER SL/TP erreicht
                if pos:
                    last = get_bars(api, config.SYMBOL, limit=1)
                    last_price = float(last["close"].iloc[-1])
                    if sig == "SELL" or risk.hit_stop_or_takeprofit(pos, last_price):
                        api.submit_order(
                            symbol=config.SYMBOL,
                            side="sell",
                            type="market",
                            qty=pos.qty,
                            time_in_force="gtc"
                        )
                        reason = "SELL-Signal" if sig == "SELL" else "SL/TP erreicht"
                        log.info("SELL %s qty=%s (%s) @ ~%.2f", config.SYMBOL, pos.qty, reason, last_price)

        except Exception as e:
            log.error("Fehler im Zyklus: %s\n%s", e, traceback.format_exc())

        # --- Warten bis zum nächsten Lauf -----------------------------------
        time.sleep(config.LOOP_SECONDS)


if __name__ == "__main__":
    run()
