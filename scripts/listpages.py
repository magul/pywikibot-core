#!/usr/bin/python
# -*- coding: utf-8  -*-
r"""
Print a list of pages, as defined by page generator parameters.

Optionally, it also prints page content to STDOUT or save it to a file
in the current directory.

These parameters are supported to specify which pages titles to print:

-format  Defines the output format.

         Can be a custom string according to pywikibot.formatter.color_format()
         notation or can be selected by a number from following (default 1):
         1 - u'{num:4d} {page}'
             -->   10 PageTitle

         2 - u'{num:4d} {[[page]]}'
             -->   10 [[PageTitle]]

         3 - u'{page}'
             --> PageTitle

         4 - u'{[[page]]}'
             --> [[PageTitle]]

         5 - u'{num:4d} {lightred}{loc_title:<40}{default}'
             -->   10 PageTitle (colorised in lightred)

         6 - u'{num:4d} {loc_title:<40} {can_title:<40}'
             -->   10 localised_Namespace:PageTitle canonical_Namespace:PageTitle

         7 - u'{num:4d} {loc_title:<40} {trs_title:<40}'
             -->   10 localised_Namespace:PageTitle outputlang_Namespace:PageTitle
             (*) requires "outputlang:lang" set.

         num is the sequential number of the listed page starting from 1.

-outputlang   Language for translation of namespaces.

-notitle Page title is not printed.

-get     Page content is printed.

-save    Save Page content to a file named as page.title(as_filename=True).
         Directory can be set with -dir:dir_name
         If no dir is specified, current direcory will be used.

-encode  File encoding can be specified with '-encode:name' (name must be a
         valid python encoding: utf-8, etc.).
         If not specified, it defaults to config.textfile_encoding.


Custom format can be applied to the following items:

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

As the script is using L{pywikibot.tools.formatter.color_format}, it is not
necessary to escape color fields using two curly brackets and it is not
necessary to prefix them using C{\03}.

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
from pywikibot.tools.formatter import color_format

docuReplacements = {'&params;': parameterHelp}


class Formatter(object):

    """Formatter handling each entry."""

    fmt_options = {
        1: '{num:4d} {title}',
        2: '{num:4d} [[{title}]]',
        3: '{title}',
        4: '[[{title}]]',
        5: '{num:4d} {lightred}{loc_title:<40}{default}',
        6: '{num:4d} {loc_title:<40} {can_title:<40}',
        7: '{num:4d} {loc_title:<40} {trs_title:<40}',
    }

    def __init__(self, fmt, outputlang=None, default='******'):
        """
        Create a new instance to format entries.

        @param fmt: The format number or a format string..
        @type fmt: int or string
        @param outputlang: language code in which namespace before title should
            be translated.

            Page ns will be searched in Site(outputlang, page.site.family)
            and, if found, its custom name will be used in page.title().

        @type outputlang: str or None, if no translation is wanted.
        @param default: default string to be used if no corresponding
            namespace is found when outputlang is not None.

        """
        try:
            fmt = int(fmt)
        except ValueError:
            self.fmt = fmt
        else:
            self.fmt = self.fmt_options[fmt]
        if outputlang is None and '{trs_title' in self.fmt:
            raise ValueError(
                u"Required format code needs 'outputlang' parameter set.")
        self.outputlang = outputlang
        self.default = default

    def output(self, num, page):
        """Output formatted string."""
        if self.outputlang is not None:
            # Cache onsite in case of translations.
            onsite = pywikibot.Site(self.outputlang, page.site.family)
            try:
                trs_title = page._link.ns_title(onsite=onsite)
            # Fallback if no corresponding namespace is found in onsite.
            except pywikibot.Error:
                trs_title = u'%s:%s' % (self.default, page._link.title)
            optional_values = {'onsite': onsite, 'trs_title': trs_title}
        else:
            optional_values = {}

        return color_format(self.fmt, num=num, site=page.site,
                            title=page._link.title,
                            loc_title=page._link.canonical_title(),
                            can_title=page._link.ns_title(),
                            **optional_values)


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

    gen = genFactory.getCombinedGenerator()
    if gen:
        i = 0
        page_fmt = Formatter(fmt, outputlang)
        for i, page in enumerate(gen, start=1):
            if not notitle:
                pywikibot.stdout(page_fmt.output(i, page))
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


if __name__ == "__main__":
    main()
