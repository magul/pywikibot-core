#!/usr/bin/python
# -*- coding: utf-8  -*-
r"""
Script to delete files that are also present on Wikimedia Commons.

Do not run this script on Wikimedia Commons itself. It works based on
a given array of templates defined below.

Files are downloaded and compared. If the files match, it can be deleted on
the source wiki. If multiple versions of the file exist, the script will not
delete. If the SHA1 comparison is not equal, the script will not delete.

A sysop account on the local wiki is required if you want all features of
this script to work properly.

This script understands various command-line arguments:
    -always         run automatically, do not ask any questions. All files
                    that qualify for deletion are deleted. Reduced screen
                    output.

    -replace        replace links if the files are equal and the file names
                    differ

    -replacealways  replace links if the files are equal and the file names
                    differ without asking for confirmation

    -replaceloose   Do loose replacements.  This will replace all occurrences
                    of the name of the image (and not just explicit image
                    syntax).  This should work to catch all instances of the
                    file, including where it is used as a template parameter
                    or in galleries.  However, it can also make more
                    mistakes.

    -replaceonly    Use this if you do not have a local sysop account, but do
                    wish to replace links from the NowCommons template.

-- Example --

    python pwb.py nowcommons -replaceonly -replaceloose -replacealways -replace

-- Known issues --
Please fix these if you are capable and motivated:
- if a file marked nowcommons is not present on Wikimedia Commons, the bot
  will exit.
"""
#
# (C) Wikipedian, 2006-2007
# (C) Siebrand Mazeland, 2007-2008
# (C) xqt, 2010-2016
# (C) Pywikibot team, 2006-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import re
import sys
import webbrowser

import pywikibot

from pywikibot import i18n
from pywikibot.bot import ExistingPageBot, NoRedirectPageBot, SingleSiteBot
from pywikibot import pagegenerators as pg
from pywikibot.tools.formatter import color_format

from scripts.image import ImageRobot as ImageBot

nowCommons = {
    '_default': [
        u'NowCommons'
    ],
    'ar': [
        u'الآن كومنز',
        u'الآن كومونز',
    ],
    'de': [
        u'NowCommons',
        u'NC',
        u'NCT',
        u'Nowcommons',
        u'NowCommons/Mängel',
        u'NowCommons-Überprüft',
    ],
    'en': [
        u'NowCommons',
        u'Ncd',
    ],
    'eo': [
        u'Nun en komunejo',
        u'NowCommons',
    ],
    'fa': [
        u'موجود در انبار',
        u'NowCommons',
    ],
    'fr': [
        u'Image sur Commons',
        u'DoublonCommons',
        u'Déjà sur Commons',
        u'Maintenant sur commons',
        u'Désormais sur Commons',
        u'NC',
        u'NowCommons',
        u'Nowcommons',
        u'Sharedupload',
        u'Sur Commons',
        u'Sur Commons2',
    ],
    'he': [
        u'גם בוויקישיתוף'
    ],
    'hu': [
        u'Azonnali-commons',
        u'NowCommons',
        u'Nowcommons',
        u'NC'
    ],
    'ia': [
        u'OraInCommons'
    ],
    'it': [
        u'NowCommons',
    ],
    'ja': [
        u'NowCommons',
    ],
    'ko': [
        u'NowCommons',
        u'공용중복',
        u'공용 중복',
        u'Nowcommons',
    ],
    'nds-nl': [
        u'NoenCommons',
        u'NowCommons',
    ],
    'nl': [
        u'NuCommons',
        u'Nucommons',
        u'NowCommons',
        u'Nowcommons',
        u'NCT',
        u'Nct',
    ],
    'ro': [
        u'NowCommons'
    ],
    'ru': [
        u'NowCommons',
        u'NCT',
        u'Nowcommons',
        u'Now Commons',
        u'Db-commons',
        u'Перенесено на Викисклад',
        u'На Викискладе',
    ],
    'zh': [
        u'NowCommons',
        u'Nowcommons',
        u'NCT',
    ],
}

namespaceInTemplate = [
    'en',
    'ia',
    'it',
    'ja',
    'ko',
    'lt',
    'ro',
    'zh',
]

# Stemma and stub are images not to be deleted (and are a lot) on it.wikipedia
# if your project has images like that, put the word often used here to skip them
word_to_skip = {
    'en': [],
    'it': ['stemma', 'stub', 'hill40 '],
}


