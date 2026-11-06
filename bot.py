#!/usr/bin/env python3
"""Bot de alertas de cripto: revisa señales en Binance y avisa por Telegram."""
import os, json, time, urllib.request, urllib.parse
from datetime import datetime

BASE = "https://api.binance.com"
SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,ADAUSDT,DOGEUSDT,AVAXUSDT").split(",") if s.strip()]
INTERVAL = os.getenv("INTERVAL", "15m")
LIMIT = int(os.getenv("LIMIT", "120"))
CHECK_MINUTES = int(os.getenv("INTERVAL_MINUTES", "5"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = os.getenv("STATE_FILE", "state.json")

def fetch_klines(symbol, interval=INTERVAL, limit=LIMIT):
    url = f"{BASE}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode())

def ema(values, period):
    if not values: return []
    k = 2/(period+1)
    out = [values[0]]
    for i in range(1, len(values)):
        out.append(values[i]*k + out[-1]*(1-k))
    return out

def rsi(closes, period=14):
    if len(closes) < period+1: return None
    gains = losses = 0.0
    for i in range(1, period+1):
        d = closes[i]-closes[i-1]
        if d > 0: gains += d
        else: losses -= d
    ag, al = gains/period, losses/period
    for i in range(period+1, len(closes)):
        d = closes[i]-closes[i-1]
        g = d if d > 0 else 0
        l = -d if d < 0 else 0
        ag = (ag*(period-1)+g)/period
        al = (al*(period-1)+l)/period
    if al == 0: return 100.0
    rs = ag/al
    return 100 - 100/(1+rs)

def compute_signal(closes):
    r = rsi(closes)
    e9 = ema(closes, 9); e21 = ema(closes, 21); e50 = ema(closes, 50)
    last9, last21, last50 = e9[-1], e21[-1], e50[-1]
    macd_line = [a-b for a,b in zip(ema(closes,12), ema(closes,26))]
    signal_line = ema(macd_line, 9)
    macd_val = macd_line[-1]; sig_val = signal_line[-1]
    buy = sell = 0
    reasons = []
    if r is not None:
        if r < 30: buy += 1; reasons.append(f"RSI sobreventa ({r:.1f})")
        elif r > 70: sell += 1; reasons.append(f"RSI sobrecompra ({r:.1f})")
        else: reasons.append(f"RSI neutral ({r:.1f})")
    if last9 > last21 and last21 > last50:
        buy += 1; reasons.append("EMAs alcistas (9>21>50)")
    elif last9 < last21 and last21 < last50:
        sell += 1; reasons.append("EMAs bajistas (9<21<50)")
    else:
        reasons.append("EMAs sin tendencia clara")
    if macd_val > sig_val:
        buy += 1; reasons.append("MACD por encima de señal")
    elif macd_val < sig_val:
        sell += 1; reasons.append("MACD por debajo de señal")
    else:
        reasons.append("MACD neutral")
    if buy >= 2 and buy > sell: sig = "COMPRA"
    elif sell >= 2 and sell > buy: sig = "VENTA"
    else: sig = "MANTENER"
    return sig, reasons, r, last9, last21, last50, macd_val, sig_val

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("Sin credenciales de Telegram; solo log:")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
    except Exception as e:
        print("Error enviando Telegram:", e)

def load_state():
    try:
        with open(STATE_FILE) as f: return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)

def check_once():
    state = load_state()
    new_state = dict(state)
    alerts = []
    first_run = (len(state) == 0)
    for sym in SYMBOLS:
        try:
            klines = fetch_klines(sym)
            closes = [float(k[4]) for k in klines]
            sig, reasons, r, e9, e21, e50, macd, macds = compute_signal(closes)
            price = closes[-1]
            prev = state.get(sym, {}).get("signal")
            new_state[sym] = {"signal": sig, "price": price, "updated": datetime.utcnow().isoformat()+"Z"}
            print(f"{sym}: {sig} @ {price:.4f} (prev {prev})")
            if (not first_run) and sig in ("COMPRA", "VENTA") and sig != prev:
                emoji = "🟢" if sig == "COMPRA" else "🔴"
                msg = (f"{emoji} <b>{sig}</b> — {sym}\n"
                       f"Precio: {price:.4f} USDT\n"
                       f"RSI: {r:.1f} | MACD: {macd:.4f}\n"
                       f"Razones:\n- " + "\n- ".join(reasons))
                alerts.append(msg)
        except Exception as e:
            print(f"Error en {sym}: {e}")
    for a in alerts:
        send_telegram(a)
    if alerts:
        send_telegram(f"📊 {len(alerts)} nueva(s) señal(es) detectada(s).")
    if first_run:
        send_telegram(f"✅ Bot iniciado. Monitoreando {len(SYMBOLS)} monedas. Recibirás alertas cuando cambie la señal.")
    save_state(new_state)

def main():
    print("Bot de alertas iniciado. Monedas:", SYMBOLS)
    while True:
        print("\n=== Check", datetime.utcnow().isoformat(), "===")
        check_once()
        time.sleep(CHECK_MINUTES*60)

if __name__ == "__main__":
    main()