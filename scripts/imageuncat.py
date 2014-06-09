#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Program to add uncat template to images without categories at commons.
See imagerecat.py (still working on that one) to add these images to categories.

"""
#
# (C) Multichill, 2008
# (C) Pywikibot team, 2009-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

from datetime import timedelta

import pywikibot
from pywikibot import pagegenerators


# Dont bother to put the template on a image with one of these templates
skipTemplates = [u'Check categories',
                 u'Delete',
                 u'Nocat',
                 u'No license',
                 u'No permission since',
                 u'No source',
                 u'No source since',
                 u'Uncategorized',
                 u'Uncat']


def uploadedYesterday(site):
    """
    Return a pagegenerator containing all the pictures uploaded yesterday.
    Should probably copied to somewhere else

    TODO: Move out of here
    """

    today = pywikibot.Timestamp.utcnow()
    yesterday = today + timedelta(days=-1)

    for logentry in site.logevents(logtype='upload', start=yesterday, end=today, reverse=True):
        yield logentry.title()


def recentChanges(site=None, delay=0, block=70):
    """
    Return a pagegenerator containing all the images edited in a certain timespan.
    The delay is the amount of minutes to wait and the block is the timespan to return images in.
    Should probably be copied to somewhere else

    TODO: Move out of here
    """
    rcstart = site.getcurrenttime() + timedelta(minutes=-(delay + block))
    rcend = site.getcurrenttime() + timedelta(minutes=-delay)

    gen = site.recentchanges(start=rcstart, end=rcend, reverse=True,
                             namespaces=6, changetype='edit|log',
                             showBot=False)
    # remove 'patrolled' from rcprop since we can't get it
    gen.request['rcprop'] = 'title|user|comment|ids'
    for p in gen:
        yield pywikibot.Page(site, p['title'], p['ns'])


class UncatBot(pywikibot.Bot):
    """
    Bot to tag uncategorized images at Wikimedia Commons
    """

    def __init__(self, generator, **kwargs):
        """
        Only accepts options defined in availableOptions
        """
        super(UncatBot, self).__init__(**kwargs)
        self.generator = pagegenerators.PreloadingGenerator(generator)

        # we might need to add some hidden categories caching here

    def run(self):
        """
        Start the bot.
        """
        for page in self.generator:
            pywikibot.output(page.title())
            if page.exists() and (page.namespace() == 6) \
                    and (not page.isRedirectPage()):
                pywikibot.output(u'Working on ' + page.title())

                foundIgnore = False
                for template in page.templates():
                    if template.title(withNamespace=False) in skipTemplates:
                        pywikibot.output(u'Found template %s which is on the ignore list'
                                         % (template.title(withNamespace=False),))
                        foundIgnore = True
                        break
                if foundIgnore:
                    continue

                foundHidden = 0
                foundRed = 0
                foundTopic = False

                for category in page.categories():
                    if not category.exists():
                        foundRed = foundRed + 1
                    elif category.isHiddenCategory():
                        foundHidden = foundHidden + 1
                    else:
                        pywikibot.output(u'Found category: %s' % (category.title(),))
                        foundTopic = True
                        continue

                if foundTopic:
                    continue

                puttext = u'\n{{Uncategorized|year={{subst:CURRENTYEAR}}|month={{subst:CURRENTMONTHNAME}}|day={{subst:CURRENTDAY}}}}'
                putcomment = u'Please add categories to this image. Image only contains %s hidden and %s non-existent categories' % (foundHidden, foundRed)

                newtext = page.get() + puttext

                pywikibot.output(putcomment)
                pywikibot.showDiff(page.get(), newtext)
                try:
                    page.put(newtext, putcomment)
                except (pywikibot.EditConflict, pywikibot.LockedPage):
                    # Skip this page
                    pass


def main(*args):
    """
    Grab a bunch of images and tag them if they are not categorized.
    """
    generator = None

    local_args = pywikibot.handleArgs(*args)

    # use the default imagerepository normally commons
    site = pywikibot.Site().image_repository()

    genFactory = pagegenerators.GeneratorFactory(site)

    for arg in local_args:
        if arg.startswith('-yesterday'):
            generator = uploadedYesterday(site)
        elif arg.startswith('-recentchanges'):
            generator = recentChanges(site=site, delay=120)
        else:
            genFactory.handleArg(arg)
    if not generator:
        generator = genFactory.getCombinedGenerator()

    if generator:
        bot = UncatBot(generator)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
