# -*- coding: utf-8 -*-
"""
This family file was auto-generated by $Id$
Configuration parameters:
  url = https://wikimania2018.wikimedia.org/wiki
  name = wikimania

"""

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
