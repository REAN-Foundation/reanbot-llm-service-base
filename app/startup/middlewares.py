# import http
# import time
#
# from fastapi import Request
#
# from app.startup.logger import logger
#
#
# async def log_request_middleware(request: Request, call_next):
#     """
#     This middleware will log all requests and their processing time.
#     E.g. log:
#     0.0.0.0:1234 - GET /ping 200 OK 1.00ms
#     """
#     logger.debug("middleware: log_request_middleware")
#     url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
#     start_time = time.time()
#     response = await call_next(request)
#     process_time = (time.time() - start_time) * 1000
#     formatted_process_time = "{0:.2f}".format(process_time)
#     host = getattr(getattr(request, "client", None), "host", None)
#     port = getattr(getattr(request, "client", None), "port", None)
#     try:
#         status_phrase = http.HTTPStatus(response.status_code).phrase
#     except ValueError:
#         status_phrase = ""
#     logger.info(f'{host}:{port} - "{request.method} {url}" {response.status_code} {status_phrase} {formatted_process_time}ms')
#     return response

import logging
import string
import time
import random
from fastapi import Request

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

logger = logging.getLogger(__name__)


async def log_request_middleware(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
    return response
