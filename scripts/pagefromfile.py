#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Bot to upload pages from a file.

This bot takes its input from a file that contains a number of
pages to be put on the wiki. The pages should all have the same
begin and end text (which may not overlap).

By default the text should have the intended title of the page
as the first text in bold (that is, between ''' and '''),
you can modify this behavior with command line options.

The default is not to include the begin and
end text in the page, if you want to include that text, use
the -include option.

Specific arguments:

-start:xxx      Specify the text that marks the beginning of a page
-end:xxx        Specify the text that marks the end of a page
-autostart      The start marker is the first line of the file (replaces -start)
-startisstop    The start marker is also the endmarker for the previous page and
                expects then the second file variant.
                (replaces -end)
-file:xxx       Give the filename we are getting our material from
                (default: dict.txt)
-include        The beginning and end markers should be included
                in the page.
-titlestart:xxx Use xxx in place of ''' for identifying the
                beginning of page title
-titleend:xxx   Use xxx in place of ''' for identifying the
                end of page title
-notitle        do not include the title, including titlestart, and
                titleend, in the page
-nocontent      If page has this statment it doesn't append
                (example: -nocontent:"{{infobox")
-noredirect     if you don't want to upload on redirect page
                it is True by default and bot adds pages to redirected pages
-summary:xxx    Use xxx as the edit summary for the upload - if
                a page exists, standard messages are appended
                after xxx for appending, prepending, or replacement
-autosummary    Use MediaWikis autosummary when creating a new page,
                overrides -summary in this case
-minor          set minor edit flag on page edits

If the page to be uploaded already exists:

-safe           do nothing (default)
-appendtop      add the text to the top of it
-appendbottom   add the text to the bottom of it
-force          overwrite the existing page

The file should contain the text of each side with the start marker in front of
it and the end marker at the end. The title of each page are the first words in
the text surrounded by the title markers. When using -startisstop the title can
also be given after the page start marker. In that mode the text starts after
the first newline after the start marker, while in the original mode it uses the
text immediately after the page start marker (so a new line is in theory not
necessary). Leading newline (CR and LF) will be removed.
"""
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2005-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import codecs
import os
import random
import re
import string

import pywikibot
from pywikibot import config, Bot, i18n
from pywikibot.tools import deprecated


class NoTitle(Exception):

    """No title found."""

    def __init__(self, offset):
        """Constructor."""
        self.offset = offset


class PageFromFileRobot(Bot):

    """
    Responsible for writing pages to the wiki.

    Titles and contents are given by a PageFromFileReader.

    """

    def __init__(self, reader, **kwargs):
        """Constructor."""
        self.availableOptions.update({
            'always': True,
            'force': False,
            'append': None,
            'summary': None,
            'minor': False,
            'autosummary': False,
            'nocontent': '',
            'redirect': True
        })

        super(PageFromFileRobot, self).__init__(**kwargs)
        self.reader = reader

    def run(self):
        """Start file processing and upload content."""
        for title, contents in self.reader.run():
            self.save(title, contents)

    def save(self, title, contents):
        """Upload page content."""
        mysite = pywikibot.Site()

        page = pywikibot.Page(mysite, title)
        self.current_page = page

        if self.getOption('summary'):
            comment = self.getOption('summary')
        else:
            comment = i18n.twtranslate(mysite, 'pagefromfile-msg')

        comment_top = comment + " - " + i18n.twtranslate(
            mysite, 'pagefromfile-msg_top')
        comment_bottom = comment + " - " + i18n.twtranslate(
            mysite, 'pagefromfile-msg_bottom')
        comment_force = "%s *** %s ***" % (
            comment, i18n.twtranslate(mysite, 'pagefromfile-msg_force'))

        # Remove trailing newlines (cause troubles when creating redirects)
        contents = re.sub('^[\r\n]*', '', contents)

        if page.exists():
            if not self.getOption('redirect') and page.isRedirectPage():
                pywikibot.output(u"Page %s is redirect, skipping!" % title)
                return
            pagecontents = page.get(get_redirect=True)
            if self.getOption('nocontent') != u'':
                if pagecontents.find(self.getOption('nocontent')) != -1 or \
                pagecontents.find(self.getOption('nocontent').lower()) != -1:
                    pywikibot.output(u'Page has %s so it is skipped' % self.getOption('nocontent'))
                    return
            if self.getOption('append') == 'top':
                pywikibot.output(u"Page %s already exists, appending on top!"
                                     % title)
                contents = contents + pagecontents
                comment = comment_top
            elif self.getOption('append') == 'bottom':
                pywikibot.output(u"Page %s already exists, appending on bottom!"
                                     % title)
                contents = pagecontents + contents
                comment = comment_bottom
            elif self.getOption('force'):
                pywikibot.output(u"Page %s already exists, ***overwriting!"
                                 % title)
                comment = comment_force
            else:
                pywikibot.output(u"Page %s already exists, not adding!" % title)
                return
        else:
            if self.getOption('autosummary'):
                comment = ''
                config.default_edit_summary = ''

        self.userPut(page, page.text, contents,
                     summary=comment,
                     minor=self.getOption('minor'),
                     show_diff=False,
                     ignore_save_related_errors=True)


class PageToFileWriter(object):

    """
    A class to write page contents into a file using the core mode.

    It flushes the data after each page so even if an exception occurs, the
    previous pages have been written. This is only possible in core file mode
    as that allows to change the marker in between in case a page contains the
    marker used on the previous pages.

    The page name is also always set explicitly so when reading, title markers
    are not necessary.
    """

    def __init__(self, filename, marker_hint=None):
        """
        Create a new writer instance and open the file object.

        @param filename: The filename of the file
        @type filename: str
        @param marker_hint: A preset marker to be used between files. If not
            set or as soon as the marker appears in the text it'll be changed.
            By default it is not set.
        @type marker_hint: str or None
        """
        super(PageToFileWriter, self).__init__()
        if marker_hint and set(marker_hint) & set(' \n'):
            raise ValueError('The marker_hint may not contain spaces or newlines.')
        self._file = codecs.open(filename, 'w', config.textfile_encoding)
        self._marker = marker_hint
        self._marker_written = False

    def _get_marker(self, text):
        """Generate a new marker when the current is not suitable."""
        # In theory it's possible that the text contains all sequences possible
        # by generating 10 digits randomly but the chance is verly low
        changed = False
        while not self._marker or self._marker in text:
            self._marker = ''.join(random.choice(string.ascii_letters + string.digits)
                                   for _ in range(10))
            changed = True
        return changed

    def write(self, page):
        """Write this page's content to the file."""
        # Test and if required select a new marker
        if self._get_marker(page.text) or not self._marker_written:
            self._marker_written = True
            self._file.write(self._marker)
        self._file.write(' {0}\n'.format(page.title(withSection=False)))
        self._file.write(page.text)
        # Don't add a new line after the marker in case the marker changes
        self._file.write('\n' + self._marker)
        self._file.flush()  # This is fine now

    def __enter__(self):
        """Enter a context and return itself."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit a context and close the file."""
        self.close()

    def close(self):
        """Close the underlying file."""
        self._file.close()


