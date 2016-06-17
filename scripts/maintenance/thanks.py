#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script to thank revisions.

This script understands the following command line arguments:

-rev                The value of a single revision_id to be thanked.
-source             A string specifying the source of thanks.

Note:   1)rev and source accept singular values, not a comma separated list.
        2)If multiple instances of -rev or -source are provided, only the ones
        provided most recently are considered.

"""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot.exceptions import UnknownSite
from pywikibot.tools import StringTypes

import pywikibot


def thank_rev(site, revid, source):
    """Thank user of the revision_id."""
    # Login.
    if not isinstance(site, pywikibot.site.APISite):
        raise UnknownSite('This is not a valid site.')
    site.login()

    # Handling possible errors and invalid arguments.
    if isinstance(revid, float):
        raise TypeError('Revision ID must be an integer.')
    try:
        revid = int(revid)
    except ValueError:
        raise TypeError('Invalid Literal for Revision_ID')
    if revid is None and revid is not 0:
        raise ValueError('No Revision_ID given, use -rev:<revid>')
    if revid <= 0:
        raise ValueError('Revision_ID must be a positive integer.')
    if not isinstance(source, StringTypes):
        raise TypeError('Source must be a string or unicode literal')

    # Get user information from revid
    props = site.get_revision(revid)
    page_info = (props['query']['pages']).values()
    revision = page_info[0].get('revisions')
    username = revision[0].get('user')

    # Extract user, and check if user can be thanked.
    user = pywikibot.User(site, username)
    can_thank = user.thanks_enabled

    # Thanks the user for the revision.
    if can_thank:
        site.thank_revision(revid, source)
    else:
        pywikibot.output('The user for this revision, {0}, cannot be thanked.'
                         .format(username))


def main(*args):
    """Process command line arguments and thank the revision."""
    # Default values
    source = 'pywikibot'
    revid = None
    no_errors = True

    # Parsing the arguments
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-source':
            source = value
        if option == '-rev':
            revid = value

    # Initializing site, and printing error outputs.
    site = pywikibot.Site()
    if not isinstance(site, pywikibot.site.APISite):
        no_errors = False
        pywikibot.output('This is not a valid site.')
    if isinstance(revid, float):
        no_errors = False
        pywikibot.output('Revision ID must be an integer.')
    try:
        revid = int(revid)
    except Exception:
        no_errors = False
        pywikibot.output('Invalid Literal for Revision_ID')
    if revid is None and revid is not 0:
        no_errors = False
        pywikibot.output('No Revision_ID given, use -rev:<revid>')
    if revid <= 0:
        no_errors = False
        pywikibot.output('Revision_ID must be a positive integer.')
    if not isinstance(source, StringTypes):
        no_errors = False
        pywikibot.output('Source must be a string or unicode literal')

    # Thanking the revision
    if no_errors:
        thank_rev(site, revid, source)
    else:
        pywikibot.output('This thanks action cannot be completed.')

if __name__ == "__main__":
    main()
