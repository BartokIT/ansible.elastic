# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Elasticsearch Jinja filters."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def dictoflist2flatlist(items, keyname='key'):
    result = []
    for key in items.keys():
        for item in items[key]:
            item.update({keyname: key})
            result.append(item)
    return result

def dictofdict2listofdict(items, keyname='key'):
    result = []
    for key in items.keys():
        items[key].update({keyname: key})
        result.append(items[key])
    return result

def sort(items, sample_list=None):
    if sample_list is None:
        sample_list = []
    """Sort element of a list like another list."""
    return [element for element in sample_list if element in items]


def after(items, element, elements):
    """Insert elements in a list after an item."""
    element_position = items.index(element)
    first_part = items[:element_position]
    second_part = items[element_position:]
    return [*first_part, *elements, *second_part]


class FilterModule(object):
    """Export filters."""

    def filters(self):
        """Return filteres."""
        return {
            'sort': sort,
            'after': after,
            'dictoflist2flatlist': dictoflist2flatlist,
            'dictofdict2listofdict': dictofdict2listofdict
        }
