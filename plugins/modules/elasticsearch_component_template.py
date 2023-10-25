#!/usr/bin/python
# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Keystore Ansible module."""

from __future__ import (absolute_import, division, print_function)
import copy
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
    user=dict(type='str', required=False, default='elastic', no_log=False),
    password=dict(type='str', required=False, default='', no_log=True),
    api_endpoint=dict(type='str', required=False,
                      default='https://localhost:9200', no_log=False),
    ssl_verify=dict(type='bool', required=False, default=True, no_log=False),
    components=dict(type='dict', required=True)
)



class BartokITElasticsearchComponentTemplate(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(mode='multiple', parameter_name_with_keys='components',
                         argument_spec=argument_spec, supports_check_mode=False,
                         log_file='ansible_elasticsearch_component_template.log')
        self.__em = ElasticManager(
                self,
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
            if current_keys[ckey]['component_template']['_meta'].get('managed', False) == True:
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
            value_copy['component_template']= {'template':value_copy.pop('template')}
            if 'settings' in value['template']:
                # initialize the settings index dictionary
                if 'index' not in value['template']['settings']:
                    value_copy['component_template']['template']['settings']['index'] = {}

                for setting in value['template']['settings'].keys():
                    # add all properties to index subkey
                    if setting.startswith('index.'):
                        setting_value = value_copy['component_template']['template']['settings'].pop(setting)
                        value_copy['component_template']['template']['settings']['index'][setting.replace('index.','')] = setting_value
                    elif setting == 'index':
                        continue
                    else:
                        setting_value = "%s" % value_copy['component_template']['template']['settings'].pop(setting)
                        value_copy['component_template']['template']['settings']['index'][setting] = setting_value

            value_copy['name']=key
            if '_meta' in value_copy:
                value_copy['component_template']['_meta'] = value_copy.pop('_meta')
            return value_copy
        else:
            return value

    def read_key(self, key):
        """Get a component template."""
        value =  self.__em.get_component_template(key)
        return value

    def delete_key(self, key, current_value):
        """Delete component key."""
        if current_value['component_template']['_meta'].get('managed', False) == True:
            return
        if key in ['data-streams-mappings', 'logs-mappings','logs-settings','metrics-mappings','metrics-settings','metrics-tsdb-settings','synthetics-mappings','synthetics-settings', 'ecs@dynamic_templates', '.deprecation-indexing-settings']:
            return
        else:
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
                if type(d1[k]) is dict:
                    if self.__find_differences(d1[k],d2[k], "%s -> %s" % (path, k) if path else k):
                        logging.debug("@@@@")
                        return True
                elif d1[k] != d2[k]:
                    result = [ "%s: " % path, " - %s : %s" % (k, d1[k]) , " + %s : %s" % (k, d2[k])]
                    logging.debug("\n".join(result))
                    return True
            else:
                logging.debug("%s%s as key not in d2\n" % ("%s: " % path if path else "", k))
                return True

        return False

    def compare_key(self, key, input_value, current_value):
        """ Compare two keys """

        difference_found =  self.__find_differences(input_value, current_value)
        if difference_found:
            logging.debug("Found differences for key {}".format(key))
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
