# -*- coding: utf-8 -*-
"""
Server-Sent Events client.

This file is part of the Pywikibot framework.

This module requires sseclient to be installed:
    pip install sseclient
"""
#
# (C) xqt, 2017
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

from pywikibot import debug, Site, warning

_logger = 'pywikibot.eventstreams'

class EventStreams(object):

    """Basic EventStreams iterator class for Server-Sent Events (SSE) protocol.

    It provides access to arbitrary streams of data including recent changes.
    It replaces rcstream.py implementation.
    """

    _streamtype = None

    def __init__(self, site=None):
        """Constructor."""
        if isinstance(EventSource, Exception):
            raise ImportError('sseclient is required for the rc stream;\n'
                              'install it with "pip install sseclient"\n')
        if self._streamtype is None:
            raise NotImplementedError('No stream type specified for class {0}'
                                      ''.format(self.__class__.__name__))
        self.site = site or Site()
        self.total = None

    @property
    def url(self):
        """Get the EventStream's url."""
        if not hasattr(self, '_url'):
            self._url = ('{0}{1}/{2}'.format(self.site.rcstream_host(),
                                             self.site.eventstreams_path(),
                                             self._streamtype))
        return self._url

    @url.setter
    def url(self, url):
        """Set the EventStream's url."""
        self._url = url

    def set_maximum_items(self, value):
        """
        Set the maximum number of items to be retrieved from the stream.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the stream.

        @param value: The value of maximum number of items to be retrieved
            in total to set.
        @type value: int
        """
        if value is not None:
            self.total = int(value)
            debug('{0}: Set limit (maximum_items) to {1}.'
                  ''.format(self.__class__.__name__, self.total), _logger)

    def __iter__(self):
        """Iterator."""
        n = 0
        for event in EventSource(self.url):
            print(event.event)
            if event.event == 'message' and event.data:
                try:
                    element = json.loads(event.data)
                except ValueError as e:
                    warning('Could not load json dato from\n{0}\n'
                            '{1}'.format(element, e))
                else:
                    if element['server_name'] == self.site.hostname():
                        yield element
                        n += 1
                        if self.total is not None and n >= self.total:
                            debug('{0}: Stopped iterating due to '
                                  'exceeding item limit.'
                                  ''.format(self.__class__.__name__), _logger)
                            return
            elif event.event == 'error':
                warning('--- Encountered error', event.data)
            else:
                warning('Unknown event {0} occured'.format(event.event))


class RCStream(EventStreams):

    """Recent changes EventStream class."""

    _streamtype = 'recentchange'

    def __init__(self):
        """Constructor."""
        super(RCStream, self).__init__()


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
        # fallback to old rcstream method
        # NOTE: this will be deprecated soon
        from pywikibot.comms.rcstream import rc_listener
        return rc_listener(
            wikihost=site.hostname(),
            rchost=site.rcstream_host(),
            rcport=site.rcstream_port(),
            rcpath=site.rcstream_path(),
            total=total,
        )

    stream = RCStream()
    stream.set_maximum_items(total)
    return stream

