from functools import partial
import logging

from app.models.candle import create_candle_with_duration
from oanda.oanda import Ticker

import constants
import settings

logger = logging.getLogger(__name__)

# TODO
from oanda.oanda import APIClient
api = APIClient(settings.access_token, settings.account_id)


class StreamData(object):

    def stream_ingestion_data(self):
        api.get_realtime_ticker(callback=self.trade)

    def trade(self, ticker: Ticker):
        logger.info(f'action=trade ticker={ticker.__dict__}')
        for duration in constants.DURATIONS:
            is_created = create_candle_with_duration(ticker.product_code, duration, ticker)
            print(is_created)


# singleton
stream = StreamData()
