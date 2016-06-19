# -*- coding: utf-8 -*-
"""Test suite for the flow based thanks script."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import itertools

from pywikibot.exceptions import UnknownSite

from pywikibot.flow import Board

from scripts.maintenance.flow_thanks import thank_flow_post

from tests.aspects import unittest, TestCase


class TestFlowThank(TestCase):

    """Test thanks for revisions."""

    family = 'test'
    code = 'test'

    def test_topic(self):
        """
        Test thanks for a Flow post.

        NOTE:   This approach requires a NEW topic and flow post on the
                Talk:Sandbox page between reruns, and will fail otherwise.
        """
        site = self.get_site()
        found_newlog = found_lastlog = False
        # Getting 'Talk:Sandbox' flow page on test:test, and a
        # a generator for topics on that page.
        # NOTE: Slicing has been used to deal with the bugs in Board.topics.
        #       Please see T138323, T138215, T138307, T138306.
        # TODO: Resolve the above, and update approach of testing here.
        page = Board(self.site, 'Talk:Sandbox')
        topics_list = page.topics()
        topics_list = itertools.islice(topics_list, 1)
        for topic in topics_list:
            post_list = topic.replies()
            for post in post_list:
                post_to_thank = post.uuid
                break
        log_initial = site.logevents(logtype='thanks', total=1)
        try:
            for x in log_initial:
                initial_timestamp = x.timestamp()
                initial_user = x.user()
        except Exception:
            raise AttributeError('Thanks log entries cannot be retrieved.')
        thank_flow_post(site, post_to_thank)
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

    def test_invalid_postds(self):
        """Test thanks script when postid is invalid."""
        site = self.get_site()
        self.assertRaises(TypeError, thank_flow_post, site, 1234)
        self.assertRaises(TypeError, thank_flow_post, site, [])
        self.assertRaises(ValueError, thank_flow_post, site, '')
        self.assertRaises(ValueError, thank_flow_post, site, 'foobarfoobarfoobar')

    def test_invalid_site(self):
        """Test thanks script when site is invalid."""
        invalid_site = "foobar"
        self.assertRaises(UnknownSite, thank_flow_post, invalid_site, 't6g7llvv2hrzewrl')


if __name__ == "__main__":
    unittest.main()
