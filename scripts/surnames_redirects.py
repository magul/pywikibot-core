#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Bot to create redirects based on name order.

By default it creates a "Surnames, Given Names" redirect
version of a given page where title is 2 or 3 titlecased words.

Command-line arguments:

&params;

-surnames_last    Creates a "Given Names Surnames" redirect version of a
                  given page where title is "Surnames, Given Names".

Example: "python surnames_redirects.py -start:B"
"""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from difflib import SequenceMatcher

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import FollowRedirectPageBot, ExistingPageBot

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class SurnamesBot(FollowRedirectPageBot, ExistingPageBot):

    """Surnames Bot."""

    def __init__(self, generator, **kwargs):
        """Constructor.

        Parameters:
            @param generator: The page generator that determines on which pages to work.
            @kwarg surnames-last: Redirect "Surnames, Given Names" to "Given Names Surnames".
        """
        self.availableOptions.update({
            'surnames_last': False,
        })

        super(SurnamesBot, self).__init__(generator=generator, **kwargs)

    def treat_page(self):
        """Create redirects to the current page if page is likely to be a person's name."""
        if self.current_page.isRedirectPage():
            return

        page_t = self.current_page.title()
        site = self.current_page.site

        possible_redirects = []
        if self.getOption('surnames_last'):
            name_parts = page_t.split(', ')
            if len(name_parts) == 2 and len(page_t.split(' ')) <= 3:
                possible_redirects.append(name_parts[1] + ' ' + name_parts[0])
        else:
            words = page_t.split()
            if len(words) == 2 and page_t == page_t.title():
                possible_redirects.append(words[1] + ', ' + words[0])
            elif len(words) == 3:
                """page title should be titlecased or at most with one non-titlecased word"""
                if len(SequenceMatcher(None, page_t, page_t.title()).get_matching_blocks()) <= 3:
                    possible_redirects.append(words[1] + ' ' + words[2] + ', ' + words[0])
                    possible_redirects.append(words[2] + ', ' + words[0] + ' ' + words[1])

        for possible_name in possible_redirects:
            page_cap = pywikibot.Page(site, possible_name)
            if page_cap.exists():
                pywikibot.output(u'%s already exists, skipping...\n'
                                 % page_cap.title(asLink=True))
            else:
                pywikibot.output(u'%s doesn\'t exist'
                                 % page_cap.title(asLink=True))
                choice = pywikibot.input_choice(
                    u'Do you want to create a redirect?',
                    [('Yes', 'y'), ('No', 'n')], 'n')
                if choice == 'y':
                    comment = i18n.twtranslate(
                        site,
                        'capitalize_redirects-create-redirect',
                        {'to': page_t})
                    page_cap.set_redirect_target(self.current_page, create=True,
                                                 summary=comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}

    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-surnames_last':
            options['surnames_last'] = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = SurnamesBot(preloadingGen, **options)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
