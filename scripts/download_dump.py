#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot downloads dump from dumps.wikimedia.org.

This script understands the following command - line arguments:

&params;

Furthermore, the following command line parameters are supported:

    -hours:#        Use this parameter if to make the script repeat itself
                    after  # hours. Hours can be defined as a decimal. 0.01
                    hours are 36 seconds; 0.1 are 6 minutes.

    -wikiname:#     The name of the wiki (e.g. frwiki).

    -filename:#     The name of the file (e.g. abstract.xml)

    -storepath:#    The stored file's path.

"""
#
# (C) Yifei He, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import os.path

import requests

from shutil import copyfile
import time

import pywikibot

from pywikibot import Bot, pagegenerators

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class DownloadDumpBot(Bot):

    """Download dump bot."""

    availableOptions = {
        'hours': 1,
        'no_repeat': True,
        'wikiname': '',
        'filename': '',
        'storepath': '',
    }

    def __init__(self, **kwargs):
        """Constructor."""
        super(DownloadDumpBot, self).__init__(**kwargs)

    def run(self):
        """Run bot."""
        while True:
            wait = False
            now = time.strftime('%d %b %Y %H:%M:%S (UTC)', time.gmtime())

            download_filename = self.getOption('wikiname') + \
                '-latest-' + self.getOption('filename')
            download_path = self.getOption('wikiname') + \
                '/latest/' + download_filename

            file_storepath = self.getOption('storepath') + download_filename

            # https://wikitech.wikimedia.org/wiki/Help:Toolforge#Dumps
            toolforge_dump_path = '/public/dumps/public/' + download_path
            if os.path.isfile(toolforge_dump_path):
                copyfile(toolforge_dump_path, file_storepath)
                pywikibot.output('Copying file from ' + toolforge_dump_path)
            else:
                url = 'https://dumps.wikimedia.org/' + download_path

                response = requests.get(url)
                pywikibot.output('Downloading file from ' + url)

                if response.status_code == 200:
                    with open(file_storepath, 'wb') as f:
                        f.write(response.content)
                else:
                    response.raise_for_status()

            if self.getOption('no_repeat'):
                pywikibot.output('Done.')
                return
            elif not wait:
                if self.getOption('hours') < 1.0:
                    pywikibot.output('Sleeping {0} minutes, now {1}'.format(
                        (self.getOption('hours') * 60), now))
                else:
                    pywikibot.output('Sleeping {0} hours, now {1}'.format(
                        self.getOption('hours'), now))
                time.sleep(self.getOption('hours') * 60 * 60)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    opts = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if arg.startswith('-hours:'):
            opts['hours'] = float(arg[len('-hours:'):])
            opts['no_repeat'] = False
        elif arg.startswith('-wikiname'):
            if len(arg) == len('-wikiname'):
                opts['wikiname'] = pywikibot.input('Enter the wiki name:')
            else:
                opts['wikiname'] = arg[len('-wikiname:'):]
        elif arg.startswith('-filename'):
            if len(arg) == len('-filename'):
                opts['filename'] = pywikibot.input('Enter the filename:')
            else:
                opts['filename'] = arg[len('-filename:'):]
        elif arg.startswith('-storepath'):
            if len(arg) == len('-storepath'):
                opts['storepath'] = pywikibot.input('Enter the store path:')
            else:
                opts['storepath'] = arg[len('-storepath:'):]
        else:
            gen_factory.handleArg(arg)

    generator = gen_factory.getCombinedGenerator(preload=True)

    bot = DownloadDumpBot(generator=generator, **opts)
    bot.run()


if __name__ == '__main__':
    main()
