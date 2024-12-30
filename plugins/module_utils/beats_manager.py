#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
from grp import getgrgid
import logging
from pwd import getpwuid
import os
import re
import json
import shutil
import tempfile
__metaclass__ = type


class BeatManager:
    def __init__(self, ansible_module, api_username=None, api_password=None, rest_api_endpoint=None, kibana_endpoint=None, ssl_verify=False):
        self.ansible_module = ansible_module
        self.__elastic_endpoints = rest_api_endpoint
        self.__kibana_endpoint = kibana_endpoint
        self.__api_username = api_username
        self.__api_password = api_password
        self.__ssl_verify = ssl_verify
        self.__beat_share_folder_parent = '/usr/share/'
        logging.debug("----- Manager initializated ---------")

    def get_beat_version(self, beattype):
        rc, stdout, stderr = self.ansible_module.run_command(
            "%s version" % beattype, check_rc=True)
        pattern = r".+beat version (\d+\.\d+\.\d+) \(.+\)"
        m = re.match(pattern,stdout)
        if m:
            return m.group(1)
        else:
            return ''


    #region Setup methods
    def do_index_management_setup(self, beattype):
        setup_command=["%s" % beattype, "setup", "--E", 'output.elasticsearch.hosts=[%s]' % self.__elastic_endpoints,
                       "-E", "output.elasticsearch.username=%s" % self.__api_username,
                       "-E", "output.elasticsearch.password=%s" % self.__api_password,
                       "-E", "setup.ilm.overwrite=true", "--index-management"]
        if not self.__ssl_verify:
            setup_command.append("-E")
            setup_command.append('output.elasticsearch.ssl.verification_mode=none')
        rc, stdout, stderr = self.ansible_module.run_command(
            setup_command, check_rc=True)

    def get_dashboard_list_with_id(self, beattype):
        """
        List the dashboard available with the
        """
        beat_object_folder = "%s/%s/kibana" % (self.__beat_share_folder_parent.rstrip('/'), beattype)
        dashboards = {}
        for version in ['7','8']:
            dashboard_folder = "%s/%s/dashboard" % (beat_object_folder, version)
            logging.debug("Searching dashboard in path: %s" % dashboard_folder)
            if os.path.exists(dashboard_folder):
                files = os.listdir(dashboard_folder)
                # get each file and directory
                for filename in files:
                    complete_path="%s/%s" % (dashboard_folder.rstrip('/'), filename)
                    with open(complete_path, 'r') as jf:
                        data = json.load(jf)
                        dashboards[data['attributes']['title']] = {'id': data['id'], 'folder': dashboard_folder, 'filename': complete_path}
        return dashboards

    def _copy_object(self, beattype, object_id, object_type, object_parent_folder, object_temporary_folder):
        """
        Recursively traverse the object to get referenced objects and copy to the temporary folder
        """
        original_filename = "%s/%s/%s.json" % (object_parent_folder, object_type, object_id)
        temporary_filename = "%s/%s/%s.json" % (object_temporary_folder, object_type, object_id)
        if not os.path.exists(os.path.dirname(temporary_filename)):
            os.makedirs(os.path.dirname(temporary_filename))
        shutil.copy(original_filename, temporary_filename)
        logging.debug("Copied object %s %s" % (object_type, object_id))

        # open the object to extract the references
        referenced_objects = []
        with open(original_filename, 'r') as of:
            data = json.load(of)
            if data.get('references', False):
                referenced_objects = data['references']

        for ref_object in referenced_objects:
            if not ref_object['name'].startswith('kibanaSavedObjectMeta'):
                self._copy_object(beattype, ref_object['id'], ref_object['type'], object_parent_folder, object_temporary_folder)


    def import_dashboard(self, beattype, name, namespace):
        """
        Import the dashboard available with the beat package
        """
        # get all dashboards
        dbs = self.get_dashboard_list_with_id(beattype)
        dashboard_info = dbs.get(name,'')
        if not dashboard_info:
            raise Exception("Dashboard %s not found" % name)
        objects_parent_folder = os.path.dirname(dashboard_info['folder'])
        version_parent_folder = os.path.basename(objects_parent_folder)

        self._copy_object(beattype, dashboard_info['id'],'dashboard', objects_parent_folder, '/tmp/fbt/%s' % version_parent_folder)
        self._do_dashboard_setup(beattype, namespace, '/tmp/fbt')


    def _do_dashboard_setup(self, beattype, namespace, foldername):
        """
        Perform dashboard setup for beat
        """
        setup_command=["%s" % beattype, "setup",
                       "-E", "output.elasticsearch.username=%s" % self.__api_username,
                       "-E", "output.elasticsearch.password=%s" % self.__api_password,
                       "-E", "setup.kibana.space.id=%s" % namespace,
                       "-E", "setup.kibana.host=%s" % self.__kibana_endpoint,
                       "-E", "setup.dashboards.directory=%s" % foldername,
                       "--dashboards"]
        if not self.__ssl_verify:
            setup_command.append("-E")
            setup_command.append('setup.kibana.ssl.verification_mode=none')

        rc, stdout, stderr = self.ansible_module.run_command(
           setup_command, check_rc=True)
        if 'error importing' in stdout:
            raise Exception(stdout)

    #endregion

    #region Keystore method
    def get_beat_keystore_path(self, beattype):
        return os.path.join("/var/lib/%sbeat/" % beattype, "%sbeat.keystore" % beattype)

    def is_beat_keystore_present(self, beattype):
        ''' Check for presence of beat keystore '''
        keystore_path = self.get_beat_keystore_path(beattype)

        if beattype not in ['heart', 'file', 'metric', 'audit']:
            raise Exception("Unsupported beat type")
        result = os.path.isfile(keystore_path)
        if not result:
            logging.debug("Keystore %s is not present", keystore_path)
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
                'mode': "0%s" % oct(keystore_stat.st_mode)[-3:],
                'group': getgrgid(keystore_stat.st_gid).gr_name
            }
        else:
            return {
                'exists': False
            }

    def create_beat_keystore(self, beattype):
        '''Create an empty beat keystore'''
        keystore_executable = "%sbeat keystore" % beattype
        create_command = keystore_executable
        create_command += " create"

        # Run the command to create a keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            create_command, check_rc=True)

        if 'created' not in stdout.lower():
            logging.error("Impossible to create the keystore RC %s | STDOUT %s | STDERR %s}", rc, stdout, stderr)
            raise Exception("Impossible to create the keystore")

    def add_beat_keystore_key(self, beattype, key, value):
        ''' Add key to beat keystore'''
        if not self.is_beat_keystore_present(beattype):
            self.create_beat_keystore(beattype)

        add_command = "%sbeat keystore add --stdin %s --force" % (beattype, key)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, data=value, check_rc=True)

        if 'keystore not found' in stdout.lower():
            raise Exception("Keystore not found")

    def delete_beat_keystore_key(self, beattype, key):
        ''' Add key to beat keystore'''

        remove_command = "%sbeat keystore remove %s" % (beattype, key)

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
        list_command = "{}beat keystore list".format(beattype)
        rc, stdout, stderr = self.ansible_module.run_command(
            list_command, check_rc=True)
        logging.debug("List command output RC %s | STDOUT %s | STDERR %s", rc, stdout.replace("\n", "\\n"), stderr.replace("\n", "\\n"))

        for line in stdout.splitlines():
            data.append(line)
        return data
    #endregion

    #region Modules method
    def list_beat_modules(self, beattype):
        ''' List enabled beat modules'''

        remove_command = "{}beat modules list".format(beattype)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            remove_command, check_rc=True)

        enabled_modules = []
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

        remove_command = "%sbeat modules enable %s" % (beattype, module)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            remove_command, check_rc=True)

    def disable_beat_module(self, beattype, module):
        ''' Enable beat modules'''

        remove_command = "%sbeat modules disable %s" % (beattype, module)

        # Run the command to aad a key to keystore
        rc, stdout, stderr = self.ansible_module.run_command(
            remove_command, check_rc=True)
    #endregion
