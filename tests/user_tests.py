# -*- coding: utf-8 -*-
"""Tests for the User page."""
#
# (C) Pywikibot team, 2016-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot import Page, Timestamp, User
from pywikibot.tools import StringTypes, suppress_warnings

from tests.aspects import DefaultSiteTestCase, TestCase, unittest


class TestUserClass(TestCase):

    """Test User class."""

    family = 'wikipedia'
    code = 'de'

    def test_registered_user(self):
        """Test registered user."""
        user = User(self.site, 'Xqt')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsInstance(user.registration(), pywikibot.Timestamp)
        self.assertGreater(user.editCount(), 0)
        self.assertFalse(user.isBlocked())
        self.assertTrue(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('userid', user.getprops())
        self.assertEqual(user.getprops()['userid'], 287832)
        self.assertEqual(user.pageid, 6927779)
        self.assertEqual(user.getUserPage(),
                         pywikibot.Page(self.site, 'Benutzer:Xqt'))
        self.assertEqual(user.getUserPage(subpage='pwb'),
                         pywikibot.Page(self.site, 'Benutzer:Xqt/pwb'))
        self.assertEqual(user.getUserTalkPage(),
                         pywikibot.Page(self.site, 'Benutzer Diskussion:Xqt'))
        self.assertEqual(user.getUserTalkPage(subpage='pwb'),
                         pywikibot.Page(self.site,
                                        'Benutzer Diskussion:Xqt/pwb'))
        self.assertTrue(user.is_thankable)
        contribs = user.contributions(total=10)
        self.assertEqual(len(list(contribs)), 10)
        self.assertTrue(all(isinstance(contrib, tuple)
                            for contrib in contribs))
        self.assertTrue(all('user' in contrib
                            and contrib['user'] == user.username
                            for contrib in contribs))
        self.assertIn('user', user.groups())
        self.assertIn('edit', user.rights())

    def test_registered_user_without_timestamp(self):
        """Test registered user when registration timestamp is None."""
        user = User(self.site, 'Ulfb')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertIsNone(user.getprops()['registration'])
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'male')
        self.assertIn('userid', user.getprops())
        self.assertTrue(user.is_thankable)

    def test_female_user(self):
        """Test female user."""
        user = User(self.site, 'Alraunenstern')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'female')
        self.assertIn('userid', user.getprops())
        self.assertTrue(user.is_thankable)

    def test_anonymous_user(self):
        """Test registered user."""
        user = User(self.site, '123.45.67.89')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertTrue(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('invalid', user.getprops())
        self.assertFalse(user.is_thankable)

    def test_unregistered_user(self):
        """Test unregistered user."""
        user = User(self.site, 'This user name is not registered yet')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('missing', user.getprops())
        self.assertFalse(user.is_thankable)

    def test_invalid_user(self):
        """Test invalid user."""
        user = User(self.site, 'Invalid char\x9f in Name')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('invalid', user.getprops())
        self.assertFalse(user.is_thankable)


class TestUserMethods(DefaultSiteTestCase):

    """Test User methods with bot user."""

    user = True

    def test_contribution(self):
        """Test the User.usercontribs() method."""
        mysite = self.get_site()
        user = User(mysite, mysite.user())
        uc = list(user.contributions(total=10))
        if not uc:
            self.skipTest('User {0} has no contributions on site {1}.'
                          .format(mysite.user(), mysite))
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
        if not le:
            self.skipTest('User {0} has no logevents on site {1}.'
                          .format(mysite.user(), mysite))
        self.assertLessEqual(len(le), 10)
        last = le[0]
        self.assertTrue(all(event.user() == user.username for event in le))
        self.assertEqual(last, user.last_event)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
