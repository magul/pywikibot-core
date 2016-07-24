# -*- coding: utf-8  -*-
"""FilePage tests."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import pywikibot

from pywikibot.tools import UnicodeType as unicode

from tests.aspects import unittest, TestCase, DeprecationTestCase


class TestShareFiles(TestCase):

    """Test methods fileIsShared, exists and fileUrl with shared files."""

    sites = {
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'itwiki': {
            'family': 'wikipedia',
            'code': 'it',
        },
        'testwiki': {
            'family': 'wikipedia',
            'code': 'test',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
    }

    cached = True

    def testSharedOnly(self):
        """Test fileIsShared() on file page with shared file only."""
        title = 'File:Sepp Maier 1.JPG'

        commons = self.get_site('commons')
        itwp = self.get_site('itwiki')
        itwp_file = pywikibot.FilePage(itwp, title)
        for using in itwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertFalse(itwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertTrue(itwp_file.fileIsShared())
        self.assertTrue(commons_file.fileIsShared())
        self.assertTrue(commons_file.fileUrl())

        self.assertIn('/wikipedia/commons/', itwp_file.fileUrl())
        self.assertRaises(pywikibot.NoPage, itwp_file.get)

    def testLocalOnly(self):
        """Test fileIsShared() on file page with local file only."""
        title = 'File:April Fools Day Adminship discussion (2005).png'

        commons = self.get_site('commons')
        enwp = self.get_site('enwiki')
        enwp_file = pywikibot.FilePage(enwp, title)
        for using in enwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertTrue(enwp_file.fileUrl())
        self.assertTrue(enwp_file.exists())
        self.assertFalse(commons_file.exists())

        self.assertFalse(enwp_file.fileIsShared())
        self.assertRaises(pywikibot.NoPage, commons_file.fileIsShared)

        self.assertRaises(pywikibot.NoPage, commons_file.fileUrl)
        self.assertRaises(pywikibot.NoPage, commons_file.get)

    def testOnBoth(self):
        """Test fileIsShared() on file page with both local and shared file."""
        title = 'File:Pulsante spam.png'

        commons = self.get_site('commons')
        itwp = self.get_site('itwiki')
        itwp_file = pywikibot.FilePage(itwp, title)
        for using in itwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertTrue(itwp_file.fileUrl())
        self.assertTrue(itwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertFalse(itwp_file.fileIsShared())
        self.assertTrue(commons_file.fileIsShared())

    def testNonFileLocal(self):
        """Test file page, without local file, existing on the local wiki."""
        title = 'File:Sepp Maier 1.JPG'

        commons = self.get_site('commons')
        testwp = self.get_site('testwiki')
        testwp_file = pywikibot.FilePage(testwp, title)

        self.assertTrue(testwp_file.fileUrl())
        self.assertTrue(testwp_file.exists())
        self.assertTrue(testwp_file.fileIsShared())

        commons_file = pywikibot.FilePage(commons, title)
        self.assertEqual(testwp_file.fileUrl(),
                         commons_file.fileUrl())


class TestFilePage(TestCase):

    """Test FilePage.latest_revision_info.

    These tests cover exceptions for all properties and methods
    in FilePage that rely on site.loadimageinfo.

    """

    family = 'wikipedia'
    code = 'test'

    file_name = 'File:Albert Einstein Head.jpg'

    cached = True

    def test_file_info_with_no_page(self):
        """FilePage:latest_file_info raises NoPage for non existing pages."""
        site = self.get_site()
        image = pywikibot.FilePage(site, u'File:NoPage')
        self.assertFalse(image.exists())
        with self.assertRaises(pywikibot.NoPage):
            image = image.latest_file_info

    def test_file_info_with_no_file(self):
        """FilePage:latest_file_info raises PagerelatedError if no file is present."""
        site = self.get_site()
        image = pywikibot.FilePage(site, u'File:Test with no image')
        self.assertTrue(image.exists())
        with self.assertRaises(pywikibot.PageRelatedError):
            image = image.latest_file_info


class TestFilePageLatestFileInfo(TestCase):

    """Test FilePage.latest_file_info.

    These tests cover properties and methods in FilePage that rely
    on site.loadimageinfo.

    """

    family = 'commons'
    code = 'commons'

    file_name = 'File:Albert Einstein Head.jpg'

    cached = True

    def setUp(self):
        """Create File page."""
        super(TestCase, self).setUp()
        self.image = pywikibot.FilePage(self.site, self.file_name)

    def test_get_file_url(self):
        """Get File url."""
        self.assertTrue(self.image.exists())
        self.assertEqual(self.image.get_file_url(),
                         'https://upload.wikimedia.org/wikipedia/commons/'
                         'd/d3/Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.url,
                         'https://upload.wikimedia.org/wikipedia/commons/'
                         'd/d3/Albert_Einstein_Head.jpg')

    def test_get_file_url_thumburl_from_width(self):
        """Get File thumburl from width."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(self.image.get_file_url(url_width=100, url_param='1000px'),
                         'https://upload.wikimedia.org/wikipedia/commons/thumb/'
                         'd/d3/Albert_Einstein_Head.jpg/100px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 100)
        self.assertEqual(self.image.latest_file_info.thumbheight, 133)

    def test_get_file_url_thumburl_from_heigth(self):
        """Get File thumburl from height."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(self.image.get_file_url(url_height=100, url_param='1000px'),
                         'https://upload.wikimedia.org/wikipedia/commons/thumb/'
                         'd/d3/Albert_Einstein_Head.jpg/75px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 75)
        self.assertEqual(self.image.latest_file_info.thumbheight, 100)

    def test_get_file_url_thumburl_from_url_param(self):
        """Get File thumburl from height."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(self.image.get_file_url(url_param='100px'),
                         'https://upload.wikimedia.org/wikipedia/commons/thumb/'
                         'd/d3/Albert_Einstein_Head.jpg/100px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 100)
        self.assertEqual(self.image.latest_file_info.thumbheight, 133)


class TestDeprecatedFilePage(DeprecationTestCase):

    """Test deprecated parts of FilePage."""

    family = 'commons'
    code = 'commons'

    cached = True

    def test_getFirstUploader(self):
        """Test getFirstUploader."""
        page = pywikibot.FilePage(self.site, 'File:Albert Einstein.jpg')
        first = page.getFirstUploader()
        self.assertOneDeprecation()
        self.assertEqual(first, ['Herbizid', '2011-03-18T10:04:48Z'])
        self.assertIsInstance(first[0], unicode)
        self.assertIsInstance(first[1], unicode)

    def test_getLatestUploader(self):
        """Test getLatestUploader."""
        page = pywikibot.FilePage(self.site, 'File:Albert Einstein.jpg')
        latest = page.getLatestUploader()
        self.assertOneDeprecation()
        self.assertEqual(len(latest), 2)
        self.assertIsInstance(latest[0], unicode)
        self.assertIsInstance(latest[1], unicode)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
