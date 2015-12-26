# -*- coding: utf-8  -*-
"""TitleTranslate test module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#

import pywikibot.page
import pywikibot.site
import pywikibot.titletranslate

from tests.aspects import unittest, TestCase

class TestTitleTranslate(TestCase):
    """ Tests for titletranslate.py """

    try:
        site = pywikibot.Site('en', 'wikipedia')
        page = pywikibot.Page(site, u"20th_century")
    except Exception as error:
        print("failed to load page: ", error)

    def test_translate(self):
        if self.page is not None:
            self.assertNotEqual(pywikibot.titletranslate.translate(page=self.page, auto=True), [])

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
