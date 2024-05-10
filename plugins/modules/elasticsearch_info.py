#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Info Ansible module."""
from __future__ import (absolute_import, division, print_function)
import requests
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elasticsearch_info

short_description: This module extract informations from an elasticsearch installation

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.0.1"

description: This module extract informations from an elasticsearch installation

options:
    gather_subset:
        description:
          - Which information the module have got to extract
          - 'The allowed item for the parameter are: I(all), I(license), I(nodes), I(health), I(cluster_health), I(component_templates)'
        type: list
        elements: str
        default: []
extends_documentation_fragment:
  - bartokit.elastic.login_options
author:
    - BartoktIT (@BartokIT)
'''

EXAMPLES = r'''
# Extract information on health and license from the active server
- name: Ensure that the only key present is the bootstrap.password with an unprotected keystore
  bartokit.elastic.elasticsearch_info:
  gather_subset:
    - license
    - health
'''

RETURN = r'''
# These are examples of possible return values
license:
    description: The informations about the license
    type: dict
    returned: success
nodes:
    description: The informations about the nodes
    type: dict
    returned: success
health:
    description: The informations about the health
    type: dict
    returned: success
cluster_health:
    description: The informations about the cluster_health
    type: dict
    returned: success
component_templates:
    description: The informations about the component_templates
    type: dict
    returned: success
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.elastic_manager import ElasticManager

# module's parameter
module_args = dict(
    user=dict(type='str', required=False, default='elastic', no_log=False),
    password=dict(type='str', required=False, default='', no_log=True),
    api_endpoint=dict(type='str', required=False,
                      default='https://localhost:9200', no_log=False),
    ssl_verify=dict(type='bool', required=False, default=True, no_log=False),
    gather_subset=dict(type='list', default=[
    ], required=False, no_log=False, elements='str')
)


class BartokITElasticsearchInfo(AnsibleModule):
    def run(self):
        """Catch all the running errors to fail gracefully."""
        try:
            output_info = {}
            em = ElasticManager(self,
                                rest_api_endpoint=self.params['api_endpoint'],
                                api_username=self.params['user'],
                                api_password=self.params['password'],
                                ssl_verify=self.params['ssl_verify'])
            gather_subset = self.params['gather_subset']
            not_allowed_parameters = list(
                set(gather_subset) - set(['all', 'license', 'nodes', 'health', 'cluster_health', 'component_templates']))
            if len(not_allowed_parameters):
                self.fail_json(msg='Gather subset not allowed {}'.format(
                    not_allowed_parameters))
            try:
                if 'license' in gather_subset or 'all' in gather_subset:
                    output_info['license'] = em.get_license_info()
                if 'nodes' in gather_subset or 'all' in gather_subset:
                    output_info['nodes'] = em.get_nodes_info()
                if 'health' in gather_subset or 'all' in gather_subset:
                    output_info['health'] = em.get_health_info()
                if 'cluster_health' in gather_subset or 'all' in gather_subset:
                    output_info['cluster_health'] = em.get_cluster_health_info()
                if 'component_templates' in gather_subset or 'all' in gather_subset:
                    output_info['component_templates'] = em.get_component_templates()
            except requests.exceptions.Timeout:
                self.exit_json({"healt":{"error":"timeout"}})
            self.exit_json(**output_info)
        except Exception as e:
            self.fail_json(msg=str(e))


def main():
    """Run module execution."""
    BartokITElasticsearchInfo(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
