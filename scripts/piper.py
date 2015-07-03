#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot uses external filtering programs for munging text.

For example:

    python pwb.py piper.py -filter:'tr A-Z a-z' -page:Wikipedia:Sandbox

Would lower case the article with tr(1).

Muliple -filter commands can be specified:

    python pwb.py piper.py -filter:cat -filter:'tr A-Z a-z' -filter:'tr a-z A-Z' -page:Wikipedia:Sandbox


Would pipe the article text through cat(1) (NOOP) and then lower case
it with tr(1) and upper case it again with tr(1)

The following parameters are supported:

&params;

    -always        Always commit changes without asking you to accept them

    -filter:       Filter the article text through this program, can be
                   given multiple times to filter through multiple programs in
                   the order which they are given

"""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import os
import pipes
import tempfile

import pywikibot

from pywikibot import pagegenerators
from pywikibot.bot import (
    MultipleSitesBot,
    ExistingPageBot,
    NoRedirectPageBot,
    AutomaticTWSummaryBot,
)
from pywikibot.tools import deprecated_args

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class PiperBot(MultipleSitesBot,
               ExistingPageBot,
               NoRedirectPageBot,
               AutomaticTWSummaryBot):

    """Bot for munging text using external filtering programs."""

    summary_key = 'piper-edit-summary'

    @deprecated_args('comment')  # introduced in core port
    def __init__(self, generator, filters, always=False):
        """
        Constructor.

        @param generator: The page generator that determines on which pages
                          to work on.
        @param filters: list of commands to pipe page text through
        @type filters: list of unicode
        @param always: If True, don't prompt for changes
        @type always: bool
        """
        self.availableOptions.update({
            'always': False,
            'filters': [],
        })
        if not filters:
            raise ValueError('no filters specified')

        super(PiperBot, self).__init__(generator=generator,
                                       filters=filters, always=always)

        self._used_filters = None

    @property
    def summary_parameters(self):
        """A dictionary of available parameters for i18n."""
        return {
            'filters': ', '.join(self._used_filters),
        }

    def pipe(self, program, text):
        """Pipe a given text through a given program.

        @return: processed text after piping
        @rtype: unicode
        """
        text = text.encode('utf-8')
        pipe = pipes.Template()
        pipe.append(program.encode('ascii'), '--')

        # Create a temporary filename to save the piped stuff to
        tempFilename = '%s.%s' % (tempfile.mktemp(), 'txt')
        with pipe.open(tempFilename, 'w') as file:
            file.write(text)

        # Now retrieve the munged text
        with open(tempFilename, 'r') as mungedText:
            unicode_text = mungedText.read().decode('utf-8')

        # clean up
        os.unlink(tempFilename)
        return unicode_text

    def treat_page(self):
        """Load the given page, does some changes, and saves it."""
        # Load the page
        text = self.current_page.text

        self._filters_used = []

        # Munge!
        for program in self.getOption('filters'):
            old_text = text
            text = self.pipe(program, text)
            if text != old_text:
                self._filters_used.append(program)

        # only save if something was changed
        self.put_current(text)


def main(*args):
    """Create and run a PiperBot instance from the given command arguments."""
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The generator gives the pages that should be worked upon.
    gen = None
    # The program to pipe stuff through
    filters = []
    options = {}

    # Parse command line arguments
    for arg in pywikibot.handle_args(args):
        if arg.startswith("-filter:"):
            prog = arg[8:]
            filters.append(prog)
        elif arg.startswith("-always"):
            options['always'] = True
        else:
            # check if a standard argument like
            # -start:XYZ or -ref:Asdf was given.
            genFactory.handleArg(arg)

    options['filters'] = filters

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = PiperBot(gen, **options)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == '__main__':
    main()
