# -*- coding: utf-8  -*-
"""Operating System tools."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import errno
import tempfile


def is_writable(path):
    """Check a path is writable."""
    try:
        test_file = tempfile.TemporaryFile(dir=path)
        test_file.close()
    except OSError as e:
        if e.errno == errno.EACCES:
            return False
        e.filename = path
        raise
    return True
