from datetime import datetime
from pprint import pformat
from typing import Dict, List, Optional, NamedTuple
import logging
from .helpers import response_logger

import requests

__all__ = [
    "EndpointApi"
]

_format = "%Y-%m-%dT%H:%M:%S.%f%z"


class Endpoint(NamedTuple):
    id: str
    type: str
    tenant: str
    hostname: str
    health: str
    os: str
    ipAddresses: Optional[List[str]]
    macAddresses: Optional[List[str]]
    group: Optional[str]
    tamperProtectionEnabled: bool
    lastSeenAt: datetime


def _dict_to_endpoint(d: Dict) -> Endpoint:
    return Endpoint(d['id'],
                    d['type'],
                    d['tenant']['id'],
                    d['hostname'],
                    d.get('health', {}).get('overall'),
                    d['os'].get('name'),
                    d.get('ipv4Addresses', []) + d.get('ipv6Addresses', []),
                    d.get('macAddresses'),
                    d.get('group', {}).get('name'),
                    d.get('tamperProtectionEnabled'),
                    datetime.strptime(d['lastSeenAt'], _format))


class Endpoints:
    _endpoints = {}

    def __init__(self, getter: requests.get, baseurl, headers) -> None:
        """"""
        self._request = getter
        self._headers = headers
        self._baseurl = baseurl

    def __getitem__(self, e_id: str) -> Endpoint:
        """https://developer.sophos.com/docs/endpoint-v1/1/routes/endpoints/%7BendpointId%7D/get
        :param str e_id: endpoint id
        """
        if self._endpoints.get(e_id) is not None:
            return self._endpoints.get(e_id)
        url = f"{self._baseurl}endpoints/{e_id}"
        endpoint = None
        result = self._request('get', url, headers=self._headers, params={"view": "summary"})
        json = result.json()
        if result:
            endpoint = _dict_to_endpoint(json)
            self._endpoints.update({endpoint.id: endpoint})
        else:
            raise KeyError
        return self._endpoints[e_id]

    def __delitem__(self, e_id: str) -> None:
        del (self._endpoints[e_id])

    def fetch_all(self, query=None) -> List[Endpoint]:
        """https://developer.sophos.com/docs/endpoint-v1/1/routes/endpoints/get
        Fetch all endpoints, replaces current endpoints"""
        params = {"view": "summary", 'pageSize': '50'}
        if query is not None:
            params.update(**query)
        url = f"{self._baseurl}endpoints"
        endpoints = list()
        while True:
            result = self._request('get', url, headers=self._headers, params=params)
            json = result.json()
            if result:
                endpoints.extend(json['items'])
            else:
                response_logger(result)
                break
            if len(json['items']) < int(params['pageSize']):
                break
            params['pageSize'] = json['pages']['maxSize']
            params['pageFromKey'] = json['pages']['nextKey']
        endpoints = dict([(point['id'], _dict_to_endpoint(point)) for point in endpoints])
        self._endpoints = endpoints
        return list(self._endpoints.values())

    def scan(self, e_id: str) -> bool:
        """https://developer.sophos.com/docs/endpoint-v1/1/routes/endpoints/%7BendpointId%7D/scans/post"""
        url = f"{self._baseurl}endpoints/{e_id}/scans"
        result = self._request('post', url, headers=self._headers, json={})
        if not result:
            response_logger(result)
            return False
        return True

    def update_agent(self, e_id: str) -> bool:
        """https://developer.sophos.com/docs/endpoint-v1/1/routes/endpoints/%7BendpointId%7D/update-checks/post"""
        url = f"""{self._baseurl}endpoints/{e_id}/update-checks"""
        result = self._request('post', url, headers=self._headers, json={})
        if not result:
            response_logger(result)
            return False
        return True


class Settings: pass


class EndpointApi(object):
    """https://developer.sophos.com/docs/endpoint-v1/1/overview
    For now, just looking for basic read only functionality"""
    endpoints: Endpoints

    def __init__(self, getter: requests.get, t_id: str, apiHost: str) -> None:
        """
        :param requests.get getter: requests getter with all appropriate wrappers
        :param str t_id: tenant ID string
        :param str apiHost: tenant apiHost
        """
        baseurl = f"{apiHost}/endpoint/v1/"
        headers = {'X-Tenant-ID': t_id}
        self.endpoints = Endpoints(getter, baseurl, headers)
        # self.settings = Settings(getter, baseurl, headers)
