# Copyright: (c) 2022, BartokIT <bartokit@tutanota.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""A module containing base Ansible module class."""
from __future__ import (absolute_import, division, print_function)
import copy
from ansible.module_utils.basic import AnsibleModule
from typing import Any
import logging
__metaclass__ = type


class BartokITAnsibleModule(AnsibleModule):
    """
    A class to represent a person.

    ...

    Attributes
    mode : str

    """

    def __init__(self, argument_spec, parameter_name_with_mode='mode', parameter_name_with_keys='keys', supports_check_mode=True, log_file=None):
        """
        Initialize the ansible modules.

        Parameters:
            mode (str): Can be one of present, absent or multiple and
                        influences the enforcing of keys
            parameter_key (str): A dictionary with key/values that sould be
                        present or not inside the resource

        """
        super().__init__(argument_spec=argument_spec, supports_check_mode=supports_check_mode)

        self.__changed = True
        self.__parameter_name_with_mode = parameter_name_with_mode
        self.__parameter_name_with_keys = parameter_name_with_keys
        self.behaviour = dict()
        self._to_be_added = []
        self._to_be_removed = []
        self._to_be_updated = []
        logging.basicConfig(filename='/tmp/' + log_file,
                            level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    def settings(self, compare_values=True, keys_to_be_skipped=None):
        """Set the module behaviour."""
        self.__compare_values = compare_values

    def initialization(self, parameter_name_with_keys, parameters):
        """Initialize the parameters."""
        return parameters[parameter_name_with_keys]

    # CRUD METHOD
    def create_key(self, key: str, new_value: Any):
        """Create the key."""
        raise Exception("Create key not implemented")

    def read_key(self, key):
        """Read a key's value."""
        raise Exception("Read key not implemented")

    def update_key(self, key, input_value, current_value):
        """Update a key's value."""
        raise Exception("Update key not implemented")

    def delete_key(self, key, current_value):
        """Delete a key."""
        raise Exception("Delete key not implemented")

    def transform_key(self, key, value, type):
        """Transform a key value input before modify operation."""
        return value

    def pre_run(self):
        """Execute actions before the manage of the keys."""
        return False

    def pre_crud(self, current_keys):
        """Execute actions before the manage of the keys."""
        return False

    def post_crud(self):
        """Execute actions after the manage of the keys."""
        return False

    # LIST OF KEYS
    def compare_key(self, key, input_value, current_value):
        """
        Compare a key's current value with the provided.

        Return:
            bool: True if values are different
        """
        if self.__compare_values:
            return input_value != current_value
        else:
            return False

    def list_current_keys(self, input_keys):
        """Return the list of keys actually present."""
        return []

    def list_input_keys(self):
        """Return the list of keys in input."""
        return self.__keys.keys()  # type: ignore

    def describe_info_for_output(self):
        """Return information to print"""
        return {}

    def _run(self):
        """Run the Ansible module."""

        # initialize the behaviour of the module
        if self.params[self.__parameter_name_with_mode] not in ['present', 'absent', 'multiple']:
            raise Exception("Mode %s not know" % self.params[self.__parameter_name_with_mode])
        self.mode = self.params[self.__parameter_name_with_mode]

        diff_before_output = {}
        diff_after_output = {}
        diff_before_keys = []
        diff_after_keys = []
        # initialization
        self.__keys = self.initialization(
            self.__parameter_name_with_keys, self.params)

        diff_before_output = copy.deepcopy(self.describe_info_for_output())
        self.__changed = self.pre_run()

        # store current keys to avoid get continuosly
        current_keys = self.list_current_keys(self.__keys)

        if self.mode == 'present':
            self._to_be_added = self.list_input_keys() - current_keys
            self._to_be_updated = list(set(current_keys) &
                                       set(self.list_input_keys()))
            diff_before_keys = set(current_keys).intersection(
                set(self.list_input_keys()))
        elif self.mode == 'absent':
            self._to_be_removed = self.list_input_keys()
            diff_before_keys = set(current_keys).intersection(
                set(self.list_input_keys()))
        else:
            self._to_be_added = self.list_input_keys() - current_keys
            self._to_be_removed = current_keys - self.list_input_keys()
            self._to_be_updated = list(set(current_keys) &
                                       set(self.list_input_keys()))
            diff_before_keys = current_keys

        # log
        # pre management hool
        self.__changed = True if self.pre_crud(current_keys) else self.__changed

        self._to_be_added and logging.debug(
            'Keys requested for add are: %s' % self._to_be_added)
        self._to_be_removed and logging.debug(
            'Keys requested for remove are: : %s' % self._to_be_removed)
        self._to_be_updated and logging.debug(
            'Keys requested for update are: %s' % self._to_be_updated)

        # delete keys
        if len(self._to_be_removed) > 0:
            self.__changed = True
            for key in self._to_be_removed:
                current_key_value = self.read_key(key)
                current_key_value = self.transform_key(key, current_key_value, 'current')
                self.delete_key(key, current_key_value)

        # add missing keys
        if len(self._to_be_added) > 0:
            self.__changed = True
            for key in self._to_be_added:
                input_key_value = self.transform_key(key, self.__keys[key], 'input')
                self.create_key(key, input_key_value)

        # update key only if input value differ from current value
        for key in self._to_be_updated:
            current_key_value = self.read_key(key)
            current_key_value = self.transform_key(key, current_key_value, 'current')
            input_key_value = self.transform_key(key, self.__keys[key], 'input')
            different = self.compare_key(
                key, input_key_value, current_key_value)
            if different:
                logging.debug("Key {} will be updated".format(key))
                self.__changed = True
                self.update_key(key, input_key_value, current_key_value)

        if self.post_crud():
            self.__changed = True

        after_run_keys = self.list_current_keys(self.__keys)
        if self.mode == 'present':
            diff_after_keys = set(after_run_keys).intersection(
                set(self.list_input_keys()))
        elif self.mode == 'absent':
            diff_after_keys = set(after_run_keys).intersection(
                set(self.list_input_keys()))
        else:
            diff_after_keys = after_run_keys

        # calculate key differences
        diff_before_keys = list(diff_before_keys)
        diff_after_keys = list(diff_after_keys)
        diff_before_keys.sort()
        diff_after_keys.sort()
        diff_after_output = copy.deepcopy(self.describe_info_for_output())
        diff_before_output.update(
            {self.__parameter_name_with_keys: diff_before_keys})
        diff_after_output.update(
            {self.__parameter_name_with_keys: diff_after_keys})
        result = {'diff': {'before': diff_before_output,
                           'after': diff_after_output}, 'changed': self.__changed}
        result.update(diff_after_output)
        self.exit_json(**result)

    def run(self):
        """Catch all the running errors to fail gracefully."""
        try:
            self._run()
        except Exception as e:
            self.fail_json(msg=str(e))
