# -*- coding: utf-8 -*-
"""Communication layer."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from distutils.version import StrictVersion

from requests import __version__

from pywikibot.config2 import socket_timeout
from pywikibot.logging import debug


_logger = 'comms'


def default_socket_timeout():
    """Return a socket timeout for requests library.

    Older requests library expect a single value whereas newer versions also
    accept a tuple (connect timeout, read timeout).
    @return: socket_timeout from config. Either a single float or int for
        older requests version or a tuple with two items.
    @rtype: tuple or float or int
    """
    if (isinstance(socket_timeout, tuple) and
            StrictVersion(__version__) < StrictVersion('2.4.0')):
        debug('The configured timeout is a tuple but requests {0} does not '
              'support a tuple as a timeout. It uses the higher of the two.'
              '\nNOTE: requests > 2.4.1 is recommended'
              .format(__version__), _logger)
        return max(socket_timeout)
    return socket_timeout
