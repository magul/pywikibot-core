# -*- coding: utf-8  -*-
"""Enums used by pywikibot."""
#
# (C) Pywikibot team, 2012-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

from enum import IntEnum


class LoginStatus(IntEnum):

    """Enum for Login statuses.

    >>> LoginStatus.NOT_ATTEMPTED
    <LoginStatus.NOT_ATTEMPTED: -3>
    >>> LoginStatus.AS_USER
    <LoginStatus.AS_USER: 0>
    >>> LoginStatus.NOT_ATTEMPTED.name
    'NOT_ATTEMPTED'
    >>> LoginStatus.AS_USER.name
    'AS_USER'
    """

    NOT_ATTEMPTED = -3
    IN_PROGRESS = -2
    NOT_LOGGED_IN = -1
    AS_USER = 0
    AS_SYSOP = 1

    @staticmethod
    def _parse_repr(value):
        """
        Parse repr from login status repr at beginning of value.

        value may contain other text after the repr.

        @param value: text containing repr.
        @type value: str
        @return: LoginStatus and the matched part of value
        @rtype: tuple of LoginStatus, str
        @raises ValueError: Unable to parse LoginStatus
        @raises KeyError: Unknown enum name
        @raises RuntimeError: Unable to find 'LoginStatus' at beginning
        """
        name = None
        # The enum class repr
        if value.startswith('<LoginStatus.'):
            end = value.index(':', 13)
            if not end:
                raise ValueError('End of new LoginStatus not found: %s'
                                 % value)
            name = value[13:end]
            end = value.index('>', end)
            matched = value[:end + 1]
        # The fake repr before using the enum clas
        elif value.startswith('LoginStatus('):
            end = value.index(')', 12)
            if not end:
                raise ValueError('End of old LoginStatus not found: %s'
                                 % value)
            name = value[12:end]
            matched = value[:end + 1]
        else:
            raise RuntimeError(
                'Value {0} is not a LoginStatus repr'.format(value))

        return LoginStatus[name], matched


class BuiltinNamespace(IntEnum):

    """Builtin namespace enum."""

    MEDIA = -2
    SPECIAL = -1
    MAIN = 0
    TALK = 1
    USER = 2
    USER_TALK = 3
    PROJECT = 4
    PROJECT_TALK = 5
    FILE = 6
    FILE_TALK = 7
    MEDIAWIKI = 8
    MEDIAWIKI_TALK = 9
    TEMPLATE = 10
    TEMPLATE_TALK = 11
    HELP = 12
    HELP_TALK = 13
    CATEGORY = 14
    CATEGORY_TALK = 15
