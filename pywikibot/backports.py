# -*- coding: utf-8 -*-
"""
This module contained backports to support older Python versions.

Their usage is deprecated and this module could be dropped.
"""
#
# (C) Pywikibot team, 2018
#
# Distributed under the terms of the MIT license.
#

from __future__ import absolute_import, unicode_literals

import logging
from difflib import _format_range_unified

from pywikibot.tools import deprecated


@deprecated('difflib._format_range_unified')
def format_range_unified(start, stop):
    """
    Convert range to the "ed" format.

    DEPRECATED (Python 2.6 backport).
    Use difflib._format_range_unified instead.
    """
    return _format_range_unified(start, stop)


# Logging/Warnings integration

_warnings_showwarning = None


@deprecated('logging.NullHandler')
class NullHandler(logging.NullHandler):

    """This handler does nothing."""

    pass


@deprecated('logging._showwarning')
def _showwarning(*args, **kwargs):
    """
    Implementation of showwarnings which redirects to logging.

    DEPRECATED (Python 2.6 backport).
    Use logging._showwarning instead.
    """
    logging._showwarning(*args, **kwargs)


@deprecated('logging.captureWarnings')
def captureWarnings(capture):
    """
    Capture warnings into logging.

    DEPRECATED (Python 2.6 backport).
    Use logging.captureWarnings instead.
    """
    logging.captureWarnings(capture)


_warnings_showwarning = logging._warnings_showwarning
