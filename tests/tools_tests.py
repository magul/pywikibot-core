#!/usr/bin/python
"""Test tools package alone which don't fit into other tests."""
# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
from __future__ import unicode_literals

__version__ = '$Id$'

import os.path
import subprocess

from pywikibot import tools

from tests import _data_dir
from tests.aspects import unittest, TestCase

_xml_data_dir = os.path.join(_data_dir, 'xml')


class ContextManagerWrapperTestCase(TestCase):

    """Test that ContextManagerWrapper is working correctly."""

    net = False

    def test_wrapper(self):
        """Create a test instance and verify the wrapper redirects."""
        class DummyClass(object):

            """A dummy class which has some values and a close method."""

            class_var = 42

            def __init__(self):
                """Create instance with dummy values."""
                self.instance_var = 1337
                self.closed = False

            def close(self):
                """Just store that it has been closed."""
                self.closed = True

        obj = DummyClass()
        wrapped = tools.ContextManagerWrapper(obj)
        self.assertIs(wrapped.class_var, obj.class_var)
        self.assertIs(wrapped.instance_var, obj.instance_var)
        self.assertIs(wrapped._wrapped, obj)
        self.assertFalse(obj.closed)
        with wrapped as unwrapped:
            self.assertFalse(obj.closed)
            self.assertIs(unwrapped, obj)
        self.assertTrue(obj.closed)


class OpenCompressedTestCase(TestCase):

    """
    Unit test class for tools.

    The tests for open_compressed requires that article-pyrus.xml* contain all
    the same content after extraction. The content itself is not important.
    The file article-pyrus.xml_invalid.7z is not a valid 7z file and
    open_compressed will fail extracting it using 7za.
    """

    net = False

    @classmethod
    def setUpClass(cls):
        """Define base_file and original_content."""
        super(OpenCompressedTestCase, cls).setUpClass()
        cls.base_file = os.path.join(_xml_data_dir, 'article-pyrus.xml')
        with open(cls.base_file, 'rb') as f:
            cls.original_content = f.read()

    @staticmethod
    def _get_content(*args):
        """Use open_compressed and return content using a with-statement."""
        with tools.open_compressed(*args) as f:
            return f.read()

    def test_open_compressed(self):
        """Test open_compressed with all compressors in the standard library."""
        self.assertEqual(self._get_content(self.base_file), self.original_content)
        self.assertEqual(self._get_content(self.base_file + '.bz2'), self.original_content)
        self.assertEqual(self._get_content(self.base_file + '.gz'), self.original_content)
        self.assertEqual(self._get_content(self.base_file + '.bz2', True), self.original_content)

    def test_open_compressed_7z(self):
        """Test open_compressed with 7za if installed."""
        try:
            subprocess.Popen(['7za'], stdout=subprocess.PIPE).stdout.close()
        except OSError:
            raise unittest.SkipTest('7za not installed')
        self.assertEqual(self._get_content(self.base_file + '.7z'), self.original_content)
        self.assertRaises(OSError, self._get_content, self.base_file + '_invalid.7z', True)


class RegexTestCase(TestCase):

    """Unit test class for the regex parts."""

    net = False

    def test_PCRE_regex(self):
        """Test converting a PCRE regex into a python regex."""
        self.assertEqual(tools.convert_PCRE('//')[0], '')
        self.assertEqual(tools.convert_PCRE('/\\x{0A80}-\\x{0AFF}/')[0],
                         '\u0A80-\u0AFF')
        self.assertEqual(tools.convert_PCRE('/^([a-z\\x{0900}-\\x{0963}\\x{0966}-\\x{A8E0}-\\x{A8FF}]+)(.*)$/sDu')[0],
                         '^([a-z\u0900-\u0963\u0966-\uA8E0-\uA8FF]+)(.*)$')
        self.assertEqual(tools.convert_PCRE('/\\x41/')[0],
                         '\u0041')

    def test_regex_group(self):
        """Test parsing the requested regex group."""
        self.assertEqual(tools.get_regex_group('f(oo)(bar)', 0), 'f(oo)(bar)')
        self.assertEqual(tools.get_regex_group('f(oo)(bar)', 1), 'oo')
        self.assertEqual(tools.get_regex_group('f(oo)(bar)', 2), 'bar')
        self.assertEqual(tools.get_regex_group('f(oo)(?P<baz>bar)', 'baz'), 'bar')
        self.assertEqual(tools.get_regex_group('f(oo)(?P<baz>bar)', 2), 'bar')
        self.assertEqual(tools.get_regex_group('f(o(o))bar', 1), 'o(o)')
        self.assertEqual(tools.get_regex_group('f(o(o))bar', 2), 'o')
        self.assertEqual(tools.get_regex_group('f(?:oo)(bar)', 1), 'bar')
        self.assertEqual(tools.get_regex_group('f(?=oo)(bar)', 1), 'bar')
        self.assertEqual(tools.get_regex_group('f(?:oo(bar))', 1), 'bar')

        self.assertRaises(ValueError, tools.get_regex_group, 'f(oo)(?:bar)', 2)
        self.assertRaises(ValueError, tools.get_regex_group, 'f(oo)(bar)', 3)
        self.assertRaises(ValueError, tools.get_regex_group, 'f(oo)(bar)', 'bar')
        self.assertRaises(ValueError, tools.get_regex_group, 'f(oo)(bar)', '1')
        self.assertRaises(ValueError, tools.get_regex_group, 'f(o(o)bar', 1)
        self.assertRaises(ValueError, tools.get_regex_group, 'f(oo)(bar', '2')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
