#!/usr/bin/python
# -*- coding: utf-8  -*-
r"""
Print a list of pages, as defined by page generator parameters.

Optionally, it also prints page content to STDOUT or save it to a file
in the current directory.

These parameters are supported to specify which pages titles to print:

-format  Defines the output format.

         Can be a custom string according to python string.format() notation or
         can be selected by a number from following list (1 is default format):
         1 - u'{num:4d} {page.title}'
             --> 10 PageTitle

         2 - u'{num:4d} {[[page.title]]}'
             --> 10 [[PageTitle]]

         3 - u'{page.title}'
             --> PageTitle

         4 - u'{[[page.title]]}'
             --> [[PageTitle]]

         5 - u'{num:4d} \03{{lightred}}{page.loc_title:<40}\03{{default}}'
             --> 10 PageTitle (colorised in lightred)

         6 - u'{num:4d} {page.loc_title:<40} {page.can_title:<40}'
             --> 10 localised_Namespace:PageTitle canonical_Namespace:PageTitle

         7 - u'{num:4d} {page.loc_title:<40} {page.trs_title:<40}'
             --> 10 localised_Namespace:PageTitle outputlang_Namespace:PageTitle
             (*) requires "outputlang:lang" set.

         num is the sequential number of the listed page.

-outputlang   Language for translation of namespaces.

-notitle Page title is not printed.

-get     Page content is printed.

-save    Save Page content to a file named as page.title(as_filename=True).
         Directory can be set with -dir:dir_name
         If no dir is specified, current direcory will be used.

-encode  File encoding can be specified with '-encode:name' (name must be a
         valid python encoding: utf-8, etc.).
         If not specified, it defaults to config.textfile_encoding.

-listify Make a list of all of the articles that are in a category and saves into 
         a page given by -dir:dir_name. If no dir is specified, current directory will be used.


Custom format can be applied to the following items extrapolated from a
    page object:

    site: obtained from page._link._site.

    title: obtained from page._link._title.

    loc_title: obtained from page._link.canonical_title().

    can_title: obtained from page._link.ns_title().
        based either the canonical namespace name or on the namespace name
        in the language specified by the -trans param;
        a default value '******' will be used if no ns is found.

    onsite: obtained from pywikibot.Site(outputlang, self.site.family).

    trs_title: obtained from page._link.ns_title(onsite=onsite).
        If selected format requires trs_title, outputlang must be set.


&params;
"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import os

import pywikibot
from pywikibot import config2 as config
from pywikibot.pagegenerators import GeneratorFactory, parameterHelp

docuReplacements = {'&params;': parameterHelp}


class Formatter(object):

    """Structure with Page attributes exposed for formatting from cmd line."""

    fmt_options = {
        '1': u"{num:4d} {page.title}",
        '2': u"{num:4d} [[{page.title}]]",
        '3': u"{page.title}",
        '4': u"[[{page.title}]]",
        '5': u"{num:4d} \03{{lightred}}{page.loc_title:<40}\03{{default}}",
        '6': u"{num:4d} {page.loc_title:<40} {page.can_title:<40}",
        '7': u"{num:4d} {page.loc_title:<40} {page.trs_title:<40}",
    }

    # Identify which formats need outputlang
    fmt_need_lang = [k for k, v in fmt_options.items() if 'trs_title' in v]

    def __init__(self, page, outputlang=None, default='******'):
        """
        Constructor.

        @param page: the page to be formatted.
        @type page: Page object.
        @param outputlang: language code in which namespace before title should
            be translated.

            Page ns will be searched in Site(outputlang, page.site.family)
            and, if found, its custom name will be used in page.title().

        @type outputlang: str or None, if no translation is wanted.
        @param default: default string to be used if no corresponding
            namespace is found when outputlang is not None.

        """
        self.site = page._link.site
        self.title = page._link.title
        self.loc_title = page._link.canonical_title()
        self.can_title = page._link.ns_title()
        self.outputlang = outputlang
        if outputlang is not None:
            # Cache onsite in case of translations.
            if not hasattr(self, "onsite"):
                self.onsite = pywikibot.Site(outputlang, self.site.family)
            try:
                self.trs_title = page._link.ns_title(onsite=self.onsite)
            # Fallback if no corresponding namespace is found in onsite.
            except pywikibot.Error:
                self.trs_title = u'%s:%s' % (default, page._link.title)

    def output(self, num=None, fmt=1):
        """Output formatted string."""
        fmt = self.fmt_options.get(fmt, fmt)
        # If selected format requires trs_title, outputlang must be set.
        if (fmt in self.fmt_need_lang or
                'trs_title' in fmt and
                self.outputlang is None):
            raise ValueError(
                u"Required format code needs 'outputlang' parameter set.")
        if num is None:
            return fmt.format(page=self)
        else:
            return fmt.format(num=num, page=self)

class Listing_Categories(object):

    def __init__(self, catTitle, base_dir=None, subCats=False, talkPages=False,
        recurse=False, encoding=config.textfile_encoding):
        """Constructor."""
        self.site = pywikibot.Site()
        self.cat = pywikibot.Category(self.site, catTitle)
        self.subCats = subCats
        self.talkPages = talkPages
        self.recurse = recurse
        self.base_dir=base_dir
        self.listString=""
        self.encoding=encoding

    def run(self):
        """writing list into file."""
        setOfArticles = set(self.cat.articles(recurse=self.recurse))
        if self.subCats:
            setOfArticles = setOfArticles.union(set(self.cat.subcategories()))
        for article in setOfArticles:
            if self.talkPages and not article.isTalkPage():
                self.listString += "%s -- %s|talk\n" % (article.title(), article.toggleTalkPage().title())
            else:
                self.listString += "%s\n" % article.title()
        if self.base_dir:
            filename=pywikibot.input(u'Enter the name of the file')
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, mode='wb') as f:
                f.write(self.listString.encode(self.encoding))



def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    gen = None
    notitle = False
    fmt = '1'
    outputlang = None
    page_get = False
    base_dir = None
    encoding = config.textfile_encoding
    flag=1
    recurse=False
    talkPages=False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = GeneratorFactory()

    for arg in local_args:
        if arg == '-notitle':
            notitle = True
        elif arg.startswith('-format:'):
            fmt = arg[len('-format:'):]
            fmt = fmt.replace(u'\\03{{', u'\03{{')
        elif arg.startswith('-outputlang:'):
            outputlang = arg[len('-outputlang:'):]
        elif arg == '-get':
            page_get = True
        elif arg.startswith('-save'):
            base_dir = arg.partition(':')[2] or '.'
        elif arg.startswith('-encode:'):
            encoding = arg.partition(':')[2]
        elif arg.startswith('-listify'):
            flag=0
            base_dir=arg.partition(':')[2] or '.'
        elif arg == '-recurse':
            recurse = True
        elif arg == '-talkpages':
            talkPages = True
        else:
            genFactory.handleArg(arg)
    
        if base_dir:
            base_dir = os.path.expanduser(base_dir)
            if not os.path.isabs(base_dir):
                base_dir = os.path.normpath(os.path.join(os.getcwd(), base_dir))

            if not os.path.exists(base_dir):
                pywikibot.output(u'Directory "%s" does not exist.' % base_dir)
                choice = pywikibot.input_yn(
                    u'Do you want to create it ("No" to continue without saving)?')
                if choice:
                    os.makedirs(base_dir, mode=0o744)
                else:
                    base_dir = None
            elif not os.path.isdir(base_dir):
                # base_dir is a file.
                pywikibot.warning(u'Not a directory: "%s"\n'
                                  u'Skipping saving ...'
                                  % base_dir)
                base_dir = None
    if flag==1:            

        gen = genFactory.getCombinedGenerator()
        if gen:
            i = 0
            for i, page in enumerate(gen, start=1):
                if not notitle:
                    page_fmt = Formatter(page, outputlang)
                    pywikibot.stdout(page_fmt.output(num=i, fmt=fmt))
                if page_get:
                    try:
                        pywikibot.output(page.text, toStdout=True)
                    except pywikibot.Error as err:
                        pywikibot.output(err)
                if base_dir:
                    filename = os.path.join(base_dir, page.title(as_filename=True))
                    pywikibot.output(u'Saving %s to %s' % (page.title(), filename))
                    with open(filename, mode='wb') as f:
                        f.write(page.text.encode(encoding))
            pywikibot.output(u"%i page(s) found" % i)
            return True
        else:
            pywikibot.bot.suggest_help(missing_generator=True)
            return False
    else:
        cat=pywikibot.input("Enter the category")
        bot = Listing_Categories(cat, base_dir,subCats=True,
            talkPages=talkPages, recurse=recurse, encoding=encoding)
        if bot:
            pywikibot.Site().login()

            try:
                bot.run()
            except pywikibot.Error:
                pywikibot.error("Fatal error:", exc_info=True)
            return True
        else:
            pywikibot.bot.suggest_help(missing_action=True)
            return False


if __name__ == "__main__":
    main()
