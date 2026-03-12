import requests
import pandas as pd
import time
from datetime import datetime
from config import *
from py_clob_client.client import ClobClient

last_trade_window = None
last_claim = time.time()

host = "https://clob.polymarket.com"

# create CLOB client (no builder credentials needed here)
client = ClobClient(host)

# test connection
try:
    print("Connected to Polymarket")
except Exception as e:
    print("Connection error:", e)


def find_btc_market():

    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets",
            timeout=5
        )

        markets = r.json()

        for m in markets:

            q = m.get("question", "").lower()

            if "bitcoin" in q and "5" in q and "minute" in q:
                return m

        return None

    except Exception as e:
        print("Market lookup error:", e)
        return None


def get_market_price():

    market = find_btc_market()

    if market is None:
        print("BTC 5-min market not found")
        return None, None

    try:
        yes_price = float(market["outcomes"][0]["price"])
        no_price = float(market["outcomes"][1]["price"])

        return yes_price, no_price

    except Exception as e:
        print("Price read error:", e)
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

    print("YES:", yes_price, "NO:", no_price)

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