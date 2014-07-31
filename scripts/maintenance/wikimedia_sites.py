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

import os
import re
import codecs

import pywikibot

familiesDict = {
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

        original = set(fam._languages)
        obsolete = set(fam.obsolete.keys() + exceptions)
        new = set(fam.languages_by_size) - obsolete

        missing = set(original) - set(new)
        if missing:
            pywikibot.output(u"WARNING: ['%s'] not listed at wikistats."
                             % "', '".join(missing))

        if original == new:
            pywikibot.output('The lists match!')
        elif new - original:
            pywikibot.output('New languages:')
            pywikibot.output(new - original)

            pywikibot.output('The new list is:')
            text = u'        self._languages = [%s' % os.linesep
            line = ' ' * 11
            for code in sorted(new):
                if len(line) + len(code) <= 76:
                    line += u" '%s'," % code
                else:
                    text += u'%s%s' % (line, os.linesep)
                    line = ' ' * 11
                    line += u" '%s'," % code
            text += u'%s%s' % (line, os.linesep)
            if missing:
                text += u'            # codes missing from wikistats:\r\n'
                text += u'           '
                for code in sorted(missing):
                    text += u" '%s'," % code
                text += os.linesep
            text += u'        ]'
            pywikibot.output(text)
            family_file_name = 'pywikibot/families/%s_family.py' % family
            family_file = codecs.open(family_file_name, 'r', 'utf8')
            family_text = family_file.read()
            old = re.findall(r'(?msu)^ {8}self._languages.+?\]',
                             family_text)[0]
            family_text = family_text.replace(old, text)
            #family_file = codecs.open(family_file_name, 'w', 'utf8')
            #family_file.write(family_text)
            #family_file.close()
        else:
            pywikibot.output('No new languages.')


if __name__ == '__main__':
    fam = []
    for arg in pywikibot.handleArgs():
        if arg in familiesDict.keys() and arg not in fam:
            fam.append(arg)
    update_family(fam)
