#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Kibana data_views Ansible module."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: kibana_dataviews

short_description: This module allow to manage data_views of an Kibana installation

version_added: "0.1.0"

author:
    - BartoktIT (@BartokIT)

description: This module allow to manage data_views of an Kibana installation

options:
    data_views:
        description:
          - This is a key value dictionary containing as key the name of the data_views and as value the specifications
          - 'The allowed keys for the subdictionary are: I(_meta) and/or I(template).'
          - 'The template key allow only three keys: I(settings), I(mapping) and I(aliases).'
        required: true
        type: dict
extends_documentation_fragment:
  - bartokit.elastic.login_options
'''

EXAMPLES = r'''
# Ensure that the only component present in the cluster are the specified
- name: Ensure that the only key present is the bootstrap.password with an unprotected keystore
  bartokit.elastic.kibana_data_views:
  components:
    template1:
        _meta:
            author: 'BartokIT'
    template2:
        template:
            mappings:
                properties:
                order_date:
                    type: 'date'
                    format: 'dd-MM-yyyy'
            settings:
                number_of_shards: 1

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
components:
    description: The list of the components present in the cluster
    type: list
    returned: always
'''

import copy
from ..module_utils.base_module import BartokITAnsibleModule
from ..module_utils.kibana_manager import KibanaManager
import logging

# module's parameter
module_args = dict(
    user=dict(type='str', required=False, default='elastic'),
    password=dict(type='str', required=False, default='', no_log=True),
    api_endpoint=dict(type='str', required=False, default='https://localhost:5601'),
    ssl_verify=dict(type='bool', required=False, default=True),
    mode=dict(type='str', required=False, choiches=['multiple', 'present', 'absent'], default='multiple'),
    data_views=dict(type='dict', required=True)
)


class BartokITKibanaDataViews(BartokITAnsibleModule):
    """A class for an Ansible module that manage Kibana Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(parameter_name_with_mode='mode', parameter_name_with_items='data_views',
                         argument_spec=argument_spec, supports_check_mode=False,
                         log_file='ansible_kibana_data_views.log')
        self.__km = KibanaManager(self,
                                   rest_api_endpoint=self.params['api_endpoint'],
                                   api_username=self.params['user'],
                                   api_password=self.params['password'],
                                   ssl_verify=self.params['ssl_verify'])
        self.__dataviews_map = {}
        self.__dataviews_cache = {}

    def initialization(self, parameter_name_with_items, parameters):
        """Initialize the base class."""
        return parameters[parameter_name_with_items]

    def pre_crud(self, current_keys):
        # Remove from the list the key managed by the system
        return False

    def transform_key(self, key, value, key_type):
        """Perform value sanitization"""
        if key_type == 'input':
            value = {'data_view':value}
        if 'default' not in value['data_view'].get('namespaces', {}):
            if 'namespaces' not in value['data_view']:
                value['data_view']['namespaces']=[]
            value['data_view']['namespaces'].append('default')
        return value

    def read_key(self, key):
        """Get a data_views."""
        # dvid = self.__dataviews_map[key]
        value = self.__km.get_data_view(key)
        return value

    def delete_key(self, key, current_value):
        """Delete role key."""
        self.__km.delete_data_view(key)

    def create_key(self, key, value):
        """Add a data_views."""
        value_detach = copy.deepcopy(value)
        self.__km.put_data_view(key, **value_detach)

    def update_key(self, key, input_value, current_value):
        """Update a data_views."""
        value_detach = copy.deepcopy(input_value)
        current_value['data_view']['namespaces'].sort()
        input_value['data_view']['namespaces'].sort()
        # It isn't possible to modify namespaces, you can only drop and recreate
        if current_value['data_view']['namespaces'] != input_value['data_view']['namespaces']:
            logging.debug(current_value['data_view']['namespaces'])
            self.__km.delete_data_view(key)
            self.__km.put_data_view(key, **value_detach)
        else:
            del value_detach['data_view']['namespaces']
            self.__km.update_data_view(key, **value_detach)

    def __find_differences(self, d1, d2, path=""):
        for k in d1:
            if k in d2:
                if isinstance(d1[k], dict):
                    if self.__find_differences(d1[k], d2[k], "%s -> %s" % (path, k) if path else k):
                        logging.debug("@@@@")
                        return True
                else:
                    if isinstance(d1[k], list):
                        d1[k].sort()
                    if isinstance(d2[k], list):
                        d2[k].sort()
                    if d1[k] != d2[k]:
                        result = ["%s: " % path, " - %s : %s" % (k, d1[k]) , " + %s : %s" % (k, d2[k])]
                        logging.debug("\n".join(result))
                        return True
            else:
                logging.debug("%s%s as key not in d2\n", "%s: " % path if path else "", k)
                return True

        return False

    def compare_key(self, key, input_value, current_value):
        """ Compare two keys """

        difference_found = self.__find_differences(input_value, current_value)
        if difference_found:
            logging.debug("Found differences for key %s", key)
        return difference_found

    def list_current_keys(self, input_keys):
        """Return the list of components template actually present."""
        data_views = self.__km.get_data_views()
        # self.__dataviews_cache, self.__dataviews_map = data_views
        return data_views


def main():
    """Run module execution."""
    BartokITKibanaDataViews(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
