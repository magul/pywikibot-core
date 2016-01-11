# -*- coding: utf-8 -*-
"""
This module contains backports to support older Python versions.

They contain the backported code originally developed for Python. It is
therefore distributed under the PSF license.
"""
#
# (C) Python Software Foundation, 2001-2014
# (C) with modifications from Pywikibot team, 2015-2017
#
# Distributed under the terms of the PSF license.
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
