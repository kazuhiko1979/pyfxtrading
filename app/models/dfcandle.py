from app.models.candle import factory_candle_class

import settings


class DataFrameCandle(object):

    def __init__(self, product_code=settings.product_code, duration=settings.trade_duration):
        self.product_code = product_code
        self.duration = duration
        self.candle_cls = factory_candle_class(self.product_code, self.duration)
        self.candles = []

    def set_all_candles(self, limit=1000):
        self.candles = self.candle_cls.get_all_candle(limit)
        return self.candles

    @property
    def value(self):
        return {
            'product_code': self.product_code,
            'duration': self.duration,
            'candles': [c.value for c in self.candles]
        }

