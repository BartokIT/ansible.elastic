#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Component Templates Ansible module."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_users

short_description: This module allow to manage user of an Elasticsearch installation

version_added: 0.0.2

author:
    - BartoktIT (@BartokIT)

description: This module allow to manage user of an Elasticsearch installation

options:
    users:
        description:
          - This is a key value dictionary containing as key the username of the usert and as value the specifications
          - 'The allowed keys for the subdictionary are: I(index_patterns), I(composed_of), I(data_stream), I(_meta), I(priority) or I(template).'
        required: true
        type: list
        elements: str
extends_documentation_fragment:
  - bartokit.elastic.login_options
'''

EXAMPLES = r'''
# Ensure that the only component present in the cluster are the specified
- name: Create two templates
  bartokit.elastic.elasticsearch_users:
  users:
    myuser:
        passowrd: notsoeasypass
        email: myuser@mydomain
        enable: true

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
users:
    description: The list of the users present in the cluster
    type: list
    returned: always
'''

import copy
from ..module_utils.base_module import BartokITAnsibleModule
from ..module_utils.elastic_manager import ElasticManager
import logging


# module's parameter
module_args = dict(
    user=dict(type='str', required=False, default='elastic'),
    password=dict(type='str', required=False, default='', no_log=True),
    api_endpoint=dict(type='str', required=False, default='https://localhost:9200'),
    ssl_verify=dict(type='bool', required=False, default=True),
    mode=dict(type='str', required=False, choiches=['multiple', 'present', 'absent'], default='multiple'),
    enforce_password=dict(type='bool', required=False, default=False),
    users=dict(type='list', required=True, no_log=False, elements='dict', options=dict(
        enabled=dict(type='bool', required=False, default=True),
        email=dict(type='str', required=False, default=None),
        full_name=dict(type='str', required=False, default=None),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        metadata=dict(type='dict', required=False, default={}),
        roles=dict(type='list', required=False, default=[])
    ))
)


class BartokITElasticsearchUsers(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super(BartokITElasticsearchUsers, self).__init__(parameter_name_with_mode='mode', parameter_name_with_items='users',
                         items_type='list', item_identifier_subkey_name='username',
                         argument_spec=argument_spec, supports_check_mode=False,
                         log_file='ansible_elasticsearch_users.log')
        self.__em = ElasticManager(self,
                                   rest_api_endpoint=self.params['api_endpoint'],
                                   api_username=self.params['user'],
                                   api_password=self.params['password'],
                                   ssl_verify=self.params['ssl_verify'])

    def initialization(self, parameter_name_with_items, parameters):
        """
        Initialize the module.

        Return the keys/values and set the behaviour of the base class
        """
        self.__enforce_password = parameters['enforce_password']
        logging.debug("Requested to enforce password: %s", self.__enforce_password)
        return parameters[parameter_name_with_items]

    def pre_crud(self, current_keys):
        # Remove from the list the key managed by the system
        return False

    def transform_key(self, key, value, key_type):
        """Perform value sanitization"""
        if key_type == 'input':
            value_copy = copy.deepcopy(value)
            if 'roles' not in value_copy or value_copy['roles'] is None:
                value_copy['roles'] = []
            if 'enabled' not in value_copy:
                value_copy['enabled'] = True
            if 'metadata' not in value_copy:
                value_copy['metadata'] = {}
            if not value_copy['full_name']:
                value_copy.pop('full_name')
            if not value_copy['email']:
                value_copy.pop('email')
            return value_copy
        else:
            if 'full_name' in value and value['full_name'] is None:
                value.pop('full_name')
            if 'email' in value and value['email'] is None:
                value.pop('email')

            return value

    def read_key(self, key):
        """Get a component template."""
        value = self.__em.get_user(key)
        return value

    def delete_key(self, key, current_value):
        """Delete component key."""
        self.__em.delete_user(key)

    def create_key(self, key, value):
        """Add a component template."""
        value_detach = copy.deepcopy(value)
        logging.debug(value_detach)
        if key not in self.__managed_users:
            self.__em.put_user(key, **value_detach)

    def update_key(self, key, input_value, current_value):
        """Update a component template."""
        value_detach = copy.deepcopy(input_value)
        value_detach.pop('password')
        logging.debug("Values %s", value_detach)
        if key not in self.__managed_users:
            self.__em.put_user(key, **value_detach)
        if self.__enforce_password:
            self.__em.set_user_password(key, input_value['password'])


    def __find_differences(self, d1, d2, path=""):
        for k in d1:
            if k in d2:
                if isinstance(d1[k], dict):
                    if self.__find_differences(d1[k], d2[k], "%s -> %s" % (path, k) if path else k):
                        logging.debug("@@@@")
                        return True
                elif d1[k] != d2[k]:
                    result = ["%s: " % path, " - %s : %s" % (k, d1[k]) , " + %s : %s" % (k, d2[k])]
                    logging.debug("\n".join(result))
                    return True
            else:
                logging.debug("%s%s as key not in d2\n" ,("%s: " % path if path else "", k))
                return True

        return False

    def compare_key(self, key, input_value, current_value):
        """ Compare two keys """

        input_value_detached = copy.deepcopy(input_value)
        input_value_detached.pop('password')
        difference_found = self.__find_differences(input_value_detached, current_value)
        if difference_found:
            logging.debug("Found differences for key %s", key)
        else:
            logging.debug("No differences found for key %s", key)
        return difference_found or self.__enforce_password

    def list_current_keys(self, input_keys):
        """Return the list of components template actually present."""
        components = self.__em.get_users()
        components_managed = self.__em.get_users(only_managed=True)
        differences = [value for value in input_keys if value in components_managed.keys()]
        logging.debug("Managed users found %s" % differences)
        self.__managed_users = []
        if differences:
            for key in differences:
                components[key]=components_managed[key]
                self.__managed_users.append(key)
        return components


def main():
    """Run module execution."""
    BartokITElasticsearchUsers(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
