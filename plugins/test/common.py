# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Jinja tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import re
from collections.abc import MutableMapping
from ansible import errors

def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str ='.') -> MutableMapping:
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def starts_like_item_in(element, items):
    """
    Compare a variable initial character with the items of a list.

    This test check if the variable start like at least
    one item inside the list.
    """
    for item in items:
        if element.startswith(item):
            return True
    return False


def contains(items, element):
    """Verify it an element is inside a list."""
    return element in items

def validate_configuration(configuration, schema):
    flatted_dict = flatten_dict(configuration)
    validation_errors = []
    for key in flatted_dict.keys():
        if not key in schema:
            validation_errors += ["The key %s is not allowed" % key]
        else:
            if schema[key]['type'] == 'bool':
                if type(flatted_dict[key]) != type(True):
                    validation_errors += ["The key {} must be boolean (found {})".format(key, type(flatted_dict[key]))]
            elif schema[key]['type'] == 'percentual':
                if not re.match("[0-0]+%", flatted_dict[key]):
                    validation_errors += ["The key {} must be a percentual (found {})".format(key, type(flatted_dict[key]))]
            elif schema[key]['type'] == 'string':
                if 'choices' in schema[key]:
                    if flatted_dict[key] not in schema[key]['choices']:
                        validation_errors += ["The key {} must be one of {} ({} found)".format(key, "%s" %  schema[key]['choices'], flatted_dict[key]['string'])]
    if validation_errors:
        raise errors.AnsibleFilterError(validation_errors)

    return True

class TestModule(object):
    """Exported tests."""

    def tests(self):
        """Available tests."""
        return {
            'starts_like_item_in': starts_like_item_in,
            'contains': contains,
            'validate_configuration': validate_configuration
        }