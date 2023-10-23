#!/usr/bin/env python
import re
import requests
import os


class ElasticManager:
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
        self.__bin_path = '/usr/share/elasticsearch/bin/'
        self.__keystore_executable = os.path.join(
            self.__bin_path, 'elasticsearch-keystore')
        self.__index_settings = {'static': ['number_of_shards', 'number_of_routing_shards', 'codec', 'routing_partition_size',
                                            'soft_deletes.enabled', 'soft_deletes.retention_lease.period', 'load_fixed_bitset_filters_eagerly', 'shard.check_on_startup'],
                                 'dynamic': ['number_of_replicas', 'auto_expand_replicas', 'search.idle.after', 'refresh_interval', 'max_result_window', 'max_inner_result_window',
                                             'max_rescore_window', 'max_docvalue_fields_search', 'max_script_fields', 'max_ngram_diff', 'max_shingle_diff', 'max_refresh_listeners',
                                             'analyze.max_token_count', 'highlight.max_analyzed_offset', 'max_terms_count', 'max_regex_length', 'query.default_field',
                                             'routing.allocation.enable', 'routing.rebalance.enable', 'gc_deletes', 'default_pipeline', 'final_pipeline']}
        self.__index_alias_properties = [
            'filter', 'index_routing', 'is_hidden', 'is_write_index', 'routing', 'search_routing']

    def _api_call(self, path, method='GET', parameters=None, body=None, ssl_verify=False, json=True):
        ''' Facility to make an API call '''
        if self._rest_api_endpoint is None:
            raise Exception("No endpoint provided")

        api_url = "{endpoint}{path}".format(
            endpoint=self._rest_api_endpoint, path=path)
        auth = (self.__api_username, self.__api_password)
        req = requests.request(
            method, api_url, params=parameters, json=body, auth=auth, verify=self._ssl_verify,
            timeout=10)
        if json:
            return req.json()
        else:
            return req

    def is_keystore_password_protected(self):
        """Check if the keystore is password protected."""
        read_command = "{} has-passwd".format(
            self.__keystore_executable,)
        rc, stdout, stderr = self.ansible_module.run_command(
            read_command, check_rc=False)

        if 'is not' in stderr:
            return False
        else:
            return True

    def set_keystore_password(self, keystore_password):
        expect_command = """
        spawn  {} passwd
        expect "Enter new password"
        send -- "{}\\n"
        expect "Enter same password"
        send -- "{}\\n"
        expect eof
        """.format(self.__keystore_executable, keystore_password,  keystore_password)
        set_command = ["expect", "-c", expect_command]
        rc, stdout, stderr = self.ansible_module.run_command(
            set_command, check_rc=True)

    def list_keystore_password(self, keystore_password=None):
        data = None
        if keystore_password is not None:
            data = keystore_password
        list_command = "{} list".format(self.__keystore_executable)
        rc, stdout, stderr = self.ansible_module.run_command(
            list_command, check_rc=True, data=data)
        return stdout.splitlines()

    def get_keystore_key(self, key, keystore_password=None):
        """Read keystore settings."""

        read_command = []
        if keystore_password is not None:

            expect_command = """
            spawn  {} show {}
            expect "Enter password for the elasticsearch keystore"
            send -- "{}\\n"
            expect eof
            """.format(self.__keystore_executable, key, keystore_password)
            read_command = ["expect", "-c", expect_command]
        else:
            read_command = [self.__keystore_executable, "show", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            read_command, check_rc=True)
        element = [item.strip()
                   for item in stdout.split("\n") if item.strip()][-1]
        return element

    def add_keystore_key(self, key, value, keystore_password=None):
        """Add keystore settings."""
        add_command = []
        if keystore_password is not None:
            data = None
            expect_command = """
            spawn  {} add {}
            expect "Enter password for the elasticsearch keystore"
            send -- "{}\\n"
            expect "Enter value for"
            send -- "{}\\n"
            expect eof
            """.format(self.__keystore_executable, key, keystore_password, value)
            add_command = ["expect", "-c", expect_command]
        else:
            data = value
            add_command = [self.__keystore_executable, "add", "--stdin", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, check_rc=True, data=data)

    def update_keystore_key(self, key, value, keystore_password=None):
        """Overwrite keystore settings."""
        add_command = []
        if keystore_password is not None:
            data = None
            expect_command = """
            spawn  {} add --force {}
            expect "Enter password for the elasticsearch keystore"
            send -- "{}\\n"
            expect "Enter value for"
            send -- "{}\\n"
            expect eof
            """.format(self.__keystore_executable, key, keystore_password, value)
            add_command = ["expect", "-c", expect_command]
        else:
            data = value
            add_command = [self.__keystore_executable,
                           "add", "--force", "--stdin", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, check_rc=True, data=data)

    def delete_keystore_key(self, key, keystore_password=None):
        """Delete keystore key."""

        delete_command = []
        if keystore_password is not None:

            expect_command = """
            spawn  {} remove {}
            expect "Enter password for the elasticsearch keystore"
            send -- "{}\\n"
            expect eof
            """.format(self.__keystore_executable, key, keystore_password)

            delete_command = ["expect", "-c", expect_command]

        else:
            delete_command = [self.__keystore_executable, "remove", key]

        rc, stdout, stderr = self.ansible_module.run_command(
            delete_command, check_rc=True)

    def get_license_info(self):
        """Call API to get license info."""
        return self._api_call('_license')

    def get_nodes_info(self):
        """Call API to get nodes info."""
        return self._api_call('_nodes')

    def get_health_info(self):
        info = self._api_call('_health_report', parameters={
                              'verbose': 'false'})
        return info

    def get_cluster_health_info(self):
        info = self._api_call('_cluster/health')
        return info

    def get_component_templates(self):
        """Get all the component templates through APIs."""
        templates_dict = {}
        templates_list = self._api_call('_component_template')[
            'component_templates']
        for template in templates_list:
            templates_dict[template['name']] = template
        return templates_dict

    def get_component_template(self, name):
        template_info = []
        templates_list = self._api_call('_component_template/{}'.format(name))
        if 'component_templates' in templates_list:
            for template in templates_list['component_templates']:
                if template['name'] == name:
                    return template
        raise Exception(
            "Impossible to find the '{}' template requrested".format(name))

    def put_component_templates(self, name, create=True, settings=None, mappings=None, aliases=None, _meta=None, allow_auto_create=False, version=None):
        """Get all the component templates through APIs."""
        body = {'template': {}}
        if not (settings or mappings or aliases):
            raise Exception(
                "A component should have at least one between 'settings','mappings' or 'aliases'")

        if settings:
            not_allowed = set(settings.keys(
            )) - set(self.__index_settings['static'] + self.__index_settings['dynamic'])
            # if len(list(not_allowed)):
            #     raise Exception(
            #         "The following settings are not allowed: {}". format(list(not_allowed)))

            body['template']['settings'] = settings
        if aliases:
            for alias in aliases.keys():
                not_allowed = set(aliases[alias].keys()) - \
                    set(self.__index_alias_properties)
                # if len(list(not_allowed)):
                #     raise Exception('The following alias properties are not allowed for alias {}: {}'.format(
                #         alias, list(not_allowed)))
            body['template']['aliases'] = aliases
        if mappings:
            body['template']['mappings'] = mappings
        if _meta:
            body['_meta'] = _meta

        result = self._api_call('_component_template/{}'.format(name),
                                method='PUT', body=body, json=False)
        result.raise_for_status()
        return result
