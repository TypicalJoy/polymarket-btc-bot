import requests
import pandas as pd
import time
from datetime import datetime
from config import *

MARKET_ID = "bitcoin-up-or-down-sep-30-5min"

last_trade_window = None
last_claim = time.time()

def get_market_price():

    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets?limit=10&search=bitcoin",
            timeout=5
        )

        markets = r.json()

        market = None
        for m in markets:
            if "5" in m["question"] and "minute" in m["question"].lower():
                market = m
                break

        if market is None:
            print("BTC 5-min market not found")
            return None, None

        yes_price = float(market["outcomes"][0]["price"])
        no_price = float(market["outcomes"][1]["price"])

        return yes_price, no_price

    except Exception as e:
        print("API error:", e)
        return None, None

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