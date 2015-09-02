#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a script written to add the template "orphan" to pages.

These command line parameters can be used to specify which pages to work on:

&params;

-xml              Retrieve information from a local XML dump (pages-articles
                  or pages-meta-current, see https://download.wikimedia.org).
                  Argument can also be given as "-xml:filename".

-page             Only edit a specific page.
                  Argument can also be given as "-page:pagetitle". You can
                  give this parameter multiple times to edit multiple pages.

Furthermore, the following command line parameters are supported:

-enable:          Enable or disable the bot via a Wiki Page.

-disambig:        Set a page where the bot saves the name of the disambig
                  pages found (default: skip the pages)

-limit:           Set how many pages check.

-always           Always say yes, won't ask

--- Examples ---

    python pwb.py lonelypages -enable:User:Bot/CheckBot -always
"""
#
# (C) Pietrodn, it.wiki 2006-2007
# (C) Filnik, it.wiki 2007
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import re
import sys

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import (
    suggest_help, SingleSiteBot, NoRedirectPageBot, SettingsBot,
    SettingsCallbackBot
)

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}


class OrphanTemplate(object):

    """The orphan template configuration."""

    def __init__(self, site, name, parameters, aliases=None, subst=False):
        self._name = name
        if not aliases:
            aliases = []
        elif not subst:
            aliases = list(aliases) + [name]
        else:
            name = 'subst:' + name
        if parameters:
            name += '|' + parameters
        self.template = '{{' + name + '}}'
        self._names = frozenset(aliases)
        self._site = site

        template_ns = site.namespaces[10]
        # TODO: Add redirects to self.names too
        if not pywikibot.Page(site, self._name, template_ns.id).exists():
            raise ValueError('Orphan template "{0}" does not exist on '
                             '"{1}".'.format(self._name, site))
        for name in self._names:
            if not pywikibot.Page(site, name, template_ns.id).exists():
                pywikibot.warning('Orphan template alias "{0}" does not exist '
                                  'on "{1}"'.format(name, site))
        self.regex = re.compile(
            r'\{\{(?:' + ':|'.join(template_ns) + '|)(' +
            '|'.join(re.escape(name) for name in self._names) +
            r')[\|\}]', re.I)


class LonelyPagesBot(NoRedirectPageBot, SingleSiteBot, SettingsBot,
                     SettingsCallbackBot):

    """Orphan page tagging bot."""

    settings_page = 'pywikibot-lonelypages'
    mandatory_settings = ['name', 'parameters']
    optional_settings = ['aliases', 'subst']
    settings_callback = OrphanTemplate

    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'enablePage': None,    # Check if someone set an enablePage or not
            'disambigPage': None,  # If no disambigPage given, not use it.
        })
        super(LonelyPagesBot, self).__init__(**kwargs)
        self.generator = generator

        # Take the configurations according to our project
        if self.getOption('enablePage'):
            self.options['enablePage'] = pywikibot.Page(
                self.site, self.getOption('enablePage'))
        self.comment = i18n.twtranslate(
            self.site, 'lonelypages-comment-add-template')
        self.commentdisambig = i18n.twtranslate(
            self.site, 'lonelypages-comment-add-disambig-template')
        self.site.login()
        try:
            orphan_template = self.get_settings(self.site)
        except ValueError as e:
            orphan_template = e
        if orphan_template is None or isinstance(orphan_template, ValueError):
            err_message = 'Missing configuration for site %s' % self.site
            suggest_help(exception=orphan_template, additional_text=err_message)
            sys.exit(err_message)
        # DisambigPage part
        if self.getOption('disambigPage') is not None:
            self.disambigpage = pywikibot.Page(self.site, self.getOption('disambigPage'))
            try:
                self.disambigtext = self.disambigpage.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't esist, skip!" % self.disambigpage.title())
                self.disambigtext = ''
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, don't use it!"
                                 % self.disambigpage.title())
                self.options['disambigPage'] = None

    def enable_page(self):
        enable = self.getOption('enablePage')
        if enable is not None:
            try:
                getenable = enable.get()
            except pywikibot.NoPage:
                pywikibot.output(
                    u"%s doesn't esist, I use the page as if it was blank!"
                    % enable.title())
                getenable = ''
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, skip!" % enable.title())
                getenable = ''
            return getenable == 'enable'
        return True

    def run(self):
        # If the enable page is set to disable, turn off the bot
        # (useful when the bot is run on a server)
        if not self.enable_page():
            pywikibot.output('The bot is disabled')
            return
        super(LonelyPagesBot, self).run()

    def treat_page(self):
        """Check if page is applicable and not marked and add template then."""
        page = self.current_page
        refs = list(page.getReferences(total=1))
        if len(refs) > 0:
            pywikibot.output(u"%s isn't orphan! Skip..." % page.title())
            return
        else:
            # no refs, no redirect; check if there's already the template
            try:
                oldtxt = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist! Skip..." % page.title())
                return
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect! Skip..." % page.title())
                return
            if self.settings.regex.search(oldtxt):
                pywikibot.output(
                    u'Your regex has found something in %s, skipping...'
                    % page.title())
                return
            if page.isDisambig() and self.getOption('disambigPage') is not None:
                pywikibot.output(u'%s is a disambig page, report..'
                                 % page.title())
                if not page.title().lower() in self.disambigtext.lower():
                    self.disambigtext = u"%s\n*[[%s]]" % (self.disambigtext, page.title())
                    self.disambigpage.text = self.disambigtext
                    self.disambigpage.save(self.commentdisambig)
                    return
            # Is the page a disambig but there's not disambigPage? Skip!
            elif page.isDisambig():
                pywikibot.output(u'%s is a disambig page, skip...'
                                 % page.title())
                return
            else:
                # Ok, the page need the template. Let's put it there!
                # Adding the template in the text
                newtxt = '%s\n%s' % (self.settings.template, oldtxt)
                self.userPut(page, oldtxt, newtxt, summary=self.comment)


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
    site = pywikibot.Site()

    for arg in local_args:
        if arg.startswith('-enable'):
            if len(arg) == 7:
                options['enablePage'] = pywikibot.input(
                    u'Would you like to check if the bot should run or not?')
            else:
                options['enablePage'] = arg[8:]
        elif arg.startswith('-disambig'):
            if len(arg) == 9:
                options['disambigPage'] = pywikibot.input(
                    u'In which page should the bot save the disambig pages?')
            else:
                options['disambigPage'] = arg[10:]
        elif arg == '-always':
            options['always'] = True
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()

    # If the generator is not given, use the default one
    if not generator:
        generator = site.lonelypages(total=genFactory.limit)

    bot = LonelyPagesBot(generator, **options)
    bot.run()


if __name__ == '__main__':
    main()
