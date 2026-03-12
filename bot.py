import requests
import pandas as pd
import time
import json
from datetime import datetime
from config import *
from py_clob_client.client import ClobClient

EVENT_SLUG = "btc-updown-5m-1773344400"

last_trade_window = None
last_claim = time.time()

host = "https://clob.polymarket.com"
client = ClobClient(host)

print("Connected to Polymarket")


def get_active_market():

    r = requests.get(
        f"https://gamma-api.polymarket.com/events/{EVENT_SLUG}",
        timeout=5
    )

    event = r.json()

    markets = event["markets"]

    for m in markets:

        if not m["closed"]:
            return m

    return None


def find_real_bid(book):

    for bid in book.bids:

        price = float(bid.price)
        size = float(bid.size)

        liquidity = price * size

        if liquidity > 25:
            return price

    return None


def get_market_price():

    market = get_active_market()

    if market is None:
        print("No active market")
        return None, None

    token_ids = market["clobTokenIds"]

    if isinstance(token_ids, str):
        token_ids = json.loads(token_ids)

    yes_token = token_ids[0]
    no_token = token_ids[1]

    yes_book = client.get_order_book(yes_token)
    no_book = client.get_order_book(no_token)

    yes_price = find_real_bid(yes_book)
    no_price = find_real_bid(no_book)

    if yes_price is None or no_price is None:
        return None, None

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