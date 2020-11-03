import logging
from datetime import datetime, timedelta
from functools import wraps

import requests


class Auth(object):
    oauth_expires = datetime.fromtimestamp(0)
    oauth_token = None

    def __init__(self, c_id, c_token):
        self.c_id = c_id
        self.c_token = c_token

    def oauth_handler(self, func: requests.request) -> requests.request:
        """This should be where oauth is managed"""

        @wraps(func)
        def return_function(*args, **kwargs) -> requests.Response:
            headers = kwargs.get('headers', dict())
            headers.update(Authorization=f"Bearer {self.oauth_token}")
            kwargs['headers'] = headers
            return func(*args, **kwargs)

        if datetime.now() >= self.oauth_expires:
            logging.debug('Requesting new oauth token')
            result = requests.post('https://id.sophos.com/api/v2/oauth2/token',
                                   headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                   data=f"grant_type=client_credentials&client_id={self.c_id}"
                                        f"&client_secret={self.c_token}&scope=token").json()
            self.oauth_expires = (timedelta(seconds=int(result['expires_in'])) + datetime.now())
            self.oauth_token = result['access_token']
        return return_function
