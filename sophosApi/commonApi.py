import logging
from datetime import datetime
from typing import Dict, List, NamedTuple

import requests
from .helpers import response_logger

__all__ = [
    'CommonApi',
    'Alerts'
]

_format = "%Y-%m-%dT%H:%M:%S.%f%z"


class Alert(NamedTuple):
    id: str
    allowedActions: List[str]
    category: str
    description: str
    groupKey: str
    managedAgent: str
    product: str
    raisedAt: datetime
    severity: str
    tenant: str
    type: str


def _dict_to_alert(d: Dict) -> Alert:
    return Alert(d['id'],
                 d.get('allowedActions', list()),
                 d.get('category'),
                 d.get('description'),
                 d.get('groupKey'),
                 d.get('managedAgent', {}).get('id'),
                 d.get('product'),
                 datetime.strptime(d['raisedAt'], _format),
                 d.get('severity'),
                 d.get('tenant', {}).get('id'),
                 d.get('type'))


class Alerts:
    _alerts = {}

    def __init__(self, getter, baseurl, headers) -> None:
        """"""
        self._request = getter
        self._headers = headers
        self._baseurl = baseurl

    def __getitem__(self, a_id: str) -> Alert:
        """https://developer.sophos.com/docs/common-v1/1/routes/alerts/%7BalertId%7D/get"""
        if self._alerts.get(a_id) is not None:
            return self._alerts.get(a_id)
        url = f"{self._baseurl}alerts/{a_id}"
        params = {}
        result = self._request('get', url, headers=self._headers, params=params)
        json = result.json()
        if result:
            alert = _dict_to_alert(json)
            self._alerts.update({alert.id: alert})
        else:
            raise KeyError
        return alert

    def __delitem__(self, key) -> None:
        del (self._alerts[key])

    def fetch_all(self) -> List[Alert]:
        """
        https://developer.sophos.com/docs/common-v1/1/routes/alerts/get
        Fetch all alerts. Overwrites current alerts."""
        """"""
        url = f"{self._baseurl}alerts"
        params = {'pageSize': '50'}
        alerts = list()
        while True:
            result = self._request('get', url, params=params, headers=self._headers)
            json = result.json()
            if result:
                alerts.extend(json['items'])
            if result.status_code == 403:
                logging.error(f"Denied access to alerts for {self._headers['X-Tenant-ID']}")
                break
            if len(json['items']) < int(params['pageSize']):
                break
            params['pageFromKey'] = json['pages']['nextKey']
            params['pageSize'] = json['pages']['maxSize']
        alerts = dict([(alert['id'], _dict_to_alert(alert)) for alert in alerts])
        self._alerts = alerts
        return list(self._alerts.values())

    def action(self, a_id, action) -> bool:
        url = f"{self._baseurl}alerts/{a_id}/actions"
        result = self._request('post', url, json={'action': action, 'message': 'clear'}, headers=self._headers)
        if not result:
            response_logger(result)
            return False
        return True


class CommonApi(object):
    alerts: Alerts

    def __init__(self, getter: requests.get, t_id: str, apiHost: str) -> None:
        """
        :param requests.get getter: requests getter with all appropriate wrappers
        :param str t_id: tenant ID string
        :param str apiHost: tenant apiHost
        """
        baseurl = f"{apiHost}/common/v1/"
        headers = {'X-Tenant-ID': t_id}
        self.alerts = Alerts(getter, baseurl, headers)