class PageFromFileReader(object):

    """
    Responsible for reading the file.

    The run() method yields a (title, contents) tuple for each found page.

    """

    def __init__(self, filename, pageStartMarker, pageEndMarker,
                 titleStartMarker, titleEndMarker, include, notitle):
        """Constructor.

        Check if self.file name exists. If not, ask for a new filename.
        User can quit.

        """
        self.filename = filename
        self.pageStartMarker = pageStartMarker
        self.pageEndMarker = pageEndMarker
        self.titleStartMarker = titleStartMarker
        self.titleEndMarker = titleEndMarker
        self.include = include
        self.notitle = notitle
        self._title_regex = re.compile('{0}(.*?){1}'.format(
            re.escape(self.titleStartMarker),
            re.escape(self.titleEndMarker)), re.DOTALL)

    def run(self):
        """Read file and yield page title and content."""
        pywikibot.output('\n\nReading \'%s\'...' % self.filename)
        try:
            with codecs.open(self.filename, 'r',
                             encoding=config.textfile_encoding) as f:
                text = f.read()

        except IOError as err:
            pywikibot.output(str(err))
            raise IOError

        if self.pageStartMarker is None:
            # In the startisstop-mode the marker also stops after the first
            # space (whichever comes first)
            search_for = r'\n'
            if self.pageEndMarker is None:
                search_for += r' '
            self.pageStartMarker = re.search(r'(.*?)[{0}]'.format(search_for),
                                             text).group(1)

        end = 0
        # search for the next pageStartMarker
        position = start = text.find(self.pageStartMarker)
        while start >= 0:
            position = start
            text_between = text[end:position].strip()
            if text_between:
                pywikibot.warning('Found text between page markers: {0}'.format(
                    text_between))
            marker_end = position + len(self.pageStartMarker)
            if self.pageEndMarker is None:
                # Read new start marker and title
                # BEWARE: the start/end are relative to marker_end OR position
                # when the marker has changed!
                after_marker_match = re.match(r'^([^ \n]*) *(.*?)\n',
                                              text[marker_end:])
                content_start = after_marker_match.end() + marker_end
                if after_marker_match.group(1):
                    self.pageStartMarker = after_marker_match.group(1)
                    # Changing the marker behaves like changing where the text
                    # starts
                    position = marker_end
                    marker_end += len(self.pageStartMarker)
                title = after_marker_match.group(2)
                # these are always the same
                start = end = text.find(self.pageStartMarker, marker_end)
                if end >= 0:
                    title, contents = self._extract_information(
                        text, position, content_start, end, title)
            else:
                try:
                    try:
                        end, title, contents = self.findpage(text[position:])
                    except NoTitle as err:
                        end = err.offset
                        title = None
                    end += position
                    start = text.find(self.pageStartMarker, end)
                except AttributeError as e:
                    assert('start' in str(e))
                    end = start = -1
                # Either both are -1 or end is at the end of the marker while
                # find finds the start of the marker
                assert(text.find(self.pageEndMarker, marker_end) ==
                       (end if end == -1 else end - len(self.pageEndMarker)))

            if start >= 0:
                if not title:
                    pywikibot.warning(
                        'No title found for page in line {0}. Skipping.'.format(
                            text.count('\n', 0, marker_end) + 1))
                else:
                    yield title, contents

        if self.pageEndMarker is None:
            # start marker is also end marker, so it wasn't matched
            position += len(self.pageStartMarker)
        rest_of_file = text[position:].strip()
        if rest_of_file:
            pywikibot.warning('Found text after the last page marker: {0}'.format(
                rest_of_file))

    @deprecated
    def findpage(self, text):
        """Find page to work on."""
        pageR = re.compile(re.escape(self.pageStartMarker) + "(.*?)" +
                           re.escape(self.pageEndMarker), re.DOTALL)

        location = pageR.search(text)
        title, contents = self._extract_information(
            text, location.start(), location.start(1), location.end(1))
        if not title:
            raise NoTitle(location.end())
        return location.end(), title, contents

    def _extract_information(self, text, start, content_start,
                             content_end, title=None):
        """Return title and contents from the given match."""
        if self.include:
            # if the pageEndMarker is not defined use the pageStartMarker
            contents = text[start:content_end + len(self.pageEndMarker or
                                                    self.pageStartMarker)]
        else:
            contents = text[content_start:content_end]
        title_match = self._title_regex.search(contents)
        if title_match:
            new_title = title_match.group(1)
            if not title:
                title = new_title
            elif title == new_title:
                if self.notitle:
                    # Remove title (to allow creation of redirects)
                    contents = (contents[:title_match.start()] +
                                contents[title_match.end():])
        return title, contents


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Adapt these to the file you are using. 'pageStartMarker' and
    # 'pageEndMarker' are the beginning and end of each entry. Take text that
    # should be included and does not occur elsewhere in the text.

    # TODO: make config variables for these.
    filename = "dict.txt"
    pageStartMarker = "{{-start-}}"
    pageEndMarker = "{{-stop-}}"
    titleStartMarker = u"'''"
    titleEndMarker = u"'''"
    options = {}
    include = False
    notitle = False

    for arg in pywikibot.handle_args(args):
        if arg.startswith("-start:"):
            pageStartMarker = arg[7:]
        elif arg.startswith("-end:"):
            pageEndMarker = arg[5:]
        elif arg == '-autostart':
            pageStartMarker = None
        elif arg == '-startisstop':
            pageEndMarker = None
        elif arg.startswith("-file:"):
            filename = arg[6:]
        elif arg == "-include":
            include = True
        elif arg.startswith('-append') and arg[7:] in ('top', 'bottom'):
            options['append'] = arg[7:]
        elif arg == "-force":
            options['force'] = True
        elif arg == "-safe":
            options['force'] = False
            options['append'] = None
        elif arg == "-noredirect":
            options['redirect'] = False
        elif arg == '-notitle':
            notitle = True
        elif arg == '-minor':
            options['minor'] = True
        elif arg.startswith('-nocontent:'):
            options['nocontent'] = arg[11:]
        elif arg.startswith("-titlestart:"):
            titleStartMarker = arg[12:]
        elif arg.startswith("-titleend:"):
            titleEndMarker = arg[10:]
        elif arg.startswith("-summary:"):
            options['summary'] = arg[9:]
        elif arg == '-autosummary':
            options['autosummary'] = True
        else:
            pywikibot.output(u"Disregarding unknown argument %s." % arg)

    failed_filename = False
    while not os.path.isfile(filename):
        pywikibot.output('\nFile \'%s\' does not exist. ' % filename)
        _input = pywikibot.input(
            'Please enter the file name [q to quit]:')
        if _input == 'q':
            failed_filename = True
            break
        else:
            filename = _input

    # show help text from the top of this file if reader failed
    # or User quit.
    if failed_filename:
        pywikibot.showHelp()
    else:
        reader = PageFromFileReader(filename, pageStartMarker, pageEndMarker,
                                    titleStartMarker, titleEndMarker, include,
                                    notitle)
        bot = PageFromFileRobot(reader, **options)
        bot.run()

if __name__ == "__main__":
    main()
