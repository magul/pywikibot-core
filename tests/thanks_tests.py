# -*- coding: utf-8 -*-
"""Test suite for the thanks script."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from tests.aspects import unittest, TestCase


def thank_rev(site, rev_id, source='pywikibot'):
    """Temporary high-level function for thanking.

    @param site: A Site object.
    @type site: Site
    @param rev_id: The ID of the revision to thank.
    @type rev_id: int
    @param source: An optional source argument to pass to the API.
    @type source: str
    """
    site.thank_revision(rev_id, source)


class TestThankRevision(TestCase):

    """Test thanks for revisions."""

    family = 'test'
    code = 'test'

    def test_thank_revision(self):
        """Test thanks for normal revisions.

        NOTE: This test relies on activity in recentchanges, and
              there must make edits made before reruns of this test.
              Please see https://phabricator.wikimedia.org/T137836.
        """
        found_newlog = found_lastlog = can_thank = False
        site = self.get_site()
        data = site.recentchanges(total=20)
        for i in data:
            revid = i['revid']
            props = site.get_revision(revid)
            page_info = (props['query']['pages']).values()
            revision = page_info[0].get('revisions')
            username = revision[0].get('user')
            user = pywikibot.User(site, username)
            if user.thanks_enabled:
                can_thank = True
                break
        if not can_thank:
            raise unittest.SkipTest('There is no recent change which can be'
                                    'test thanked.')
        log_initial = site.logevents(logtype='thanks', total=1)
        try:
            for x in log_initial:
                initial_timestamp = x.timestamp()
                initial_user = x.user()
        except Exception:
            raise AttributeError('Thanks log entries cannot be retrieved.')
        thank_rev(site, revid, source='pywikibot')
        log_final = site.logevents(logtype='thanks', total=50)
        try:
            for x in log_final:
                if x.timestamp() > initial_timestamp:
                    found_newlog = True
                if found_newlog and x.timestamp() == initial_timestamp and \
                   x.user() == initial_user:
                    found_lastlog = True
                    break
        except Exception:
            raise AttributeError('Thanks log entries cannot be retrieved.')
        self.assertTrue(found_lastlog)


if __name__ == "__main__":
    unittest.main()
