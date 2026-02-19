# =========================

# TELEGRAM CONFIG

# =========================

BOT_TOKEN = "8219284415:AAHWuXHa712VCK4aJT03iXi0xqdXTUDLyCo"
CHAT_ID = "6265701232"

# =========================

import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

# =========================

# SETTINGS (SAFE MODE)

# =========================

RISK_PER_TRADE = 0.01
CAPITAL = 10000
TARGET_RR = 1.5

STOCKS = [
"RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TATASTEEL.NS","ITC.NS","INFY.NS","LT.NS"
]

open_positions = {}

# =========================

def send(msg):
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.get(url, params={"chat_id": CHAT_ID, "text": msg})

# =========================

def rsi(series, period=14):
delta = series.diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(period).mean()
avg_loss = loss.rolling(period).mean()
rs = avg_gain / avg_loss
return 100 - (100/(1+rs))

# =========================

def get_data(symbol):
df = yf.download(symbol, period="2d", interval="5m", progress=False)
if df is None or len(df) < 50:
return None

```
df["EMA9"] = df["Close"].ewm(span=9).mean()
df["EMA21"] = df["Close"].ewm(span=21).mean()
df["RSI"] = rsi(df["Close"])
df["VOL_AVG"] = df["Volume"].rolling(20).mean()
return df.dropna()
```

# =========================

def check_entry(symbol):
df = get_data(symbol)
if df is None:
return

```
last = df.iloc[-1]
prev = df.iloc[-2]

price = float(last["Close"])
vol_spike = last["Volume"] > last["VOL_AVG"]

buy = (
    last["EMA9"] > last["EMA21"] and
    prev["EMA9"] <= prev["EMA21"] and
    last["RSI"] > 55 and
    vol_spike
)

sell = (
    last["EMA9"] < last["EMA21"] and
    prev["EMA9"] >= prev["EMA21"] and
    last["RSI"] < 45 and
    vol_spike
)

if symbol in open_positions:
    return

if buy or sell:
    direction = "BUY" if buy else "SELL"

    sl = price * (0.997 if buy else 1.003)
    target = price + (price-sl)*TARGET_RR if buy else price - (sl-price)*TARGET_RR

    qty = int((CAPITAL*RISK_PER_TRADE)/abs(price-sl))
    if qty <= 0: return

    open_positions[symbol] = {
        "dir": direction,
        "entry": price,
        "sl": sl,
        "target": target,
        "qty": qty
    }

    send(f"{direction} {symbol}\nEntry: {price:.2f}\nSL: {sl:.2f}\nTarget: {target:.2f}\nQty: {qty}")
```

# =========================

def check_exit():
remove = []
for sym,pos in open_positions.items():
df = get_data(sym)
if df is None: continue

```
    price = float(df.iloc[-1]["Close"])

    if pos["dir"]=="BUY":
        if price<=pos["sl"] or price>=pos["target"]:
            pnl = (price-pos["entry"])*pos["qty"]
            send(f"EXIT {sym}\nPrice: {price:.2f}\nPnL: ₹{pnl:.2f}")
            remove.append(sym)
    else:
        if price>=pos["sl"] or price<=pos["target"]:
            pnl = (pos["entry"]-price)*pos["qty"]
            send(f"EXIT {sym}\nPrice: {price:.2f}\nPnL: ₹{pnl:.2f}")
            remove.append(sym)

for r in remove:
    open_positions.pop(r,None)
```

# =========================

def market_hours():
now = datetime.now().time()
return now >= datetime.strptime("09:20","%H:%M").time() and now <= datetime.strptime("15:20","%H:%M").time()

# =========================

send("🤖 Trading Bot Started (Cloud Running)")

while True:
try:
if market_hours():
for s in STOCKS:
check_entry(s)
check_exit()
else:
time.sleep(60)
continue

```
    time.sleep(60)

except Exception as e:
    send(f"Error: {e}")
    time.sleep(30)
```