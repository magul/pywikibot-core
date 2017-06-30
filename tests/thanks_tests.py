# -*- coding: utf-8 -*-
"""Tests for thanks-related code."""
#
# (C) Pywikibot team, 2016-17
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot.flow import Topic
from pywikibot.page import Page, Revision, User

from tests.aspects import TestCase


NO_THANKABLE_REVS = 'There is no recent change which can be test thanked.'
NO_THANKABLE_POSTS = 'There is no recent post which can be test thanked.'


class TestThankRevision(TestCase):

    """Test thanks for revisions."""

    family = 'test'
    code = 'test'

    write = True

    def test_thank_revision(self):
        """Test thanks for normal revisions.

        NOTE: This test relies on activity in recentchanges, and
              there must make edits made before reruns of this test.
              Please see https://phabricator.wikimedia.org/T137836.
        """
        found_log = False
        site = self.get_site()
        data = site.recentchanges(total=20)
        for rev in data:
            revid = rev['revid']
            username = rev['user']
            user = User(site, username)
            if user.is_thankable:
                break
        else:
            self.skipTest(NO_THANKABLE_REVS)
        before_time = site.getcurrenttimestamp()
        Revision._thank(revid, site, source='pywikibot test')
        log_entries = site.logevents(logtype='thanks', total=5, page=user,
                                     start=before_time, reverse=True)
        for __ in log_entries:
            found_log = True
            break
        self.assertTrue(found_log)

    def test_self_thank(self):
        """Test that thanking oneself causes an error.

        This test is not in TestThankRevisionErrors because it may require
        making a successful edit in order to test the API call thanking the user
        running the test.
        """
        site = self.get_site()
        my_name = self.get_userpage().username
        data = site.usercontribs(user=my_name, total=1)
        for rev in data:
            revid = rev['revid']
            break
        else:
            test_page = Page(site, 'Pywikibot Thanks test')
            test_page.text += '* ~~~~\n'
            test_page.save('Pywikibot Thanks test')
            revid = test_page.latest_revision_id
        self.assertAPIError('invalidrecipient', None, Revision._thank,
                            revid, site, source='pywikibot test')


class TestThankRevisionErrors(TestCase):

    """Test errors when thanking revisions."""

    family = 'test'
    code = 'test'

    write = -1

    def test_bad_recipient(self):
        """Test that thanking a bad recipient causes an error."""
        site = self.get_site()
        data = site.recentchanges(total=20)
        for rev in data:
            revid = rev['revid']
            username = rev['user']
            user = User(site, username)
            if not user.is_thankable:
                break
        else:
            self.skipTest(NO_THANKABLE_REVS)
        self.assertAPIError('invalidrecipient', None, Revision._thank,
                            revid, site, source='pywikibot test')

    def test_invalid_revision(self):
        """Test that passing an invalid revision ID causes an error."""
        site = self.get_site()
        invalid_revids = (0, -1, 0.99, 'zero, minus one, and point nine nine',
                          (0, -1, 0.99), [0, -1, 0.99])
        for invalid_revid in invalid_revids:
            self.assertAPIError('invalidrevision', None, Revision._thank,
                                invalid_revid, site, source='pywikibot test')


class TestThankFlowPost(TestCase):

    """Test thanks for Flow posts."""

    family = 'test'
    code = 'test'

    write = True

    def test_thank_post(self):
        """Test thanks for Flow posts."""
        self.skipTest('Users not yet found in Post.')
        found_log = False
        site = self.get_site()
        data = site.randompages(namespaces='Topic', total=20)
        for page in data:
            topic = Topic(page)
            post = topic.root
            # user = User(site, post.creator)
            # if user.is_thankable:
            if True:
                break
        else:
            self.skipTest(NO_THANKABLE_REVS)
        before_time = site.getcurrenttimestamp()
        post.thank()
        log_entries = site.logevents(logtype='thanks', total=5, # page=user,
                                     start=before_time, reverse=True)
        for __ in log_entries:
            found_log = True
            break
        self.assertTrue(found_log)

    def test_self_thank(self):
        """Test that thanking one's own Flow post causes an error."""
        self.skipTest('Users not yet found in Post.')
        site = self.get_site()
        my_name = self.get_userpage().username
        data = site.usercontribs(user=my_name, total=1)
        for rev in data:
            revid = rev['revid']
            break
        else:
            test_page = Page(site, 'Pywikibot Thanks test')
            test_page.text += '* ~~~~\n'
            test_page.save('Pywikibot Thanks test')
            revid = test_page.latest_revision_id
        self.assertAPIError('invalidrecipient', None, Revision._thank,
                            revid, site, source='pywikibot test')
