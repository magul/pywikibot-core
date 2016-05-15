# -*- coding: utf-8  -*-
"""Test methods in panoramiopicker script."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from scripts import panoramiopicker

from tests.aspects import unittest, require_modules, TestCase


@require_modules('bs4')
class TestPanoramioMethods(TestCase):
    """Test methods in panoramiopicker."""

    net = True

    @unittest.expectedFailure
    def test_get_license(self):
        """Test getLicense() method."""
        x = panoramiopicker.getPhotos(photoset='public', start_id='0', end_id='5')
        for photoinfo in x:
            photoinfo_test = panoramiopicker.getLicense(photoinfo)
            self.assertIsNotNone(photoinfo_test)

if __name__ == '__main__':
    unittest.main()
