import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
from app.controllers.webserver import start
import app.models

import settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":

    from app.controllers.ai import AI
    ai = AI(
        product_code=settings.product_code,
        use_percent=settings.use_percent,
        duration=settings.trade_duration,
        past_period=settings.past_period,
        stop_limit_percent=settings.stop_limit_percent,
        back_test=settings.back_test
    )

    ai.update_optimize_params(True)
    # # streamThread = Thread(target=stream.stream_ingestion_data)
    # serverThread = Thread(target=start)
    #
    # # streamThread.start()
    # serverThread.start()
    #
    # # streamThread.join()
    # serverThread.join()