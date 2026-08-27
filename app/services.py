import logging

logger = logging.getLogger(__name__)


class EchoService:
    def echo(self, msg):
        logger.info("echoing something from the app logger")
        print(msg)
