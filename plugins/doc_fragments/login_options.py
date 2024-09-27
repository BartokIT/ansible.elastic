# Copyright: (c) 2023, BartoktIT
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    # Standard documentation
    DOCUMENTATION = r'''
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
'''
