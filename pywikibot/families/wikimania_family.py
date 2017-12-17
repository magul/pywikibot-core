# -*- coding: utf-8 -*-
"""Family module for Wikimania wikis."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated

class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family for Wikimania wikis hosted on wikimedia.org."""

    name = 'wikimania2018'
    code = 'en'
