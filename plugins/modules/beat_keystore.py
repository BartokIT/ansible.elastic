#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Keystore Ansible module."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: beat_keystore

short_description: This module allow to manage the beats keystore.

version_added: "0.0.5"

description: This module allow to manage the beats keystore.

options:
    type:
        description: choose the keystore to be managed
        required: true
        type: str
        choices:
          - file
          - heart
          - metric
          - audit
    force:
        description: Force the overwrite of a key if it already exists.
        required: false
        type: bool
        default: false
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
        default: multiple
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
  bartokit.elastic.beat_keystore:
  credentials:
    elastic_password: p4SSw0rd.1nIti4l

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
credentials:
    description: The list of the key present in the keystore
    type: list
    returned: success
'''


from ..module_utils.base_module import BartokITAnsibleModule
from ..module_utils.beats_manager import BeatManager
import logging

# module's parameter
module_args = dict(
    type=dict(type='str', required=True, choices=['file', 'metric', 'audit', 'heart']),
    force=dict(type='bool', required=False, default=False),
    credentials=dict(type='dict', required=True, no_log=True),
    mode=dict(type='str', required=False, choices=['multiple', 'present', 'absent'], default='multiple')
)


class BartokITElasticsearchBeatKeystore(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super(BartokITElasticsearchBeatKeystore, self).__init__(parameter_name_with_mode='mode', parameter_name_with_items='credentials',
                                                                argument_spec=argument_spec, supports_check_mode=False,
                                                                log_file='ansible_beat_keystore.log')
        self.__em = BeatManager(self)

    def initialization(self, parameters_argument, parameters):
        """
        Initialize the module.

        Return the keys/values and set the behaviour of the base class
        """
        self.settings(compare_values=parameters['force'])
        self.__beat_type = parameters['type']

        return parameters[parameters_argument]

    def read_key(self, key):
        """Read keystore settings."""
        return 'UNKNOWN'

    def delete_key(self, key, current_value):
        """Delete keystore key."""
        logging.debug("Deleting key %s", key)
        return self.__em.delete_beat_keystore_key(self.__beat_type, key)

    def create_key(self, key, value):
        """Add keystore settings."""
        logging.debug("Adding key %s", key)
        return self.__em.add_beat_keystore_key(self.__beat_type, key, value,)

    def update_key(self, key, input_value, current_value):
        """Overwrite keystore settings."""
        logging.debug("Updating key %s", key)
        self.create_key(key, input_value)

    def describe_info_for_output(self):
        """Return information to print"""
        return {}

    def list_current_keys(self, input_keys):
        """Return the list of keys actually present."""
        current_keys = self.__em.list_beat_keystore_keys(self.__beat_type)
        logging.debug("Keys present are: %s", current_keys)
        return current_keys


def main():
    """Run module execution."""
    BartokITElasticsearchBeatKeystore(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
