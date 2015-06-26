# -*- coding: utf-8  -*-
"""Family module for Incubator Wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Wikimedia Incubator family
class IncubatorFamily(family.WikimediaFamily):

    """Family class for Incubator Wiki."""

    name = 'incubator'

    langs = {
        'incubator': 'incubator.wikimedia.org',
    }
