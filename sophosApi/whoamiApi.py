from typing import NamedTuple

import requests

__all__ = [
    'WhoamiApi',
    'IAm'
]


class IAm(NamedTuple):
    id: str
    idType: str


class WhoamiApi(object):
    baseurl = "https://api.central.sophos.com/whoami/v1"

    def __init__(self, getter: requests.get) -> None:
        self._request = getter

    @property
    def whoami(self) -> IAm:
        result = self._request('get', self.baseurl)
        if result:
            json = result.json()
            return IAm(json['id'], json['idType'])
        raise Exception('''Aborting! Can't tell who I am!''')
