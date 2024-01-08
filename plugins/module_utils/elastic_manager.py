#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
from grp import getgrgid
import logging
from pwd import getpwuid
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
        logging.debug("----- Manager initializated ---------")

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

        try:
            if req.status_code == 401:
                # try to guess elastic password and resubmit password
                password = self.guess_elastic_default_password()
                auth = ('elastic', password)
                req = requests.request(
                        method, api_url, params=parameters, json=body, auth=auth, verify=self._ssl_verify,
                        timeout=10)
            req.raise_for_status()
        except Exception as exc:
            logging.error("{}".format(exc))
            raise
        if json:
            return req.json()
        else:
            return req

    # BEATS
    def get_beat_keystore_path(self, beattype):
        return os.path.join("/var/lib/{}beat/".format(beattype), "{}beat.keystore".format(beattype))

    def is_beat_keystore_present(self, beattype):
        ''' Check for presence of beat keystore '''
        keystore_path = self.get_beat_keystore_path(beattype)

        if beattype not in ['heart', 'file', 'metric','audit']:
            raise Exception("Unsupported beat type")
        result = os.path.isfile(keystore_path)
        if not result:
            logging.debug("Keystore {} is not present".format(keystore_path))
            return False

        return True

    def get_beat_keystore_stat(self, beattype):
        ''' Get information on keystore file'''

        keystore_path = self.get_beat_keystore_path(beattype)
        if self.is_beat_keystore_present(beattype):
            keystore_stat = os.stat(keystore_path)
            return {
                'exists': True,
                'owner': getpwuid(keystore_stat.st_uid).pw_name,
                'mode': "0{}".format(oct(keystore_stat.st_mode))[-3:],
                'group': getgrgid(keystore_stat.st_gid).gr_name
            }
        else:
            return {
                'exists': False
            }

    def create_beat_keystore(self, beattype):
        '''Create an empty beat keystore'''
        keystore_executable = "{}beat keystore".format(beattype)
        create_command = keystore_executable
        create_command += " create"

        # Run the command to create a keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            create_command, check_rc=True)

        if 'created' not in stdout.lower():
            logging.error("Impossible to create the keystore RC {} | STDOUT {} | STDERR {}".format(rc, stdout, stderr))
            raise Exception("Impossible to create the keystore")

    def add_beat_keystore_key(self, beattype, key, value):
        ''' Add key to beat keystore'''
        if not self.is_beat_keystore_present(beattype):
            self.create_beat_keystore(beattype)

        add_command = "{}beat keystore add --stdin {} --force".format(beattype, key)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, data=value, check_rc=True)

        if 'keystore not found' in stdout.lower():
            raise Exception("Keystore not found")

    def delete_beat_keystore_key(self, beattype, key):
        ''' Add key to beat keystore'''

        remove_command = "{}beat keystore remove {}".format(beattype, key)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            remove_command, check_rc=True)

        if 'keystore not found' in stdout.lower():
            raise Exception("Keystore not found")

    def list_beat_keystore_keys(self, beattype):
        ''' List keys of keystore'''
        if not self.is_beat_keystore_present(beattype):
            return []

        data = []
        list_command =  "{}beat keystore list".format(beattype)
        rc, stdout, stderr = self.ansible_module.run_command(
            list_command, check_rc=True)
        logging.debug("List command output RC {} | STDOUT {} | STDERR {}".format(rc, stdout.replace("\n","\\n"), stderr.replace("\n","\\n")))

        for line in stdout.splitlines():
            data.append(line)
        return data

    def list_beat_modules(self, beattype):
        ''' List enabled beat modules'''

        remove_command = "{}beat modules list".format(beattype)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            remove_command, check_rc=True)

        enabled_modules= []
        for line in stdout.splitlines():
            if line.strip() == 'Enabled:':
                continue
            elif line.strip() == 'Disabled:':
                break
            elif line.strip() == '':
                continue
            else:
                enabled_modules.append(line)

        return enabled_modules

    def enable_beat_module(self, beattype, module):
        ''' Enable beat modules'''

        remove_command = "{}beat modules enable {}".format(beattype, module)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            remove_command, check_rc=True)

    def disable_beat_module(self, beattype, module):
        ''' Enable beat modules'''

        remove_command = "{}beat modules disable {}".format(beattype, module)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            remove_command, check_rc=True)


    # ------------------ Elasticsearch keystore methods------------------------
    def guess_keystore_password(self):
        systemd_envfile = '/etc/systemd/system/elasticsearch.service.d/keystore.conf'
        with open(systemd_envfile,'r') as f:
            envfile_content = f.readlines()
        for line in envfile_content:
            if 'ES_KEYSTORE_PASSPHRASE_FILE' in line:
                # search the keystore file
                m = re.search(".*ES_KEYSTORE_PASSPHRASE_FILE=(.*)\"", line)
                if m:
                    password_file = m.group(1)
                    with open(password_file,'r') as f:
                        keystore_password = f.read()
                        return keystore_password
        raise Exception("Impossible to guess elastic password")

    def guess_elastic_default_password(self):
        keystore_password = self.guess_keystore_password()
        return self.get_keystore_key('bootstrap.password', keystore_password)

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
        """Set the password for a not-protected keystore."""
        expect_command = """
        spawn  {exec} passwd
        expect "Enter new password"
        send -- "{passfirst}\\n"
        expect "Enter same password"
        send -- "{passconfirm}\\n"
        expect eof
        """.format(exec=self.__keystore_executable, passfirst=keystore_password, passconfirm=keystore_password)
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
    def get_index_templates(self, hidden=False):
        """Get all the component templates through APIs."""
        templates_dict = {}
        templates_list = self._api_call('_index_template')['index_templates']

        for template in templates_list:
            if not template['name'].startswith('.') or hidden:
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

    def put_index_templates(self, name, index_patterns, composed_of=None, data_stream=None, template=None, _meta=None, priority=None, version=None, create=False):
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
    def get_ilm_policies(self, hidden=False, managed=False):
        """Get all the _ilm policies  templates through APIs."""
        ilm_policies_output = {}
        ilm_policies = self._api_call('_ilm/policy')

        for policy_name in ilm_policies.keys():

            if policy_name.startswith('.'):
                if hidden:
                    ilm_policies_output[policy_name] = ilm_policies[policy_name]
            elif ilm_policies[policy_name]['policy'].get('_meta',{}).get('managed', False):
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
        body =  {'policy': policy}
        logging.debug("Body: %s" % body)
        result = self._api_call('_ilm/policy/{}'.format(name),
                                method='PUT', body=body, json=False)
        return result

    def delete_ilm_policy(self, name):
        """Delete the ILM policy through APIs."""
        result = self._api_call('_ilm/policy/{}'.format(name),
                                method='DELETE', json=False)
        return result

    # --------------------- Users method --------------------------------------
    def get_users(self, managed=False):
        """Get all the users through APIs."""
        users_output = {}
        users = self._api_call('_security/user')
        for user in users.keys():
            if users[user].get('metadata',{}).get('_reserved', False):
                if managed:
                    users_output[user] = users[user]
            else:
                users_output[user] = users[user]

        return users_output

    def get_user(self, name):
        """ _security/usery"""
        ilm_policy = self._api_call('_security/user/{}'.format(name))

        for policy_name in ilm_policy.keys():
                if policy_name == name:
                    return ilm_policy[policy_name]
        raise Exception(
            "Impossible to find the '{}' ILM policy requested".format(name))

    def put_user(self, username, **kwargs):
        """Create a user through APIs."""
        body =  {}
        if set(kwargs.keys()) - set(['enabled', 'email', 'full_name', 'password', 'metadata', 'roles']):
            raise Exception("Not valid user paramteres")
        body=kwargs
        if 'roles' not in body or body['roles'] is None:
            body['roles'] = []

        logging.debug("Body: %s" % body)
        result = self._api_call('_security/user/{}'.format(username),
                                method='PUT', body=body, json=False)
        return result

    def delete_user(self, name):
        """Delete a user through APIs."""
        result = self._api_call('_security/user/{}'.format(name),
                                method='DELETE', json=False)
        return result
