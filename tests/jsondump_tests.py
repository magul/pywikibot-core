# -*- coding: utf-8  -*-
"""Tests for the Wikidata parts of the page module."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import json

from pywikibot.data import jsondump
from pywikibot.page import ItemPage

from tests import join_pages_path

from tests.aspects import (
    unittest,
    require_modules,
    WikidataTestCase,
)


@require_modules('ijson')
class TestJsondump(WikidataTestCase):

    """Test JSONDump class."""

    dry = True

    def setUp(self):
        """Create a new dump instance."""
        self.dump = jsondump.JSONDump(self.repo, join_pages_path('dump.wd'))
        with open(join_pages_path('Q60.wd'), 'r') as f:
            self.content = json.load(f)
        super(TestJsondump, self).setUp()

    def test_dump_item(self):
        """Test generating item entities."""
        generated = list(self.dump.generator())
        # assert that the length is one in a way which will show a more helpful
        # error message when it isn't (as it shows the difference in lists)
        self.assertEqual(generated, [generated[0]])
        first = generated[0]
        self.assertTrue(hasattr(first, '_content'))
        self.assertIsInstance(first, ItemPage)
        self.assertEqual(first._content, self.content)
        self.assertEqual(list(self.dump.generator('item')), generated)

    def test_dump_property(self):
        """Test generating property entities."""
        generated = list(self.dump.generator('property'))
        self.assertFalse(generated)  # assert an empty list

    def test_dump_invalid(self):
        """Test using the generator with an invalid type."""
        self.assertRaises(NameError, list, self.dump.generator('invalid'))

    def test_dump_any(self):
        """Test generating entries without restricting the type."""
        any_generated = set(self.dump.generator(None))
        item_generated = set(self.dump.generator('item'))
        prop_generated = set(self.dump.generator('property'))
        self.assertGreaterEqual(any_generated, item_generated)
        self.assertGreaterEqual(any_generated, prop_generated)
        self.assertFalse(prop_generated & item_generated)
        self.assertEqual(any_generated, prop_generated | item_generated)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
