#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Template harvesting script.

Usage:

* python pwb.py harvest_template -transcludes:"..." \
    [default optional arguments] \
    template_parameter PID [local optional arguments] \
    [template_parameter PID [local optional arguments]]
* python pwb.py harvest_template [generators] -template:"..." \
    [default optional arguments] \
    template_parameter PID [local optional arguments] \
    [template_parameter PID [local optional arguments]]

This will work on all pages that transclude the template in the article
namespace

These command line parameters can be used to specify which pages to work on:

&params;

The following command line parameters can be used to change the bot's behavior.
If you specify them before all parameters, they are global and are applied to
all param-property pairs. If you specify them after a param-property pair,
they are local and are only applied to this pair. If you specify the same
argument as both local and global, the local argument overrides the global one.

-islink             Treat plain text values as links ("text" -> "[[text]]").

Examples:

    python pwb.py harvest_template -lang:nl -cat:Sisoridae -namespace:0 \
        -template:"Taxobox straalvinnige" orde P70 familie P71 geslacht P74

"""
#
# (C) Multichill, Amir, 2013
# (C) Pywikibot team, 2013-2017
#
# Distributed under the terms of MIT License.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import signal

willstop = False


def _signal_handler(signal, frame):
    global willstop
    if not willstop:
        willstop = True
        print('Received ctrl-c. Finishing current item; '
              'press ctrl-c again to abort.')  # noqa
    else:
        raise KeyboardInterrupt


signal.signal(signal.SIGINT, _signal_handler)

import pywikibot
from pywikibot import pagegenerators as pg, textlib
from pywikibot.bot import WikidataBot, OptionHandler

docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}


class PropertyOptionHandler(OptionHandler):

    """Class holding options for a param-property pair."""

    availableOptions = {
        'islink': False,
    }


class HarvestRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    def __init__(self, generator, templateTitle, fields, **kwargs):
        """
        Constructor.

        @param generator: A generator that yields Page objects
        @type generator: iterator
        @param templateTitle: The template to work on
        @type templateTitle: str
        @param fields: A dictionary of fields that are of use to us
        @type fields: dict
        @keyword islink: Whether non-linked values should be treated as links
        @type islink: bool
        """
        self.availableOptions.update({
            'always': True,
            'islink': False,
        })
        super(HarvestRobot, self).__init__(**kwargs)
        self.generator = generator
        self.templateTitle = templateTitle.replace(u'_', u' ')
        # TODO: Make it a list which also includes the redirects to the template
        self.fields = {}
        for key, value in fields.items():
            if isinstance(value, tuple):
                self.fields[key] = value
            else:  # backwards compatibility
                self.fields[key] = (value, PropertyOptionHandler())
        self.cacheSources()
        self.templateTitles = self.getTemplateSynonyms(self.templateTitle)
        self.linkR = textlib.compileLinkR()

    def getTemplateSynonyms(self, title):
        """Fetch redirects of the title, so we can check against them."""
        temp = pywikibot.Page(pywikibot.Site(), title, ns=10)
        if not temp.exists():
            pywikibot.error(u'Template %s does not exist.' % temp.title())
            exit()

        # Put some output here since it can take a while
        pywikibot.output('Finding redirects...')
        if temp.isRedirectPage():
            temp = temp.getRedirectTarget()
        titles = [page.title(withNamespace=False)
                  for page in temp.getReferences(redirectsOnly=True,
                                                 namespaces=[10],
                                                 follow_redirects=False)]
        titles.append(temp.title(withNamespace=False))
        return titles

    def _template_link_target(self, item, link_text):
        link = pywikibot.Link(link_text)
        linked_page = pywikibot.Page(link)

        if not linked_page.exists():
            pywikibot.output('%s does not exist so it cannot be linked. '
                             'Skipping.' % (linked_page))
            return

        if linked_page.isRedirectPage():
            linked_page = linked_page.getRedirectTarget()

        try:
            linked_item = pywikibot.ItemPage.fromPage(linked_page)
        except pywikibot.NoPage:
            linked_item = None

        if not linked_item or not linked_item.exists():
            pywikibot.output('%s does not have a wikidata item to link with. '
                             'Skipping.' % (linked_page))
            return

        if linked_item.title() == item.title():
            pywikibot.output('%s links to itself. Skipping.' % (linked_page))
            return

        return linked_item

    def _get_option_with_fallback(self, handler, option):
        # TODO: only works with booleans
        default = self.getOption(option)
        local = handler.getOption(option)
        return default is not local

    def treat(self, page, item):
        """Process a single page/item."""
        if willstop:
            raise KeyboardInterrupt
        self.current_page = page
        item.get()
        if set(val[0] for val in self.fields.values()) <= set(
                item.claims.keys()):
            pywikibot.output('%s item %s has claims for all properties. '
                             'Skipping.' % (page, item.title()))
            return

        templates = page.raw_extracted_templates
        for (template, fielddict) in templates:
            # Clean up template
            try:
                template = pywikibot.Page(page.site, template,
                                          ns=10).title(withNamespace=False)
            except pywikibot.exceptions.InvalidTitle:
                pywikibot.error(
                    "Failed parsing template; '%s' should be the template name."
                    % template)
                continue
            # We found the template we were looking for
            if template in self.templateTitles:
                for field, value in fielddict.items():
                    field = field.strip()
                    value = value.strip()
                    if not field or not value:
                        continue

                    # This field contains something useful for us
                    if field in self.fields:
                        prop, options = self.fields[field]
                        # Check if the property isn't already set
                        claim = pywikibot.Claim(self.repo, prop)
                        if claim.getID() in item.get().get('claims'):
                            pywikibot.output(
                                'A claim for %s already exists. Skipping.'
                                % claim.getID())
                            # TODO: Implement smarter approach to merging
                            # harvested values with existing claims esp.
                            # without overwriting humans unintentionally.
                        else:
                            if claim.type == 'wikibase-item':
                                # Try to extract a valid page
                                match = pywikibot.link_regex.search(value)
                                if match:
                                    link_text = match.group(1)
                                else:
                                    if self._get_option_with_fallback(
                                            options, 'islink'):
                                        link_text = value
                                    else:
                                        pywikibot.output(
                                            '%s field %s value %s is not a '
                                            'wikilink. Skipping.'
                                            % (claim.getID(), field, value))
                                        continue

                                linked_item = self._template_link_target(
                                    item, link_text)
                                if not linked_item:
                                    continue

                                claim.setTarget(linked_item)
                            elif claim.type in ('string', 'external-id'):
                                claim.setTarget(value.strip())
                            elif claim.type == 'url':
                                match = self.linkR.search(value)
                                if not match:
                                    continue
                                claim.setTarget(match.group('url'))
                            elif claim.type == 'commonsMedia':
                                commonssite = pywikibot.Site('commons',
                                                             'commons')
                                imagelink = pywikibot.Link(value,
                                                           source=commonssite,
                                                           defaultNamespace=6)
                                image = pywikibot.FilePage(imagelink)
                                if image.isRedirectPage():
                                    image = pywikibot.FilePage(
                                        image.getRedirectTarget())
                                if not image.exists():
                                    pywikibot.output(
                                        "{0} doesn't exist. I can't link to it"
                                        ''.format(image.title(asLink=True)))
                                    continue
                                claim.setTarget(image)
                            else:
                                pywikibot.output(
                                    '%s is not a supported datatype.'
                                    % claim.type)
                                continue

                            # A generator might yield pages from multiple sites
                            self.user_add_claim(item, claim, page.site)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    template_title = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    current_args = []
    fields = {}
    options = {}
    for arg in local_args:
        if arg.startswith('-template'):
            if len(arg) == 9:
                template_title = pywikibot.input(
                    u'Please enter the template to work on:')
            else:
                template_title = arg[10:]
        elif gen.handleArg(arg):
            if arg.startswith(u'-transcludes:'):
                template_title = arg[13:]
        else:
            optional = arg.startswith('-')
            complete = len(current_args) == 3
            if optional:
                needs_second = len(current_args) == 1
                if needs_second:
                    break  # will stop below

                arg, sep, value = arg[1:].partition(':')
                if len(current_args) == 0:
                    assert not fields
                    options[arg] = value if value != '' else True
                else:
                    assert complete
                    current_args[2].update({
                        arg: value if value != '' else True
                    })
            else:
                if complete:
                    handler = PropertyOptionHandler(**current_args[2])
                    fields[current_args[0]] = (current_args[1], handler)
                    current_args.clear()
                else:
                    current_args.append(arg)
                    if len(current_args) == 2:
                        current_args.append({})

    # handle leftover
    if len(current_args) == 3:
        handler = PropertyOptionHandler(**current_args[2])
        fields[current_args[0]] = (current_args[1], handler)
    elif len(current_args) == 1:
        pywikibot.error('Incomplete command line param-property pair.')
        return False

    if not template_title:
        pywikibot.error(
            'Please specify either -template or -transcludes argument')
        return

    generator = gen.getCombinedGenerator(preload=True)
    if not generator:
        gen.handleArg(u'-transcludes:' + template_title)
        generator = gen.getCombinedGenerator(preload=True)

    bot = HarvestRobot(generator, template_title, fields, **options)
    bot.run()


if __name__ == "__main__":
    main()
