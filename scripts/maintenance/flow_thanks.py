#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script to thank flow posts.

This script understands the following command line arguments:

-flow_post:  The value of the postid to be thanked.

"""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot.exceptions import UnknownSite

from pywikibot.tools import StringTypes

import pywikibot


def thank_flow_post(site, postid):
    """Thank the given Post ID on a Flow Board."""
    # Login
    if not isinstance(site, pywikibot.site.APISite):
        raise UnknownSite('This is not a valid site.')
    site.login()
    # Make Thank API call to site
    if not isinstance(postid, StringTypes):
        raise TypeError('Postid must be a string literal.')
    try:
        site.thank_flowpost(postid)
    except Exception as e:
        raise ValueError('Invalid postid throwing up {0}'.format(e))


def main(*args):
    """Process command line arguments and thank the post."""
    # Default
    postid = None

    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-flow_post':
            postid = value
    # Initializing Site
    site = pywikibot.Site()
    # Errors relayed to User.
    if not isinstance(site, pywikibot.site.APISite):
        pywikibot.output('This is not a valid site.')
    if not isinstance(postid, StringTypes):
        pywikibot.output('Postid must be a string literal.')
    thank_flow_post(site, postid)


if __name__ == "__main__":
    main()