class NowCommonsDeleteBot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot):

    """Bot to delete migrated files."""

    def __init__(self, **kwargs):
        """Constructor."""
        self.availableOptions.update({
            'replace': False,
            'replacealways': False,
            'replaceloose': False,
            'replaceonly': False,
        })
        super(NowCommonsDeleteBot, self).__init__(**kwargs)

        if not self.site.has_image_repository:
             sys.exit('There must be a file repository to run this script')
        else:
            self.commons = self.site.image_repository()
            if self.site == self.commons:
                sys.exit(
                    'You cannot run this bot on file repository like Commons.')
        self.summary = i18n.twtranslate(self.site,
                                       'imagetransfer-nowcommons_notice')

    def ncTemplates(self):
        """Return nowcommons templates."""
        if self.site.lang in nowCommons:
            return nowCommons[self.site.lang]
        else:
            return nowCommons['_default']

    @property
    def nc_templates(self):
        """A set of now commons template Page instances."""
        if not hasattr(self, '_nc_templates'):
            self._nc_templates = set(pywikibot.Page(self.site, title, ns=10)
                                     for title in self.ncTemplates())
        return self._nc_templates

    @property
    def generator(self):
        """Generator method."""
        gens = [t.getReferences(follow_redirects=True, namespaces=[6],
                                onlyTemplateInclusion=True)
                for t in self.nc_templates]
        gen = pg.CombinedPageGenerator(gens)
        gen = pg.DuplicateFilterPageGenerator(gen)
        gen = pg.PreloadingGenerator(gen)
        return gen

    def findFilenameOnCommons(self, localImagePage):
        """Find filename on Commons."""
        filenameOnCommons = None
        for templateName, params in localImagePage.templatesWithParams():
            if templateName in self.nc_templates:
                if params == []:
                    filenameOnCommons = localImagePage.title(withNamespace=False)
                elif self.site.lang in namespaceInTemplate:
                    skip = False
                    filenameOnCommons = None
                    for par in params:
                        val = par.split('=')
                        if len(val) == 1 and not skip:
                            filenameOnCommons = par[par.index(':') + 1:]
                            break
                        if val[0].strip() == '1':
                            filenameOnCommons = val[1].strip()[val[1].strip().index(':') + 1:]
                            break
                        skip = True
                    if not filenameOnCommons:
                        filenameOnCommons = localImagePage.title(withNamespace=False)
                else:
                    val = params[0].split('=')
                    if len(val) == 1:
                        filenameOnCommons = params[0].strip()
                    else:
                        filenameOnCommons = val[1].strip()
                return filenameOnCommons

    def treat_page(self):
        """Process a single file."""
        localImagePage = pywikibot.FilePage(self.current_page)
        if localImagePage.fileIsShared():
            pywikibot.output(u'File is already on Commons.')
            return
        sha1 = localImagePage.latest_file_info.sha1
        filenameOnCommons = self.findFilenameOnCommons(localImagePage)
        if not filenameOnCommons:
            pywikibot.output(u'NowCommons template not found.')
            return
        commonsImagePage = pywikibot.FilePage(self.commons, 'Image:%s'
                                              % filenameOnCommons)
        if (localImagePage.title(withNamespace=False) !=
                commonsImagePage.title(withNamespace=False)):
            usingPages = list(localImagePage.usingPages())
            if usingPages and usingPages != [localImagePage]:
                pywikibot.output(color_format(
                    '"{lightred}{0}{default}" is still used in {1} pages.',
                    localImagePage.title(withNamespace=False),
                    len(usingPages)))
                if self.getOption('replace') is True:
                        pywikibot.output(color_format(
                            'Replacing "{lightred}{0}{default}" by '
                            '"{lightgreen}{1}{default}\".',
                            localImagePage.title(withNamespace=False),
                            commonsImagePage.title(withNamespace=False)))
                        bot = ImageBot(
                            pg.FileLinksGenerator(localImagePage),
                            localImagePage.title(withNamespace=False),
                            commonsImagePage.title(withNamespace=False),
                            '', self.getOption('replacealways'),
                            self.getOption('replaceloose'))
                        bot.run()
                        # If the image is used with the urlname the
                        # previous function won't work
                        is_used = bool(list(pywikibot.FilePage(
                            self.site, page.title()).usingPages(total=1)))
                        if is_used and self.getOption('replaceloose'):
                            bot = ImageBot(
                                pg.FileLinksGenerator(
                                    localImagePage),
                                localImagePage.title(
                                    withNamespace=False, asUrl=True),
                                commonsImagePage.title(
                                    withNamespace=False),
                                '', self.getOption('replacealways'),
                                self.getOption('replaceloose'))
                            bot.run()
                        # refresh because we want the updated list
                        usingPages = len(list(pywikibot.FilePage(
                            self.site, page.title()).usingPages()))
                else:
                    pywikibot.output(u'Please change them manually.')
                return
            else:
                pywikibot.output(color_format(
                    'No page is using "{lightgreen}{0}{default}" '
                    'anymore.',
                    localImagePage.title(withNamespace=False)))
        commonsText = commonsImagePage.get()
        if self.getOption('replaceonly') is False:
            if sha1 == commonsImagePage.latest_file_info.sha1:
                pywikibot.output(
                    u'The image is identical to the one on Commons.')
                if len(localImagePage.getFileVersionHistory()) > 1:
                    pywikibot.output(
                        u"This image has a version history. Please \
                        delete it manually after making sure that the \
                        old versions are not worth keeping.""")
                    return
                if self.getOption('always') is False:
                    format_str = color_format(
                        '\n\n>>>> Description on {lightpurple}%s'
                        '{default} <<<<\n')
                    pywikibot.output(format_str % page.title())
                    pywikibot.output(localImagePage.get())
                    pywikibot.output(format_str %
                                     commonsImagePage.title())
                    pywikibot.output(commonsText)
                    if pywikibot.input_yn(
                            u'Does the description on Commons contain '
                            'all required source and license\n'
                            'information?',
                            default=False, automatic_quit=False):
                        localImagePage.delete(
                            '%s [[:commons:Image:%s]]'
                            % (comment, filenameOnCommons), prompt=False)
                else:
                    localImagePage.delete(
                        comment + ' [[:commons:Image:%s]]'
                        % filenameOnCommons, prompt=False)
            else:
                pywikibot.output(
                    u'The image is not identical to the one on Commons.')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}

    for arg in pywikibot.handle_args(args):
        if arg == '-replacealways':
            options['replace'] = True
            options['replacealways'] = True
        elif arg == '-autonomous':
            pywikibot.warning(u"The '-autonomous' argument is DEPRECATED,"
                              u" use '-always' instead.")
            options['always'] = True
        elif arg.startswith('-'):
            if arg[1:] in ('always', 'replace', 'replaceloose', 'replaceonly'):
                options[arg[1:]] = True

    bot = NowCommonsDeleteBot(**options)
    bot.run()

if __name__ == "__main__":
    main()
