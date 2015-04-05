#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Tool to read all your talk pages.

This tool will output the content of the bot account talk page.
It also cleans the account new message notice.

The following command line parameters are supported:
-all              Use all accounts configured in user-config

-sysop            The sysop account(s) will be used
"""
#
# (C) Pywikibot team, 2008-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot.comms import http
from pywikibot import config2 as config


def readtalk(lang, familyName, sysop=False):
    """Read the talk page and output it."""
    site = pywikibot.Site(code=lang, fam=familyName)
    if sysop:
        user = pywikibot.User(site, config.sysopnames[familyName][lang])
    else:
        user = pywikibot.User(site, config.usernames[familyName][lang])
    page = user.getUserTalkPage()
    if not site.username(sysop):
        site.login()
    pywikibot.output('Reading talk page from {0}.'.format(user))
    try:
        page.get(get_redirect=True)
    except pywikibot.NoPage:
        pywikibot.output('Talk page does not exist.\n')
    else:
        if site.messages(sysop):
            pywikibot.output('Cleaning up the account new message notice.')

            http.fetch(uri=page.full_url())
        pywikibot.output(page.text + '\n')


def main():
    """Process command line arguments."""
    getall = False
    sysop = False

    for arg in pywikibot.handle_args():
        if arg.startswith('-all'):
            getall = True
        elif arg.startswith('-sysop'):
            sysop = True

    if getall:
        # Get a dictionary of all the usernames
        if sysop:
            namedict = config.sysopnames
        else:
            namedict = config.usernames
        for familyName in namedict.iterkeys():
            for lang in namedict[familyName].iterkeys():
                readtalk(lang, familyName, sysop)
    else:
        readtalk(config.mylang, config.family, sysop)

if __name__ == "__main__":
    main()
