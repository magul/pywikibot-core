# -*- coding: utf-8 -*-

"""Family module for Wikimedia wikimania wikis."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals
from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.SubdomainFamily, family.WikimediaFamily):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikimania'
        self.langs = {
            'en': 'wikimania2018.wikimedia.org',
        }

    def scriptpath(self, code):
        return {
            'en': '/wiki',
        }[code]

    @deprecated('APISite.version()')
    def version(self, code):
        return {
            'en': u'1.31.0-wmf.12',
        }[code]

    def protocol(self, code):
        return {
            'en': u'https',
        }[code]
