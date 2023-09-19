#!/usr/bin/python
# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Keystore Ansible module."""

from __future__ import (absolute_import, division, print_function)
from ..module_utils.BaseModule import BartokITAnsibleModule
import os.path
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
    force=dict(type='bool', required=False, default=False),
    credentials=dict(type='dict', required=True)
)


class BartokITElasticsearchKeystore(BartokITAnsibleModule):
    """A class for an Ansible module that manage Elasticsearch Keystore."""

    def __init__(self, module_args):
        """Call the constructor of the parent class."""
        super().__init__(mode='present', parameters_argument='credentials',
                         module_args=module_args, supports_check_mode=False)
        self.__bin_path = '/usr/share/elasticsearch/bin/'
        self.__keystore_executable = os.path.join(
            self.__bin_path, 'elasticsearch-keystore')

    def initialization(self, parameters_argument, parameters):
        """
        Initialize the module.

        Return the keys/values and set the behaviour of the base class
        """
        self.settings(compare_values=parameters['force'])
        return parameters[parameters_argument]

    def read_key(self, key):
        """Read keystore settings."""
        read_command = "{} show {}".format(
            self.__keystore_executable, key)
        rc, stdout, stderr = self.run_command(
            read_command, check_rc=True)
        return stdout

    def create_key(self, key, value):
        """Add keystore settings."""
        add_command = "{} add --stdin {}".format(
            self.__keystore_executable, key)
        rc, stdout, stderr = self.run_command(
            add_command, check_rc=True, data=value)

    def update_key(self, key, input_value, current_value):
        """Add keystore settings."""
        add_command = "{} add --force --stdin {}".format(
            self.__keystore_executable, key)
        rc, stdout, stderr = self.run_command(
            add_command, check_rc=True, data=input_value)

    def list_current_keys(self, input_keys):
        """Return the list of keys actually present."""
        list_command = "{} list".format(self.__keystore_executable)
        rc, stdout, stderr = self.run_command(list_command, check_rc=True)
        return stdout.splitlines()


def main():
    """Run module execution."""
    BartokITElasticsearchKeystore(module_args=module_args).run()


if __name__ == '__main__':
    main()