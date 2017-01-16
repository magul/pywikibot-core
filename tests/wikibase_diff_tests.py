#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test diff module."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import json

try:
    import pycountry
except ImportError:
    pycountry = None

from pywikibot.wikibase_diff import WikibasePatchManager

from tests.aspects import TestCase
from tests import join_pages_path


class DryWikibasePatchManagerTests(TestCase):
    """Test WikibasePatchManager with dry tests."""

    net = False

    def check_hunks(self, first, second, results):
        """Helper method, used to check if WikibasePatchManager returned expected results."""
        p = WikibasePatchManager(first, second, None)
        self.assertEqual(len(p.hunks), len(results))
        for i in range(0, len(p.hunks)):
            self.assertEqual(p.hunks[i].diff_plain_text, results[i])

    def test_labels(self):
        """Test comparing labels."""
        first = {
            'labels': {
                'en': {
                    'language': 'en',
                    'value': 'World',
                },
                'de': {
                    'language': 'de',
                    'value': 'Welt',
                },
                'foo': {
                    'language': 'foo',
                    'value': 'World',
                },
            },
        }
        second = {}
        if pycountry:
            results = [
                '- labels: Welt (in German)\n',
                '- labels: World (in English)\n',
                '- labels: World (in [Unknown language: foo])\n',
            ]
        else:
            results = [
                '- labels: Welt (in de)\n',
                '- labels: World (in en)\n',
                '- labels: World (in foo)\n',
            ]
        self.check_hunks(first, second, results)

    def test_aliases(self):
        """Test comparing aliases."""
        first = {
            'aliases': {
                'en': [
                    {
                        'language': 'en',
                        'value': 'Earth',
                    },
                    {
                        'language': 'en',
                        'value': 'Blue Planet',
                    }
                ],
                'foo': [
                    {
                        'language': 'foo',
                        'value': 'Earth',
                    },
                ],
            },
        }
        second = {}
        if pycountry:
            results = [
                '- aliases: Earth (in English)\n',
                '- aliases: Blue Planet (in English)\n',
                '- aliases: Earth (in [Unknown language: foo])\n',
            ]
        else:
            results = [
                '- aliases: Earth (in en)\n',
                '- aliases: Blue Planet (in en)\n',
                '- aliases: Earth (in foo)\n',
            ]
        self.check_hunks(first, second, results)

    def test_timestamp_format(self):
        """Test format_timestamp method."""
        tests = {
            '2017-01-10T09:17:08Z': '2017-01-10T09:17:08Z',
            '2017-01-10T00:00:00Z': '01/10/2017',
            '1650-01-01T00:00:00Z': '1650 AD',
            '1234-00-00T00:00:00Z': '1234 AD',
            '-150-01-01T00:00:00Z': '150 BC',
            '-1000000000-01-01T00:00:00Z': '1000000000 BC',
            '1000000000-01-01T00:00:00Z': '1000000000 AD',
            '2016-25-01T00:00:00Z': '2016-25-01T00:00:00Z',
        }
        for key in tests:
            self.assertEqual(WikibasePatchManager.format_timestamp(key), tests[key])


class LiveWikibasePatchManagerTests(TestCase):
    """Test WikibasePatchManager using live tests."""

    family = 'wikidata'
    code = 'wikidata'

    def check_hunks(self, first, second, results):
        """Helper method, used to check if WikibasePatchManager returned expected results."""
        p = WikibasePatchManager(first, second, self.site)
        self.assertEqual(len(p.hunks), len(results))
        for i in range(0, len(p.hunks)):
            self.assertEqual(p.hunks[i].diff_plain_text, results[i])

    def load_wikibase_entity(self, name):
        """Load wikibase entity located in file in pages."""
        with open(join_pages_path(name + '.wd')) as f:
            return json.load(f)

    def setUp(self):
        """Setup test."""
        self.q2 = self.load_wikibase_entity('Q2')
        self.q60 = self.load_wikibase_entity('Q60')
        super(LiveWikibasePatchManagerTests, self).setUp()

    def test_claims(self):
        """Test comparing and simplifying output of claims."""
        first = {
            'claims': {
                'P18': self.q2['claims']['P18'],
                'P138': self.q2['claims']['P138'],
                'P1334': self.q2['claims']['P1334'],
                'P1332': self.q2['claims']['P1332'],
                'P1335': self.q2['claims']['P1335'],
                'P1343': self.q2['claims']['P1343'][0:1],
                'P3417': self.q2['claims']['P3417'],
                'P1': [
                    {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': 'P1',
                            'type': 'unknown',
                            'datavalue': {
                                'value': 'unknown',
                                'type': 'unknown',
                            },
                            'datatype': 'unknown',
                        },
                    },
                ],
            },
        }
        second = {
            'claims': {
                'P138': self.q60['claims']['P138'],
            },
        }
        results = [
            '- claims.P1 ([Unknown Property])[0]: [Unknown property type: unknown]\n',

            '- claims.P1332 (coordinate of northernmost point)[0]:'
            ' lat: 90 long: 0 ±2.77778e-07 (on Earth)\n',

            '- claims.P1334 (coordinate of easternmost point)[0]: No data\n',
            '- claims.P1335 (coordinate of westernmost point)[0]: No data\n',
            '- claims.P1343 (described by source)[0]: Otto\'s encyclopedia ([No English label])\n',

            '- claims.P138 (named after)[0]: soil\n'
            '+ claims.P138 (named after)[0]: York\n',

            '- claims.P18 (image)[0]: The Earth seen from Apollo 17.jpg (Commons Media)\n',
            '- claims.P3417 (Quora topic ID)[0]: Earth-planet\n',
        ]
        self.check_hunks(first, second, results)

    def test_qualifiers(self):
        """Test qualifiers being added to output while comparing claims."""
        first = {
            'claims': {
                'P1082': self.q2['claims']['P1082'][0:1],
            }
        }
        second = {}
        results = [
            '- claims.P1082 (population)[0]: +7000000 [+6000000...+8000000]'
            ' (4000 BC (Proleptic Gregorian calendar))\n',
        ]
        self.check_hunks(first, second, results)
