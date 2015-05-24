# -*- coding: utf-8  -*-
"""
UploadRobot test.

These tests write to the wiki.
"""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import os

from scripts import pagefromfile

from tests import _data_dir
from tests.aspects import unittest, TestCase


combined_file = os.path.join(_data_dir, 'pages-file-combined.txt')
core_file = os.path.join(_data_dir, 'pages-file-core.txt')
# The first four parameters for the PageFromFileReader constructor (except file)
compat_params = ('XXXXXX', 'XXXXXX', "'''", "'''")
core_params = (None, None, "'''", "'''")


class TestPageFromFileReader(TestCase):

    """Test cases for upload."""

    net = False

    def test_read_combined_compat(self):
        """Read the combined file in compat compatible mode."""
        reader = pagefromfile.PageFromFileReader(combined_file, *compat_params,
                                                 include=False, notitle=False)
        read_pages = list(reader.run())
        self.assertEqual([title for title, contents in read_pages],
                         ['Page', 'Other', 'third'])
        self.assertIn('Fifth', read_pages[-1][1])

    def test_read_combined_core(self):
        """Read the combined file in core compatible mode."""
        reader = pagefromfile.PageFromFileReader(combined_file, *core_params,
                                                 include=False, notitle=False)
        read_pages = list(reader.run())
        self.assertEqual([title for title, contents in read_pages],
                         ['Page', 'pretend', 'Other', 'XKCD', 'Fifth', 'note'])
        # The 'Fifth' entry is special as it uses the new filename mode
        self.assertNotIn('Fifth', read_pages[4][1])

    def test_read_core_only(self):
        """Read the file only working in core compatible mode."""
        reader = pagefromfile.PageFromFileReader(core_file, *core_params,
                                                 include=False, notitle=False)
        read_pages = list(reader.run())
        self.assertEqual([title for title, contents in read_pages],
                         ['Good', 'Bad', 'Good again', 'Changed length',
                          'Changed length but same chars'])
        self.assertIn('XXXXXX', read_pages[1][1])
        self.assertTrue(read_pages[1][1].startswith('Okay'))
        self.assertTrue(read_pages[1][1].endswith('Ys.\n'))
        self.assertIn('XXXXXX', read_pages[2][1])
        self.assertIn('YYYYY', read_pages[2][1])


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
