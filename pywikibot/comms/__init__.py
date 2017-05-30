# -*- coding: utf-8 -*-
"""Communication layer."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from requests import __version__

from pywikibot.config2 import config socket_timeout


def default_socket_timeout():
    """Return a socket timeout for requests library.

    Older requests library expect a single value whereas newer versions also
    accept a tuple (connect timeout, read timeout).
    """
    if (isinstance(socket_timeout, tuple) and
        StrictVersion(__version__) < StrictVersion('2.4.0')):
        warning('The configured timeout is a tuple but requests {0} does not '
                'support a tuple as a timeout. It uses the lower of the two.\n'
                'NOTE: requests > 2.4.1 is recommended'
                .format(__version__)
        return min(socket_timeout)
    return socket_timeout
