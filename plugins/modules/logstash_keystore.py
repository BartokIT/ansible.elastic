#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""logstash Keystore Ansible module."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: logstash_keystore

short_description: This module allow to manage the logstash keystore.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.1.4"

author:
    - BartoktIT (@BartokIT)

description: This module allow to manage the logstash keystore.

options:
    force:
        description: Force the overwrite of a key if it already exists.
        required: false
        type: bool
    credentials:
        description:
          - This is a key value dictionary containing the key of the keystore and the corresponde value.
        required: true
        type: dict
    mode:
        description:
          - Set the behaviour of the module.
          - If multiple then the credentials specified will be the only present inside the keystore
          - If present the module ensure that the credentials specified will be present
          - If absent the specified credentials will be removed.
        required: false
        type: str
        choices:
          - multiple
          - present
          - absent
author:
    - BartoktIT (@BartokIT)
'''

EXAMPLES = r'''
# Ensure that the only key present is the bootstrap.password with an unprotected keystore
- name: Ensure that the only key present is the bootstrap.password with an unprotected keystore
  bartokit.elastic.logstash_keystore:
  credentials:
    bootstrap.password: p4SSw0rd.1nIti4l

# Ensure that the credentials specified are inside the keystore
- name: Add the
  bartokit.elastic.logstash_keystore:
  credentials:
    bootstrap.password: p4SSw0rd.1nIti4l
    keystore.seed: 'J=Z4Y50EUvoAUS?^rQ_@'
  mode: present

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
credentials:
    description: The list of the key present in the keystore
    type: list
    returned: success
'''


from ..module_utils.base_module import BartokITAnsibleModule
from ..module_utils.logstash_manager import LogstashManager
import logging

# module's parameter
module_args = dict(
    force=dict(type='bool', required=False, default=False),
    keystore_path=dict(type='str', required=False, default='/etc/logstash'),
    keystore_password=dict(type='str', required=False, default=None, no_log=True),
    credentials=dict(type='dict', required=True),
    mode=dict(type='str', required=False, choiches=['multiple', 'present', 'absent'], default='multiple')
)


class BartokITLogstashKeystore(BartokITAnsibleModule):
    """A class for an Ansible module that manage logstash Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(parameter_name_with_mode='mode', parameter_name_with_items='credentials',
                         argument_spec=argument_spec, supports_check_mode=False,
                         log_file='ansible_logstash_keystore.log')
        self.__lm = LogstashManager(self, 'https://localhost:9200')

    def initialization(self, parameters_argument, parameters):
        """
        Initialize the module.

        Return the keys/values and set the behaviour of the base class
        """
        self.__lm.set_keystore_path(parameters['keystore_path'])
        self.__keystore_password=parameters['keystore_password']
        self.settings(compare_values=parameters['force'])
        return parameters[parameters_argument]

    def read_key(self, key):
        """Read keystore settings."""
        return "****"

    def delete_key(self, key, current_value):
        """Delete keystore key."""
        logging.debug("Deleting key %s", key)
        return self.__lm.delete_keystore_key(key, self.__keystore_password)

    def create_key(self, key, value):
        """Add keystore settings."""
        return self.__lm.add_keystore_key(key, value, self.__keystore_password)

    def update_key(self, key, input_value, current_value):
        """Overwrite keystore settings."""
        logging.debug("Updating key %s", key)
        return self.__lm.add_keystore_key(key, input_value, self.__keystore_password, True)

    def list_current_keys(self, input_keys):
        """Return the list of keys actually present."""
        return self.__lm.list_keystore_keys( self.__keystore_password)


def main():
    """Run module execution."""
    BartokITLogstashKeystore(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
