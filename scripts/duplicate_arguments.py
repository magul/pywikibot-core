# -*- coding: utf-8  -*-
"""Script to fix template calls with duplicate arguments."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#

import sys
from collections import defaultdict

import mwparserfromhell

import pywikibot
from pywikibot import i18n, pagegenerators, Bot
from pywikibot.data import api

if sys.version_info[0] > 2:
    unicode = str


class DuplicateArgumentsBot(Bot):

    """Bot to fix template calls with duplicate arguments."""

    comment = {
        'en': u'remove duplicate arguments in template calls'
    }

    def __init__(self, **kwargs):
        self.availableOptions.update({
            'action_if_all_empty': None,
        })
        super(DuplicateArgumentsBot, self).__init__(**kwargs)

    def treat(self, page):
        self.current_page = page
        code = mwparserfromhell.parse(page.text)
        edited = False  # to prevent unwanted changes
        for template in code.ifilter_templates():
            params = defaultdict(list)
            for param in template.params:
                params[param.name.strip()].append(param)
            for name, items in params.items():
                if len(items) == 1:
                    # unique parameters
                    continue
                empty = [param for param in items if param.value.strip() == '']
                diff = len(items) - len(empty)
                title = u'Found {count} params with name "{name}"'.format(
                    count=len(items), name=name)
                if diff == 0:
                    pywikibot.output(u'{title}, all empty.'.format(title=title))
                    choice = self.getOption('action_if_all_empty')
                else:
                    pywikibot.output(u'{title}:'.format(title=title))
                    for index, param in enumerate(items):
                        pywikibot.output(u'\03{{lightblue}}#{index}\03{{default}} = {value!r}'.format(
                            index=index, value=param.value))
                    choice = None
                if not choice:
                    choices = []
                    for index, param in enumerate(items):
                        choices.append((u'keep only occurrence #{index}'.format(index=index),
                                        unicode(index)))
                    choices += [(u'keep only the last occurrence', 'l'),
                                (u'remove all occurrences', 'r'),
                                (u'skip these params', 's')]
                    choice = pywikibot.input_choice(u'What to do?', choices)
                if choice == 's':
                    continue
                to_remove = items[:]
                if choice != 'r':
                    to_remove.pop(-1 if choice == 'l' else int(choice))
                for param in to_remove:
                    template.remove(param)
                    edited = True
        if edited:
            text = unicode(code)
            comment = i18n.translate(page.site.lang, self.comment, fallback=True)
            self.userPut(page, page.text, text, comment=comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    message_key = 'duplicate-args-category'
    tracking = False

    for arg in local_args:
        if arg == '-tracking':
            tracking = True
        else:
            genFactory.handleArg(arg)

    tracking_gen = None
    if tracking:
        site = pywikibot.Site()
        # TODO FIXME: make APISite.mediawiki_messages() support 'amenableparser'
        message_query = api.QueryGenerator(
            site=site,
            meta='allmessages',
            ammessages=message_key,
            amlang=site.lang,
            amenableparser=True
        )
        message = None
        for item in message_query:
            if item['name'] == message_key and '*' in item:
                message = item['*']
                break
        if message:
            category = pywikibot.Category(site, message)
            tracking_gen = pagegenerators.CategorizedPageGenerator(category)
        else:
            raise KeyError(u'Message "{key}" not found on site {site}'.format(
                key=message_key, site=site))
    gen = genFactory.getCombinedGenerator(gen=tracking_gen)
    if gen:
        bot = DuplicateArgumentsBot(generator=gen)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == '__main__':
    main()
