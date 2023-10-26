#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Keystore Ansible module."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_keystore

short_description: This module allow to manage the elasticsearch keystore.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.0.1"

description: This module allow to manage the elasticsearch keystore.

options:
    password:
        description:
          - This is the password protecting the keystore.
          - If the keystore is not password protected it will be securized with the password provided.
        required: false
        type: str
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
  bartokit.elastic.elasticsearch_keystore:
  credentials:
    bootstrap.password: p4SSw0rd.1nIti4l

# Ensure that the credentials specified are inside the keystore
- name: Add the
  bartokit.elastic.elasticsearch_keystore:
  password: kE1st0re.pass
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
protected:
    description: It the keystore is protected or not
    type: bool
    returned: success
'''


from ..module_utils.BaseModule import BartokITAnsibleModule
from ..module_utils.ElasticManager import ElasticManager
import logging

# module's parameter
module_args = dict(
    password=dict(type='str', required=False, default='', no_log=True),
    force=dict(type='bool', required=False, default=False),
    credentials=dict(type='dict', required=True),
    mode=dict(type='str', required=False, choiches=['multiple', 'present', 'absent'], default='multiple')
)


class BartokITElasticsearchKeystore(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(parameter_name_with_mode='mode', parameter_name_with_keys='credentials',
                         argument_spec=argument_spec, supports_check_mode=False,
                         log_file='ansible_elasticsearch_keystore.log')
        self.__em = ElasticManager(self, 'https://localhost:9200')
        self.__password_protected = False

    def is_password_protected(self):
        return self.__em.is_keystore_password_protected()

    def initialization(self, parameters_argument, parameters):
        """
        Initialize the module.

        Return the keys/values and set the behaviour of the base class
        """
        self.settings(compare_values=parameters['force'])
        self.__password_protected = self.is_password_protected()
        return parameters[parameters_argument]

    def pre_run(self):
        """Execute actions before the manage of the keys."""

        if not self.__password_protected:
            # Protect the keystore with the specified password
            self.__em.set_keystore_password(self.params['password'])
            self.__password_protected = self.is_password_protected()
            logging.debug("Changed elasticsearch keystore to password protected")
            return True
        else:
            # verify if the password is correct
            pass

        return False

    def read_key(self, key):
        """Read keystore settings."""
        if self.__password_protected:
            return self.__em.get_keystore_key(key, self.params['password'])
        else:
            return self.__em.get_keystore_key(key)

    def delete_key(self, key, current_value):
        """Delete keystore key."""
        logging.debug("Deleting key %s" % key)
        if self.__password_protected:
            return self.__em.delete_keystore_key(key, self.params['password'])
        else:
            return self.__em.delete_keystore_key(key)

    def create_key(self, key, value):
        """Add keystore settings."""
        logging.debug("Adding key %s" % key)
        if self.__password_protected:
            return self.__em.add_keystore_key(key, value, self.params['password'])
        else:
            return self.__em.add_keystore_key(key, value)

    def update_key(self, key, input_value, current_value):
        """Overwrite keystore settings."""
        logging.debug("Updating key %s" % key)
        if self.__password_protected:
            return self.__em.update_keystore_key(key, input_value, self.params['password'])
        else:
            return self.__em.update_keystore_key(key, input_value)

    def describe_info_for_output(self):
        """Return information to print"""
        return {'protected': self.__password_protected}

    def list_current_keys(self, input_keys):
        """Return the list of keys actually present."""
        if self.__password_protected:
            return self.__em.list_keystore_password(self.params['password'])
        else:
            return self.__em.list_keystore_password()


def main():
    """Run module execution."""
    BartokITElasticsearchKeystore(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
