#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
import logging
import re
import requests
import os
__metaclass__ = type


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
                req = requests.request(method, api_url, params=parameters, json=body, auth=auth, verify=self._ssl_verify,
                                       timeout=10)
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

    # ------------------ Elasticsearch keystore methods------------------------
    def guess_keystore_password(self):
        systemd_envfile = '/etc/systemd/system/elasticsearch.service.d/keystore.conf'
        if os.path.exists(systemd_envfile):
            with open(systemd_envfile, 'r') as f:
                envfile_content = f.readlines()
            for line in envfile_content:
                if 'ES_KEYSTORE_PASSPHRASE_FILE' in line:
                    # search the keystore file
                    m = re.search(".*ES_KEYSTORE_PASSPHRASE_FILE=(.*)\"", line)
                    if m:
                        password_file = m.group(1)
                        with open(password_file, 'r') as f:
                            keystore_password = f.read()
                            return keystore_password
        raise Exception("Impossible to guess elastic password")

    def guess_elastic_default_password(self):
        keystore_password = self.guess_keystore_password()
        return self.get_keystore_key('bootstrap.password', keystore_password)

    def is_keystore_password_protected(self):
        """Check if the keystore is password protected."""
        read_command = "%s has-passwd" % self.__keystore_executable
        rc, stdout, stderr = self.ansible_module.run_command(
            read_command, check_rc=False)

        if 'is not' in stderr:
            return False
        else:
            return True

    def set_keystore_password(self, keystore_password):
        """Set the password for a not-protected keystore."""
        expect_command = """
        spawn  %s passwd
        expect "Enter new password"
        send -- "%s\\n"
        expect "Enter same password"
        send -- "%s\\n"
        expect eof
        """ % (self.__keystore_executable, keystore_password, keystore_password)
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
        # removed expect due to bugs: https://github.com/blink1073/oct2py/issues/248
        data = None
        if keystore_password is not None:
            data = keystore_password

        read_command = [self.__keystore_executable, "show", key]
        rc, stdout, stderr = self.ansible_module.run_command(
            read_command, check_rc=True, data=data)

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

    # ------------------ Get info methods------------------------

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

    # ------------------ Component template methods------------------------
    def get_component_templates(self):
        """Get all the component templates through APIs."""
        templates_dict = {}
        templates_list = self._api_call('_component_template')['component_templates']
        for template in templates_list:
            if not template['name'].startswith('.'):
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

    def put_component_templates(self, name, create=False, settings=None, mappings=None, aliases=None, _meta=None, allow_auto_create=False, version=None):
        """Get all the component templates through APIs."""
        body = {'template': {}}
        if not (settings or mappings or aliases):
            raise Exception(
                "A component should have at least one between 'settings','mappings' or 'aliases'")

        if settings:
            body['template']['settings'] = settings
        if aliases:
            body['template']['aliases'] = aliases
        if mappings:
            body['template']['mappings'] = mappings
        if _meta:
            body['_meta'] = _meta

        result = self._api_call('_component_template/{}'.format(name),
                                method='PUT', parameters=create, body=body, json=False)
        return result

    def delete_component_templates(self, name):
        """Delete the component templates through APIs."""
        result = self._api_call('_component_template/{}'.format(name),
                                method='DELETE', json=False)
        return result

    # ------------------ Index template methods------------------------
    def get_index_templates(self, hidden=False, managed=False, beats=False, only_beats=False):
        """Get all the component templates through APIs."""
        templates_dict = {}
        templates_list = self._api_call('_index_template')['index_templates']

        for template in templates_list:
            if template['name'].startswith('metricbeat') or \
                 template['name'].startswith('filebeat') or \
                 template['name'].startswith('heartbeat') or \
                 template['name'].startswith('auditbeat') or \
                 template['name'].startswith('packetbeat') or \
                 template['name'].startswith('winlogbeat') or \
                 template['name'].startswith('functionbeat'):
                if beats or only_beats:
                    templates_dict[template['name']] = template
                    if only_beats:
                        continue
            elif template['index_template'].get('_meta', {}).get('managed', False):
                if managed:
                    templates_dict[template['name']] = template
            elif template['name'].startswith('.'):
                if hidden:
                    templates_dict[template['name']] = template
            else:
                templates_dict[template['name']] = template

        return templates_dict

    def get_index_template(self, name):
        template_info = []
        templates_list = self._api_call('_index_template/{}'.format(name))
        if 'index_templates' in templates_list:

            for template in templates_list['index_templates']:
                if template['name'] == name:
                    return template
        raise Exception(
            "Impossible to find the '{}' template requested".format(name))

    def put_index_templates(self, name, index_patterns, composed_of=None, data_stream=None,
                            template=None, _meta=None, priority=None, version=None, create=False):
        """Get all the component templates through APIs."""
        body = {'index_patterns': index_patterns}

        if composed_of:
            body['composed_of'] = composed_of
        if data_stream:
            body['data_stream'] = data_stream
        if template:
            body['template'] = template
        if _meta:
            body['_meta'] = _meta
        if version:
            body['version'] = version
        if priority:
            body['priority'] = priority
        if version:
            body['version'] = version

        result = self._api_call('_index_template/{}'.format(name),
                                method='PUT', parameters=create, body=body, json=False)
        return result

    def delete_index_templates(self, name):
        """Delete the component templates through APIs."""
        result = self._api_call('_index_template/{}'.format(name),
                                method='DELETE', json=False)
        return result

    # ------------------Index management policy methods------------------------
    def get_ilm_policies(self, hidden=False, managed=False, beats=False, only_beats=False):
        """Get all the _ilm policies  templates through APIs."""
        ilm_policies_output = {}
        ilm_policies = self._api_call('_ilm/policy')

        for policy_name in ilm_policies.keys():
            if policy_name.startswith('metricbeat') or \
               policy_name.startswith('filebeat') or \
               policy_name.startswith('heartbeat') or \
               policy_name.startswith('auditbeat') or \
               policy_name.startswith('packetbeat') or \
               policy_name.startswith('winlogbeat') or \
               policy_name.startswith('functionbeat'):
                if beats or only_beats:
                    ilm_policies_output[policy_name] = ilm_policies[policy_name]
                    if only_beats:
                        continue
            elif policy_name.startswith('.'):
                if hidden:
                    ilm_policies_output[policy_name] = ilm_policies[policy_name]
            elif ilm_policies[policy_name]['policy'].get('_meta', {}).get('managed', False):
                if managed:
                    ilm_policies_output[policy_name] = ilm_policies[policy_name]
            else:
                ilm_policies_output[policy_name] = ilm_policies[policy_name]

        return ilm_policies_output

    def get_ilm_policy(self, name):
        """ _ilm/policy"""
        ilm_policy = self._api_call('_ilm/policy/{}'.format(name))

        for policy_name in ilm_policy.keys():
            if policy_name == name:
                return ilm_policy[policy_name]
        raise Exception(
            "Impossible to find the '{}' ILM policy requested".format(name))

    def put_ilm_policy(self, name, policy):
        """Create a ILM policy through APIs."""
        body = {'policy': policy}
        logging.debug("Body: %s", body)
        result = self._api_call('_ilm/policy/{}'.format(name),
                                method='PUT', body=body, json=False)
        return result

    def delete_ilm_policy(self, name):
        """Delete the ILM policy through APIs."""
        result = self._api_call('_ilm/policy/{}'.format(name),
                                method='DELETE', json=False)
        return result

    # --------------------- Users method --------------------------------------
    def get_users(self, managed=False, only_managed=False):
        """Get all the users through APIs."""
        users_output = {}
        users = self._api_call('_security/user')
        for user in users.keys():
            if users[user].get('metadata', {}).get('_reserved', False):
                if managed or only_managed:
                    users_output[user] = users[user]
            elif not only_managed:
                users_output[user] = users[user]

        return users_output

    def get_user(self, name):
        """ Get a user details _security/usery"""
        user = self._api_call('_security/user/%s' % name)

        for policy_name in user.keys():
            if policy_name == name:
                return user[policy_name]
        raise Exception(
            "Impossible to find the '{}' user requested".format(name))

    def put_user(self, username, **kwargs):
        """Create a user through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['enabled', 'email', 'full_name', 'password', 'metadata', 'roles']):
            raise Exception("Not valid user paramteres")
        body = kwargs
        if 'roles' not in body or body['roles'] is None:
            body['roles'] = []

        logging.debug("Body: %s", body)
        result = self._api_call('_security/user/%s' % username,
                                method='PUT', body=body, json=False)
        return result

    def delete_user(self, name):
        """Delete a user through APIs

        Args:
            name (string): the user to be deleted

        Returns:
            _type_: _description_
        """
        result = self._api_call('_security/user/%s' % name,
                                method='DELETE', json=False)
        return result

    def set_user_password(self, username, password):
        """ User to manage the password

        Args:
            username (string): the username of the user which password will be changed
            password (string): the password to be set
        """
        body = {'password': password}
        logging.debug("Set user for password: %s", username)
        result = self._api_call('_security/user/%s/_password' % username,
                                method='PUT', body=body, json=True)

    # ------------------Roles methods----------------------------
    def get_roles(self, managed=False, only_managed=False):
        """Get all the roles through APIs."""
        roles_output = {}
        roles = self._api_call('_security/role')
        for role in roles.keys():
            if roles[role].get('metadata', {}).get('_reserved', False):
                if managed or only_managed:
                    roles_output[role] = roles[role]
            elif not only_managed:
                roles_output[role] = roles[role]

        return roles_output

    def get_role(self, name):
        """ Get a role details _security/role"""
        role = self._api_call('_security/role/%s' % name)

        for policy_name in role.keys():
            if policy_name == name:
                return role[policy_name]
        raise Exception(
            "Impossible to find the '{}' role requested".format(name))

    def put_role(self, name, **kwargs):
        """Create a role through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['applications', 'cluster', 'global', 'indices', 'metadata', 'run_as', 'remote_indices', 'transient_metadata']):
            raise Exception("Not valid role paramteres")
        body = kwargs
        logging.debug("Body: %s", body)
        result = self._api_call('_security/role/%s' % name,
                                method='PUT', body=body, json=False)
        return result

    def delete_role(self, name):
        """Delete a role through APIs

        Args:
            name (string): the role to be deleted

        Returns:
            _type_: _description_
        """
        result = self._api_call('_security/role/%s' % name,
                                method='DELETE', json=False)
        return result

    # ------------------Role mapping methods---------------------
    def get_role_mappings(self, managed=False, only_managed=False):
        """Get all the roles through APIs."""
        role_mappings_output = {}
        role_mappings = self._api_call('_security/role_mapping')
        for role_map in role_mappings.keys():
            if role_mappings[role_map].get('metadata', {}).get('_reserved', False):
                if managed or only_managed:
                    role_mappings_output[role_map] = role_mappings[role_map]
            elif not only_managed:
                role_mappings_output[role_map] = role_mappings[role_map]

        return role_mappings_output

    def get_role_mapping(self, name):
        """ Get a role mapping details _security/role_mapping"""
        role_mapping = self._api_call('_security/role_mapping/%s' % name)

        for rm in role_mapping.keys():
            if rm == name:
                return role_mapping[rm]
        raise Exception(
            "Impossible to find the '{}' role mapping requested".format(name))

    def put_role_mapping(self, name, **kwargs):
        """Create a role mapping through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['enabled', 'metadata', 'roles', 'role_templates', 'rules']):
            raise Exception("Not valid role paramteres")
        body = kwargs
        logging.debug("Body: %s", body)
        result = self._api_call('_security/role_mapping/%s' % name,
                                method='PUT', body=body, json=False)
        return result

    def delete_role_mapping(self, name):
        """Delete a role mapping through APIs

        Args:
            name (string): the role to be deleted

        Returns:
            _type_: _description_
        """
        result = self._api_call('_security/role_mapping/%s' % name,
                                method='DELETE', json=False)
        return result

    # ------------------Pipelines methods------------------------
    def get_pipelines(self, hidden=False, managed=False):
        """Get all the _ilm policies  templates through APIs."""
        pipelines_output = {}
        pipelines = self._api_call('_ingest/pipeline')

        for pipeline_name in pipelines.keys():

            if pipeline_name.startswith('.'):
                if hidden:
                    pipelines_output[pipeline_name] = pipelines[pipeline_name]
            elif pipelines[pipeline_name].get('_meta', {}).get('managed', False):
                if managed:
                    pipelines_output[pipeline_name] = pipelines[pipeline_name]
            else:
                pipelines_output[pipeline_name] = pipelines[pipeline_name]

        return pipelines_output

    def get_pipeline(self, name):
        """ _ilm/policy"""
        pipeline = self._api_call('_ingest/pipeline/{}'.format(name))

        for pipeline_name in pipeline.keys():
            if pipeline_name == name:
                return pipeline[pipeline_name]
        raise Exception(
            "Impossible to find the '{}' ingest pipeline requested".format(name))

    def put_pipeline(self, name, **kwargs):
        """Create a ILM policy through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['description', 'on_failure', 'processors', 'version', '_meta', 'deprecated']):
            raise Exception("Not valid pipeline parametres")
        body = kwargs

        result = self._api_call('_ingest/pipeline/{}'.format(name),
                                method='PUT', body=body, json=False)
        return result

    def delete_pipeline(self, name):
        """Delete the ILM policy through APIs."""
        result = self._api_call('_ingest/pipeline/{}'.format(name),
                                method='DELETE', json=False)
        return result

    # ------------------Logstash pipelines methods------------------------
    def get_logstash_pipelines(self):
        """Get all the logstash pipeline through APIs."""
        pipelines_output = {}
        pipelines = self._api_call('_logstash/pipeline')

        for pipeline_name in pipelines.keys():
            pipelines_output[pipeline_name] = pipelines[pipeline_name]

        return pipelines_output

    def get_logstash_pipeline(self, name):
        """ get a logstash pipeline"""
        pipeline = self._api_call('_logstash/pipeline/{}'.format(name))

        for pipeline_name in pipeline.keys():
            if pipeline_name == name:
                return pipeline[pipeline_name]
        raise Exception(
            "Impossible to find the '{}' ingest pipeline requested".format(name))

    def put_logstash_pipeline(self, name, **kwargs):
        """Create a logstash pipeline through APIs."""
        body = {}
        if set(kwargs.keys()) - set(['description', 'last_modified', 'pipeline', 'pipeline_metadata', 'pipeline_settings', 'username']):
            raise Exception("Not valid pipeline parametres")
        body = kwargs

        result = self._api_call('_logstash/pipeline/{}'.format(name),
                                method='PUT', body=body, json=False)
        return result

    def delete_logstash_pipeline(self, name):
        """Delete the logstash pipeline through APIs."""
        result = self._api_call('_logstash/pipeline/{}'.format(name),
                                method='DELETE', json=False)
        return result
