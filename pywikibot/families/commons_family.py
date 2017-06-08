# -*- coding: utf-8 -*-
"""Family module for Wikimedia Commons."""
#
# (C) Pywikibot team, 2005-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Wikimedia Commons family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia Commons."""

    name = 'commons'

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()

        self.interwiki_forward = 'wikipedia'

        # do not add redirected templates
        self.category_redirect_templates = {
            'commons': (
                u'Category redirect',
                u'Synonym taxon category redirect',
                u'Invalid taxon category redirect',
                u'Monotypic taxon category redirect',
            ),
        }

        # Subpages for documentation.
        self.doc_subpages = {
            '_default': ((u'/doc', ), ['commons']),
        }
