# -*- coding: utf-8  -*-
"""
Tests for LoginManager classes.

e.g. used to test password-file based login.
"""
#
# (C) Pywikibot team, 2012-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
import mock

from pywikibot import config
from pywikibot.login import LoginManager

from tests.aspects import (
    unittest,
    DefaultDrySiteTestCase,
    TestCase,
)


class FakeFamily(object):
    """Mock."""

    name = "~FakeFamily"


class FakeSite(object):
    """Mock."""

    code = "~FakeCode"
    family = FakeFamily
    oauth = 'Some data'

FakeUsername = "~FakeUsername"


class FakeConfig(object):
    """Mock."""

    usernames = {
        FakeFamily.name: {
            FakeSite.code: FakeUsername
        }
    }


@mock.patch("pywikibot.Site", FakeSite)
@mock.patch("pywikibot.login.config", FakeConfig)
class TestOfflineLoginManager(DefaultDrySiteTestCase):
    """Test offline operation of login.LoginManager."""

    dry = True

    def test_default_init(self):
        """Test initialization of LoginManager without parameters."""
        obj = LoginManager()
        self.assertIsInstance(obj.site, FakeSite)
        self.assertEqual(obj.username, FakeUsername)
        self.assertEqual(obj.login_name, FakeUsername)
        self.assertIsNone(obj.password)


@mock.patch("pywikibot.Site", FakeSite)
class TestPasswordFile(DefaultDrySiteTestCase):
    """Test parsing password files."""

    def patch(self, name):
        """Patch up <name> in self.setUp."""
        patcher = mock.patch(name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _file_lines(self, lines=[]):
        for line in lines:
            yield line

    def setUp(self):
        """Patch a variety of dependencies."""
        super(TestPasswordFile, self).setUp()
        self.config = self.patch("pywikibot.login.config")
        self.config.usernames = FakeConfig.usernames
        self.config.password_file = "~FakeFile"
        self.config.private_files_permission = 0o600
        self.config.base_dir = ""  # ensure that no path modifies password_file

        self.stat = self.patch("os.stat")
        self.stat.return_value.st_mode = 0o100600

        self.chmod = self.patch("os.chmod")

        self.open = self.patch("codecs.open")
        self.open.return_value = self._file_lines()

    def test_auto_chmod_OK(self):
        """Do not chmod files that have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100600
        LoginManager()
        self.stat.assert_called_with(self.config.password_file)
        self.assertFalse(self.chmod.called)

    def test_auto_chmod_not_OK(self):
        """Chmod files that do not have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100644
        LoginManager()
        self.stat.assert_called_with(self.config.password_file)
        self.chmod.assert_called_once_with(
            self.config.password_file,
            0o600
        )

    def _test_pwfile(self, contents, password):
        self.open.return_value = self._file_lines(contents.split("\n"))
        obj = LoginManager()
        self.assertEqual(obj.password, password)
        return obj

    def test_none_matching(self):
        """No matching passwords."""
        self._test_pwfile("""
            ('NotTheUsername', 'NotThePassword')
            """, None)

    def test_match_global_username(self):
        """Test global username/password declaration."""
        self._test_pwfile("""
            ('~FakeUsername', '~FakePassword')
            """, "~FakePassword")

    def test_match_family_username(self):
        """Test matching by family."""
        self._test_pwfile("""
            ('~FakeFamily', '~FakeUsername', '~FakePassword')
            """, "~FakePassword")

    def test_match_code_username(self):
        """Test matching by full configuration."""
        self._test_pwfile("""
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePassword')
            """, "~FakePassword")

    def test_ordering(self):
        """Test that the last matching password is selected."""
        self._test_pwfile("""
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePasswordA')
            ('~FakeUsername', '~FakePasswordB')
            """, "~FakePasswordB")

        self._test_pwfile("""
            ('~FakeUsername', '~FakePasswordA')
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePasswordB')
            """, "~FakePasswordB")

    def test_BotPassword(self):
        """Test BotPassword entries.

        When a BotPassword is used, the login_name changes to contain a suffix,
        while the password is read from an object (instead of being read from
        the password file directly).
        """
        obj = self._test_pwfile("""
            ('~FakeUsername', BotPassword('~FakeSuffix', '~FakePassword'))
            """, '~FakePassword')
        self.assertEqual(obj.login_name, "~FakeUsername@~FakeSuffix")


class TestGetAuthenticationConfig(TestCase):
    # TODO: move in config2.tests

    """Test pywikibot.get_authentication."""

    net = False

    def setUp(self):
        """Set up test by configuring config.authenticate."""
        self._authenticate = config.authenticate
        config.authenticate = {
            'zh.wikipedia.beta.wmflabs.org': ('1', '2'),
            '*.wikipedia.beta.wmflabs.org': ('3', '4', '3', '4'),
            '*.beta.wmflabs.org': ('5', '6'),
            '*.wmflabs.org': ('7', '8', '8'),
        }

    def tearDown(self):
        """Tear down test by resetting config.authenticate."""
        config.authenticate = self._authenticate

    def test_url_based_authentication(self):
        """Test url-based authentication info."""
        pairs = {
            'https://zh.wikipedia.beta.wmflabs.org': ('1', '2'),
            'https://en.wikipedia.beta.wmflabs.org': ('3', '4', '3', '4'),
            'https://wiki.beta.wmflabs.org': ('5', '6'),
            'https://beta.wmflabs.org': None,
            'https://wmflabs.org': None,
            'https://www.wikiquote.org/': None,
        }
        for url, auth in pairs.items():
            self.assertEqual(config.get_authentication(url), auth)

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
