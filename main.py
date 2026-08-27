import os

import uvicorn
from uvicorn.config import LOGGING_CONFIG
from app.startup.middlewares import log_request_middleware
from app.config.config import get_settings
from app.startup.application import app
from app.config.constants import PORT
import logging

# setup loggers
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)

# Run the application server

if __name__ == "__main__":
    settings = get_settings()
    app.middleware("http")(log_request_middleware)
    if os.environ['ENVIRONMENT'] == "development":
        uvicorn.run(app, host="localhost", port=PORT)
    else:
        uvicorn.run(app, host="0.0.0.0", port=PORT)
