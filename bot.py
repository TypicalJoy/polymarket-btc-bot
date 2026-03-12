import requests
import pandas as pd
import time
import json
from datetime import datetime
from config import *
from py_clob_client.client import ClobClient

# Globals to cache token IDs per window
last_window = None
yes_token = None
no_token = None

host = "https://clob.polymarket.com"
client = ClobClient(host)

print("Connected to Polymarket CLOB")

def get_market_price():
    global last_window, yes_token, no_token

    # Determine current 5-min window (timestamp // 300)
    now = datetime.utcnow()
    current_window = int(now.timestamp() // 300)

    # If we entered a new window, fetch new tokens
    if current_window != last_window:
        slug = f"btc-updown-5m-{current_window}"
        print(f"Fetching tokens for event slug: {slug}")
        resp = requests.get(f"https://gamma-api.polymarket.com/events?slug={slug}", timeout=5)
        data = resp.json()
        if not data:
            print("No event data returned for slug:", slug)
            return None, None
        event = data[0]
        # Take the first market of the event
        market = event.get("markets", [None])[0]
        if market is None:
            print("No market found in event data.")
            return None, None

        # Extract clobTokenIds (Yes/No)
        token_ids = market["clobTokenIds"]
        if isinstance(token_ids, str):
            token_ids = json.loads(token_ids)
        yes_token, no_token = token_ids[0], token_ids[1]
        print("Yes token:", yes_token)
        print("No token:", no_token)
        last_window = current_window

    # Query the orderbook for each token
    yes_book = client.get_order_book(yes_token)
    no_book = client.get_order_book(no_token)

    # Helper to find a real bid (price with significant liquidity)
    def find_real_bid(book):
        for bid in book.bids:
            price = float(bid.price)
            size = float(bid.size)
            if price * size > 25:  # threshold to avoid tiny bids
                return price
        return None

    yes_price = find_real_bid(yes_book)
    no_price = find_real_bid(no_book)
    return yes_price, no_price

# Main loop
while True:
    now = datetime.utcnow()
    current_window = int(now.timestamp() // 300)
    seconds_into_window = now.timestamp() % 300
    seconds_remaining = 300 - seconds_into_window

    prices = get_market_price()
    if prices is None or prices[0] is None:
        time.sleep(1)
        continue
    yes_price, no_price = prices

    print("YES:", yes_price, "NO:", no_price)

    if last_window != current_window and seconds_remaining <= 120:
        if yes_price >= BUY_THRESHOLD:
            # place_yes_order()  (your trading logic here)
            print("Placing bet: YES for $", BET_SIZE)
            last_window = current_window
        elif no_price >= BUY_THRESHOLD:
            # place_no_order()
            print("Placing bet: NO for $", BET_SIZE)
            last_window = current_window

    # Optionally claim rewards here if needed
    if time.time() - last_claim > CLAIM_INTERVAL:
        print("Claiming rewards")
        last_claim = time.time()

    time.sleep(1)