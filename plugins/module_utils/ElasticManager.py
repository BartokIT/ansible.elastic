#!/usr/bin/env python
import re
import requests


class ElasticManager:
    def __init__(self, rest_api_endpoint=None, api_username=None, api_password=None, ssl_verify=True):
        self._rest_api_endpoint = rest_api_endpoint.rstrip('/') + '/'
        self._ssl_verify = ssl_verify
        self.__api_username = api_username
        self.__api_password = api_password

    def _api_call(self, path, method='GET', parameters=None, body=None, ssl_verify=False, json=True):
        if self._rest_api_endpoint is None:
            raise Exception("No endpoint provided")

        api_url = "{endpoint}{path}".format(
            endpoint=self._rest_api_endpoint, path=path)
        auth = ('elastic', 'bA3nb0g.Hyw')
        req = requests.request(
            method, api_url, params=parameters, auth=auth, verify=self._ssl_verify,
            timeout=10)
        if json:
            return req.json()
        else:
            return req

    def get_license_info(self):
        return self._api_call('_license')

    def get_nodes_info(self):
        return self._api_call('_nodes/_all')

    def get_health_info(self):
        info = self._api_call('_health_report',parameters={'verbose': 'false'})
        return info