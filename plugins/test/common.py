# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Jinja tests."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


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


class TestModule(object):
    """Exported tests."""

    def tests(self):
        """Available tests."""
        return {
            'starts_like_item_in': starts_like_item_in,
            'contains': contains
        }