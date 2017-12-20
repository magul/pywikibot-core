#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot downloads dump from dumps.wikimedia.org.

This script supports the following command line parameters:

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

import io
import os.path
import sys

from shutil import copyfile, copyfileobj

import pywikibot

from pywikibot import Bot

from pywikibot.comms.http import fetch


class DownloadDumpBot(Bot):

    """Download dump bot."""

    availableOptions = {
        'wikiname': '',
        'filename': '',
        'storepath': './',
    }

    def __init__(self, **kwargs):
        """Constructor."""
        super(DownloadDumpBot, self).__init__(**kwargs)

    def get_dump_name(self, db_name, typ):
        """Check if dump file exists locally in a Toolforge server."""
        db_path = '/public/dumps/public/{0}/'.format(db_name)
        if os.path.isdir(db_path):
            dates = map(int, os.listdir(db_path))
            dates = sorted(dates, reverse=True)
            for date in dates:
                dump_filepath = '/public/dumps/public/' + \
                    '{0}/{1}/{2}-{3}-{4}'.format(db_name, date, db_name, date, typ)
                if os.path.isfile(dump_filepath):
                    return dump_filepath
        return None

    def run(self):
        """Run bot."""
        pywikibot.output('Downloading dump from ' + self.getOption('wikiname'))

        download_filename = self.getOption('wikiname') + \
            '-latest-' + self.getOption('filename')
        file_storepath = os.path.join(
            self.getOption('storepath'), download_filename)

        # https://wikitech.wikimedia.org/wiki/Help:Toolforge#Dumps
        toolforge_dump_filepath = self.get_dump_name(
            self.getOption('wikiname'), self.getOption('filename'))
        if toolforge_dump_filepath:
            pywikibot.output('Copying file from ' + toolforge_dump_filepath)
            copyfile(toolforge_dump_filepath, file_storepath)
        else:
            url = 'https://dumps.wikimedia.org/' + \
                os.path.join(self.getOption('wikiname'),
                    'latest', download_filename)
            pywikibot.output('Downloading file from ' + url)
            response = fetch(url)
            if response.status == 200:
                try:
                    with open(file_storepath, 'wb') as result_file:
                        copyfileobj(io.BytesIO(response.raw), result_file)
                except IOError:
                    pywikibot.exception()
                    return False
            else:
                return

        pywikibot.output('Done! File stored as ' + file_storepath)
        return


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
            if option == 'filename':
                opts[option] = value or pywikibot.input(
                    'Enter the filename: ')
            elif option == 'storepath':
                opts[option] = os.path.abspath(value) or pywikibot.input(
                    'Enter the store path: ')
        else:  # discard
            pywikibot.output('Unknown argument: ' + arg)
            continue

    if not pywikibot.config.family:
        pywikibot.error("The family wasn't given.")
        sys.exit(1)
    if not pywikibot.config.mylang:
        pywikibot.error("The wiki language wasn't given.")
        sys.exit(1)
    if 'filename' not in opts:
        pywikibot.error("The filename wasn't given.")
        sys.exit(1)

    wikiname_family = pywikibot.config.family
    if wikiname_family == 'wikipedia':
        wikiname_family = 'wiki'
    opts['wikiname'] = pywikibot.config.mylang + wikiname_family

    bot = DownloadDumpBot(**opts)
    bot.run()


if __name__ == '__main__':
    main()
