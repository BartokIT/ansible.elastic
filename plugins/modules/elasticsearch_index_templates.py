#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Component Templates Ansible module."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_index_template

short_description: This module allow to manage index templates of an Elasticsearch installation

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.0.2"

author:
    - BartoktIT (@BartokIT)

description: This module allow to manage index templates of an Elasticsearch installation

options:
    templates:
        description:
          - This is a key value dictionary containing as key the name of the component template and as value the specifications
          - 'The allowed keys for the subdictionary are: I(index_patterns), I(composed_of), I(data_stream), I(_meta), I(priority) or I(template).'
        required: true
        type: dict
extends_documentation_fragment:
  - bartokit.elastic.login_options
'''

EXAMPLES = r'''
# Ensure that the only component present in the cluster are the specified
- name: Create two templates
  bartokit.elastic.elasticsearch_index_template:
  templates:
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
templates:
    description: The list of the components present in the cluster
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
    templates=dict(type='dict', required=True)
)


class BartokITElasticsearchIndexTemplate(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(parameter_name_with_mode='mode', parameter_name_with_items='templates',
                         argument_spec=argument_spec, supports_check_mode=False,
                         log_file='ansible_elasticsearch_index_template.log')
        self.__em = ElasticManager(self,
                                   rest_api_endpoint=self.params['api_endpoint'],
                                   api_username=self.params['user'],
                                   api_password=self.params['password'],
                                   ssl_verify=self.params['ssl_verify'])

    def initialization(self, parameters_argument, parameters):
        """
        Initialize the module.

        Return the keys/values and set the behaviour of the base class
        """
        self.settings(compare_values=parameters['force'])
        return parameters[parameters_argument]

    def initialization(self, parameter_name_with_items, parameters):
        """Initialize the base class."""
        return parameters[parameter_name_with_items]

    def pre_crud(self, current_keys):
        # Remove from the list the key managed by the system
        for ckey in current_keys.keys():
            if ckey in ['behavioral_analytics-events-default', 'synthetics', 'ilm-history', 'metrics', 'logs']:
                if ckey in self._to_be_added:
                    self._to_be_added.remove(ckey)
                if ckey in self._to_be_removed:
                    self._to_be_removed.remove(ckey)
                if ckey in self._to_be_updated:
                    self._to_be_updated.remove(ckey)
        return False

    def transform_key(self, key, value, key_type):
        """Perform value sanitization"""
        if key_type == 'input':
            value_copy = copy.deepcopy(value)
            if 'template' in value_copy:
                value_copy['index_template'] = {'template': value_copy.pop('template')}
            transformed_value = {'name': key, 'index_template': copy.deepcopy(value)}
            # create an index key between the settings
            if 'template' in transformed_value['index_template'] and \
               'settings' in transformed_value['index_template']['template']:

                settings_swp = transformed_value['index_template']['template'].pop('settings')
                if 'index' not in settings_swp:
                    settings_swp['index'] = {}
                settings_key = list(settings_swp.keys())
                for setting in settings_key:
                    if setting.startswith('index.'):
                        setting_value = settings_swp.pop(setting)
                        settings_swp['index'][setting.replace('index.', '')] = setting_value
                    elif setting == 'index':
                        continue
                    else:
                        setting_value = "%s" % settings_swp.pop(setting)
                        settings_swp['index'][setting] = setting_value
                transformed_value['index_template']['template']['settings'] = settings_swp
            return transformed_value

        else:
            return value

    def read_key(self, key):
        """Get a component template."""
        value = self.__em.get_index_template(key)
        return value

    def delete_key(self, key, current_value):
        """Delete component key."""
        self.__em.delete_index_templates(key)

    def create_key(self, key, value):
        """Add a component template."""
        self.update_key(key, value, None)

    def update_key(self, key, input_value, current_value):
        """Update a component template."""
        value_detach = copy.deepcopy(input_value)
        value_detach = input_value['index_template']
        self.__em.put_index_templates(key, **value_detach)

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

        difference_found = self.__find_differences(input_value, current_value)
        if difference_found:
            logging.debug("Found differences for key %s", key)
        return difference_found

    def list_current_keys(self, input_keys):
        """Return the list of components template actually present."""
        components = self.__em.get_index_templates()
        return components


def main():
    """Run module execution."""
    BartokITElasticsearchIndexTemplate(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
