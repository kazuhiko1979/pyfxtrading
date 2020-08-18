from datetime import datetime
import logging
import math
import time

import dateutil.parser
from oandapyV20 import API
from oandapyV20.endpoints import accounts
from oandapyV20.endpoints import instruments
from oandapyV20.endpoints import orders
from oandapyV20.endpoints import trades
from oandapyV20.endpoints.pricing import PricingInfo
from oandapyV20.endpoints.pricing import PricingStream
from oandapyV20.exceptions import V20Error

import constants
import settings


ORDER_FILLED = 'FILLED'

logger = logging.getLogger(__name__)


class Balance(object):
    def __init__(self, currency, available):
        self.currency = currency
        self.available = available


class Ticker(object):
    def __init__(self, product_code, timestamp, bid, ask, volume):
        self.product_code = product_code
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask
        self.volume = volume

    @property
    def mid_price(self):
        return (self.bid + self.ask) / 2

    @property
    def time(self):
        return datetime.utcfromtimestamp(self.timestamp)

    def truncate_date_time(self, duration):
        ticker_time = self.time
        if duration == constants.DURATION_5S:
            new_sec = math.floor(self.time.second / 5) * 5
            ticker_time = datetime(
                self.time.year, self.time.month, self.time.day,
                self.time.hour, self.time.minute, new_sec)
            time_format = '%Y-%m-%d %H:%M:%S'
        elif duration == constants.DURATION_1M:
            time_format = '%Y-%m-%d %H:%M'
        elif duration == constants.DURATION_1H:
            time_format = '%Y-%m-%d %H'
        else:
            logger.warning('action=truncate_date_time error=no_datetime_format')
            return None

        str_date = datetime.strftime(ticker_time, time_format)
        return datetime.strptime(str_date, time_format)


class Order(object):
    def __init__(self, product_code, side, units, order_type='MARKET', order_state=None, filling_transaction_id=None):
        self.product_code = product_code
        self.side = side
        self.units = units
        self.order_type = order_type
        self.order_state = order_state
        self.filling_transaction_id = filling_transaction_id


class OrderTimeoutError(Exception):
    """Order timeout error"""


class Trade(object):
    def __init__(self, trade_id, side, price, units):
        self.trade_id = trade_id
        self.side = side
        self.price = price
        self.units = units


