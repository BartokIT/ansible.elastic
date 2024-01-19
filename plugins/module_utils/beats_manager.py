#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
from grp import getgrgid
import logging
from pwd import getpwuid
import os


class BeatManager:
    def __init__(self, ansible_module):
        self.ansible_module = ansible_module
        logging.debug("----- Manager initializated ---------")

    # BEATS
    def get_beat_keystore_path(self, beattype):
        return os.path.join("/var/lib/%sbeat/" % beattype, "%sbeat.keystore"% beattype)

    def is_beat_keystore_present(self, beattype):
        ''' Check for presence of beat keystore '''
        keystore_path = self.get_beat_keystore_path(beattype)

        if beattype not in ['heart', 'file', 'metric','audit']:
            raise Exception("Unsupported beat type")
        result = os.path.isfile(keystore_path)
        if not result:
            logging.debug("Keystore %s is not present" % keystore_path)
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
                'mode': "0%s" % oct(keystore_stat.st_mode) [-3:],
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
            logging.error("Impossible to create the keystore RC %s | STDOUT %s | STDERR %s}" % (rc, stdout, stderr))
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
        list_command =  "{}beat keystore list".format(beattype)
        rc, stdout, stderr = self.ansible_module.run_command(
            list_command, check_rc=True)
        logging.debug("List command output RC %s | STDOUT %s | STDERR %s" % (rc, stdout.replace("\n","\\n"), stderr.replace("\n","\\n")))

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



 