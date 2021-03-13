import requests
import json
from config import *

HEADERS = {'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': SECRET_KEY}
BASE_URL = 'https://paper-api.alpaca.markets'
ACCOUNT_URL = '{}/v2/account'.format(BASE_URL)
ORDERS_URL = '{}/v2/orders'.format(BASE_URL)


def get_account():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)

    return json.loads(r.content)

def create_order(symbol, qty, side, type, time_in_force):
    data = {
        'symbol': symbol,
        'qty': qty,
        'side': side,
        'type': type,
        'time_in_force': time_in_force
        }

    r = requests.post(ORDERS_URL, json=data, headers=HEADERS)

    return json.loads(r.content)

def get_orders():
    r = requests.get(ORDERS_URL, headers=HEADERS)

    return json.loads(r.content)

def cancel_order(order_id):
    orders_url_id = '{}/'.format(ORDERS_URL) + order_id

    r = requests.delete(orders_url_id, headers=HEADERS)

    return r

#response = create_order('SE', 100, 'buy', 'market', 'gtc')
#response = create_order('AAPL', 100, 'buy', 'market', 'gtc')

orders = get_orders()
print(orders)

confirmation = cancel_order('id_for_your_order')
print('\n\nConfirmation:')
print(confirmation)