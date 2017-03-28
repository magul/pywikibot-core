# -*- coding: utf-8 -*-
"""
EventStreams based RecentChange stream interface.

This file is part of the Pywikibot framework.

This module requires sseclient to be installed:
    pip install sseclient
"""
#
# (C) 2014 Merlijn van Deen
# (C) Pywikibot team, 2014-2016
# (C) 2017 Andrew Otto
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

from pywikibot.bot import debug, warning
from pywikibot.comms.eventstreams import EventStreamThread, eventstream
_logger = 'pywikibot.rcstream'


def create_wikihost_filter_fn(wikihost):
    if wikihost in [None, '*']:
        filter_fn = None
    else:
        filter_fn = lambda e: e['server_name'] == wikihost

    return filter_fn


def get_eventstreams_recentchange_url(rchost, rcport, rcpath):
    url = rchost
    if rcport:
        url += ':' + str(rcport)
    url += rcpath
    return url


class RcListenerThread(EventStreamThread):

    """
    Low-level RC Listener Thread, pushing RC stream events into a queue.

    @param wikihost: the hostname of the wiki we want to get changes for. This
                     is used to filter events for server_name. Pass
                     None or '*' to listen to all wikis.
    @param rchost: the eventstreams host to connect to. For Wikimedia
                   wikis, this is 'https://stream.wikimedia.org'
    @param rcport: the port to connect to (default: None)
    @param rcpath: the recentchange stream path. For Wikimedia wikis,
                   this is '/v2/stream/recentchange'.
                   (default: '/v2/stream/recentchange')
    @param total: the maximum number of entries to return. The underlying
                  thread is shut down then this number is reached.

    This part of the rc listener runs in a Thread. It makes the actual
    socketIO/websockets connection to the rc stream server, subscribes
    to a single site and pushes those entries into a queue.

    Usage:

    >>> t = RcListenerThread('en.wikipedia.org', 'https://stream.wikimedia.org')
    >>> t.start()
    >>> change = t.queue.get()
    >>> change
    {'server_name': 'en.wikipedia.org', 'wiki': 'enwiki', 'minor': True,
     'length': {'new': 2038, 'old': 2009}, 'timestamp': 1419964350,
     'server_script_path': '/w', 'bot': False, 'user': 'Od Mishehu',
     'comment': 'stub sorting', 'title': 'Bradwell Bay Wilderness',
     'server_url': 'http://en.wikipedia.org', 'id': 703158386,
     'revision': {'new': 640271171, 'old': 468264850},
     'type': 'edit', 'namespace': 0}
    >>> t.stop()  # optional, the thread will shut down on exiting python
    """

    def __init__(self, wikihost=None, rchost='https://stream.wikimedia.org', rcport=None, rcpath='/v2/stream/recentchange', total=None):
        """Constructor for RcListenerThread."""

        super(RcListenerThread, self).__init__(
            url=get_eventstreams_recentchange_url(rchost, rcport, rcpath),
            filter_fn=create_wikihost_filter_fn(wikihost),
            total=total
        )


def rc_listener(wikihost=None, rchost='https://stream.wikimedia.org', rcport=None, rcpath='/v2/stream/recentchange', total=None):
    """Yield changes received from RCstream.

    @param wikihost: the hostname of the wiki we want to get changes for. This
                     is used to filter events for server_name. Pass
                     None or '*' to listen to all wikis.
    @param rchost: the eventstreams host to connect to. For Wikimedia
                   wikis, this is 'https://stream.wikimedia.org'
    @param rcport: the port to connect to (default: None)
    @param rcpath: the recentchange stream path. For Wikimedia wikis, this is '/v2/stream/recentchange'.
                   (default: '/v2/stream/recentchange')
    @param total: the maximum number of entries to return. The underlying thread
                  is shut down then this number is reached.

    @return: yield dict as formatted by MediaWiki's
        MachineReadableRCFeedFormatter, which consists of at least id
        (recent changes id), type ('edit', 'new', 'log' or 'external'),
        namespace, title, comment, timestamp, user and bot (bot flag for the
        change).
    @see: U{MachineReadableRCFeedFormatter<https://doc.wikimedia.org/
        mediawiki-core/master/php/classMachineReadableRCFeedFormatter.html>}
    @rtype: generator
    """

    return eventstream(
        url=get_eventstreams_recentchange_url(rchost, rcport, rcpath),
        filter_fn=create_wikihost_filter_fn(wikihost),
        total=total
    )


def site_rc_listener(site, total=None):
    """Yield changes received from RCstream.

    @param site: the Pywikibot.Site object to yield live recent changes for
    @type site: Pywikibot.BaseSite
    @param total: the maximum number of changes to return
    @type total: int

    @return: pywikibot.comms.rcstream.rc_listener configured for the given site
    """
    return rc_listener(
        wikihost=site.hostname(),
        rchost=site.rcstream_host(),
        rcport=site.rcstream_port(),
        total=total,
    )
