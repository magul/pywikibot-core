#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Interactively add information from a Wikipedia article to wikidata.

This script is used to add interactively add information from a Wikipedia
article to wikidata. It reads Wikipedia articles, and based on keywords
that are found there, guesses what can be added to Wikidata. The user can
then select one or more of these options and/or add possibilities of their
own.

The script is called using "python pwb.py textdata.py <model>" where model
is the name for the information being used. Before running, there should
be a file <model>.txt in the directory data/textdatamodels, with the following
content:

QQ:<query>
LL:<language>
PP:<languageitem>
<pcode>:<plabel>

where:
query is a wikidata query, for example

    "claim[31:5] AND link[nlwiki] and noclaim[106]",

which means that only wikidata items are checked that have a claim P31
with value Q5, have a sitelink to the Dutch Wikipedia, and do not have a
claim P106.

language is the (usually 2-letter) code of the Wikipedia language used
(for example en)

languageitem is the item number of that language Wikipedia on Wikidata
(for example Q328 for the English Wikipedia)

pcode is the property number Pxxx for the main (default) property to be added.

plabel is the label for that property in the language used.

More pcode:plabel pairs (for different codes) may be added if those can be
added too, but the main (default) property should be given first.
"""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id $'

import codecs
import os
import random
import re

import pywikibot
from pywikibot import pagegenerators

propertyre = re.compile('P\d+')
itemre = re.compile('Q\d+')
letter = re.compile('\w')


def ShuffleGenerator(generator):
    """Read items from generator and yield them randomly."""
    content = []
    counter = 0
    for item in generator:
        content.append(item)
        counter += 1
        if len(content) % 1000 == 0:
            pywikibot.output('content now has %i items' % len(content))
    random.shuffle(content)
    for item in content:
        yield item


class TextDataBot(object):

    """Bot Class."""

    def __init__(self):
        """Constructor."""
        self.mainproperty = None
        self.properties = {}
        self.values = {}
        self.identifiers = {}
        self.query = ''
        self.language = None
        self.langitem = 'Q52'

    def loaddata(self, file):
        """Read data items from file."""
        f = codecs.open(file, 'r', 'utf-8')
        for line in f.readlines():
            try:
                if ':' not in line:
                    continue
                (key, value) = line.strip().split(':', 1)
                if key.endswith('QQ'):
                    self.query = value
                elif key.endswith("LL"):
                    self.language = value
                elif key.endswith('PP'):
                    self.langitem = value
                elif propertyre.match(key):
                    self.properties[key] = value
                    if not self.mainproperty:
                        self.mainproperty = key
                elif itemre.match(key):
                    self.values[key] = value
                else:
                    (prop, value) = value.split(':')
                    self.identifiers[key.lower()] = (prop, value)
            except UnicodeDecodeError:
                continue
        f.close()
        self.site = pywikibot.Site(self.language, 'wikipedia')
        self.repo = self.site.data_repository()

    def savedata(self, file):
        """Write data items to file."""
        f = codecs.open(file, 'w', 'utf-8')
        f.write('QQ:%s\r\n' % self.query)
        f.write('LL:%s\r\n' % self.language)
        f.write('PP:%s\r\n' % self.langitem)
        if self.mainproperty:
            f.write('%s:%s\r\n' % (self.mainproperty,
                                   self.properties[self.mainproperty]))
        for prop in self.properties:
            if prop != self.mainproperty:
                f.write('%s:%s\r\n' % (prop, self.properties[prop]))
        for item in self.values:
            f.write('%s:%s\r\n' % (item, self.values[item]))
        for id in self.identifiers:
            f.write('%s:%s:%s\r\n' % (id, self.identifiers[id][0],
                                      self.identifiers[id][1]))
        f.close()

    def label(self, item, dosave=True):
        """Find a label for a given item."""
        title = item.title().split(':')[-1]
        if title in self.properties:
            return self.properties[title]
        elif title in self.values:
            return self.values[title]
        mylabel = None
        try:
            labels = item.get()['labels']
            if not labels:
                labels = item.labels
        except (KeyError, TypeError):
            pass
        else:
            for lang in ('nl', 'en', 'de', 'fr', 'es', 'it', 'no', 'sv', 'da',
                         'pt', 'ro'):
                if lang in item.get()['labels']:
                    mylabel = item.labels[lang]
                    break
            if mylabel:
                if propertyre.match(title):
                    self.properties[title] = mylabel
                elif dosave:
                    self.values[title] = mylabel
        mylabel = mylabel or title
        return mylabel

    def getguesses(self, text, toguess=None, useid=True):
        """Try property and item."""
        if toguess is None:
            toguess = self.identifiers
        adaptedtext = [' '] + [char.lower()
                               if letter.match(char) else ''
                               if char in '[]' else ' '
                               for char in text] + [' ']
        adaptedtext = ''.join(adaptedtext)
        while '  ' in adaptedtext:
            adaptedtext = adaptedtext.replace('  ', ' ')
        guesses = []
        for id in toguess:
            if ' %s ' % id in adaptedtext:
                if useid:
                    guesses.append(self.identifiers[id])
                else:
                    guesses.append(id)
        return guesses

    def runitem(self, item):
        """Run the bot for a given item."""
        item.get()
        page = self.sitelink(item)
        if not page:
            return True
        try:
            page.get()
        except pywikibot.exceptions.IsRedirectPage:
            return True
        pywikibot.output('-' * 80)
        pywikibot.output('== %s ==' % self.label(item, dosave=False))
        pywikibot.output(page.text[:2000])
        shownchars = 2000
        pywikibot.output('-' * 80)
        pywikibot.output('Already present:')
        ispresent = []
        for prop in self.properties:
            if prop in item.claims:
                for claim in item.claims[prop]:
                    pywikibot.output('%s:%s'
                                     % (self.label(prop),
                                        self.label(claim.getTarget())))
                    if self.label(claim.getTarget()) not in self.identifiers:
                        key = self.label(claim.getTarget()).lower()
                        self.identifiers[key] = (prop.title(),
                                                 claim.getTarget().title())
                    ispresent.append(claim.getTarget().title())
        guesses = self.getguesses(page.text)
        guesses = [guess for guess in guesses if guess[1] not in ispresent]
        if guesses:
            pywikibot.output('My guesses:')
            for i in range(len(guesses)):
                pywikibot.output(
                    '%i: %s:%s'
                    % (i, self.label(pywikibot.PropertyPage(self.repo,
                                                            guesses[i][0])),
                       self.label(pywikibot.ItemPage(self.repo, guesses[i][1]))))
            pywikibot.output('')
        else:
            pywikibot.output('No guesses from me...\n')
        claimstoadd = []
        while True:
            whattodo = pywikibot.input(
                'Which value to add (a for new value, m to see more text, '
                'x to close script, enter to stop adding values): ')
            if not whattodo:
                break
            try:
                i = int(whattodo)
                if i < len(guesses):
                    claimstoadd.append(guesses[i])
                else:
                    pywikibot.output("I don't have that many ideas...")
            except ValueError:
                if whattodo[0].lower() == "a":
                    value = pywikibot.input(
                        'Give the item number (Qxxxx). '
                        'If the property is not %s (%s), '
                        'then also the property number (Pxxx:Qxxx): '
                        % (self.label(pywikibot.PropertyPage(
                            self.repo, self.mainproperty)), self.mainproperty))
                    if ':' in value:
                        if propertyre.match(value.split(':', 1)[0]) and \
                           itemre.match(value.split(':', 1)[1]):
                            claimstoadd.append((value.split(':')[0],
                                                value.split(':')[1]))
                        else:
                            pywikibot.output('Not understood')
                            continue
                    else:
                        if itemre.match(value):
                            claimstoadd.append((self.mainproperty, value))
                        else:
                            pywikibot.output('Not understood')
                            continue
                    id = self.label(
                        pywikibot.ItemPage(self.repo,
                                           value.split(':')[-1])).lower()
                    if not self.getguesses(page.text, [id], False):
                        id = pywikibot.input(
                            'Give the word from which I could have seen this '
                            "was an option (I don't see %s): " % id)
                    if id:
                        if ':' in value:
                            self.identifiers[id.lower()] = (value.split(':')[0],
                                                            value.split(':')[1])
                        else:
                            self.identifiers[id.lower()] = (self.mainproperty,
                                                            value)
                elif whattodo[0].lower() == "m":
                    shownchars += 1000
                    pywikibot.output(page.text[:shownchars])
                elif whattodo[0].lower() == "x":
                    return False
                else:
                    pywikibot.output('Not understood')
        if claimstoadd:
            for claimtoadd in claimstoadd:
                claim = pywikibot.Claim(self.repo, claimtoadd[0])
                target = pywikibot.ItemPage(self.repo, claimtoadd[1])
                statedin = pywikibot.Claim(self.repo, 'P143')
                itis = pywikibot.ItemPage(self.repo, self.langitem)
                statedin.setTarget(itis)
                claim.setTarget(target)
                pywikibot.output(
                    'Adding: %s %s (%s)'
                    % (self.label(pywikibot.PropertyPage(self.repo,
                                                         claimtoadd[0])),
                       claimtoadd[1],
                       self.label(pywikibot.ItemPage(self.repo,
                                                     claimtoadd[1]))))
                item.addClaim(claim,
                              'add profession or similar from Wikipedia text')
                pywikibot.output('Sourcing this claim')
                claim.addSources([statedin])
            self.savedata('data/textdatamodels/nlberoepen.bck')
        return True

    def sitelink(self, item):
        """Return a sitelink Page object for a given language."""
        try:
            return pywikibot.Page(self.site,
                                  item.sitelinks['%swiki' % self.language])
        except (KeyError, ValueError):
            pywikibot.output('item %s has no valid link; skipping'
                             % self.label(item, dosave=False))
            return None


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    program = local_args[0]

    bot = TextDataBot()
    bot.loaddata(os.path.join('data', 'textdatamodels', '%s.txt' % program))
    try:
        bot.loaddata(os.path.join('data', 'textdatamodels', '%s.bck' % program))
    except IOError:
        pass
    bot.savedata('data/textdatamodels/%s.txt' % program)

    pregen = pagegenerators.WikidataQueryPageGenerator(bot.query, bot.repo)
    gen = pagegenerators.PreloadingGenerator(ShuffleGenerator(pregen))

    for item in gen:
        if not bot.runitem(item):
            break

if __name__ == '__main__':
    main()
