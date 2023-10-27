#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Component Templates Ansible module."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_component_template

short_description: This module allow to manage component templates of an Elasticsearch installation

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.0.1"

description: This module allow to manage component templates of an Elasticsearch installation

options:
    user:
        description:
          - The user used to connect with elasticsearch service
        required: false
        type: str
        default: elastic
    password:
        description:
          - The password used to connect with elasticsearch service
        required: false
        default: ''
        type: str

    api_endpoint:
        description:
          - The url used to connect with elasticsearch service
        required: false
        type: str
        default: 'https://localhost:9200'
    ssl_verify:
        description:
          - Choose to verify the ssl certificate or not
        required: false
        type: bool
        default: true
    components:
        description:
          - This is a key value dictionary containing as key the name of the component template and as value the specifications
          - 'The allowed keys for the subdictionary are: I(_meta) and/or I(template).'
          - 'The template key allow only three keys: I(settings), I(mapping) and I(aliases).'
        required: true
        type: dict
author:
    - BartoktIT (@BartokIT)
'''

EXAMPLES = r'''
# Ensure that the only component present in the cluster are the specified
- name: Ensure that the only key present is the bootstrap.password with an unprotected keystore
  bartokit.elastic.elasticsearch_component_template:
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
from ..module_utils.elastic_manager import ElasticManager
import logging

# module's parameter
module_args = dict(
    user=dict(type='str', required=False, default='elastic'),
    password=dict(type='str', required=False, default='', no_log=True),
    mode=dict(type='str', required=False, choiches=['multiple', 'present', 'absent'], default='multiple'),
    api_endpoint=dict(type='str', required=False, default='https://localhost:9200'),
    ssl_verify=dict(type='bool', required=False, default=True),
    components=dict(type='dict', required=True)
)


class BartokITElasticsearchComponentTemplate(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(parameter_name_with_mode='mode', parameter_name_with_keys='components',
                         argument_spec=argument_spec, supports_check_mode=False,
                         log_file='ansible_elasticsearch_component_template.log')
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

    def initialization(self, parameter_name_with_keys, parameters):
        """Initialize the base class."""
        return parameters[parameter_name_with_keys]

    def pre_crud(self, current_keys):
        # Remove from the list the key managed by the system
        for ckey in current_keys.keys():
            if current_keys[ckey]['component_template']['_meta'].get('managed', False) is True:
                if ckey in self._to_be_added:
                    self._to_be_added.remove(ckey)
                if ckey in self._to_be_removed:
                    self._to_be_removed.remove(ckey)
                if ckey in self._to_be_updated:
                    self._to_be_updated.remove(ckey)
        return False

    def transform_key(self, key, value, type):
        """Perform value sanitization"""
        if type == 'input':
            value_copy = copy.deepcopy(value)
            value_copy['component_template'] = {'template': value_copy.pop('template')}
            if 'settings' in value['template']:
                # initialize the settings index dictionary
                if 'index' not in value['template']['settings']:
                    value_copy['component_template']['template']['settings']['index'] = {}

                for setting in value['template']['settings'].keys():
                    # add all properties to index subkey
                    if setting.startswith('index.'):
                        setting_value = value_copy['component_template']['template']['settings'].pop(setting)
                        value_copy['component_template']['template']['settings']['index'][setting.replace('index.', '')] = setting_value
                    elif setting == 'index':
                        continue
                    else:
                        setting_value = "%s" % value_copy['component_template']['template']['settings'].pop(setting)
                        value_copy['component_template']['template']['settings']['index'][setting] = setting_value

            value_copy['name'] = key
            if '_meta' in value_copy:
                value_copy['component_template']['_meta'] = value_copy.pop('_meta')
            return value_copy
        else:
            return value

    def read_key(self, key):
        """Get a component template."""
        value = self.__em.get_component_template(key)
        return value

    def delete_key(self, key, current_value):
        """Delete component key."""
        self.__em.delete_component_templates(key)

    def create_key(self, key, value):
        """Add a component template."""
        self.update_key(key, value, None)

    def update_key(self, key, input_value, current_value):
        """Update a component template."""
        value_detach = copy.deepcopy(input_value)
        value_detach.pop('name')
        if '_meta' in value_detach['component_template']:
            value_detach['component_template']['template']['_meta'] = value_detach['component_template']['_meta']

        self.__em.put_component_templates(key, **value_detach['component_template']['template'])

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
        components = self.__em.get_component_templates()
        return components


def main():
    """Run module execution."""
    BartokITElasticsearchComponentTemplate(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
