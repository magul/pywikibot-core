# -*- coding: utf-8  -*-
"""Tests for the proofreadpage module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import json

import pywikibot

from pywikibot.proofreadpage import ProofreadPage
from pywikibot.data import api
from tests.aspects import unittest, TestCase

from tests.basepage_tests import (
    BasePageMethodsTestBase,
    BasePageLoadRevisionsCachingTestBase,
)


class TestProofreadPageInvalidSite(TestCase):

    """Test ProofreadPage class."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_invalid_site_source(self):
        """Test ProofreadPage from invalid Site as source."""
        self.assertRaises(pywikibot.UnknownExtension,
                          ProofreadPage, self.site, 'title')


class TestBasePageMethods(BasePageMethodsTestBase):

    """Test behavior of ProofreadPage methods inherited from BasePage."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = ProofreadPage(
            self.site, 'Page:Popular Science Monthly Volume 1.djvu/12')
        super(TestBasePageMethods, self).setUp()

    def test_basepage_methods(self):
        """Test ProofreadPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_return_datatypes()


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase):

    """Test site.loadrevisions() caching."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = ProofreadPage(
            self.site, 'Page:Popular Science Monthly Volume 1.djvu/12')
        super(TestLoadRevisionsCaching, self).setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestProofreadPageValidSite(TestCase):

    """Test ProofreadPage class."""

    family = 'wikisource'
    code = 'en'

    cached = True

    valid = {
        'title': 'Page:Popular Science Monthly Volume 1.djvu/12',
        'level': 4,
        'user': 'T. Mazzei',
        'header': u"{{rh|2|''THE POPULAR SCIENCE MONTHLY.''}}",
        'footer': u'\n{{smallrefs}}',
    }

    existing_invalid = {
        'title': 'Main Page',
    }

    not_existing_invalid = {
        'title': 'User:cannot_exists',
        'title1': 'User:Popular Science Monthly Volume 1.djvu/12'
    }

    def test_valid_site_source(self):
        """Test ProofreadPage from valid Site as source."""
        page = ProofreadPage(self.site, 'title')
        self.assertEqual(page.namespace(), self.site.proofread_page_ns)

    def test_invalid_existing_page_source_in_valid_site(self):
        """Test ProofreadPage from invalid existing Page as source."""
        source = pywikibot.Page(self.site, self.existing_invalid['title'])
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_invalid_not_existing_page_source_in_valid_site(self):
        """Test ProofreadPage from invalid not existing Page as source."""
        # namespace is forced
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title'])
        fixed_source = pywikibot.Page(self.site,
                                      source.title(withNamespace=False),
                                      ns=self.site.proofread_page_ns)
        page = ProofreadPage(fixed_source)
        self.assertEqual(page.title(), fixed_source.title())

    def test_invalid_not_existing_page_source_in_valid_site_wrong_ns(self):
        """Test ProofreadPage from Page not existing in non-Page ns as source."""
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title1'])
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_invalid_link_source_in_valid_site(self):
        """Test ProofreadPage from invalid Link as source."""
        source = pywikibot.Link(self.not_existing_invalid['title'],
                                source=self.site)
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_valid_link_source_in_valid_site(self):
        """Test ProofreadPage from valid Link as source."""
        source = pywikibot.Link(
            self.valid['title'],
            source=self.site,
            defaultNamespace=self.site.proofread_page_ns)
        page = ProofreadPage(source)
        self.assertEqual(page.title(withNamespace=False), source.title)
        self.assertEqual(page.namespace(), source.namespace)

    def test_valid_parsing(self):
        """Test ProofreadPage page parsing functions."""
        page = ProofreadPage(self.site, self.valid['title'])
        self.assertEqual(page.level, self.valid['level'])
        self.assertEqual(page.user, self.valid['user'])
        self.assertEqual(page.header, self.valid['header'])
        self.assertEqual(page.footer, self.valid['footer'])

    def test_decompose_recompose_text(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, self.valid['title'])
        plain_text = pywikibot.Page(self.site, self.valid['title']).text
        # import pdb; pdb.set_trace()
        assert page.text
        self.assertEqual(plain_text, page.text)

    def test_preload_from_not_existing_page(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'dummy test page')
        self.assertEqual(page.text,
                         '<noinclude><pagequality level="1" user="%s" />'
                         '<div class="pagetext">\n\n\n</noinclude>'
                         '<noinclude><references/></div></noinclude>'
                         % self.site.username())

    def test_preload_from_empty_text(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'dummy test page')
        self.assertEqual(page.text,
                         '<noinclude><pagequality level="1" user="%s" />'
                         '<div class="pagetext">\n\n\n</noinclude>'
                         '<noinclude><references/></div></noinclude>'
                         % self.site.username())

    def test_json_format(self):
        """Test conversion to json format."""
        page = ProofreadPage(self.site, self.valid['title'])

        rvargs = {'rvprop': 'ids|flags|timestamp|user|comment|content',
                  'rvcontentformat': 'application/json',
                  'titles': page,
                  }

        rvgen = self.site._generator(api.PropertyGenerator,
                                     type_arg='info|revisions',
                                     total=1, **rvargs)
        rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter

        try:
            pagedict = next(iter(rvgen))
            loaded_text = pagedict.get('revisions')[0].get('*')
        except (StopIteration, TypeError, KeyError, ValueError, IndexError):
            page_text = ''

        page_text = page._page_to_json()
        self.assertEqual(json.loads(page_text), json.loads(loaded_text))


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
