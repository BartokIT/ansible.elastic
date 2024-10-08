# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Jinja tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import re
from collections.abc import MutableMapping
from ansible import errors


def flatten_dict(d: MutableMapping, schema: MutableMapping = None, parent_key: str = '', sep: str = '.') -> MutableMapping:
    items = []
    if schema is None:
        schema = {}
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if new_key in schema:
            items.append((new_key, v))
        elif isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, schema, new_key, sep=sep).items())
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
    flatted_dict = flatten_dict(configuration, schema)

    # added attribute for routing awareness
    if 'cluster.routing.allocation.awareness.attributes' in flatted_dict:
        schema['node.attr.' + flatted_dict['cluster.routing.allocation.awareness.attributes']] = {'type': 'string'}
    validation_errors = []
    for key in flatted_dict.keys():
        found_schema_key = key

        if key not in schema:
            validation_errors += ["The key %s is not allowed" % key]

        elif found_schema_key:
            if schema[found_schema_key]['type'] == 'bool':
                if not isinstance(flatted_dict[key], bool):
                    validation_errors += ["The key {} must be boolean (found {})".format(found_schema_key, type(flatted_dict[key]))]
            if schema[found_schema_key]['type'] == 'int':
                try:
                    int(flatted_dict[key])
                except ValueError:
                    validation_errors += ["The key {} must be int (found {})".format(found_schema_key, flatted_dict[key])]
            elif schema[found_schema_key]['type'] == 'percentual':
                if not re.match("[0-9]+%", flatted_dict[key]):
                    validation_errors += ["The key {} must be a percentual (found {})".format(found_schema_key, flatted_dict[key])]
            elif schema[found_schema_key]['type'] == 'byte':
                if not re.match("[0-9]+(b|kb|mb|gb|tb|pb)", flatted_dict[key]):
                    validation_errors += ["The key {} must be a byte multiple (found {})".format(found_schema_key, flatted_dict[key])]
            elif schema[found_schema_key]['type'] == 'string':
                if 'choices' in schema[found_schema_key]:
                    if flatted_dict[key] not in schema[found_schema_key]['choices']:
                        validation_errors += ["The key {} must be one of {} ({} found)".format(found_schema_key, "%s" %
                                              schema[found_schema_key]['choices'], flatted_dict[key])]

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
