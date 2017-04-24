#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This script transfers pages from a source wiki to a target wiki.

It also copies edit history to a subpage.

-tocode:          The target site code.

-tosite:          The target site family.

-prefix:          Page prefix on the new site.

-overwrite:       Existing pages are skipped by default. Use his option to
                  overwrite pages.

Internal links are *not* repaired!

Pages to work on can be specified using any of:

&params;

Example commands:

Transfer all pages in category "Query service" from the English Wikipedia to
the Arabic Wiktionary, adding "Wiktionary:Import enwp/" as prefix:

    python pwb.py transferbot -family:wikipedia -code:en -cat:"Query service" \
        -tofamily:wiktionary -tocode:ar -prefix:"Wiktionary:Import enwp/"

Copy the template "Query service" from the Toolserver wiki to wikitech:

    python pwb.py transferbot -family:wikipedia -code:en \
        -tofamily:wiktionary -tocode:ar -page:"Template:Query service"

"""
#
# (C) Merlijn van Deen, 2014
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot.exceptions import ArgumentDeprecationWarning
from pywikibot import pagegenerators
from pywikibot.tools import issue_deprecation_warning

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class WikiTransferException(Exception):

    """Base class for exceptions from this script.

    Makes it easier for clients to catch all expected exceptions that the script might
    throw
    """

    pass


class TargetSiteMissing(WikiTransferException):

    """Thrown when the target site is the same as the source site.

    Based on the way each are initialized, this is likely to happen when the target site
    simply hasn't been specified.
    """

    pass


class TargetPagesMissing(WikiTransferException):

    """Thrown if no page range has been specified for the script to operate on."""

    pass


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    local_args = pywikibot.handle_args(args)

    fromsite = pywikibot.Site()
    tolang = fromsite.code
    tofamily = fromsite.family.name
    prefix = ''
    overwrite = False
    gen_args = []

    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        option, sep, value = arg.partition(':')
        if genFactory.handleArg(arg):
            gen_args.append(arg)
            continue
        if option == '-tofamily':
            tofamily = value
        elif option in ('-tolang', '-tocode'):
            if option == '-tolang':
                issue_deprecation_warning(
                    option, '-tocode', 1, ArgumentDeprecationWarning)
            tolang = value
        elif option == '-prefix':
            prefix = value
        elif option == '-overwrite':
            overwrite = True

    tosite = pywikibot.Site(tolang, tofamily)
    if fromsite == tosite:
        raise TargetSiteMissing('Target site not different from source site')

    gen = genFactory.getCombinedGenerator()
    if not gen:
        raise TargetPagesMissing('Target pages not specified')

    gen_args = ' '.join(gen_args)
    pywikibot.output(u"""
    Page transfer configuration
    ---------------------------
    Source: %(fromsite)r
    Target: %(tosite)r

    Pages to transfer: %(gen_args)s

    Prefix for transferred pages: %(prefix)s
    """ % {'fromsite': fromsite, 'tosite': tosite,
           'gen_args': gen_args, 'prefix': prefix})

    for page in gen:
        summary = "Moved page from %s" % page.title(asLink=True)
        targetpage = pywikibot.Page(tosite, prefix + page.title())
        edithistpage = pywikibot.Page(tosite, prefix + page.title() + '/edithistory')

        if targetpage.exists() and not overwrite:
            pywikibot.output(
                u"Skipped %s (target page %s exists)" % (
                    page.title(asLink=True),
                    targetpage.title(asLink=True)
                )
            )
            continue

        pywikibot.output(u"Moving %s to %s..."
                         % (page.title(asLink=True),
                            targetpage.title(asLink=True)))

        pywikibot.log("Getting page text.")
        text = page.get(get_redirect=True)
        text += ("<noinclude>\n\n<small>This page was moved from %s. It's "
                 "edit history can be viewed at %s</small></noinclude>"
                 % (page.title(asLink=True, insite=targetpage.site),
                    edithistpage.title(asLink=True, insite=targetpage.site)))

        pywikibot.log("Getting edit history.")
        historytable = page.getVersionHistoryTable()

        pywikibot.log("Putting page text.")
        targetpage.put(text, summary=summary)

        pywikibot.log("Putting edit history.")
        edithistpage.put(historytable, summary=summary)


if __name__ == "__main__":
    try:
        main()
    except TargetSiteMissing as e:
        pywikibot.error(u'Need to specify a target site and/or language')
        pywikibot.error(u'Try running this script with -help for help/usage')
        pywikibot.exception()
    except TargetPagesMissing as e:
        pywikibot.error(u'Need to specify a page range')
        pywikibot.error(u'Try running this script with -help for help/usage')
        pywikibot.exception()