class APIClient(object):
    def __init__(self, access_token, account_id, environment='practice'):
        self.access_token = access_token
        self.account_id = account_id
        self.client = API(access_token=access_token, environment=environment)

    def get_balance(self) -> Balance:
        req = accounts.AccountSummary(accountID=self.account_id)
        try:
            resp = self.client.request(req)
        except V20Error as e:
            logger.error(f'action=get_balance error={e}')
            raise

        available = float(resp['account']['balance'])
        currency = resp['account']['currency']
        return Balance(currency, available)

    def get_ticker(self, product_code) -> Ticker:
        params = {
            'instruments': product_code
        }
        req = PricingInfo(accountID=self.account_id, params=params)
        try:
            resp = self.client.request(req)
        except V20Error as e:
            logger.error(f'action=get_ticker error={e}')
            raise

        timestamp = datetime.timestamp(
            dateutil.parser.parse(resp['time']))
        price = resp['prices'][0]
        instrument = price['instrument']
        bid = float(price['bids'][0]['price'])
        ask = float(price['asks'][0]['price'])
        volume = self.get_candle_volume()
        return Ticker(instrument, timestamp, bid, ask, volume)

    def get_candle_volume(self, count=1, granularity=constants.TRADE_MAP[settings.trade_duration]['granularity']):
        params = {
            'count': count,
            'granularity': granularity
        }
        req = instruments.InstrumentsCandles(instrument=settings.product_code, params=params)
        try:
            resp = self.client.request(req)
        except V20Error as e:
            logger.error(f'action=get_candle_volume error={e}')
            raise

        return int(resp['candles'][0]['volume'])

    def get_realtime_ticker(self, callback):
        req = PricingStream(accountID=self.account_id, params={
            'instruments': settings.product_code})
        try:
            for resp in self.client.request(req):
                if resp['type'] == 'PRICE':
                    timestamp = datetime.timestamp(
                        dateutil.parser.parse(resp['time']))
                    instrument = resp['instrument']
                    bid = float(resp['bids'][0]['price'])
                    ask = float(resp['asks'][0]['price'])
                    volume = self.get_candle_volume()
                    ticker = Ticker(instrument, timestamp, bid, ask, volume)
                    callback(ticker)

        except V20Error as e:
            logger.error(f'action=get_realtime_ticker error={e}')
            raise

    def send_order(self, order: Order) -> Trade:
        if order.side == constants.BUY:
            side = 1
        elif order.side == constants.SELL:
            side = -1
        order_data = {
            'order': {
                'type': order.order_type,
                'instrument': order.product_code,
                'units': order.units * side
            }
        }
        req = orders.OrderCreate(accountID=self.account_id, data=order_data)
        try:
            resp = self.client.request(req)
            logger.info(f'action=send_order resp={resp}')
        except V20Error as e:
            logger.error(f'action=send_order error={e}')
            raise
        order_id = resp['orderCreateTransaction']['id']
        order = self.wait_order_complete(order_id)

        if not order:
            logger.error('action=send_order error=timeout')
            raise OrderTimeoutError

        return self.trade_details(order.filling_transaction_id)

    def wait_order_complete(self, order_id) -> Order:
        count = 0
        timeout_count = 5
        while True:
            order = self.get_order(order_id)
            if order.order_state == ORDER_FILLED:
                return order
            time.sleep(1)
            count += 1
            if count > timeout_count:
                return None

    def get_order(self, order_id) -> Order:
        req = orders.OrderDetails(accountID=self.account_id, orderID=order_id)
        try:
            resp = self.client.request(req)
            logger.info(f'action=get_order resp={resp}')
        except V20Error as e:
            logger.error(f'action=get_order error={e}')
            raise

        order = Order(
            product_code=resp['order']['instrument'],
            side=constants.BUY if float(resp['order']['units']) > 0 else constants.SELL,
            units=float(resp['order']['units']),
            order_type=resp['order']['type'],
            order_state=resp['order']['state'],
            filling_transaction_id=resp['order'].get('fillingTransactionID')
        )
        return order

    def trade_details(self, trade_id) -> Trade:
        req = trades.TradeDetails(self.account_id, trade_id)
        try:
            resp = self.client.request(req)
            logger.info(f'action=trade_details resp={resp}')
        except V20Error as e:
            logger.error(f'action=trade_details error={e}')
            raise

        trade = Trade(
            trade_id=trade_id,
            side=constants.BUY if float(resp['trade']['currentUnits']) > 0 else constants.SELL,
            units=float(resp['trade']['currentUnits']),
            price=float(resp['trade']['price'])
        )
        return trade

    def get_open_trade(self) -> list:
        req = trades.OpenTrades(self.account_id)
        try:
            resp = self.client.request(req)
            logger.info(f'action=get_open_trade resp={resp}')
        except V20Error as e:
            logger.error(f'action=get_open_trade error={e}')
            raise

        trades_list = []
        for trade in resp['trades']:
            trades_list.insert(0, Trade(
                trade_id=trade['id'],
                side=constants.BUY if float(trade['currentUnits']) > 0 else constants.SELL,
                units=float(trade['currentUnits']),
                price=float(trade['price'])
            ))
        return trades_list

    def trade_close(self, trade_id) -> Trade:
        req = trades.TradeClose(self.account_id, trade_id)
        try:
            resp = self.client.request(req)
            logger.info(f'action=trade_close resp={resp}')
        except V20Error as e:
            logger.error(f'action=trade_close error={e}')
            raise

        trade = Trade(
            trade_id=trade_id,
            side=constants.BUY if float(resp['orderFillTransaction']['units']) > 0 else constants.SELL,
            units=float(resp['orderFillTransaction']['units']),
            price=float(resp['orderFillTransaction']['price'])
        )
        return trade
