from __future__ import (absolute_import, division, print_function)
import logging
import os
import re
__metaclass__ = type


class LogstashManager:
    def __init__(self,
                 ansible_module,
                 rest_api_endpoint=None):
        self.ansible_module = ansible_module
        self._rest_api_endpoint = rest_api_endpoint.rstrip('/') + '/'
        self.__bin_path = '/usr/share/logstash/bin/'
        self.__keystore_path = '/etc/logstash'
        self.__keystore_executable = os.path.join(
            self.__bin_path, 'logstash-keystore')
        logging.debug("----- Manager initializated ---------")

    # ------------------ Kibana keystore methods------------------------
    def set_keystore_path(self, keystore_path):
        """Set the keystore path"""
        self.__keystore_path = keystore_path

    def is_keystore_present(self):
        """
        Check if a keystore exists by checking the file existence
        """
        keystore_file = os.path.join(self.__keystore_path, "logstash.keystore" )
        result = os.path.isfile(keystore_file)
        if not result:
            logging.debug("Keystore %s is not present" % keystore_file)
        return result

    def create_keystore(self, keystore_password=None):
        """
        Create the keystore
        """

        create_command = "{} --path.settings {} create".format(self.__keystore_executable, self.__keystore_path)
        logging.info("Creating the keystore on %s" % self.__keystore_path)
        if keystore_password:
            env_dict = {'LOGSTASH_KEYSTORE_PASS': keystore_password}
        rc, stdout, stderr = self.ansible_module.run_command(
            create_command, environ_update=env_dict, check_rc=True)
        if 'created' not in stdout.lower():
            raise Exception("Impossible to create the keystore")
        return True

    def list_keystore_keys(self, keystore_password=None):
        list_command = "{} --path.settings {} list".format(self.__keystore_executable, self.__keystore_path)

        if not self.is_keystore_present():
            return []

        env_dict = {}
        if keystore_password:
            env_dict = {'LOGSTASH_KEYSTORE_PASS': keystore_password}

        rc, stdout, stderr = self.ansible_module.run_command(
            list_command, environ_update=env_dict, check_rc=True)
        parts = stdout.split("\n\n")
        return parts[1].strip().splitlines() if len(parts) > 1 else []

    def add_keystore_key(self, key, value, keystore_password=None, force=False):
        """Add keystore settings."""

        if not self.is_keystore_present():
            self.create_keystore(keystore_password)

        data = value
        add_command = "{} --path.settings {} add {}".format(self.__keystore_executable, self.__keystore_path, key)

        add_command += " %s" % key
        if force:
            add_command += " --force"

        env_dict = {}
        if keystore_password:
            env_dict = {'LOGSTASH_KEYSTORE_PASS': keystore_password}

        rc, stdout, stderr = self.ansible_module.run_command(
            add_command, environ_update=env_dict, check_rc=True, data=data)

        if 'keystore not found' in stdout.lower():
            return False

    def delete_keystore_key(self, key, keystore_password=None):
        """Delete keystore key."""

        delete_command = "{} --path.settings {} remove {}".format(self.__keystore_executable, self.__keystore_path, key)

        env_dict = {}
        if keystore_password:
            env_dict = {'LOGSTASH_KEYSTORE_PASS': keystore_password}

        rc, stdout, stderr = self.ansible_module.run_command(
            delete_command, environ_update=env_dict, check_rc=True)