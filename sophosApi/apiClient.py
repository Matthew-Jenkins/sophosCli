"""
Sophos Api Client.

Author: Matthew Jenkins
Email: matt.jenkins@dataprise.com

Version: 1.0.0
"""
from typing import Dict

import requests

import sophosApi.partnerApi as partnerApi
import sophosApi.whoamiApi as whoamiApi
from sophosApi.auth import Auth
from sophosApi.helpers import backoff_handler

__all__ = [
    'ApiClient'
]


class ApiClient(object):
    _request: requests.request
    _whoami: whoamiApi.IAm
    tenants: Dict[str, partnerApi.Tenant]

    def __init__(self, c_id: str, c_token: str) -> None:
        """loads initial state"""
        # All requests to be wrapped with oauth and backoff handler
        auth = Auth(c_id, c_token)
        self._session = requests.Session()
        self._request = auth.oauth_handler(backoff_handler(self._session.request))

    @property
    def _whoami(self):
        return whoamiApi.WhoamiApi(self._request).whoami

    @property
    def tenants(self) -> Dict[str, partnerApi.Tenant]:
        return partnerApi.PartnerApi(self._request, self._whoami.id).tenants

    def __getitem__(self, item) -> partnerApi.Tenant:
        return partnerApi.PartnerApi(self._request, self._whoami.id)[item]

    def close(self):
        self._session.close()
