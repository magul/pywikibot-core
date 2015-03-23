# -*- coding: utf-8 -*-
u"""
This script will collect articles that have n or m dash character in title.

After collecting, it will create a redirect to them automatically from the
corresponding hyphenated title. If the target exists, will be skipped.
It may take several hours. You may quit by Ctrl C at any time and continue
later. Type the first few characters of the last shown title after -start.

The script is primarily designed for work in article namespace, but can be used
in any other one. Use in accordance with the rules of your community.

Can be used with:
&params;

Known parameters:

-nosub            Will not process subpages. Useful in template or portal
                  namespace. (Not recommended for main namespace that has no
                  real subpages.)

-save             Saves the title of existing hyphenated articles whose content
                  is _other_ than a redirect to the corresponding article with
                  n dash or m dash in the title and thus may need manual
                  treatment. If omitted, these titles will be written only to
                  the screen (or the log if logging is on). The file is in the
                  form you may upload it to a wikipage.
                  May be given as "-save:<filename>". If it exists, titles
                  will be appended.
                  After checking these titles, you may want to write them to
                  your ignore file (see below).

-ignore           A file that contains titles that are not to be claimed to
                  redirect somewhere else. For example, if X-1 (with hyphen)
                  redirects to a disambiguation page that lists X–1 (with n
                  dash), that's OK and you don't want it to appear at each run
                  as a problematic article.
                  File must be encoded in UTF-8 and contain titles among double
                  square brackets (e.g. *[[X-1]] or [[:File:X-1.gif]]).
                  May be given as "-ignore:<filename>".
"""

#
# (c) Bináris, 2012
# (c) pywikibot team, 2012-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import codecs
import re
import pywikibot
from pywikibot import pagegenerators, i18n


class NdashRedirBot(pywikibot.Bot):

    """Bot class used for implementation of re-direction norms."""

    def __init__(self, generator, titlefile, ignorelist):
        """Constructor.

        Parameters:
        titlefile        # The file object itself
        ignorelist       # A list to ignore titles that redirect to somewhere else
        """
        super(NdashRedirBot, self).__init__(generator=generator)

        # Ready to initialize
        self.site = pywikibot.Site()
        self.titlefile = titlefile
        self.ignorelist = ignorelist

    def treat(self, page):
        # Processing:
        title = page.title()
        editSummary = i18n.twtranslate(self.site, 'ndashredir-create',
                                       {'title': title})
        newtitle = title.replace(u'–', '-').replace(u'—', '-')
        # n dash -> hyphen, m dash -> hyphen, respectively
        redirpage = pywikibot.Page(self.site, newtitle)
        pywikibot.output(redirpage)
        if redirpage.exists():
            if (redirpage.isRedirectPage() and
               redirpage.getRedirectTarget() == page):
                pywikibot.output(u'[[%s]] already redirects to [[%s]], nothing'
                                 u' to do with it.' % (newtitle, title))
            elif newtitle in self.ignorelist:
                pywikibot.output(
                    u'Skipping [[%s]] because it is on your ignore list.'
                    % newtitle)
            else:
                pywikibot.output(
                    u'\03{lightyellow}Skipping [[%s]] because it exists '
                    u'already with a different content.\03{default}'
                    % newtitle)
                if self.titlefile:
                    s = u'\n#%s does not redirect to %s.' % (
                        redirpage.title(asLink=True, textlink=True),
                        page.title(asLink=True, textlink=True))
                    # For the unlikely case if someone wants to run it in
                    # file namespace.
                    self.titlefile.write(s)
                    self.titlefile.flush()
        else:
            page.set_redirect_target(target_page=redirpage)
            try:
                self.userPut(redirpage, redirpage.text, title, comment=editSummary)
            except pywikibot.LockedPage:
                pywikibot.error(
                    u'\03{lightyellow}Skipping [[%s]] because it is '
                    u'protected.\03{default}' % newtitle)
            except KeyboardInterrupt:
                pywikibot.error(u'Page title is {0}'.format(title))
            except:
                pywikibot.error(
                    u'\03{lightyellow}Skipping [[%s]] because of an error.'
                    u'\03{default}' % newtitle)


def main(*args):
    filename = None  # The name of the file to save titles
    titlefile = None  # The file object itself
    ignorefilename = None  # The name of the ignore file
    ignorelist = []  # A list to ignore titles that redirect to somewhere else
    regex = u'.*[–—]'  # Alt 0150 (n dash), alt 0151 (m dash), respectively.
    genFactory = pagegenerators.GeneratorFactory()

    # Handling parameters:
    for arg in pywikibot.handle_args(*args):
        if arg == '-nosub':
            regex = u'[^/]*[–—][^/]*$'
        elif arg == '-save':
            filename = pywikibot.input('Please enter the filename:')
        elif arg.startswith('-save:'):
            filename = arg[6:]
        elif arg == '-ignore':
            ignorefilename = pywikibot.input('Please enter the filename:')
        elif arg.startswith('-ignore:'):
            ignorefilename = arg[8:]
        else:
            genFactory.handleArg(arg)

    # File operations:
    if filename:
        try:
            # This opens in strict error mode, that means bot will stop
            # on encoding errors with ValueError.
            # See http://docs.python.org/library/codecs.html#codecs.open
            titlefile = codecs.open(filename, encoding='utf-8', mode='a')
        except (OSError, IOError):
            pywikibot.output('%s cannot be opened.' % filename)
            return
    if ignorefilename:
        try:
            with codecs.open(ignorefilename, encoding='utf-8', mode='r') as igfile:
                ignorelist = set(re.findall(u'\[\[:?(.*?)\]\]',
                                 igfile.read()))
        except (OSError, IOError):
            pywikibot.output('%s cannot be opened.' % ignorefilename)
            return

    site = pywikibot.Site()
    generator = pagegenerators.RegexFilterPageGenerator(site.allpages(
        start='!', namespace=0, filterredir=False), [regex])

    bot = NdashRedirBot(generator, titlefile, ignorelist)
    bot.run()
    if bot.titlefile:
        bot.titlefile.close()

if __name__ == '__main__':
    main()
