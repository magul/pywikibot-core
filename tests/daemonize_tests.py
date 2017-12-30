# -*- coding: utf-8 -*-
"""Tests for BasePage subclasses."""

from __future__ import absolute_import, unicode_literals

import os
import unitest

from pywikibot import daemonize


def test_daemonize_os_exit():
    os.fork()
    os.fork()
    daemonize.daemonize()
    daemonize.daemonize()


def test_daemonize_closedstream_true():
    daemonize.daemonize(True, True, False, None)


def test_daemonize_closedstream_false():
    daemonize.daemonize(False, True, False, None)


def test_daemonize_changedirectory_true():
    daemonize.daemonize(True, True, False, None)


def test_daemonize_changeddirectory_false():
    daemonize.daemonize(True, False, False, None)


def test_redirectstd_true():
    daemonize.daemonize(True, True, False, 'Test')


def test_daemonize_writepid_True():
    os.fork()
    # cannot be tested because spaghetti code


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
