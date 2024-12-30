#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Component Templates Ansible module."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: beat_dashboards_setup

short_description: This module allow to import beat dashboards into kibana

version_added: "0.1.2"

author:
    - BartoktIT (@BartokIT)

description: >-
  This module call the setup for the beat agent creating
  related dashboard

options:
    beats:
        description:
          - This is a dict with key as names of the dashboards wich setup is performed
          - The dict must be a dictionary with a namespaces name key containing a list where dashboard need to be imported
        required: true
        type: dict
extends_documentation_fragment:
  - bartokit.elastic.login_options
'''

EXAMPLES = r'''
# Ensure that the only component present in the cluster are the specified
- name: Perform metricbeat setup
  bartokit.elastic.beat_index_management_setup:
    dashboards:
      '[Metricbeat System] Containers overview ECS':
         namespaces:
           - default
           - testspace
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
  beats:
    description: The list of the dashboards with setup performed
    type: list
    returned: always
'''

import copy
from ..module_utils.base_module import BartokITAnsibleModule
from ..module_utils.kibana_manager import KibanaManager
from ..module_utils.beats_manager import BeatManager
import logging


# module's parameter
module_args = dict(
    user=dict(type='str', required=False, default='elastic'),
    password=dict(type='str', required=False, default='', no_log=True),
    api_endpoint=dict(type='str', required=False, default='https://localhost:5601'),
    ssl_verify=dict(type='bool', required=False, default=True),
    mode=dict(type='str', required=False, choices=['multiple', 'present', 'absent'], default='multiple'),
    dashboards=dict(type='dict', required=True)
)


class BartokITIMBeatsSetup(BartokITAnsibleModule):
    """A class for an Ansible module that manage setup of beats."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(parameter_name_with_mode='mode', parameter_name_with_items='dashboards',
                         argument_spec=argument_spec, supports_check_mode=False,
                         items_type='dict', log_file='beat_dashboards_setup.log')

        self.__km = KibanaManager(self,
                                   rest_api_endpoint=self.params['api_endpoint'],
                                   api_username=self.params['user'],
                                   api_password=self.params['password'],
                                   ssl_verify=self.params['ssl_verify'])
        self.__bm = BeatManager(self,
                                   kibana_endpoint=self.params['api_endpoint'],
                                   api_username=self.params['user'],
                                   api_password=self.params['password'],
                                   ssl_verify=self.params['ssl_verify'])
        self.__dashboard_map_cache = {}

    def transform_key(self, key, value, key_type):
        """Perform value sanitization"""
        if key_type == 'input':
            value_copy = copy.deepcopy(value)
            return value_copy

        else:
            return value

    def read_key(self, key):
        """Get a dashboards."""
        return self.__dashboard_map_cache[key]

    def delete_key(self, key, current_value):
        """Delete dashboards key."""
        for item in current_value['ids']:
            self.__km.delete_dashboard(item['namespace'],item['id'])

    def create_key(self, key, value):
        """Add a dashboards."""
        for ns in value['namespaces']:
            self.__bm.import_dashboard(key, ns)

    def update_key(self, key, input_value, current_value):
        """Update dashboards."""
        to_be_deleted = set(current_value['namespaces']) - set(input_value['namespaces'])
        to_be_added = set(input_value['namespaces']) - set(current_value['namespaces'])

        for cns in to_be_added:
            self.__bm.import_dashboard(key, cns)
        for cns in to_be_deleted:
            for item in current_value['ids']:
                if item['namespace'] == cns:
                    self.__km.delete_dashboard(item['namespace'],item['id'])


    def __find_differences(self, d1, d2, path=""):
        d1['namespaces'].sort()
        d2['namespaces'].sort()
        return d1['namespaces'] != d2['namespaces']

    def compare_key(self, key, input_value, current_value):
        """ Compare two keys """

        difference_found = self.__find_differences(input_value, current_value)
        if difference_found:
            logging.debug("Found differences for key %s", key)
        return difference_found

    def list_current_keys(self, input_keys):
        """Return the list of index management actually present."""
        _, dashboard_name_id_map  = self.__km.get_dashboards()
        metricbeat_dashboard_available = self.__bm.get_dashboard_list_with_file()
        metricbeat_dashboard_imported = set(dashboard_name_id_map.keys()).intersection(set(metricbeat_dashboard_available.keys()))
        self.__dashboard_map_cache = dashboard_name_id_map
        return metricbeat_dashboard_imported


def main():
    """Run module execution."""
    BartokITIMBeatsSetup(argument_spec=module_args).run()


if __name__ == '__main__':
    main()

