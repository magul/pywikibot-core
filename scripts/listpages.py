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
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import os

import pywikibot

from pywikibot import config2 as config
from pywikibot.bot import (
    EverySitePageGeneratorBot,
    QuietCurrentPageBot,
    ExistingPageBot
)

from pywikibot.pagegenerators import parameterHelp

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


class ListPageTitlesBot(EverySitePageGeneratorBot, QuietCurrentPageBot):

    def __init__(self, fmt='1', lang=None, *args, **kwargs):
        """Constructor."""
        super(ListPageTitlesBot, self).__init__(*args, **kwargs)
        self.fmt = fmt
        self.lang = lang

    def treat_page(self):
        """Print page."""
        page = self.current_page
        fmt = self.fmt
        i = self._treat_counter
        outputlang = self.lang

        page_fmt = Formatter(page, outputlang)
        pywikibot.stdout(page_fmt.output(num=i, fmt=fmt))


class SavePagesBot(ExistingPageBot):

    def __init__(self, base_dir=None, encoding=None, *args, **kwargs):
        """Constructor."""
        super(SavePagesBot, self).__init__(*args, **kwargs)
        self.base_dir = base_dir
        self.encoding = encoding or config.textfile_encoding

    def treat_page(self):
        """Save page."""
        base_dir = self.base_dir
        encoding = self.encoding

        page = self.current_page

        family_name = page.site.family.name
        code = page.site.code

        site_dir = os.path.join(base_dir, family_name, code)
        if not os.path.exists(site_dir):
            os.makedirs(site_dir, mode=0o744)

        filename = os.path.join(site_dir, page.title(as_filename=True))
        pywikibot.output(u'Saving %s to %s' % (page.title(), filename))
        with open(filename, mode='wb') as f:
            f.write(page.text.encode(encoding))


class ListPagesBot(ListPageTitlesBot, SavePagesBot):

    def __init__(self, show_title=True, *args, **kwargs):
        """Constructor."""
        super(ListPagesBot, self).__init__(*args, **kwargs)
        self.show_title = show_title

    def treat_page(self):
        if self.show_title:
            ListPageTitlesBot.treat_page(self)

        pywikibot.output(self.current_page.text, toStdout=True)

        if self.base_dir:
            SavePagesBot.treat_page(self)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # gen = None
    notitle = False
    fmt = '1'
    # outputlang = None
    page_get = False
    base_dir = None
    encoding = config.textfile_encoding

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)

    generator_args = []

    for arg in local_args:
        if arg == '-notitle':
            notitle = True
        elif arg.startswith('-format:'):
            fmt = arg[len('-format:'):]
            fmt = fmt.replace(u'\\03{{', u'\03{{')
        # elif arg.startswith('-outputlang:'):
        #     outputlang = arg[len('-outputlang:'):]
        elif arg == '-get':
            page_get = True
        elif arg.startswith('-save'):
            base_dir = arg.partition(':')[2] or '.'
        elif arg.startswith('-encode:'):
            encoding = arg.partition(':')[2]
        else:
            generator_args.append(arg)

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

    if generator_args and (not notitle or page_get or base_dir):
        if page_get or base_dir:
            bot = ListPagesBot(fmt=fmt, show_title=not notitle,
                               base_dir=base_dir, encoding=encoding,
                               families='all', codes='all',
                               generator_args=generator_args)
        else:
            bot = ListPageTitlesBot(fmt=fmt,
                                    families='all', codes='all',
                                    generator_args=generator_args)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == "__main__":
    main()
