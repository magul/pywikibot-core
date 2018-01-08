# -*- coding: utf-8 -*-
"""
Platform independent terminal interface module.

It imports the appropriate operating system specific implementation.
"""
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import sys

if sys.platform == 'win32':
    from pywikibot.userinterfaces.terminal_interface_win32 import Win32UI as UI
else:
    from pywikibot.userinterfaces.terminal_interface_unix import UnixUI as UI

__all__ = ('UI',)
