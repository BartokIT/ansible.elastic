#!/usr/bin/python
# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Keystore Ansible module."""

from __future__ import (absolute_import, division, print_function)
from ..module_utils.BaseModule import BartokITAnsibleModule
from ..module_utils.ElasticManager import ElasticManager
import logging
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_keystore

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.0.1"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''


# module's parameter
module_args = dict(
    password=dict(type='str', required=False, default='', no_log=True),
    force=dict(type='bool', required=False, default=False),
    credentials=dict(type='dict', required=True)
)


class BartokITElasticsearchKeystore(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(mode='multiple', parameter_name_with_keys='credentials',
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
        if self.__password_protected:
            return self.__em.delete_keystore_key(key, self.params['password'])
        else:
            return self.__em.delete_keystore_key(key)

    def create_key(self, key, value):
        """Add keystore settings."""
        if self.__password_protected:
            return self.__em.add_keystore_key(key, value, self.params['password'])
        else:
            return self.__em.add_keystore_key(key, value)


    def update_key(self, key, input_value, current_value):
        """Overwrite keystore settings."""
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
