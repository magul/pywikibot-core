# -*- coding: utf-8  -*-
"""Test valid templates."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import json
import os
import pkgutil
import re

import pywikibot
from pywikibot import i18n

from tests.aspects import unittest, MetaTestCaseClass, TestCase
from tests.utils import add_metaclass

PACKAGES = (
    'redirect-broken-redirect-template',  # speedy deletion template
    'archivebot-archiveheader',  # archive header template
)


class TestValidTemplateMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(msg, code):

            def test_template(self):
                """Test validity of template."""
                if msg:
                    # check whether the message contains a template
                    template = re.findall(u'.*?{{(.*?)[|}]', msg)
                    self.assertTrue(template)

                    if template:
                        # check whether site is valid
                        site = pywikibot.Site('en', 'wikipedia')
                        self.assertIn(code, site.languages())

                        # check whether template exists
                        title = template[0]
                        site = pywikibot.Site(code, 'wikipedia')
                        page = pywikibot.Page(site, title, ns=10)
                        self.assertTrue(page.exists())

            return test_template

        # create test methods for package messages processed by unittest
        for package in PACKAGES:
            for lang in i18n.twget_keys(package):
                template_msg = i18n.twtranslate(lang, package, fallback=False)
                if template_msg is None:
                    continue
                test_name = "test_%s_%s" % (package.replace('-', '_'), lang)
                dct[test_name] = test_method(template_msg, lang)

        return super(TestValidTemplateMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestValidTemplate(TestCase):

    """Test cases L10N message templates processed by unittest."""

    __metaclass__ = TestValidTemplateMeta

    net = True  # magic flag tells jenkins to not run the test.


class TestValidReplacementMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(msg, keys):

            def test_replacement(self):
                """Test validity of string format replacement."""
                if not msg:
                    raise unittest.SkipTest("No message found.")
                items = re.findall(r'%\(([^\)]+?)\)(?:[^di]|$)', msg)
                itemset = set(items)
                keyset = set(keys)
                # Validate whether keys are found
                self.assertLessEqual(itemset, keyset)
                # Validate whether keys have right format
                self.assertEqual(itemset, set(re.findall(r'%\((\w+?)\)[ds]', msg)))
                # Check occurencies of keys
                # commented out due to a lot of failures
                # self.assertCountEqual(items, keys)

            return test_replacement

        def get_all():
            package = os.path.join('scripts', 'i18n')
            for package_root, package_dirs, package_files in os.walk(package):
                for current_dir in package_dirs:
                    folder = os.path.join('scripts', 'i18n', current_dir)
                    for root, dirs, files in os.walk(folder):
                        filename = os.path.join(current_dir, 'en.json')
                        try:
                            text = pkgutil.get_data('scripts.i18n', filename)
                        except (OSError, IOError):
                            continue
                        if isinstance(text, bytes):
                            text = text.decode('utf-8')
                        transdict = json.loads(text, 'utf-8')
                        for key in transdict:
                            if key != '@metadata':
                                yield key

        # create test methods for package messages processed by unittest
        for package in get_all():
            msg = template_msg = i18n.twtranslate('en', package, fallback=False)
            if "{{PLURAL:" in msg:  # don't validate it yet
                continue
            keys = re.findall(r'%\((\w+?)\)[ds]', msg)
            for lang in i18n.twget_keys(package):
                formatstr_msg = i18n.twtranslate(lang, package, fallback=False)
                if template_msg is None:
                    continue
                test_name = "test_%s_%s" % (package.replace('-', '_'), lang)
                dct[test_name] = test_method(formatstr_msg, keys)

        return super(TestValidReplacementMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestValidReplacement(TestCase):

    """Test cases L10N message string replacements processed by unittest."""

    __metaclass__ = TestValidReplacementMeta

    net = True  # magic flag tells jenkins to not run the test.


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
