#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot downloads dump from dumps.wikimedia.org.

This script supports the following command line parameters:

    -hours:#        Use this parameter if to make the script repeat itself
                    after  # hours. Hours can be defined as a decimal. 0.01
                    hours are 36 seconds; 0.1 are 6 minutes.

    -wikiname:#     The name of the wiki (e.g. frwiki).

    -filename:#     The name of the file (e.g. abstract.xml)

    -storepath:#    The stored file's path.

"""
#
# (C) Pywikibot team, 2017
# (C) Yifei He, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import os.path

from shutil import copyfile
import time

import pywikibot

from pywikibot import Bot

from pywikibot.comms.http import fetch


class DownloadDumpBot(Bot):

    """Download dump bot."""

    availableOptions = {
        'hours': 1,
        'no_repeat': True,
        'wikiname': '',
        'filename': '',
        'storepath': '/data/',
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


                try:
                    response = fetch(url)
                    pywikibot.output('Downloading file from ' + url)

                    with open(file_storepath, 'w') as result_file:
                        result_file.write(response.content)
                except IOError:
                    pywikibot.output('Got an IOError, let\'s try again')

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
    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option.startswith('-'):
            option = option[1:]
            if option == 'hours':
                opts['hours'] = float(value)
                opts['no_repeat'] = False
            elif option == 'wikiname':
                opts['wikiname'] = value or pywikibot.input('Enter the wiki name:')
            elif option == 'filename':
                opts['filename'] = value or pywikibot.input('Enter the filename:')
            elif option == 'storepath':
                opts['storepath'] = value or pywikibot.input('Enter the store path:')
        else:  # discard
            continue

    if 'wikiname' not in opts:
        pywikibot.error("The wiki name wasn't given.")
        return
    if 'filename' not in opts:
        pywikibot.error("The filename wasn't given.")
        return

    bot = DownloadDumpBot(**opts)
    bot.run()


if __name__ == '__main__':
    main()
