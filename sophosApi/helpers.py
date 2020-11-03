import logging
from functools import wraps
from pprint import pformat
from random import randint
from time import sleep
from typing import Dict, Optional

import requests


__all__ = [
    'dicter',
    'response_logger',
    'backoff_handler'
]


def dicter(d: Optional[Dict]) -> Dict:
    """Return the provided dict, or an empty dict."""
    if type(d) is dict:
        return d
    return {}


def response_logger(response: requests.Response) -> None:
    logging.error(f"""Unable to update agent: {pformat({
        "request": {
            "headers": response.request.headers,
            "method": response.request.method,
            "url": response.request.url,
            "body": getattr(response.request, "body", None)
        },
        "response": {
            "headers": response.headers,
            "url": response.url,
            "body": response.text,
            "status_code": response.status_code
        }})}""")


def backoff_handler(func: requests.request):
    """Where backoffs and retries happen
    Important that the requests are not cached!"""

    def exception_handler(*args, **kwargs):
        success = False
        while not success:
            try:
                result = func(*args, **kwargs)
                success = True
            except TimeoutError:
                logging.error('Request timed out.')
            except requests.exceptions.ConnectionError as e:
                logging.error(f'Connection exception happened. {e}')
            except Exception as e:
                logging.error(f"Unknown connection error {e}")
        return result

    @wraps(func)
    def return_function(*args, **kwargs) -> requests.Response:
        count = 1
        while True:
            return_result = exception_handler(*args, **kwargs)
            logging.debug(pformat({
                "request": {
                    "headers": return_result.request.headers,
                    "method": return_result.request.method,
                    "url": return_result.request.url,
                    "data": getattr(return_result.request, "data", None)
                },
                "response": {
                    "headers": return_result.headers,
                    "url": return_result.url,
                    "body": return_result.text

                }}, depth=3))
            if return_result.status_code == 429 or str(return_result.status_code).startswith('5'):
                count = count + 1
                backoff = randint(0, min(30000, (1000 * (2 ** count))))
                logging.warning(f"Backing off for {backoff}ms")
                if 10 > count > 5:
                    logging.warning(f"This is the {count} retry.")
                if count > 10:
                    logging.error(f"This is the {count} retry.")
                sleep(backoff / 1000)
            else:
                break
        return return_result

    return return_function
