# -*- coding: utf-8 -*-
"""
Server-Sent Events client.

This file is part of the Pywikibot framework.

This module requires sseclient to be installed:
    pip install sseclient
"""
#
# (C) Xqt, 2017
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import json

try:
    from sseclient import SSEClient as EventSource
except ImportError as e:
    EventSource = e

from pywikibot.bot import debug, warning
from pywikibot.tools import has_module, redirect_func

_logger = 'pywikibot.eventstream'



def rc_listener(wikihost, rchost, rcport=443, rcpath='/v2/stream', total=None):
    """Yield changes received from EventStream.

    @param wikihost: the hostname of the wiki we want to get changes for. This
                     is passed to rcstream using a 'subscribe' command. Pass
                     '*' to listen to all wikis for a given rc host.
    @param rchost: the recent changes stream host to connect to. For Wikimedia
                   wikis, this is 'https://stream.wikimedia.org'
    @param rcport: the port to connect to (default: 80)
    @param rcpath: the sockets.io path. For Wikimedia wikis, this is '/rc'.
                   (default: '/rc')
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
    @raises ImportError
    """
    if isinstance(EventSource, Exception):
        raise ImportError('sseclient is required for the rc stream;\n'
                          'install it with "pip install sseclient"\n')

    url = rchost + rcpath + '/' + 'recentchange'
    i = 0
    for event in EventSource(url):
        if event.event == 'message' and event.data:
            element = json.loads(event.data)
            if element['server_name'] == wikihost:
                yield element
                i += 1
                if total and i >= total:
                    return
        elif event.event == 'error':
            print('--- Encountered error', event.data)
        else:
            print('.')

def site_rc_listener(site, total=None):
    """Yield changes received from EventStream.

    @param site: the Pywikibot.Site object to yield live recent changes for
    @type site: Pywikibot.BaseSite
    @param total: the maximum number of changes to return
    @type total: int

    @return: pywikibot.comms.eventstream.rc_listener configured for given site
    """
    if isinstance(EventSource, Exception):
        warning('sseclient is required for EventStream;\n'
                'install it with "pip install sseclient"\n')
        from pywikibot.comms.rcstream import rc_listener
    else:
        from pywikibot.comms.eventstream import rc_listener

    return rc_listener(
        wikihost=site.hostname(),
        rchost=site.rcstream_host(),
        rcport=site.rcstream_port(),
        total=total,
    )
