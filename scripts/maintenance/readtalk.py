#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Tool to read all your talk pages.

This tool will go through all the normal (not sysop) accounts configured in
user-config and output the contents of the talk page.

TODO:
*Error checking
"""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import sys
sys.path.append(re.sub('/[^/]*$', '', sys.path[0]))
sys.path.insert(1, '..')
import pywikibot
from pywikibot import config2 as config
from pywikibot.comms import http


def readtalk(lang, familyName, sysop=False):
    site = pywikibot.Site(code=lang, fam=familyName)
    if sysop:
        user = pywikibot.User(site, config.sysopnames[familyName][lang])
    else:
        user = pywikibot.User(site, config.usernames[familyName][lang])
    page = user.getUserTalkPage()
    if not site.username(sysop=True):
        site.login()
    if site.messages(sysop):
        pywikibot.output("cleaning up the account new message notice")

        pagetext = http.fetch(uri=page.full_url())
        del pagetext
    pywikibot.output(u'Reading talk page from %s' % user)
    try:
        pywikibot.output(page.text + "\n")
    except pywikibot.NoPage:
        pywikibot.output('Talk page is not exist.')
    except pywikibot.UserBlocked:
        pywikibot.output('Account is blocked.')


def main():
    # Get a dictionary of all the usernames
    all = False
    sysop = False

    for arg in pywikibot.handle_args():
        if arg.startswith('-all'):
            all = True
        elif arg.startswith('-sysop'):
            sysop = True
    if all is True:
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
