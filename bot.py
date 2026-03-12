import requests
import pandas as pd
import time
import json
from datetime import datetime, timezone
from config import *
from py_clob_client.client import ClobClient

last_window = None
yes_token = None
no_token = None

host = "https://clob.polymarket.com"
client = ClobClient(host)

print("Connected to Polymarket CLOB")

while True:
    now = datetime.now(timezone.utc)  # use UTC explicitly
    # Calculate 5-minute window start epoch
    window_index = int(now.timestamp() // 300)
    window_start = window_index * 300
    if window_index != last_window:
        # New window: fetch tokens
        slug = f"btc-updown-5m-{window_start}"
        print(f"Fetching tokens for event slug: {slug}")
        resp = requests.get(f"https://gamma-api.polymarket.com/events?slug={slug}", timeout=5)
        data = resp.json()
        if not data:
            print("No event data returned for slug:", slug)
            time.sleep(1)
            continue
        event = data[0]
        market = event.get("markets", [None])[0]
        if market is None:
            print("No market found in event data.")
            time.sleep(1)
            continue
        token_ids = market["clobTokenIds"]
        if isinstance(token_ids, str):
            token_ids = json.loads(token_ids)
        yes_token, no_token = token_ids[0], token_ids[1]
        print("Yes token:", yes_token)
        print("No token:", no_token)
        last_window = window_index

    # Query the CLOB orderbook for each token
    try:
        yes_book = client.get_order_book(yes_token)
        no_book  = client.get_order_book(no_token)
    except Exception as e:
        print("Orderbook query error:", e)
        time.sleep(1)
        continue

    # Helper: find best bid above a liquidity threshold
    def find_real_bid(book):
        for bid in book.bids:
            price = float(bid.price)
            size  = float(bid.size)
            if price * size > 25:
                return price
        return None

    yes_price = find_real_bid(yes_book)
    no_price  = find_real_bid(no_book)

    if yes_price is None or no_price is None:
        time.sleep(1)
        continue

    print("YES:", yes_price, "NO:", no_price)

    # Trading logic: place one trade per window when price > threshold
    seconds_into = now.timestamp() % 300
    seconds_remain = 300 - seconds_into
    if last_window == window_index and seconds_remain <= 120:
        if yes_price >= BUY_THRESHOLD:
            print("Placing bet: YES for $", BET_SIZE)
            last_window = None  # prevent another trade this window
        elif no_price >= BUY_THRESHOLD:
            print("Placing bet: NO for $", BET_SIZE)
            last_window = None

    # Claim rewards periodically (if implemented)
    if time.time() - last_claim > CLAIM_INTERVAL:
        print("Claiming rewards")
        last_claim = time.time()

    time.sleep(1)
