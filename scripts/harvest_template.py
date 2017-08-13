#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Template harvesting script.

Usage (see below for explanations and examples):

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

You can also use additional parameters:

-create             Create missing items before importing.

The following command line parameters can be used to change the bot's behavior.
If you specify them before all parameters, they are global and are applied to
all param-property pairs. If you specify them after a param-property pair,
they are local and are only applied to this pair. If you specify the same
argument as both local and global, the local argument overrides the global one
(see also examples).

-islink           Treat plain text values as links ("text" -> "[[text]]").

-exists           If set to 'p', add a new value, even if the item already
                  has the imported property but not the imported value.
                  If set to 'pt', add a new value, even if the item already
                  has the imported property with the imported value and
                  some qualifiers.

Examples:

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" image P18

    will try to import existing images from "image" parameter of "Infobox
    person" on English Wikipedia as Wikidata property "P18" (image).

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" image P18 birth_place P19

    will behave the same as the previous example and also try to import
    [[links]] from "birth_place" parameter of the same template as Wikidata
    property "P19" (place of birth).

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" -islink birth_place P19 death_place P20

    will import both "birth_place" and "death_place" params with -islink
    modifier, ie. the bot will try to import values, even if it doesn't find
    a [[link]].

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" birth_place P19 -islink death_place P20

    will do the same but only "birth_place" can be imported without a link.

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox person" occupation P106 -exists:p

    will import an occupation from "occupation" parameter of "Infobox
    person" on English Wikipedia as Wikidata property "P106" (occupation). The
    page won't be skipped if the item already has that property but there is
    not the new value.

    python pwb.py harvest_template -lang:en -family:wikipedia -namespace:0 \
        -template:"Infobox musical artist" current_members P527 -exists:p -multi

    will import band members from the "current_members" parameter of "Infobox
    musical artist" on English Wikipedia as Wikidata property "P527" (has part).
    This will only extract multiple band members if each is linked, and will not
    add duplicate claims for the same member.

    TODO: 'multi' implies at least exists:p - set that automatically?
