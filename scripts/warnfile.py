"""
Robot to implement backlinks from an interwiki.log file.

A robot to implement backlinks from a interwiki.log file without checking them
against the live wikipedia.

Just run this with the warnfile name as parameter. If not specified, the
default filename for the family and language given by global parameters or
user-config.py will be used.

Example:

   python pwb.py warnfile.py -lang:es

"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Pywikibot team, 2003-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#
import os
import re

import pywikibot
import interwiki
from pywikibot import Bot


class WarnfileReader:

    """Tool to read warnfile and return hints for further processing."""

    def __init__(self, filename):
        self.filename = filename

    def getHints(self):
        pywikibot.output('Parsing warnfile...')
        R = re.compile(
            r'WARNING: (?P<family>.+?): \[\[(?P<locallang>.+?):' +
            r'(?P<localtitle>.+?)\]\](?P<warningtype>.+?)\[\[(?P' +
            r'<targetlang>.+?):(?P<targettitle>.+?)\]\]')
        import codecs
        f = codecs.open(self.filename, 'r', 'utf-8')
        hints = {}
        remove_hints = {}
        mysite = pywikibot.Site()
        for line in f.readlines():
            m = R.search(line)
            if m:
                pywikibot.output('working')
                # print "DBG>",line
                if m.group('locallang') == mysite.lang and \
                   m.group('family') == mysite.family.name:
                    # pywikibot.output(u' '.join([m.group('locallang'),
                    #                             m.group('localtitle'),
                    #                             m.group('warningtype'),
                    #                             m.group('targetsite'),
                    #                             m.group('targettitle')]))
                    #   print m.group(3)
                    page = pywikibot.Page(mysite, m.group('localtitle'))
                    removing = (m.group('warningtype') ==
                                ' links to incorrect ')
                    try:
                        target_site = mysite.Site(code=m.group('targetlang'))
                        target_page = pywikibot.Page(target_site,
                                                     m.group('targettitle'))
                        if removing:
                            if page not in remove_hints:
                                remove_hints[page] = []
                            remove_hints[page].append(target_page)
                        else:
                            if page not in hints:
                                hints[page] = []
                            hints[page].append(target_page)
                    except pywikibot.Error:
                        pywikibot.output("DBG> Failed to add"), line
        f.close()
        return hints, remove_hints


class WarnfileRobot(Bot):

    """Robot to implement backlinks from an interwiki.log file."""

    def __init__(self, warnfileReader):
        self.warnfileReader = warnfileReader

    def run(self):
        hints, remove_hints = self.warnfileReader.getHints()
        k = hints.keys()
        k.sort()
        pywikibot.output("Fixing... %i pages" % len(k))
        for page in k:
            old = {}
            try:
                for page2 in page.interwiki():
                    old[page2.site()] = page2
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect page; not changing"
                                 % page.title(asLink=True))
                continue
            except pywikibot.NoPage:
                pywikibot.output(u"Page %s not found; skipping"
                                 % page.title(asLink=True))
                continue
            new = {}
            new.update(old)
            if page in hints:
                for page2 in hints[page]:
                    site = page2.site
                    new[site] = page2
            if page in remove_hints:
                for page2 in remove_hints[page]:
                    site = page2.site
                    try:
                        del new[site]
                    except KeyError:
                        pass
            (mods, mcomment, adding, removing,
             modifying) = interwiki.compareLanguages(old, new,
                                                     insite=page.site)
            if mods:
                pywikibot.output(page.title(asLink=True) + mods)
                newtext = pywikibot.replaceLanguageLinks(page.text, new)
                # TODO: special warnfile comment needed like in previous
                # releases?
                status, reason, data = self.userPut(page, page.text, newtext,
                                                        comment=mcomment)
                if str(status) != '302':
                    pywikibot.output(status, reason)


def main(*args):
    filename = None
    for arg in pywikibot.handle_args(*args):
        if os.path.isabs(arg):
            filename = arg
        else:
            filename = pywikibot.config.datafilepath("logs", arg)

    if not filename:
        mysite = pywikibot.Site()
        filename = pywikibot.config.datafilepath(
            'logs', 'warning-%s-%s.log' % (mysite.family.name, mysite.lang))
    reader = WarnfileReader(filename)
    bot = WarnfileRobot(reader)
    bot.run()

if __name__ == "__main__":
    main()
