#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test pywikibot.tools.collections package."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import types

from pywikibot.tools import collections
from pywikibot.tools import PY2

from tests.aspects import unittest, TestCase


class TestProxyDict(TestCase):

    """Test the ProxyDict class."""

    net = False

    def setUp(self):
        """Create default dict and expectation."""
        super(TestProxyDict, self).setUp()
        self.expected = {'a': 'b'}
        self.tested_dict = self._create(self.expected)

    def tearDown(self):
        """Verify that the dict hasn't changed."""
        super(TestProxyDict, self).tearDown()
        self.assertIsNot(self.tested_dict, self.expected)
        self.assertEqual(self.tested_dict, self.expected)

    def _create(self, mapping):
        """Create an instance of the mapping."""
        return collections.ProxyDict(mapping)

    def test_mutables(self):
        """Verify that the update method is raising TypeError."""
        self.assertFalse(hasattr(self.tested_dict, '__setitem__'))
        self.assertFalse(hasattr(self.tested_dict, '__delitem__'))
        self.assertFalse(hasattr(self.tested_dict, 'update'))
        self.assertFalse(hasattr(self.tested_dict, 'pop'))
        self.assertFalse(hasattr(self.tested_dict, 'popitem'))
        self.assertFalse(hasattr(self.tested_dict, 'setdefault'))
        self.assertFalse(hasattr(self.tested_dict, 'clear'))
        self.assertFalse(hasattr(self.tested_dict, 'fromkeys'))

    def test_immutables(self):
        """Test that it's immutable."""
        self.assertEqual(self.tested_dict['a'], 'b')
        with self.assertRaises(KeyError):
            self.tested_dict['c']
        self.assertEqual(self.tested_dict.get('a'), 'b')
        self.assertIsNone(self.tested_dict.get('c'))

    def test_proxy(self):
        """Test that changes in the underlying dict are reflected."""
        implicit_iter = iter(self.tested_dict)
        if PY2:
            keys_iter = self.tested_dict.iterkeys()
            values_iter = self.tested_dict.itervalues()
            items_iter = self.tested_dict.iteritems()
        else:
            keys_iter = iter(self.tested_dict.keys())
            values_iter = iter(self.tested_dict.values())
            items_iter = iter(self.tested_dict.items())
        self.expected['c'] = 'd'
        self.assertEqual(self.tested_dict['c'], 'd')
        self.assertRaises(RuntimeError, next, implicit_iter)
        self.assertRaises(RuntimeError, next, keys_iter)
        self.assertRaises(RuntimeError, next, values_iter)
        self.assertRaises(RuntimeError, next, items_iter)

    def test_copy(self):
        """Test that copy returns correct result."""
        copy = self.tested_dict.copy()
        self.assertIsInstance(copy, dict)
        self.assertEqual(copy, self.tested_dict)
        self.assertEqual(copy, self.expected)

    def test_create(self):
        """Test create classmethod."""
        original = {1: 2}
        copy = self.tested_dict.create(original)
        original[3] = 4
        self.assertIn(1, original)
        self.assertNotIn(3, copy)


class TestMappingProxyType(TestProxyDict):

    """Test MappingProxyType implementation in collections."""

    net = False

    def _create(self, mapping):
        """Create an instance of the mapping."""
        return collections.MappingProxyType(mapping)

    @unittest.skipIf(PY2, 'Python 2 does not have MappingProxyType')
    def test_class(self):
        """Verify that Python's implementation is tested."""
        self.assertIsInstance(self.tested_dict, types.MappingProxyType)

    def test_repr_class(self):
        """Test that the right repr string prefix is used."""
        self.assertEqual(repr(self.tested_dict),
                         'mappingproxy({{{0!r}: {1!r}}})'.format('a', 'b'))

    def test_create(self):
        """Test create classmethod."""
        if PY2:
            super(TestMappingProxyType, self).test_create()
        else:
            self.assertFalse(hasattr(self.tested_dict, 'create'))


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
