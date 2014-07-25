#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to remove links that are being or have been spammed.

Usage:

spamremove.py www.spammedsite.com

It will use Special:Linksearch to find the pages on the wiki that link to
that site, then for each page make a proposed change consisting of removing
all the lines where that url occurs. You can choose to:
* accept the changes as proposed
* edit the page yourself to remove the offending link
* not change the page in question

Command line options:
-always           Do not ask, but remove the lines automatically. Be very
                  careful in using this option!

In addition, these arguments can be used to restrict changes to some pages:

&params;

"""

#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import pywikibot
from pywikibot import i18n, pagegenerators, Bot
from pywikibot.editor import TextEditor

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class SpamRemoveBot(Bot):

    """Bot to remove links that are being or have been spammed."""

    def __init__(self, generator, spam_external_url, **kwargs):
        super(SpamRemoveBot, self).__init__(**kwargs)
        self.generator = generator
        self.spam_external_url = spam_external_url
        self.changed_pages = 0

    def treat(self, page):
        text = page.text
        if self.spam_external_url not in text:
            continue
        self.current_page = page
        lines = text.split('\n')
        newpage = []
        lastok = ''
        for line in lines:
            if self.spam_external_url in line:
                if lastok:
                    pywikibot.output(lastok)
                pywikibot.output('\03{lightred}%s\03{default}' % line)
                lastok = None
            else:
                newpage.append(line)
                if line.strip():
                    if lastok is None:
                        pywikibot.output(line)
                    lastok = line
        if self.getOption('always'):
            answer = 'y'
        else:
            answer = pywikibot.input_choice(
                u'\nDelete the red lines?',
                [('yes', 'y'), ('no', 'n'), ('edit', 'e')],
                'n', automatic_quit=False)
        if answer == 'n':
            continue
        elif answer == 'e':
            editor = TextEditor()
            newtext = editor.edit(text, highlight=self.spam_external_url,
                                  jumpIndex=text.find(self.spam_external_url))
        else:
            newtext = '\n'.join(newpage)
        if newtext != text:
            summary = i18n.twtranslate(page.site, 'spamremove-remove',
                                       {'url': self.spam_external_url})
            page.text = newtext
            page.save(summary)
            self.changed_pages += 1


def main(*args):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    spam_external_url = None
    options = {}
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif genFactory.handleArg(arg):
            continue
        else:
            spam_external_url = arg

    if not spam_external_url:
        pywikibot.showHelp()
        pywikibot.output(u'No spam site specified.')
        return

    link_search = pagegenerators.LinksearchPageGenerator(spam_external_url)
    generator = genFactory.getCombinedGenerator(gen=link_search)
    generator = pagegenerators.PreloadingGenerator(generator)

    bot = SpamRemoveBot(generator, spam_external_url, **options)
    bot.run()
    pywikibot.output(u'\n%d pages changed.' % bot.changed_pages)


if __name__ == '__main__':
    main()
