#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Template harvesting script.

Usage:

python harvest_template.py -transcludes:"..." template_parameter PID [template_parameter PID]

   or

python harvest_template.py [generators] -template:"..." template_parameter PID [template_parameter PID]

This will work on all pages that transclude the template in the article
namespace

These command line parameters can be used to specify which pages to work on:

-regex          A regex to catch strings in templates. Works only when the property is string.
                    Like catching ISBN

-first          Used with -regex. The bot adds only first catches in templates.
                    If you don't use it it adds all of them.

&params;

Examples:

python harvest_template.py -lang:nl -cat:Sisoridae -template:"Taxobox straalvinnige" -namespace:0 orde P70 familie P71 geslacht P74

python harvest_template.py -lang:en -template:"Infobox book" -namespace:0 isbn P212 -regex:"(\d{3}\-\d\-\d{4}\-\d{4}\-\d)" -first
"""
#
# (C) Multichill, Amir, 2013
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of MIT License.
#
__version__ = '$Id$'
#

import re

import pywikibot
from pywikibot import pagegenerators as pg, textlib, WikidataBot

docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}


class HarvestRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    def __init__(self, generator, templateTitle, fields, regex, regex_type):
        """
        Constructor.


        @param generator: A generator that yields Page objects.
        @param templateTitle: The template to work on
        @type templateTitle: unicode
        @param fields: Fields that are of use to us
        @type fields: dictionary
        @param regex: Regex to catch in raw values
        @type regex: unicode
        @param regex_type: Method to add regex matches to the item.
            defult: All of matches, acceptable values: all, first
        @type regex_type: unicode

        """
        super(HarvestRobot, self).__init__()
        self.generator = pg.PreloadingGenerator(generator)
        self.templateTitle = templateTitle.replace(u'_', u' ')
        # TODO: Make it a list which also includes the redirects to the template
        self.fields = fields
        self.cacheSources()
        self.templateTitles = self.getTemplateSynonyms(self.templateTitle)
        self.regex = regex
        self.regex_type = regex_type

    def getTemplateSynonyms(self, title):
        """Fetch redirects of the title, so we can check against them."""
        temp = pywikibot.Page(pywikibot.Site(), title, ns=10)
        if not temp.exists():
            pywikibot.error(u'Template %s does not exist.' % temp.title())
            exit()

        pywikibot.output('Finding redirects...')  # Put some output here since it can take a while
        if temp.isRedirectPage():
            temp = temp.getRedirectTarget()
        titles = [page.title(withNamespace=False)
                  for page
                  in temp.getReferences(redirectsOnly=True, namespaces=[10], follow_redirects=False)]
        titles.append(temp.title(withNamespace=False))
        return titles

    def _template_link_target(self, item, link_text):
        linked_page = None

        link = pywikibot.Link(link_text)
        linked_page = pywikibot.Page(link)

        if not linked_page.exists():
            pywikibot.output(u'%s doesn\'t exist so it can\'t be linked. Skipping' % (linked_page))
            return

        if linked_page.isRedirectPage():
            linked_page = linked_page.getRedirectTarget()

        try:
            linked_item = pywikibot.ItemPage.fromPage(linked_page)
        except pywikibot.NoPage:
            linked_item = None

        if not linked_item or not linked_item.exists():
            pywikibot.output(u'%s doesn\'t have a wikidata item to link with. Skipping' % (linked_page))
            return

        if linked_item.title() == item.title():
            pywikibot.output(u'%s links to itself. Skipping' % (linked_page))
            return

        return linked_item

    def treat(self, page, item):
        """Process a single page/item."""
        self.current_page = page
        item.get()
        if set(self.fields.values()) <= set(item.claims.keys()):
            pywikibot.output(u'%s item %s has claims for all properties. Skipping' % (page, item.title()))
            return

        pagetext = page.get()
        templates = textlib.extract_templates_and_params(pagetext)
        for (template, fielddict) in templates:
            # Clean up template
            try:
                template = pywikibot.Page(page.site, template,
                                          ns=10).title(withNamespace=False)
            except pywikibot.exceptions.InvalidTitle:
                pywikibot.error(u"Failed parsing template; '%s' should be the template name." % template)
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
                        # Check if the property isn't already set
                        claim = pywikibot.Claim(self.repo, self.fields[field])
                        if claim.getID() in item.get().get('claims'):
                            pywikibot.output(
                                u'A claim for %s already exists. Skipping'
                                % claim.getID())
                            # TODO: Implement smarter approach to merging
                            # harvested values with existing claims esp.
                            # without overwriting humans unintentionally.
                        else:
                            if claim.type == 'wikibase-item':
                                # Try to extract a valid page
                                match = re.search(pywikibot.link_regex, value)
                                if not match:
                                    pywikibot.output(
                                        u'%s field %s value %s isnt a wikilink. Skipping'
                                        % (claim.getID(), field, value))
                                    continue

                                link_text = match.group(1)
                                linked_item = self._template_link_target(item, link_text)
                                if not linked_item:
                                    continue

                                claim.setTarget(linked_item)
                            elif claim.type == 'string':
                                if self.regex:
                                    catch_list = re.findall(self.regex, value.strip())
                                    if not catch_list:
                                        pywikibot.output(
                                            "The regex couldn't catch anything. Skipping")
                                        continue
                                    if self.regex_type == 'all':
                                        for catch in catch_list:
                                            claim.setTarget(value.strip())
                                    elif self.regex_type == 'first' and catch_list:
                                        claim.setTarget(catch_list[0])
                                else:
                                    claim.setTarget(value.strip())
                            elif claim.type == 'commonsMedia':
                                commonssite = pywikibot.Site("commons", "commons")
                                imagelink = pywikibot.Link(value, source=commonssite, defaultNamespace=6)
                                image = pywikibot.FilePage(imagelink)
                                if image.isRedirectPage():
                                    image = pywikibot.FilePage(image.getRedirectTarget())
                                if not image.exists():
                                    pywikibot.output('[[%s]] doesn\'t exist so I can\'t link to it' % (image.title(),))
                                    continue
                                claim.setTarget(image)
                            else:
                                pywikibot.output("%s is not a supported datatype." % claim.type)
                                continue

                            pywikibot.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                            item.addClaim(claim)
                            # A generator might yield pages from multiple sites
                            source = self.getSource(page.site)
                            if source:
                                claim.addSource(source, bot=True)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    commandline_arguments = list()
    template_title = u''
    regex = None
    regex_type = 'all'
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    for arg in local_args:
        if arg.startswith('-template'):
            if len(arg) == 9:
                template_title = pywikibot.input(
                    u'Please enter the template to work on:')
            else:
                template_title = arg[10:]
        elif arg.startswith('-regex'):
            if len(arg) == 6:
                regex = pywikibot.input(
                    u'Please enter the regex:')
            else:
                regex = arg[7:]
        elif arg.startswith('-first'):
            regex_type = 'first'
        elif gen.handleArg(arg):
            if arg.startswith(u'-transcludes:'):
                template_title = arg[13:]
        else:
            commandline_arguments.append(arg)

    if not template_title:
        pywikibot.error('Please specify either -template or -transcludes argument')
        return

    if len(commandline_arguments) % 2:
        raise ValueError  # or something.
    fields = dict()

    for i in range(0, len(commandline_arguments), 2):
        fields[commandline_arguments[i]] = commandline_arguments[i + 1]

    generator = gen.getCombinedGenerator()
    if not generator:
        gen.handleArg(u'-transcludes:' + template_title)
        generator = gen.getCombinedGenerator()

    bot = HarvestRobot(generator, template_title, fields, regex, regex_type)
    bot.run()

if __name__ == "__main__":
    main()
