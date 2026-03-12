import pandas as pd
import time
import json
from datetime import datetime
from config import *
from py_clob_client.client import ClobClient

last_trade_window = None
last_claim = time.time()

host = "https://clob.polymarket.com"
client = ClobClient(host)

print("Connected to Polymarket CLOB")


def find_btc_market():

    market_ids = client.get_markets()

    for market_id in market_ids:

        try:

            market = client.get_market(market_id)

            question = market["question"]

            print("MARKET:", question)

            q = question.lower()

            if "bitcoin" in q:
                print("SELECTED MARKET:", question)
                return market

        except:
            continue

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

    market = find_btc_market()

    if market is None:
        print("BTC market not found")
        return None, None

    try:

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

    except Exception as e:
        print("Orderbook read error:", e)
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