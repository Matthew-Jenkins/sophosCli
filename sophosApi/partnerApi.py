from typing import Dict, NamedTuple

import requests

import sophosApi.commonApi as commonApi
import sophosApi.endpointApi as endpointApi
from .helpers import dicter

__all__ = {
    'PartnerApi',
    'Tenant'
}


class Tenant(NamedTuple):
    alerts: commonApi.Alerts
    apiHost: str
    billingType: str
    dataGeography: str
    dataRegion: str
    endpoints: endpointApi.Endpoints
    id: str
    name: str
    shortName: str
    organization: str
    partner: str


class PartnerApi(object):
    """https://developer.sophos.com/docs/partner-v1/1/overview
    Allows creation but not updation. Lets just go with read only read all for now."""
    baseurl = "https://api.central.sophos.com/partner/v1/"

    def __init__(self, getter: requests.get, iam: str) -> None:
        self.headers = {'X-Partner-ID': iam}
        self._request = getter

    @property
    def tenants(self) -> Dict[str, Tenant]:
        """https://developer.sophos.com/docs/partner-v1/1/routes/tenants/get"""
        maxSize = 100
        params = {"page": 1,
                  "pageSize": maxSize}
        tenants = list()
        while True:
            result = self._request('get', f"{self.baseurl}tenants", headers=self.headers, params=params)
            json = result.json()
            params['page'] += 1
            if result:
                tenants.extend(json['items'])
            if len(json['items']) < maxSize:
                break
            params['pageSize'] = json['pages']['maxSize']
        tenants = dict([(ten['id'],
                         Tenant(commonApi.CommonApi(self._request, ten['id'], ten['apiHost']).alerts,
                                ten['apiHost'],
                                ten['billingType'],
                                ten['dataGeography'],
                                ten['dataRegion'],
                                endpointApi.EndpointApi(self._request, ten['id'], ten['apiHost']).endpoints,
                                ten['id'],
                                ten['name'],
                                str(ten['name']).split()[0] or ten['name'],
                                dicter(ten['organization']).get('id'),
                                dicter(ten['partner']).get('id')))
                        for ten in tenants])
        return tenants

    def __getitem__(self, item: str) -> Tenant:
        result = self._request('get', f"{self.baseurl}tenants/{item}", headers=self.headers)
        if result.status_code == 404:
            raise KeyError
        if result:
            ten = result.json()
            return Tenant(commonApi.CommonApi(self._request, ten['id'], ten['apiHost']).alerts,
                          ten['apiHost'],
                          ten['billingType'],
                          ten['dataGeography'],
                          ten['dataRegion'],
                          endpointApi.EndpointApi(self._request, ten['id'], ten['apiHost']).endpoints,
                          ten['id'],
                          ten['name'],
                          str(ten['name']).split()[0] or ten['name'],
                          dicter(ten['organization']).get('id'),
                          dicter(ten['partner']).get('id'))
        else:
            raise Exception("Unexpected exception!")

    @tenants.setter
    def tenants(self, tenant: Tenant):
        # self.tenants.cache_clear()
        raise NotImplemented
