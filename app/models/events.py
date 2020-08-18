import datetime

import omitempty
from sqlalchemy import Column
from sqlalchemy import desc
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String

from app.models.base import session_scope
from app.models.base import Base
import constants
import settings


class SignalEvent(Base):
    __tablename__ = 'signal_event'

    time = Column(DateTime, primary_key=True, nullable=False)
    product_code = Column(String)
    side = Column(String)
    price = Column(Float)
    units = Column(Integer)

    def save(self):
        with session_scope() as session:
            session.add(self)

    @property
    def value(self):
        dict_values = omitempty({
            'time': self.time,
            'product_code': self.product_code,
            'side': self.side,
            'price': self.price,
            'units': self.units,
        })
        if not dict_values:
            return None
        return dict_values

    @classmethod
    def get_signal_events_by_count(cls, count, prduct_code=settings.product_code):
        with session_scope() as session:
            rows = session.query(cls).filter(cls.product_code == prduct_code).order_by(desc(cls.time)).limit(count).all()
            if rows is None:
                return []
            rows.reverse()
            return rows

    @classmethod
    def get_signal_events_after_time(cls, time):
        with session_scope() as session:
            rows = session.query(cls).filter(cls.time >= time).all()

            if rows is None:
                return []

            return rows


class SignalEvents(object):
    def __init__(self, signals=None):
        if signals is None:
            self.signals = []
        else:
            self.signals = signals

    def can_buy(self, time):
        if len(self.signals) == 0:
            return True

        last_signal = self.signals[-1]
        if last_signal.side == constants.SELL and last_signal.time < time:
            return True

        return False

    def can_sell(self, time):
        if len(self.signals) == 0:
            return False

        last_signal = self.signals[-1]
        if last_signal.side == constants.BUY and last_signal.time < time:
            return True

        return False

    def buy(self, product_code, time, price, units, save):
        if not self.can_buy(time):
            return False

        signal_event = SignalEvent(
            time=time, product_code=product_code, side=constants.BUY, price=price, units=units)
        if save:
            signal_event.save()

        self.signals.append(signal_event)
        return True

    def sell(self, product_code, time, price, units, save):
        if not self.can_sell(time):
            return False

        signal_event = SignalEvent(
            time=time, product_code=product_code, side=constants.SELL, price=price, units=units)
        if save:
            signal_event.save()

        self.signals.append(signal_event)
        return True

    @staticmethod
    def get_signal_events_by_count(count:int):
        signal_events = SignalEvent.get_signal_events_by_count(count)
        return SignalEvents(signal_events)

    @staticmethod
    def get_signal_events_after_time(time: datetime.datetime.time):
        signal_events = SignalEvent.get_signal_events_after_time(time)
        return SignalEvents(signal_events)

    @property
    def profit(self):
        total = 0.0
        before_sell = 0.0
        is_holding = False
        for i in range(len(self.signals)):
            signal_event = self.signals[i]
            if i == 0 and signal_event.side == constants.SELL:
                continue
            if signal_event.side == constants.BUY:
                total -= signal_event.price * signal_event.units
                is_holding = True
            if signal_event.side == constants.SELL:
                total += signal_event.price * signal_event.units
                is_holding = False
                before_sell = total
        if is_holding:
            return before_sell
        return total

    @property
    def value(self):
        signals = [s.value for s in self.signals]
        if not signals:
            signals = None

        profit = self.profit
        if not self.profit:
            profit = None

        return {
            'signals': signals,
            'profit': profit
        }

