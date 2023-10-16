#!/usr/bin/python
# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Keystore Ansible module."""

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ElasticManager import ElasticManager
import os.path
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
    gather_subset=dict(type='list', choiches=['license'], default=[
    ], required=False, no_log=False, elements='str')
)


class BartokITElasticsearchInfo(AnsibleModule):
    def run(self):
        """Catch all the running errors to fail gracefully."""
        try:
            output_info = {}
            em = ElasticManager(
                self,
                rest_api_endpoint=self.params['api_endpoint'],
                    api_username=self.params['user'],
                    api_password=self.params['password'],
                    ssl_verify=self.params['ssl_verify'])
            gather_subset = self.params['gather_subset']
            not_allowed_parameters = list(
                set(gather_subset) - set(['all', 'license', 'nodes', 'health', 'cluster_health']))
            if len(not_allowed_parameters):
                self.fail_json(msg='Gather subset not allowed {}'.format(
                    not_allowed_parameters))

            if 'license' in gather_subset or 'all' in gather_subset:
                output_info['license'] = em.get_license_info()
            if 'nodes' in gather_subset or 'all' in gather_subset:
                output_info['nodes'] = em.get_nodes_info()
            if 'health' in gather_subset or 'all' in gather_subset:
                output_info['health'] = em.get_health_info()
            if 'cluster_health' in gather_subset or 'all' in gather_subset:
                output_info['cluster_health'] = em.get_cluster_health_info()

            self.exit_json(**output_info)
        except Exception as e:
            self.fail_json(msg=str(e))


def main():
    """Run module execution."""
    BartokITElasticsearchInfo(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
