from __future__ import (absolute_import, division, print_function)
from grp import getgrgid
import logging
from pwd import getpwuid
import re
import requests
import os


class KibanaManager:
    def __init__(self,
                 ansible_module,
                 rest_api_endpoint=None,
                 api_username=None,
                 api_password=None,
                 ssl_verify=True):
        self.ansible_module = ansible_module
        self._rest_api_endpoint = rest_api_endpoint.rstrip('/') + '/'
        self._ssl_verify = ssl_verify
        self.__api_username = api_username
        self.__api_password = api_password
        self.__bin_path = '/usr/share/kibana/bin/'
        self.__keystore_executable = os.path.join(
            self.__bin_path, 'kibana-keystore')
        logging.debug("----- Manager initializated ---------")

    def _api_call(self, path, method='GET', parameters=None, body=None, ssl_verify=False, json=True):
        ''' Facility to make an API call '''
        if self._rest_api_endpoint is None:
            raise Exception("No endpoint provided")

        api_url = "%s%s" % (self._rest_api_endpoint, path)

        auth = (self.__api_username, self.__api_password)
        req = requests.request(
            method, api_url, params=parameters, json=body, auth=auth, verify=self._ssl_verify,
            timeout=10)
        response = {}
        try:
            if req.status_code == 401:
                # try to guess elastic password and resubmit password
                password = self.guess_elastic_default_password()
                auth = ('elastic', password)
                req = requests.request(
                        method, api_url, params=parameters, json=body, auth=auth, verify=self._ssl_verify,
                        timeout=10)
            response = req.json()
            req.raise_for_status()
        except requests.exceptions.Timeout as exctimeout:
            logging.error("{}".format(exctimeout))
        except Exception as exc:
            logging.error("{}".format(exc))
            if 'error' in response:
                logging.error("Error: %s" % response['error'])
            raise

        if json:
            return req.json()
        else:
            return req

    # ------------------ Kibana keystore methods------------------------
    def list_keystore_password(self):
        list_command = "{} list".format(self.__keystore_executable)
        rc, stdout, stderr = self.ansible_module.run_command(
            list_command, check_rc=True)
        return stdout.strip().splitlines()

    def get_keystore_key(self, key):
        """Read keystore settings."""

        read_command = "{} show {}".format(self.__keystore_executable, key)
        logging.debug(read_command)
        rc, stdout, stderr = self.ansible_module.run_command(
            read_command, check_rc=True)
        element = stdout.strip()
        return element

    def add_keystore_key(self, key, value, keystore_password=None):
        """Add keystore settings."""
        data = value
        add_command = [self.__keystore_executable, "add", "--stdin", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, check_rc=True, data=data)

    def update_keystore_key(self, key, value, keystore_password=None):
        """Overwrite keystore settings."""
        data = value
        add_command = [self.__keystore_executable,
                      "add", "--force", "--stdin", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, check_rc=True, data=data)

    def delete_keystore_key(self, key, keystore_password=None):
        """Delete keystore key."""

        delete_command = [self.__keystore_executable, "remove", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            delete_command, check_rc=True)

