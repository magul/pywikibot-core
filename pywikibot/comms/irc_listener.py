# -*- coding: utf-8 -*-
"""
IRC listener to recent changes of wikis of Wikimedia.

It gives similar API to that of rcstream.

(C) 2015 Eranroz

Distributed under the terms of the MIT license.
"""
from __future__ import unicode_literals

import re
import sys
import threading

import pywikibot
from pywikibot.botirc import IRCBot

if sys.version_info[0] > 2:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty


class IRCRecentChangesBot(IRCBot):
    """IRC bot for parsing recent changes IRC messages in similar way to rcstream."""

    def __init__(self, site, channel, nickname, server, filter_generator=None):
        """
        Instantiate a IRCRecentChangesBot object.

        @param site: the site object to yield changes for
        @type site: pywikibot.Site
        @param channel: IRC channel to listen for
        @type channel: str
        @param nickname: nickname in the IRC channel
        @type nickname: str
        @param server: IRC server
        @type server: str
        @param filter_generator: generator to use for filtering the yielded pages. For None there is no filtering
        @type filter_generator: callable
        """
        super(IRCRecentChangesBot, self).__init__(site, channel, nickname, server)
        self.re_new_page_diff = re.compile(r'.+index\.php\?oldid=(?P<new>[0-9]+)')
        self.re_edit_page_diff = re.compile(r'.+index\.php\?diff=(?P<new>\d+)&oldid=(?P<old>\d+)')
        self.queue = Queue()
        filter_generator = filter_generator if filter_generator else lambda x: x
        self.filter_generator = filter_generator

    def on_pubmsg(self, c, e):
        match = self.re_edit.match(e.arguments()[0])
        if not match:
            return

        try:
            msg = e.arguments()[0].decode('utf-8')
        except UnicodeDecodeError:
            return

        page_title_end = msg.find(u'\x0314', 9)
        if page_title_end == -1:
            return
        name = msg[8:page_title_end]
        page = pywikibot.Page(self.site, name)

        if 'N' in match.group('flags'):  # new page
            diff_matcher = self.re_new_page_diff
            old_rev = 0
        else:
            diff_matcher = self.re_edit_page_diff
            old_rev = None
        diff_match = diff_matcher.match(match.group('url'))
        if not diff_match:
            return

        diff_revisions = {'new': int(diff_match.group('new')),
                          'old': int(diff_match.group('old')
                                     if old_rev is None else old_rev)}
        diff_data = {
            'type': 'edit',
            'comment': match.group('summary'),
            'user': match.group('user'),
            'namespace': page.namespace(),
            'revision': diff_revisions,
            'diff_bytes': int(match.group('bytes')),
            'bot': 'B' in match.group('flags')
        }
        page._rcinfo = diff_data

        # use of generator rather than simple if allow easy use of pagegenerators
        try:
            for filtered_page in self.filter_generator([page]):
                self.queue.put(filtered_page)
        except:
            # whatever reason the filter fail we can ignore it
            pass


class IRCRcBotThread(threading.Thread):
    """Wrapper thread for IRCRecentChangesBot.

    @param site: the pywikibot.Site object to yield changes for
    @param channel: IRC channel to listen for
    @param nickname: nickname in the IRC channel
    @param server: IRC server
    @param filter_generator: generator to use for filtering the yielded pages
    """

    def __init__(self, site, channel, nickname, server, filter_generator=None):
        super(IRCRcBotThread, self).__init__()
        self.daemon = True
        self.irc_bot = IRCRecentChangesBot(site, channel, nickname, server, filter_generator)

    def run(self):
        self.irc_bot.start()

    def stop(self):
        self.irc_bot.die()


def irc_rc_listener(site, filter_gen=None):
    """RC Changes Generator. Yields changes received from IRC channel.

    @param site: the pywikibot.Site object to yield live recent changes for
    @type site: pywikibot.BaseSite
    @param filter_gen: generator to use for filtering the yielded pages
    """
    channel = site.irc_rc_channel()
    server = site.irc_rc_host()
    nickname = site.username()
    irc_thread = IRCRcBotThread(site, channel, nickname, server, filter_gen)
    irc_thread.start()
    while True:
        try:
            element = irc_thread.irc_bot.queue.get(timeout=0.1)
        except Empty:
            continue
        if element is None:
            return
        yield element
