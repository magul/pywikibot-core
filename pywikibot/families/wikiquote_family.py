# -*- coding: utf-8 -*-
"""Family module for Wikiquote."""
#
# (C) Pywikibot team, 2005-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikiquote
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikiquote."""

    name = 'wikiquote'

    closed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'als', 'am', 'ang', 'ast', 'bm', 'co', 'cr', 'ga', 'kk',
        'kr', 'ks', 'kw', 'lb', 'na', 'nds', 'qu', 'simple',
        'tk', 'tt', 'ug', 'vo', 'za', 'zh_min_nan',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=deleted.dblist
        'tokipona',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'it', 'pl', 'ru', 'cs', 'de', 'pt', 'es', 'fa', 'uk', 'sk',
            'fr', 'bs', 'tr', 'he', 'ca', 'lt', 'bg', 'eo', 'sl', 'fi', 'th',
            'el', 'hy', 'nn', 'id', 'hr', 'zh', 'hu', 'li', 'su', 'nl', 'az',
            'ko', 'ja', 'ar', 'gu', 'sv', 'gl', 'ur', 'te', 'ta', 'cy', 'la',
            'vi', 'no', 'ml', 'et', 'ku', 'kn', 'sr', 'ro', 'eu', 'be', 'hi',
            'ka', 'da', 'sa', 'is', 'sq', 'mr', 'br', 'uz', 'af', 'zh-min-nan',
            'am', 'wo', 'ky',
        ]

        super(Family, self).__init__()

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/BPI#Current_implementation
        # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
        self.cross_allowed = [
            'af', 'ar', 'az', 'be', 'bg', 'br', 'bs', 'ca', 'cs',
            'cy', 'da', 'el', 'eo', 'es', 'et', 'eu', 'fa', 'fi',
            'fr', 'gl', 'gu', 'he', 'hi', 'hu', 'hy', 'id', 'is',
            'it', 'ja', 'ka', 'kn', 'ko', 'ku', 'ky', 'la', 'li',
            'lt', 'ml', 'mr', 'nl', 'nn', 'no', 'pt', 'ro', 'ru',
            'sk', 'sl', 'sq', 'sr', 'su', 'sv', 'ta', 'te', 'tr',
            'uk', 'ur', 'uz', 'vi', 'wo', 'zh',
        ]

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['en']
                         ),
        }

    def code2encodings(self, code):
        """
        Return a list of historical encodings for a specific language.

        @param code: site code
        """
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        return self.code2encoding(code),
