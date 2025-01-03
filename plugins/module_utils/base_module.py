# Copyright: (c) 2022, BartokIT <bartokit@tutanota.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""A module containing base Ansible module class."""
from __future__ import (absolute_import, division, print_function)
import copy
import re
from ansible.module_utils.basic import AnsibleModule
import logging
__metaclass__ = type


class BartokITAnsibleModule(AnsibleModule):
    """
    A class to represent a person.

    ...

    Attributes
    mode : str

    """

    def __init__(self, argument_spec, parameter_name_with_mode='mode',
                 parameter_name_with_items='keys', items_type='dict',
                 item_identifier_subkey_name='name', supports_check_mode=True, log_file=None):
        """
        Initialize the ansible modules.

        Parameters:
            mode (str): Can be one of present, absent or multiple and
                        influences the enforcing of keys
            parameter_key (str): A dictionary with key/values that sould be
                        present or not inside the resource

        """
        super(BartokITAnsibleModule, self).__init__(
            argument_spec=argument_spec, supports_check_mode=supports_check_mode)

        self.__changed = True
        self.__parameter_name_with_mode = parameter_name_with_mode
        self.__parameter_name_with_items = parameter_name_with_items
        self.__items_type = items_type
        self.__item_identifier_subkey_name = item_identifier_subkey_name
        self.behaviour = dict()
        self._to_be_added = []
        self._to_be_removed = []
        self._to_be_updated = []
        self.__compare_values = True
        self.__keys_to_be_skipped = []
        self.exclude_skipped_only_if_not_present = False
        logging.basicConfig(filename='/tmp/' + log_file,
                            level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    def settings(self, compare_values=True, keys_to_be_skipped=None, exclude_skipped_only_if_not_present=False):
        """Set the module behaviour."""
        self.__compare_values = compare_values
        self.__keys_to_be_skipped = keys_to_be_skipped
        self.exclude_skipped_only_if_not_present=exclude_skipped_only_if_not_present

    def __list_or_dict_support(self, parameters):
        """Convert list or dictionary."""
        if self.__items_type == 'dict':
            pass
        elif self.__items_type == 'list':
            # cast list to dict
            dictionary_from_list = {}
            for _item in parameters[self.__parameter_name_with_items]:
                dictionary_from_list[_item[self.__item_identifier_subkey_name]] = _item
                _item.pop(self.__item_identifier_subkey_name)
            self.params[self.__parameter_name_with_items] = dictionary_from_list
        else:
            raise Exception("items type must be list or dict")

    def initialization(self, parameter_name_with_items, parameters):
        """Initialize the parameters and also the behaviour of the module."""
        self.settings(compare_values=True)
        return parameters[parameter_name_with_items]

    # CRUD METHOD
    def create_key(self, key, new_value):
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

    def pre_crud(self, current_keys, input_keys=None):
        """Execute actions before keys create, update or delete."""
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

    def filter_list_of_current_keys(self, input_keys):
        """Eventually filter current keys"""
        # TODO: add parameter to manage also input
        current_keys = self.list_current_keys(input_keys)
        if self.__keys_to_be_skipped:
            for current_key in current_keys.copy():
                for key_regex in self.__keys_to_be_skipped:
                    if ((current_key in input_keys and not self.exclude_skipped_only_if_not_present) or \
                        (current_key not in input_keys)) and re.match(key_regex, current_key):
                        logging.debug("Removing key %s" % current_key)
                        del current_keys[current_key]
        return current_keys


    def list_current_keys(self, input_keys):
        """Return the list of keys actually present."""
        return []

    def list_input_keys(self):
        """Return the list of keys in input."""
        return self.__input_keys.keys()  # type: ignore

    def describe_info_for_output(self):
        """Return information to print"""
        return {}

    def _run(self):
        """Run the Ansible module."""

        # initialize the behaviour of the module
        if self.params[self.__parameter_name_with_mode] not in ['present', 'absent', 'multiple']:
            raise Exception("Mode %s not know" %
                            self.params[self.__parameter_name_with_mode])
        self.mode = self.params[self.__parameter_name_with_mode]

        diff_before_output = {}
        diff_after_output = {}
        diff_before_keys = []
        diff_after_keys = []

        # initialization
        logging.debug("Start list transformation call")
        self.__list_or_dict_support(self.params)
        logging.debug("Start initialization call")
        self.__input_keys = self.initialization(
            self.__parameter_name_with_items, self.params)

        diff_before_output = copy.deepcopy(self.describe_info_for_output())
        self.__changed = self.pre_run()

        # store current keys to avoid get continuosly
        current_keys = self.filter_list_of_current_keys(self.__input_keys)

        if self.mode == 'present':
            self._to_be_added = list(
                set(self.list_input_keys()) - set(current_keys))
            self._to_be_updated = list(set(current_keys) &
                                       set(self.list_input_keys()))
            diff_before_keys = set(current_keys).intersection(
                set(self.list_input_keys()))
        elif self.mode == 'absent':
            self._to_be_removed = self.list_input_keys()
            diff_before_keys = set(current_keys).intersection(
                set(self.list_input_keys()))
        else:
            self._to_be_added = list(
                set(self.list_input_keys()) - set(current_keys))
            self._to_be_removed = list(
                set(current_keys) - set(self.list_input_keys()))
            self._to_be_updated = list(set(current_keys) &
                                       set(self.list_input_keys()))
            diff_before_keys = current_keys

        # log
        # pre management hook
        self.__changed = True if self.pre_crud(
            current_keys) else self.__changed

        self._to_be_added and logging.debug(
            'Keys requested for add are: %s', self._to_be_added)
        self._to_be_removed and logging.debug(
            'Keys requested for remove are: %s', self._to_be_removed)
        self._to_be_updated and logging.debug(
            'Keys requested for update are: %s', self._to_be_updated)

        # delete keys7
        if len(self._to_be_removed) > 0:
            self.__changed = True
            for key in self._to_be_removed:
                current_key_value = self.read_key(key)
                current_key_value = self.transform_key(
                    key, current_key_value, 'current')
                self.delete_key(key, current_key_value)

        # add missing keys
        if len(self._to_be_added) > 0:
            self.__changed = True
            for key in self._to_be_added:
                input_key_value = self.transform_key(
                    key, self.__input_keys[key], 'input')
                self.create_key(key, input_key_value)

        # update key only if input value differ from current value
        for key in self._to_be_updated:
            current_key_value = self.read_key(key)
            current_key_value = self.transform_key(
                key, current_key_value, 'current')
            input_key_value = self.transform_key(
                key, self.__input_keys[key], 'input')
            different = self.compare_key(
                key, input_key_value, current_key_value)
            if different:
                logging.debug("Key %s will be updated", key)
                self.__changed = True
                self.update_key(key, input_key_value, current_key_value)

        if self.post_crud():
            self.__changed = True

        after_run_keys = self.filter_list_of_current_keys(self.__input_keys)
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
            {self.__parameter_name_with_items: diff_before_keys})
        diff_after_output.update(
            {self.__parameter_name_with_items: diff_after_keys})
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
