# -*- coding: utf-8 -*-
"""Family module for Wikimania wikis."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'translatewiki'
        self.langs = {
            'en': 'translatewiki.net',
        }