import pywikibot
from pywikibot import daemonize
import os

class TestCase1:
   def test_daemonize_os_exit():
      os.fork()
      daemonize.daemonize()
   def test_daemonize_closedstream_true():
      daemonize.daemonize(True, True, False, None)

   def test_daemonize_closedstream_false():
      daemonize.daemonize(False, True, False, None)

   def test_daemonize_changedirectory_true():
      daemonize.daemonize(True, True, False, None)

   def test_daemonize_changeddirectory_false():
      daemonize.daemonize(True, False, False, None)

   def test_daemonize_writepid_True():
      os.fork()

def load_tests(loader, tests, pattern):
   TestCase1.test_daemonize_os_exit()
   TestCase1.test_daemonize_closedstream_true()
   TestCase1.test_daemonize_closedstream_false()
   TestCase1.test_daemonize_changedirectory_true()
   TestCase1.test_daemonize_changeddirectory_false()
TestCase1.test_daemonize_writepid_True()
