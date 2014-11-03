# -*- coding: utf-8 -*-
"""Semantic MediaWiki family module."""

from pywikibot import family


class Family(family.Family):

    """Family class Semantic MediaWiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'semantic-mw'
        self.langs = {
            'en': 'semantic-mediawiki.org',
        }

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"

    def ignore_certificate_error(self, code):
        """Ignore certificate errors."""
        return True  # has an expired certificate.
