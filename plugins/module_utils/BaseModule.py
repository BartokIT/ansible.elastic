#!/usr/bin/python
# Copyright: (c) 2022, BartokIT <bartokit@tutanota.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""A module containing base Ansible module class."""
import copy
from ansible.module_utils.basic import AnsibleModule
from typing import Any
import logging


class BartokITAnsibleModule(AnsibleModule):
    """
    A class to represent a person.

    ...

    Attributes
    mode : str

    """

    def __init__(self, mode, module_args, parameter_name_with_keys='keys', supports_check_mode=True, log_file=None):
        """
        Initialize the ansible modules.

        Parameters:
            mode (str): Can be one of present, absent or multiple and
                        influences the enforcing of keys
            parameter_key (str): A dictionary with key/values that sould be
                        present or not inside the resource

        """
        super().__init__(argument_spec=module_args, supports_check_mode=supports_check_mode)
        if mode not in ['present', 'absent', 'multiple']:
            raise Exception("Mode %s not know" % mode)
        self.mode = mode
        self.__changed = True
        self.__parameter_name_with_keys = parameter_name_with_keys
        self.behaviour = dict()
        logging.basicConfig(filename='/tmp/' + log_file,
                            level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    def settings(self, compare_values=True):
        """Set the module behaviour."""
        self.__compare_values = compare_values

    def initialization(self, parameters_argument, parameters):
        """Initialize the parameters."""
        return parameters[parameters_argument]

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

    def pre_run(self):
        """Execute actions before the manage of the keys."""
        return False

    def pre_crud(self):
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
        to_be_added = []
        to_be_removed = []
        diff_before_output = {}
        diff_after_output = {}

        # initialization
        self.__keys = self.initialization(
            self.__parameter_name_with_keys, self.params)

        diff_before_output = copy.deepcopy(self.describe_info_for_output())
        self.__changed = self.pre_run()

        # store current keys to avoid get continuosly
        current_keys = self.list_current_keys(self.__keys)
        to_be_added = []
        to_be_removed = []
        to_be_updated = []
        diff_before_keys = []
        diff_after_keys = []

        if self.mode == 'present':
            to_be_added = self.list_input_keys() - current_keys
            to_be_updated = list(set(current_keys) &
                                 set(self.list_input_keys()))
            diff_before_keys = set(current_keys).intersection(
                set(self.list_input_keys()))
        elif self.mode == 'absent':
            to_be_removed = self.list_input_keys()
            diff_before_keys = set(current_keys).intersection(
                set(self.list_input_keys()))
        else:
            to_be_added = self.list_input_keys() - current_keys
            to_be_removed = current_keys - self.list_input_keys()
            to_be_updated = list(set(current_keys) &
                                 set(self.list_input_keys()))
            diff_before_keys = current_keys

        # log
        to_be_added and logging.debug(
            'Keys requested for add are: {}'.format(to_be_added))
        to_be_removed and logging.debug(
            'Keys requested for remove are: {}'.format(to_be_removed))
        to_be_updated and logging.debug(
            'Keys requested for updated are: {}'.format(to_be_updated))

        # pre management hool
        self.__changed = True if self.pre_crud() else self.__changed

        # delete keys
        for key in to_be_removed:
            self.delete_key(key, self.read_key(key))
        if len(to_be_removed) > 0:
            self.__changed = True

        # add missing keys
        for key in to_be_added:
            self.create_key(key, self.__keys[key])
        if len(to_be_added) > 0:
            self.__changed = True

        # update key only if input value differ from current value
        for key in to_be_updated:
            different = self.compare_key(
                key, self.__keys[key], self.read_key(key))
            if different:
                logging.debug("Key {} will be updated".format(key))
                self.__changed = True
                self.update_key(key, self.__keys[key], self.read_key(key))

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
