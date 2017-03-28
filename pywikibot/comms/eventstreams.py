# -*- coding: utf-8 -*-
"""
EventStreams based stream client.

This file is part of the Pywikibot framework.

This module requires sseclient to be installed:
    pip install sseclient
"""
#
# (C) 2014 Merlijn van Deen
# (C) Pywikibot team, 2014-2016
# (C) Andrew Otto, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import sys
import threading

from sseclient import SSEClient as EventSource
import json

if sys.version_info[0] > 2:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty

from pywikibot.bot import debug, warning

_logger = 'pywikibot.eventstream'


class EventStreamThread(threading.Thread):

    """
    Low-level EventStreams Listener Thread, pushing stream events into a queue.

    @param url: The SSE/EventSource endpoint from which to consume events.
    @param filter_fn: A function returns true if an event should be enqueued,
                      or false if it should be skipped.
    @param total: the maximum number of entries to return. The underlying
                  thread is shut down then this number is reached.

    This runs in a Thread. It makes the actual SSE/EventSource
    connection to the EventStreams server and pushes
    event dicts into a queue.

    Usage:

    >>> t = EventStreamThread('https://stream.wikimedia.org/v2/recentchange')
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
    def __init__(
        self,
        url,
        filter_fn=None,
        total=None
    ):
        """Constructor for EventStreamThread."""

        super(EventStreamThread, self).__init__()
        self.url = url
        self.filter_fn = filter_fn

        self.daemon = True
        self.running = False
        self.queue = Queue()

        self.warn_queue_length = 100

        self.total = total
        self.count = 0

        debug('Opening connection to %r' % self, _logger)


    def __repr__(self):
        """Return representation."""
        return "<EventStream from %s>" % (self.url)


    def enqueue(self, element):
        """
        Enqueues element.  If we have reached our total, stop the thread.
        If the queue starts to grow, beyond warn_queue_length, this will
        log a warning.
        """
        self.count += 1
        self.queue.put(element)
        if self.queue.qsize() > self.warn_queue_length:
            warning('%r queue length exceeded %i'
                    % (self,
                       self.warn_queue_length),
                    _logger=_logger)
            self.warn_queue_length = self.warn_queue_length + 100

        if self.total is not None and self.count >= self.total:
            self.stop()


    def filter(self, element):
        """
        Returns True if not filter_fn or returns filter_fn(element)
        This just wraps up filter_fn so we don't have to check for
        its existence while filtering.
        """
        if not self.filter_fn:
            return True
        else:
            return bool(self.filter_fn(element))


    def run(self):
        """
        Threaded function.

        Runs inside the thread when started with .start().
        """
        self.running = True

        # Connect to the SSE/EventSource endpoint
        eventsource = EventSource(self.url)
        while self.running:
            # Consume an event.
            event = next(eventsource)

            # If event type is error, log and continue.
            if event.event == 'error':
                warning(
                    'Encountered error reading event: %s \'%s\''
                    % (self, event.data), _logger=_logger
                )

            # Else assume event.data is a JSON string.
            elif event.event == 'message' and event.data:
                try:
                    element = json.loads(event.data)
                except Exception as e:
                    warning('Could not parse event.data as json: %s'
                        % (event), _logger=_logger
                    )
                else:
                    # If this element passes the filter, then enqueue it.
                    if self.filter(element):
                        self.enqueue(element)

        debug('Shut down event loop for %r' % self, _logger)
        del eventsource
        debug('Disconnected %r' % self, _logger)
        self.queue.put(None)

    def stop(self):
        """Stop the thread."""
        self.running = False


def eventstream(url, total=None, filter_fn=None):
        """Yield changes received from an EventStream.

        @param url: The SSE/EventSource endpoint from which to consume events.
        @param filter_fn: A function returns true if an event should be enqueued,
                          or false if it should be skipped.
        @param total: the maximum number of entries to return. The underlying
                      thread is shut down then this number is reached.

        @return: yield dict event consumed from the stream.
        @rtype: generator
        """
    thread = EventStreamThread(
        url=url,
        total=total,
        filter_fn=filter_fn
    )

    debug('Starting EventStreams thread from %r' % url, _logger)
    thread.start()

    while True:
        try:
            element = thread.queue.get(timeout=0.1)
        except Empty:
            continue
        if element is None:
            return
        yield element
