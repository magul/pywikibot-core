# -*- coding: utf-8 -*-
"""
Used to find expensive templates that are subject to be converted to Lua.

It counts parser functions and then orders templates by number of these
and uploads the first n titles or alternatively templates having count()>n.

Parameters:

-start            Will start from the given title (it does not have to exist).
                  Parameter may be given as "-start" or "-start:title".
                  Defaults to '!'.

-first            Returns the first n results in decreasing order of number
                  of hits (or without ordering if used with -nosort)
                  Parameter may be given as "-first" or "-first:n".

-atleast          Returns templates with at least n hits.
                  Parameter may be given as "-atleast" or "-atleast:n".

-nosort           Keeps the original order of templates. Default behaviour is
                  to sort them by decreasing order of count(parserfunctions).

-save             Saves the results. The file is in the form you may upload it
                  to a wikipage. May be given as "-save:<filename>".
                  If it exists, titles will be appended.

-upload           Specify a page in your wiki where results will be uploaded.
                  Parameter may be given as "-upload" or "-upload:title".
                  Say good-bye to previous content if existed.

Precedence of evaluation: results are first sorted in decreasing order of
templates, unless nosort is switched on. Then first n templates are taken if
first is specified, and at last atleast is evaluated. If nosort and first are
used together, the program will stop at the nth hit without scanning the rest
of the template namespace. This may be used to run it in more sessions
(continue with -start next time).

First is strict. That means if results #90-120 have the same number of parser
functions and you specify -first:100, only the first 100 will be listed (even
if atleast is used as well).

Should you specify neither first nor atleast, all templates using parser
functions will be listed.

"""

#
# (C) Bináris, 2013
# (C) Pywikibot team, 2013-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

"""
Todo:
* Using xml and xmlstart
* Using categories
* Error handling for uploading (anyway, that's the last action, it's only
  for the beauty of the program, does not effect anything).
"""

import codecs
import re
import pywikibot
from pywikibot import pagegenerators, Bot


class ParserFunctionCountBot(Bot):

    """Bot class used for obtaining Parser function Count."""

    def __init__(self, site, **kwargs):
        """Constructor.

        Parameters:
            @param start:xxx Specify the place in the alphabet to start
            searching.
        """
        self.count = 0
        word = []
        super(ParserFunctionCountBot, self).__init__(**kwargs)
        self.nosort = kwargs.get('nosort', False)
        self.filename = kwargs.get('filename', None)
        self.uploadpage = kwargs.get('uploadpage', None)
        self.start = kwargs.get('start', '!')
        self.atleast = kwargs.get('atleast', None)
        self.first = kwargs.get('first', None)

        if not site.doc_subpage:
            self.doc_subpage = {
                # You may write here a regex representing the name of template doc
                # subpages in your wiki. Defaults to /doc.
                # These subpages will be excluded for faster run.
            '_default': (u'/doc', ),
        }
        else:
            self.doc_subpage = site.doc_subpage

        editcomment = {
            # This will be used for uploading the list to your wiki.
            'en':
            u'Bot: uploading list of templates having too many parser functions',
            'hu':
            u'A túl sok parserfüggvényt használó sablonok listájának feltöltése',
        }

        # Limitations for result:
        if self.first:
            try:
                self.first = int(self.first)
                if self.first < 1:
                    self.first = None
            except ValueError:
                self.first = None
        if self.atleast:
            try:
                self.atleast = int(self.atleast)
                if self.atleast < 2:  # 1 has no effect, don't waste resources.
                    self.atleast = None
            except ValueError:
                self.atleast = None

        # Ready to initizalize
        words = site.siteinfo['magicwords']
        for magic_word in words:
            aliases = magic_word['aliases']
            for alias in aliases:
                word.append(alias)
        lang = site.lang
        self.comment = editcomment.get(lang, editcomment['en'])

        # Finding document subpage names
        self.doc_subpages = list(self.doc_subpage.get(lang, self.doc_subpage['_default'][0]))
        self.regex = re.compile(r'#(' + r'|'.join(word) + '):', re.I)

    def run(self):
        """Process 'whitelist' page absent in generator."""
        results = []
        gen1 = pagegenerators.AllpagesPageGenerator(start=self.start,
                                                    namespace=10,
                                                    includeredirects=False,
                                                    site=self.site)
        if self.doc_subpage:
            self.gen = gen1
        else:
            self.gen = pagegenerators.RegexFilterPageGenerator(gen1, self.doc_subpages,
                                                               quantifier='none')

        # Processing:
        pywikibot.output(u'Hold on, this will need some time. '
                         u'You will be notified by 50 templates.')
        for page in self.gen:
            self.count += 1
            title = page.title()
            if self.count % 50 == 0:
                # Don't let the poor user panic in front of a black screen.
                pywikibot.output('%dth template is being processed: %s'
                                 % (self.count, title))
            try:
                text = page.get()
                functions = self.regex.findall(text)
                if functions and (self.atleast is None or self.atleast <= len(functions)):
                    results.append((title, len(functions)))
                if self.nosort and self.first and len(results) == self.first:
                    break
            except (pywikibot.NoPage, pywikibot.IsRedirectPage):
                return

        # Combining the results:
        if not self.nosort:
            results.sort(key=lambda x: (5000 - x[1], x[0]))
        results = results[:self.first]

        # Outputs:
        resultlist = '\n'.join(
            '#[[%s]] (%d)' % (result[0], result[1]) for result in results)
        pywikibot.output(resultlist)
        pywikibot.output(u'%d templates were examined.' % self.count)
        pywikibot.output(u'%d templates were found.' % len(results))

        # File operations:
        if self.filename:
            try:
                # This opens in strict error mode, that means bot will stop
                # on encoding errors with ValueError.
                # See http://docs.python.org/library/codecs.html#codecs.open
                with codecs.open(self.filename, encoding='utf-8', mode='a') as titlefile:
                    titlefile.write(resultlist)
            except (IOError, OSError):
                raise pywikibot.Error("File cannot be opened.")
        if self.uploadpage:
            page = pywikibot.Page(self.site, self.uploadpage)
            self.userPut(page, ignore_save_related_errors=True, comment=self.comment)


def main(*args):
    """Process command line arguments and invoke ParserFunctionCountBot."""
    local_args = pywikibot.handle_args(*args)
    genFactory = pagegenerators.GeneratorFactory()
    genFactory.handleArg('-namespace:10')
    options = {}

    # Parse command line arguments
    for arg in local_args:
        if arg == '-start':
            options['start'] = pywikibot.input(
                u'From which title do you want to continue?')
        elif arg.startswith('-start:'):
            options['start'] = arg[7:]
        elif arg == '-save':
            options['filename'] = pywikibot.input('Please enter the filename:')
        elif arg.startswith('-save:'):
            options['filename'] = arg[6:]
        elif arg == '-upload':
            options['uploadpage'] = pywikibot.input('Please enter the pagename:')
        elif arg.startswith('-upload:'):
            options['uploadpage'] = arg[8:]
        elif arg == '-first':
            options['first'] = pywikibot.input(
                'Please enter the max. number of templates to display:')
        elif arg.startswith('-first:'):
            options['first'] = arg[7:]
        elif arg == '-atleast':
            options['atleast'] = pywikibot.input(
                'Please enter the min. number of functions to display:')
        elif arg.startswith('-atleast:'):
            options['atleast'] = arg[9:]
        elif arg == '-nosort':
            options['nosort'] = True
        else:
            genFactory.handleArg(arg)
    site = pywikibot.Site()
    bot = ParserFunctionCountBot(site, **options)
    bot.run()

if __name__ == "__main__":
    main()
