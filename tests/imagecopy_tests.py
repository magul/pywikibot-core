# -*- coding: utf-8 -*-
"""Tests for imagecopy script."""
#
# (C) Pywikibot team, 2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from scripts.imagecopy import pageTextPost

from tests import join_data_path
from tests.aspects import TestCase


class ImagecopyMethodTest(TestCase):
    """Test methods in imagecopy"""

    net = False

    def test_pageTextPost(self):
        parameters_dict = {
            'language': b'id',
            'image': b'Ahmad Syaikhu Wakil Walikota Bekasi.jpg',
            'newname': b'Ahmad Syaikhu Wakil Walikota Bekasi.jpg',
            'project': b'wikipedia',
            'username': '',
            'commonsense': '1',
            'remove_categories': '1',
            'ignorewarnings': '1',
            'doit': 'Uitvoeren'}

        CH = pageTextPost('', parameters_dict)
        tablock = CH.split('<textarea ')[1].split('>')[0]
        CH = CH.split('<textarea ' + tablock + '>')[1].split('</textarea>')[0]
        with open(join_data_path('commonsHelper_description.txt')) as f:
            self.assertEqual(f.read(), CH)