"""
#
# (C) Multichill, Amir, 2013
# (C) Pywikibot team, 2013-2017
#
# Distributed under the terms of MIT License.
#
from __future__ import absolute_import, unicode_literals

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

import re
import pywikibot
from pywikibot import pagegenerators as pg, textlib
from pywikibot.bot import WikidataBot, OptionHandler

docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}
list_template_regex = re.compile(r'{{\s*(plain|flat)list\s*\|(?P<items>.*)}}')
list_delimiter_regex = re.compile(r',?\s?<br ?/?>\n?', re.IGNORECASE)


class PropertyOptionHandler(OptionHandler):

    """Class holding options for a param-property pair."""

    availableOptions = {
        'exists': '',
        'islink': False,
        'multi': False,
        'reciprocal': '',
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
        @keyword create: Whether to create a new item if it's missing
        @type create: bool
        @keyword exists: pattern for merging existing claims with harvested
            values
        @type exists: str
        @keyword multi: Whether multiple values should be extracted from a
            single parameter
        @type multi: bool
        @keyword reciprocal: a property to populate on the target, pointing to the page item
        @type reciprocal: string
        """
        self.availableOptions.update({
            'always': True,
            'create': False,
            'exists': '',
            'islink': False,
            'multi': False,
            'reciprocal': '',
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
        self.create_missing_item = self.getOption('create')

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
        try:
            linked_page = pywikibot.Page(link)
        except pywikibot.exceptions.InvalidTitle:
            pywikibot.error('%s is not a valid title so it cannot be linked. '
                            'Skipping.' % link_text)
            return

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
        """
        Compare bot's (global) and provided (local) options.

        @see: L{OptionHandler.getOption}
        """
        default = self.getOption(option)
        local = handler.getOption(option)
        if isinstance(default, bool) and isinstance(local, bool):
            return default is not local
        else:
            return local or default

    def treat_page_and_item(self, page, item):
        """Process a single page/item, possibly including multiple values."""
        if willstop:
            raise KeyboardInterrupt

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

            if template not in self.templateTitles:
                continue
            # We found the template we were looking for
            for field, value in fielddict.items():
                field = field.strip()
                value = value.strip()
                if not field or not value:
                    continue

                if field not in self.fields:
                    continue
                # This field contains something useful for us
                prop, options = self.fields[field]
                if self._get_option_with_fallback(options, 'multi'):
                    for sub_value in self.split_list(value):
                        self.treat_item_value(page, item, field, sub_value, prop, options)
                else:
                    self.treat_item_value(page, item, field, value, prop, options)

    def treat_item_value(self, page, item, field, value, prop, options):
        """Saves a single value for a single page/item."""
        claim = pywikibot.Claim(self.repo, prop)
        if claim.type == 'wikibase-item':
            # Try to extract a valid page
            match = pywikibot.link_regex.search(value)
            if match:
                link_text = match.group(1)
            else:
                if self._get_option_with_fallback(options, 'islink'):
                    link_text = value
                else:
                    pywikibot.output(
                        '%s field %s value %s is not a wikilink. '
                        'Skipping.' % (claim.getID(), field, value))
                    return

            linked_item = self._template_link_target(item, link_text)
            if not linked_item:
                return

            claim.setTarget(linked_item)
        elif claim.type in ('string', 'external-id'):
            claim.setTarget(value.strip())
        elif claim.type == 'url':
            match = self.linkR.search(value)
            if not match:
                return
            claim.setTarget(match.group('url'))
        elif claim.type == 'commonsMedia':
            commonssite = pywikibot.Site('commons', 'commons')
            imagelink = pywikibot.Link(
                value, source=commonssite, defaultNamespace=6)
            image = pywikibot.FilePage(imagelink)
            if image.isRedirectPage():
                image = pywikibot.FilePage(image.getRedirectTarget())
            if not image.exists():
                pywikibot.output(
                    "{0} doesn't exist. I can't link to it"
                    ''.format(image.title(asLink=True)))
                return
            claim.setTarget(image)
        else:
            pywikibot.output('%s is not a supported datatype.'
                             % claim.type)
            return

        # A generator might yield pages from multiple sites
        exists_option = self._get_option_with_fallback(options, 'exists')
        self.user_add_claim_unless_exists(
            item, claim, exists_option,
            page.site, pywikibot.output)
        reciprocal = self._get_option_with_fallback(options, 'reciprocal')
        if reciprocal != '':
            reciprocal_claim = pywikibot.Claim(self.repo, reciprocal)
            reciprocal_claim.setTarget(item)
            self.user_add_claim_unless_exists(
                claim.getTarget(), reciprocal_claim,
                exists_option, page.site, pywikibot.output)

    @staticmethod
    def split_list(value):
        """Extracts multiple items from a list."""
        template_list = list_template_regex.match(value)
        if template_list:
            list_body = str(template_list.group('items'))
            first_separator_position = len(list_body)
            chosen_separator = None
            for separator in ['*', '#']:
                separator_position = list_body.find(separator)
                if list_body.count(separator) and separator_position < first_separator_position:
                    chosen_separator = separator
                    first_separator_position = separator_position
            if chosen_separator is None:
                items = [list_body]
            else:
                items = list_body.split(chosen_separator)
        elif list_delimiter_regex.search(value):
            items = list_delimiter_regex.split(value)
        elif ',' in value:
            # don't split on commas inside links
            placeholder = u'\ufffc'
            value = textlib.replaceExcept(value, ',', placeholder, ['link'])
            items = value.split(placeholder)
        else:
            items = [value]
        return list(map(
            lambda text: str.strip(pywikibot.html2unicode(text)),
            items))


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
        elif arg.startswith('-create'):
            options['create'] = True
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
                    options[arg] = value or True
                else:
                    assert complete
                    current_args[2][arg] = value or True
            else:
                if complete:
                    handler = PropertyOptionHandler(**current_args[2])
                    fields[current_args[0]] = (current_args[1], handler)
                    del current_args[:]
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
