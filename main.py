import time
import logging
import alpaca_trade_api as tradeapi
import config, strategy, risk

log = logging.getLogger("bot")

def get_api():
    return tradeapi.REST(
        key_id=config.API_KEY,
        secret_key=config.API_SECRET,
        base_url=config.API_BASE_URL
    )

def get_position(api):
    try:
        return api.get_position(config.SYMBOL)
    except Exception:
        return None

def run():
    api = get_api()
    log.info("Bot gestartet (BTC/USD, EMA %s/%s, 1h, Long-only).",
             config.EMA_FAST, config.EMA_SLOW)

    while True:
        try:
            # 1) Bars laden (genug Historie für EMAs)
            df = api.get_crypto_bars([config.SYMBOL], config.TIMEFRAME,
                                     limit=config.EMA_SLOW + 3).df

            # 2) Signal
            sig = strategy.generate_signal(df)
            pos = get_position(api)

            # 3) Ausführen (simpel)
            if sig == "BUY" and risk.should_enter(pos):
                qty = risk.calc_qty(api)
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
                    log.info("Kein Kauf: zu wenig Cash.")
            elif sig == "SELL" and risk.should_exit(pos):
                qty = pos.qty if pos else "0"
                if float(qty) > 0:
                    api.submit_order(
                        symbol=config.SYMBOL,
                        side="sell",
                        type="market",
                        qty=qty,
                        time_in_force="gtc"
                    )
                    log.info("SELL %s qty=%s", config.SYMBOL, qty)
                else:
                    log.info("Kein Verkauf: keine Position.")
            else:
                log.info("Signal: %s (keine Aktion).", sig)

        except Exception as e:
            log.error("Fehler im Loop: %s", e)

        time.sleep(config.LOOP_SECONDS)

if __name__ == "__main__":
    run()
