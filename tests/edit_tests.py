# -*- coding: utf-8  -*-
"""Tests for editing pages."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import re
import time

import pywikibot

from pywikibot import page_put_queue

from tests.aspects import unittest, TestCase

called_back = False


class TestGeneralWrite(TestCase):

    """Run general write tests."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    def test_async(self):
        """Test writing to a page."""
        global called_back

        def callback(page, err):
            global called_back
            self.assertEqual(page, p)
            self.assertIsNone(err)
            called_back = True

        self.assertTrue(page_put_queue.empty())
        called_back = False
        ts = str(time.time())
        p = pywikibot.Page(self.site, 'User:John Vandenberg/async test write')
        p.text = ts
        p.save(async=True, callback=callback)

        page_put_queue.join()

        p = pywikibot.Page(self.site, 'User:John Vandenberg/async test write')
        self.assertEqual(p.text, ts)
        self.assertTrue(called_back)

    def test_edit_conflict(self):
        r"""
        Test if an edit conflict occurs.

        It uses two Page instances initialized at the same point. One of them
        then changes the text so that when the other now saves two an edit
        conflict occurs.

        The page must exist and follow the format '\d+.\d+ #\d'.
        """
        previous_page = pywikibot.Page(self.site, 'User:BobBot/Test edit conflict')
        if not previous_page.exists():
            raise unittest.SkipTest('The page "{0}" does not exist. Please '
                                    'create it.'.format(previous_page))
        content_match = re.match('^\d+.\d+ #(\d)$', previous_page.get())
        if not content_match:
            raise unittest.SkipTest('The page "{0}" does not '
                                    'match.'.format(previous_page))
        ts = time.time()
        # At least two of the numbers aren't used
        contents = ['{0} #{1}'.format(ts, n)
                    for n in range(1, 4) if n != int(content_match.group(1))]

        previous_page.text = contents[0]
        conflict_page = pywikibot.Page(self.site, previous_page.title())
        conflict_page.text = contents[1]
        conflict_page.save(summary='An intermediate save so that it conflicts.')
        self.assertRaises(pywikibot.EditConflict, previous_page.save,
                          summary='This save should not happen as it conflicts')
        self.assertEqual(previous_page.text, contents[0])
        self.assertEqual(conflict_page.get(force=True), contents[1])


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
