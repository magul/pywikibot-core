# -*- coding: utf-8 -*-
"""Family module for Referata."""

from pywikibot import family


class Family(family.AutoSubdomainFamily):

    """Family class for Referata."""

    name = 'referata'
    domain = 'referata.com'
    # Only useful 'meta' wikis are included here.
    # Any other valid wiki may also be accessed, but a warning will appear.
    # To disable the warning, you may add other subdomains here, however
    # changes to this file are not supported and may cause conflicts in
    # the future.
    codes = ['www', 'scratchpad', 'wikilit', 'wikipapers', 'smw']
