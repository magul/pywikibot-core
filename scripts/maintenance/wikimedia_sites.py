# -*- coding: utf-8  -*-
"""Script that updates the language lists in Wikimedia family files."""
#
# (C) xqt, 2009-2014
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import codecs
from xml.etree import cElementTree

import pywikibot
from pywikibot.family import Family
from pywikibot.comms.http import fetch

URL = 'https://wikistats.wmflabs.org/api.php?action=dump&table=%s&format=xml'

familiesDict = {
    'anarchopedia': 'anarchopedias',
    'wikibooks':    'wikibooks',
    'wikinews':     'wikinews',
    'wikipedia':    'wikipedias',
    'wikiquote':    'wikiquotes',
    'wikisource':   'wikisources',
    'wikiversity':  'wikiversity',
    'wikivoyage':   'wikivoyage',
    'wiktionary':   'wiktionaries',
}

exceptions = ['www']


def update_family(families):
    for family in families or familiesDict.keys():
        pywikibot.output('\nChecking family %s:' % family)

        original = Family.load(family).languages_by_size
        obsolete = Family.load(family).obsolete

        feed = fetch(URL % familiesDict[family]).content
        tree = cElementTree.fromstring(feed)

        new = []
        for field in tree.findall('row/field'):
            if field.get('name') == 'prefix':
                code = field.text
                if not (code in obsolete or code in exceptions):
                    new.append(code)
                continue

        # put the missing languages to the right place
        missing = set(original) - set(new)
        if missing:
            pywikibot.output(u"WARNING: ['%s'] not listed at wikistats."
                             % "', '".join(missing))
            index = {}
            for code in missing:
                index[original.index(code)] = code
            i = len(index) - 1
            for key in sorted(index.keys(), reverse=True):
                new.insert(key - i, index[key])
                i -= 1

        if original == new:
            pywikibot.output(u'The lists match!')
        else:
            pywikibot.output(u"The lists don't match, the new list is:")
            text = u'        self.languages_by_size = [\n'
            line = u''
            for code in new:
                if len(line) + len(code) > 80 - 11 - 4:
                    text += u' ' * 11 + u'%s\n' % line
                    line = u''
                line += u" '%s'," % code
            text += u' ' * 11
            text += u'%s\n' % line
            text += u'        ]'
            pywikibot.output(text)
            family_file_name = 'pywikibot/families/%s_family.py' % family
            with codecs.open(family_file_name, 'r', 'utf8') as family_file:
                family_text = family_file.read()
            old = re.findall(r'(?msu)^ {8}self.languages_by_size.+?\]',
                             family_text)[0]
            family_text = family_text.replace(old, text)
            with codecs.open(family_file_name, 'w', 'utf8') as family_file:
                family_file.write(family_text)


if __name__ == '__main__':
    fams = set(arg for arg in pywikibot.handle_args() if arg in familiesDict)
    update_family(fams)
