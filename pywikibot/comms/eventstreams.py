# -*- coding: utf-8 -*-
"""
EventStreams based stream client.

This file is part of the Pywikibot framework.

This module requires sseclient to be installed:
    pip install sseclient
"""
#
# (C) Andrew Otto, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import json

from pywikibot.bot import debug, warning
from pywikibot import BaseSite

from sseclient import SSEClient as EventSource

import sys


_logger = 'pywikibot.eventstream'


def eventstream(url, total=None, filter_fn=None):
    """Yield event dicts received from an EventStream.

    @param url: The SSE/EventSource endpoint from which to consume events.
                To get the Wikimedia recentchange stream, use:
                https://stream.wikimedia.org/v2/stream/eventstreams.
    @param filter_fn: A function that returns true if an event should be
                      yielded or false if it should be skipped.
                      If not specified, all events will be yielded.
    @param total: The maximum number of entries to return. The underlying
                  thread is shut down then this number is reached.  If not
                  specified, this will iterate the stream forever.

    @return: yield dict event consumed from the stream.
    @rtype: generator
    """

    count = 0

    debug('Consuming EventStream from %r' % url, _logger)

    eventsource = EventSource(url)
    # Connect to the SSE/EventSource endpoint
    for e in eventsource:
        # If event type is error, log and continue.
        if e.event == 'error':
            warning(
                'Encountered error reading event: %s'
                % (event), _logger=_logger
            )

        # Else assume event.data is a JSON string.
        elif e.event == 'message' and e.data:
            try:
                event = json.loads(e.data)
            except Exception as exc:
                warning(
                    'Could not parse event data as JSON: %s. %s'
                    % (e, exc), _logger=_logger
                )
            else:
                # If this element passes the filter, then enqueue it.
                if filter_fn is None or filter_fn(event):
                    count += 1
                    yield event

        if total is not None and count > total:
            del eventsource
            break


def create_field_filter_fn(key, value):
    """
    Returns a function that takes a dict.  If that dict has key
    and the value is value, then the function will return true, else false.

    @param key
    @param value
    @return function
    """
    return lambda event: key in event and event[key] == value


def recentchanges(
    url='https://stream.wikimedia.org/v2/stream/recentchange',
    total=None,
    site=None,
):
    """
    Returns a stream of recentchange events, optionally filterd by wiki site.

    @param url
    @param total
    @param site: Either a pywikibot.BaseSite or a string site server_name.
    """

    filter_fn = None
    if isinstance(site, BaseSite):
        site = site.hostname()
    if site is not None:
        filter_fn = create_field_filter_fn('server_name', site)

    return eventstream(url, total, filter_fn)
