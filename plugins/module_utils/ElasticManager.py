#!/usr/bin/env python
import re
import requests

class ElasticManager(object):
    def __init(self, rest_api_endpoint=None, api_username=None, api_password=None):
        self._rest_api_endpoint = rest_api_endpoint.rstrip('/') + '/'
        self.__api_username = api_username
        self.__api_password = api_password

    def _api_call(self, path, method='GET', parameters=None, body=None):
        if self._rest_api_endpoint is None:
            raise Exception("No endpoint provided")

        api_url = "{endpoint}{path}".form(endpoint=self._rest_api_endpoint, path=path)
