import requests
import pandas as pd
import time
from datetime import datetime
from config import *

MARKET_ID = "BTC_5_MIN_MARKET_ID"

last_trade_window = None
last_claim = time.time()

def get_market_price():
    r = requests.get(f"https://clob.polymarket.com/markets/{MARKET_ID}")
    data = r.json()

    if "outcomes" not in data:
        print("Market data not ready:", data)
        return None, None

    yes_price = data["outcomes"][0]["price"]
    no_price = data["outcomes"][1]["price"]

    return yes_price, no_price

def place_bet(side):
    print("Placing bet:", side, "for $", BET_SIZE)

def claim_rewards():
    print("Claiming rewards")

def log_trade(side, price):
    df = pd.DataFrame([{
        "time": datetime.now(),
        "side": side,
        "price": price
    }])

    df.to_csv("metrics.csv", mode="a", header=False, index=False)

while True:

    now = datetime.utcnow()
    current_window = int(now.timestamp() // 300)

    seconds_into_window = now.timestamp() % 300
    seconds_remaining = 300 - seconds_into_window

    yes_price, no_price = get_market_price()

    if yes_price is None:
        time.sleep(1)
        continue

    if last_trade_window != current_window and seconds_remaining <= 120:

        if yes_price >= BUY_THRESHOLD:
            place_bet("YES")
            log_trade("YES", yes_price)
            last_trade_window = current_window

        elif no_price >= BUY_THRESHOLD:
            place_bet("NO")
            log_trade("NO", no_price)
            last_trade_window = current_window

    if time.time() - last_claim > CLAIM_INTERVAL:
        claim_rewards()
        last_claim = time.time()

    time.sleep(1)