# -*- coding: utf-8 -*-
"""Tests for the User page."""
#
# (C) Pywikibot team, 2016-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot import Page, Timestamp, User
from pywikibot.tools import StringTypes

from tests.aspects import DefaultSiteTestCase, TestCase, unittest


class TestUserClass(TestCase):

    """Test User class."""

    family = 'wikipedia'
    code = 'de'

    def test_registered_user(self):
        """Test registered user."""
        user = User(self.site, 'Xqt')
        self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsInstance(user.registration(), pywikibot.Timestamp)
        self.assertGreater(user.editCount(), 0)
        self.assertFalse(user.isBlocked())
        self.assertTrue(user.isEmailable())
        self.assertIn('userid', user.getprops())

    def test_registered_user_without_timestamp(self):
        """Test registered user when registration timestamp is None."""
        user = User(self.site, 'Ulfb')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertIsNone(user.getprops()['registration'])
        self.assertGreater(user.editCount(), 0)
        self.assertIn('userid', user.getprops())

    def test_anonymous_user(self):
        """Test registered user."""
        user = User(self.site, '123.45.67.89')
        self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertTrue(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertIn('invalid', user.getprops())

    def test_unregistered_user(self):
        """Test unregistered user."""
        user = User(self.site, 'This user name is not registered yet')
        self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertIn('missing', user.getprops())

    def test_invalid_user(self):
        """Test invalid user."""
        user = User(self.site, 'Invalid char\x9f in Name')
        self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertIn('invalid', user.getprops())


class TestUserMethods(DefaultSiteTestCase):

    """Test User methods with bot user."""

    user = True

    def test_contribution(self):
        """Test the User.usercontribs() method."""
        mysite = self.get_site()
        user = User(mysite, mysite.user())
        uc = list(user.contributions(total=10))
        self.assertLessEqual(len(uc), 10)
        last = uc[0]
        for contrib in uc:
            self.assertIsInstance(contrib, tuple)
            self.assertEqual(len(contrib), 4)
            p, i, t, c = contrib
            self.assertIsInstance(p, Page)
            self.assertIsInstance(i, int)
            self.assertIsInstance(t, Timestamp)
            self.assertIsInstance(c, StringTypes)
        self.assertEqual(last, user.last_edit)

    def test_logevents(self):
        """Test the User.logevents() method."""
        mysite = self.get_site()
        user = User(mysite, mysite.user())
        le = list(user.logevents(total=10))
        self.assertLessEqual(len(le), 10)
        last = le[0]
        self.assertTrue(all(event.user() == user.username for event in le))
        self.assertEqual(last, user.last_event)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
