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
        headers = {'kbn-xsrf': 'true'}

        req = requests.request(
            method, api_url, headers=headers, params=parameters, json=body, auth=auth, verify=self._ssl_verify,
            timeout=10)
        response = {}

        try:
            if req.status_code == 401:
                # try to guess elastic password and resubmit password
                password = self.guess_elastic_default_password()
                auth = ('elastic', password)
                req = requests.request(method, api_url, headers=headers, params=parameters, json=body, auth=auth, verify=self._ssl_verify,
                                       timeout=10)
            if json:
                response = req.json()
            req.raise_for_status()
        except requests.exceptions.Timeout as exctimeout:
            logging.error("%s", exctimeout)
        except Exception as exc:
            logging.error("%s", exc)
            logging.error("Error: %s", response)
            raise

        if json:
            return req.json()
        else:
            return req


    # region Kibana keystore methods
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
    # endregion
    # region Spaces methods
    def get_spaces(self, reserved=False):
        """Get all the spaces through APIs."""
        spaces_output = {}
        spaces = self._api_call('api/spaces/space')

        for space in spaces:
            if space.get('_reserved', False):
              if reserved:
                spaces_output[space['id']] = space
            else:
                spaces_output[space['id']] = space

        return spaces_output

    def get_space(self, space_id):
        """Get specific space"""
        space = self._api_call('api/spaces/space/{}'.format(space_id))

        if space_id == space['id']:
            return space
        raise Exception(
            "Impossible to find the '{}' space requested".format(space_id))

    def put_space(self, space_id, **kwargs):
        """Create a space through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['color', 'description', 'disabledFeatures', 'imageUrl', 'initials', 'name','solution']):
            raise Exception("Not valid space parametres")
        body = kwargs
        body['id'] = space_id
        result = self._api_call('api/spaces/space',
                                method='POST', body=body, json=True)
        logging.debug("%s" %result)

    def update_space(self, space_id, **kwargs):
        """Update a space through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['color', 'description', 'disabledFeatures', 'imageUrl', 'initials', 'name','solution']):
            raise Exception("Not valid space parametres")
        body = kwargs
        body['id'] = space_id
        result = self._api_call('api/spaces/space/{}'.format(space_id),
                                method='PUT', body=body, json=True)

    def delete_space(self, space_id):
        """Delete a space through APIs."""
        result = self._api_call('api/spaces/space/{}'.format(space_id),
                                method='DELETE', json=False)

    # endregion
    # region Data view methods
    def get_data_views(self, reserved=False):
        """Get all the data views through APIs."""
        data_views_output = {}
        data_views_id_map = {}
        spaces=self.get_spaces(reserved=True)

        for space in spaces.keys():
            data_views = self._api_call('s/%s/api/data_views' % space)
            for data_view in data_views['data_view']:
                data_views_output[data_view['id']] = data_view
            # data_views_id_map[data_view['name']] = data_view['id']
        return data_views_output

    def get_data_view(self, dataview_id, namespaces=None):
        """Get specific data view"""
        data_view = self._api_call('s/{}/api/data_views/data_view/{}'.format(namespaces[0], dataview_id,))
        if dataview_id == data_view['data_view']['id']:
            del data_view['data_view']['fields']
            return data_view
        raise Exception(
            "Impossible to find the '{}' data view requested".format(dataview_id))

    def put_data_view(self, dataview_id, **kwargs):
        """Create a data view through APIs."""
        body = {}
        if set(kwargs['data_view'].keys()) - set(['allowNoIndex', 'fieldAttrs', 'fields', 'fieldFormats', 'name', 'namespaces', 'runtimeFieldMap','sourceFilters', 'timeFieldName', 'title', 'typeMeta']):
            raise Exception("Not valid pipeline parametres")
        body = kwargs
        body['data_view']['id'] = dataview_id
        result = self._api_call('api/data_views/data_view',
                                method='POST', body=body, json=True)


    def update_data_view(self, dataview_id, **kwargs):
        """Update a space through APIs."""
        body = {}
        if set(kwargs['data_view'].keys()) - set(['allowNoIndex', 'fieldAttrs', 'fields', 'fieldFormats', 'name', 'namespaces', 'runtimeFieldMap','sourceFilters', 'timeFieldName', 'title', 'typeMeta']):
            raise Exception("Not valid pipeline parametres")
        body = kwargs
        result = self._api_call('api/data_views/data_view/{}'.format(dataview_id),
                                method='POST', body=body, json=True)

    def delete_data_view(self, dataview_id):
        """Delete a data view through APIs."""
        result = self._api_call('api/data_views/data_view/{}'.format(dataview_id),
                                method='DELETE', json=False)
    # endregion

    # region Dashboards
    def get_dashboards(self):
        """Get all the dashboards through APIs."""
        dashboards_output = {}
        dashboards_id_map = {}
        spaces=self.get_spaces(reserved=True)

        for space in spaces.keys():
            dashboards = self._api_call('s/%s/api/dashboards/dashboard' % space)
            for dashboard in dashboards['items']:
                title = dashboard['attributes']['title']
                dashboards_output[dashboard['id']]=dashboard
                if title not in dashboards_id_map:
                    dashboards_id_map[title] = {'ids':[], 'namespaces':[]}
                for namespace in dashboard['namespaces']:
                    dashboards_id_map[title]['ids'].append({'id': dashboard['id'], 'namespace': namespace})
                    dashboards_id_map[title]['namespaces'].append(namespace)
        return dashboards_output, dashboards_id_map

    def delete_dashboard(self, dashboard_namespace, dashboard_id):
        """Delete a dashboard through APIs."""
        result = self._api_call('s/{}/api/dashboards/dashboard/{}'.format(dashboard_namespace, dashboard_id),
                                method='DELETE', json=False)

    # endregion