#!/usr/bin/python
# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Info Ansible module."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: kibana_info

short_description: This module extract informations from an elasticsearch installation

version_added: "0.0.1"

description: This module extract informations from an elasticsearch installation

options:
    gather_subset:
        description:
          - Which information the module have got to extract
          - 'The allowed item for the parameter are: I(all), I(spaces)'
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
  bartokit.elastic.kibana_info:
  gather_subset:
    - spaces

'''

RETURN = r'''
# These are examples of possible return values
spaces:
    description: The informations about the spaces
    type: dict
    returned: success
'''

import requests
import logging
from ansible.module_utils.basic import AnsibleModule
from ..module_utils.kibana_manager import KibanaManager

# module's parameter
module_args = dict(
    user=dict(type='str', required=False, default='elastic', no_log=False),
    password=dict(type='str', required=False, default='', no_log=True),
    api_endpoint=dict(type='str', required=False,
                      default='https://localhost:5601', no_log=False),
    ssl_verify=dict(type='bool', required=False, default=True, no_log=False),
    gather_subset=dict(type='list', default=[
    ], choices=['all', 'spaces', 'data_views', 'features', 'health'], required=False, no_log=False, elements='str')
)


class BartokITElasticsearchInfo(AnsibleModule):
    def run(self):
        """Catch all the running errors to fail gracefully."""
        try:
            output_info = {}
            logging.basicConfig(filename='/tmp/' + 'kibana_info.log',
                level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

            km = KibanaManager(self,
                                rest_api_endpoint=self.params['api_endpoint'],
                                api_username=self.params['user'],
                                api_password=self.params['password'],
                                ssl_verify=self.params['ssl_verify'])
            gather_subset = self.params['gather_subset']
            not_allowed_parameters = list(
                set(gather_subset) - set(['all', 'spaces', 'health', 'features']))
            if len(not_allowed_parameters):
                self.fail_json(msg='Gather subset not allowed {}'.format(
                    not_allowed_parameters))
            try:
                if 'spaces' in gather_subset or 'all' in gather_subset:
                    output_info['spaces'] = km.get_spaces()
                if 'features' in gather_subset or 'all' in gather_subset:
                    output_info['features'] = km.get_features()
                if 'data_views' in gather_subset or 'all' in gather_subset:
                    output_info['data_views'] = km.get_data_views()
                if 'health' in gather_subset or 'all' in gather_subset:
                    output_info['health'] = km.get_health_info()
            except requests.exceptions.Timeout as exctimeout:
                self.exit_json(**{"error": "{}".format(exctimeout), "health": {"error": "timeout"}})
            except Exception as exc:
                self.exit_json(**{"error": "{}".format(exc)})
            self.exit_json(**output_info)
        except Exception as e:
            self.fail_json(msg=str(e))


def main():
    """Run module execution."""
    BartokITElasticsearchInfo(argument_spec=module_args).run()


if __name__ == '__main__':
    main()
