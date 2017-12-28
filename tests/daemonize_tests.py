from __future__ import absolute_import, unicode_literals

from pywikibot import daemonize

import os

def test_daemonize_os_exit():
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
    #cannot be tested because spaghetti code

def load_tests(loader, tests, pattern):
    test_daemonize_os_exit()
    test_daemonize_closedstream_true()
    test_daemonize_closedstream_false()
    test_daemonize_changedirectory_true()
    test_daemonize_changeddirectory_false()
    test_daemonize_writepid_True()
    test_redirectstd_true()
