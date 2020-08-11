from datetime import datetime
import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
from app.controllers.webserver import start
import app.models

import settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if __name__ == "__main__":
    """
    streamThread = Thread(target=stream.stream_ingestion_data)
    streamThread.start()
    streamThread.join()
    """
    # from app.models.dfcandle import DataFrameCandle
    # df = DataFrameCandle(settings.product_code, settings.trade_duration)
    # df.set_all_candles(settings.past_period)
    # print(df.value)

    serverThread = Thread(target=start)
    serverThread.start()
    serverThread.join()













































