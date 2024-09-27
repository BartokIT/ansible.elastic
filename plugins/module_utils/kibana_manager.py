from __future__ import (absolute_import, division, print_function)
import logging
import requests
import os
__metaclass__ = type


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
        response = {}
        try:
            req = requests.request(method, api_url, params=parameters, json=body, auth=auth, verify=self._ssl_verify, timeout=10)
            response = req.json()
            req.raise_for_status()
        except requests.exceptions.Timeout as exctimeout:
            logging.error("%s", exctimeout)
        except Exception as exc:
            logging.error("%s", exc)
            if 'error' in response:
                logging.error("Error: %s", response['error'])
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
        add_command = [self.__keystore_executable, "add", "--force", "--stdin", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, check_rc=True, data=data)

    def delete_keystore_key(self, key, keystore_password=None):
        """Delete keystore key."""

        delete_command = [self.__keystore_executable, "remove", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            delete_command, check_rc=True)

    # feature
    def get_features(self):
        """Get all the features through APIs."""
        features_output = {}
        features = self._api_call('api/features')

        for feature in features:
            features_output[feature['id']] = feature

        return features_output

    # spaces
    def get_spaces(self, reserved=False):
        """Get all the spaces through APIs."""
        spaces_output = {}
        spaces = self._api_call('api/spaces/space')

        for space in spaces:
            if reserved or not space["_reserved"]:
                spaces_output[space['id']] = space

        return spaces_output

    def put_space(self, sid, **kwargs):
        """Create a space mapping through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['name', 'description', 'color', 'disabledFeatures', 'initials', 'imageUrl', 'solution']):
            raise Exception("Not valid space paramteres")
        body = kwargs
        body['id'] = sid
        logging.debug("Body: %s", body)
        result = self._api_call('api/spaces/space',
                                method='POST', body=body, json=True)
        return result

    def get_space(self, id):
        """Create a space mapping through APIs."""
        return self._api_call('api/spaces/space/%s' % id)

    def delete_space(self, id):
        """Delete a space through APIs

        Args:
            id (string): the space to be deleted

        Returns:
            _type_: _description_
        """
        result = self._api_call('api/spaces/space/%s' % id,
                                method='DELETE', json=False)
        return result


    # data views
    def get_data_views(self):
        """Get all the data views through APIs."""
        views_output = {}
        views = self._api_call('api/data_views')

        for view in views['data_view']:
            views_output[view['name']] = view

        return views_output

    # status
    def get_health_info(self):
        """Get status through APIs."""
        return  self._api_call('api/status')
