#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Component Templates Ansible module."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_ingest_pipelines

short_description: This module allow to managepipeline of an Elasticsearch installation

version_added: "0.0.14"

author:
    - BartoktIT (@BartokIT)

description: This module allow to manage pipeline of an Elasticsearch installation

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
  bartokit.elastic.elasticsearch_pipeline:
  pipelines:
    pipeline1:
        description: 'a new fresh pipeline'
        processors:
          - set:
              description : "My optional processor description"
              field: "my-keyword-field"
              value: "foo"

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
  pipelines:
    description: The list of the pipelines present in the cluster
    type: list
    returned: always
'''

import copy
from ..module_utils.base_module import BartokITAnsibleModule
from ..module_utils.elastic_manager import ElasticManager
from ..module_utils.beats_manager import BeatManager
import logging


# module's parameter
module_args = dict(
    user=dict(type='str', required=False, default='elastic'),
    password=dict(type='str', required=False, default='', no_log=True),
    api_endpoint=dict(type='str', required=False, default='https://localhost:9200'),
    ssl_verify=dict(type='bool', required=False, default=True),
    mode=dict(type='str', required=False, choiches=['present'], default='present'),
    beats=dict(type='list', required=True)
)


class BartokITIMBeatsSetup(BartokITAnsibleModule):
    """A class for an Ansible module that manage setup of beats."""

    def __init__(self, argument_spec):
        """Call the constructor of the parent class."""
        super().__init__(parameter_name_with_mode='mode', parameter_name_with_items='beats',
                         argument_spec=argument_spec, supports_check_mode=False,
                         items_type='list', log_file='beat_index_management_setup.log')

        self.__em = ElasticManager(self,
                                   rest_api_endpoint=self.params['api_endpoint'],
                                   api_username=self.params['user'],
                                   api_password=self.params['password'],
                                   ssl_verify=self.params['ssl_verify'])
        self.__bm = BeatManager(self,
                                   rest_api_endpoint=self.params['api_endpoint'],
                                   api_username=self.params['user'],
                                   api_password=self.params['password'],
                                   ssl_verify=self.params['ssl_verify'])

    def initialization(self, parameter_name_with_items, parameters):
        """Initialize the base class."""
        return parameters[parameter_name_with_items]

    def transform_key(self, key, value, key_type):
        """Perform value sanitization"""
        if key_type == 'input':
            value_copy = copy.deepcopy(value)
            return value_copy

        else:
            return value

    def read_key(self, key):
        """Get a beat index management."""
        return {'name': key, 'version': self.__bm.get_beat_version(key)}

    def delete_key(self, key, current_value):
        """Delete index management key."""
        pass

    def create_key(self, key, value):
        """Add a index management."""
        self.__bm.do_index_management_setup(key)

    def update_key(self, key, input_value, current_value):
        """Update a index management."""
        pass

    def __find_differences(self, d1, d2, path=""):
        for k in d1:
            if k in d2:
                if isinstance(d1[k], dict):
                    if self.__find_differences(d1[k], d2[k], "%s -> %s" % (path, k) if path else k):
                        return True
                elif d1[k] != d2[k]:
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
        """Return the list of index management actually present."""
        index_templates = self.__em.get_index_templates(only_beats=True)
        versions = {}
        components = []
        for beattype in input_keys:
            versions[beattype] = self.__bm.get_beat_version(beattype)
        for beattype in input_keys:
            index_template_name = "%s-%s" % (beattype, versions[beattype])
            if  index_template_name in index_templates:
                components.append(beattype)
        return components


def main():
    """Run module execution."""
    BartokITIMBeatsSetup(argument_spec=module_args).run()


if __name__ == '__main__':
    main()

