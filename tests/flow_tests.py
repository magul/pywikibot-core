# -*- coding: utf-8 -*-
"""Tests for the flow module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot.exceptions import NoPage
from pywikibot.flow import Board, Topic, Post
from pywikibot.tools import UnicodeType as unicode

from tests.aspects import (
    TestCase,
)
from tests.basepage_tests import (
    BasePageMethodsTestBase,
    BasePageLoadRevisionsCachingTestBase,
)

# variables to check regex used in assertRaisesRegex

illegal_post_data_error = 'Illegal post data.*'
topic_must_exist_error = 'Topic must exist:.*'
cur_post_rev = 'Current revision of postnot found in supplied data.*'
pywiki_flow_object_error = 'board must be a pywikibot.flow.Board object.'
topic_uuid_string_error = 'Topic/root UUID must be a string.'
page_topic_object_error = 'Page must be a Topic object'
post_uuid_string_error = 'Post UUID must be a string'
post_not_found_error = 'Post not found in supplied data.*'


class TestMediaWikiFlowSandbox(TestCase):

    """Test the Flow sandbox on MediaWiki.org."""

    family = 'mediawiki'
    code = 'mediawiki'

    def setUp(self):
        """Set up unit test."""
        self._page = Board(self.site,
                           'Project talk:Sandbox/Structured_Discussions_test')
        super(TestMediaWikiFlowSandbox, self).setUp()


class TestBoardBasePageMethods(BasePageMethodsTestBase,
                               TestMediaWikiFlowSandbox):

    """Test Flow board pages using BasePage-defined methods."""

    def test_basepage_methods(self):
        """Test basic Page methods on a Flow board page."""
        self._test_invoke()
        self._test_return_datatypes()
        self.assertFalse(self._page.isRedirectPage())

    def test_content_model(self):
        """Test Flow page content model."""
        self.assertEqual(self._page.content_model, 'flow-board')


class TestTopicBasePageMethods(BasePageMethodsTestBase):

    """Test Flow topic pages using BasePage-defined methods."""

    family = 'mediawiki'
    code = 'mediawiki'

    def setUp(self):
        """Set up unit test."""
        self._page = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        super(TestTopicBasePageMethods, self).setUp()

    def test_basepage_methods(self):
        """Test basic Page methods on a Flow topic page."""
        self._test_invoke()
        self._test_return_datatypes()
        self.assertFalse(self._page.isRedirectPage())
        self.assertEqual(self._page.latest_revision.parent_id, 0)

    def test_content_model(self):
        """Test Flow topic page content model."""
        self.assertEqual(self._page.content_model, 'flow-board')


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                               TestMediaWikiFlowSandbox):

    """Test site.loadrevisions() caching."""

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self.skipTest('See T107537')
        self._test_page_text()


class TestFlowLoading(TestMediaWikiFlowSandbox):

    """Test loading of Flow objects from the API."""

    cached = True

    def test_board_uuid(self):
        """Test retrieval of Flow board UUID."""
        board = self._page
        self.assertEqual(board.uuid, 'rl7iby6wgksbpfno')

    def test_topic_uuid(self):
        """Test retrieval of Flow topic UUID."""
        topic = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        self.assertEqual(topic.uuid, 'sh6wgo5tu3qui1w2')

    def test_post_uuid(self):
        """Test retrieval of Flow post UUID.

        This doesn't really "load" anything from the API. It just tests
        the property to make sure the UUID passed to the constructor is
        stored properly.
        """
        topic = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        post = Post(topic, 'sh6wgoagna97q0ia')
        self.assertEqual(post.uuid, 'sh6wgoagna97q0ia')

    def test_post_contents(self):
        """Test retrieval of Flow post contents."""
        # Load
        topic = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        post = Post(topic, 'sh6wgoagna97q0ia')
        # Wikitext
        wikitext = post.get(format='wikitext')
        self.assertIn('wikitext', post._content)
        self.assertNotIn('html', post._content)
        self.assertIsInstance(wikitext, unicode)
        self.assertNotEqual(wikitext, '')
        # HTML
        html = post.get(format='html')
        self.assertIn('html', post._content)
        self.assertIn('wikitext', post._content)
        self.assertIsInstance(html, unicode)
        self.assertNotEqual(html, '')
        # Caching (hit)
        post._content['html'] = 'something'
        html = post.get(format='html')
        self.assertIsInstance(html, unicode)
        self.assertEqual(html, 'something')
        self.assertIn('html', post._content)
        # Caching (reload)
        post._content['html'] = 'something'
        html = post.get(format='html', force=True)
        self.assertIsInstance(html, unicode)
        self.assertNotEqual(html, 'something')
        self.assertIn('html', post._content)

    def test_topiclist(self):
        """Test loading of topiclist."""
        board = self._page
        i = 0
        for topic in board.topics(limit=7):
            i += 1
            if i == 10:
                break
        self.assertEqual(i, 10)


class TestFlowFactoryErrors(TestCase):

    """Test errors associated with class methods generating Flow objects."""

    family = 'test'
    code = 'test'

    cached = True

    def test_illegal_arguments(self):
        """Test illegal method arguments."""
        board = Board(self.site, 'Talk:Pywikibot test')
        real_topic = Topic(self.site, 'Topic:Slbktgav46omarsd')
        fake_topic = Topic(self.site, 'Topic:Abcdefgh12345678')
        # Topic.from_topiclist_data
        self.assertRaisesRegex(TypeError,
                               pywiki_flow_object_error,
                               Topic.from_topiclist_data, self.site, '', {})
        self.assertRaisesRegex(TypeError,
                               topic_uuid_string_error,
                               Topic.from_topiclist_data, board, 521, {})
        self.assertRaisesRegex(TypeError,
                               illegal_post_data_error,
                               Topic.from_topiclist_data, board,
                          'slbktgav46omarsd', [0, 1, 2])
        self.assertRaisesRegex(NoPage,
                               topic_must_exist_error,
                               Topic.from_topiclist_data, board,
                          'abc', {'stuff': 'blah'})

        # Post.fromJSON
        self.assertRaisesRegex(TypeError,
                               page_topic_object_error,
                               Post.fromJSON, board, 'abc', {})
        self.assertRaisesRegex(TypeError,
                               post_uuid_string_error,
                               Post.fromJSON, real_topic, 1234, {})
        self.assertRaisesRegex(TypeError,
                               illegal_post_data_error,
                               Post.fromJSON, real_topic, 'abc', [])
        self.assertRaisesRegex(NoPage,
                               topic_must_exist_error,
                               Post.fromJSON, fake_topic, 'abc',
                          {'posts': [], 'revisions': []})

    def test_invalid_data(self):
        """Test invalid "API" data."""
        board = Board(self.site, 'Talk:Pywikibot test')
        real_topic = Topic(self.site, 'Topic:Slbktgav46omarsd')
        # Topic.from_topiclist_data
        self.assertRaisesRegex(ValueError,
                               illegal_post_data_error, Topic.from_topiclist_data,
                          board, 'slbktgav46omarsd', {'stuff': 'blah'})
        self.assertRaisesRegex(ValueError,
                               post_not_found_error, Topic.from_topiclist_data,
                          board, 'slbktgav46omarsd',
                          {'posts': [], 'revisions': []})
        self.assertRaisesRegex(ValueError,
                               cur_post_rev,
                               Topic.from_topiclist_data, board,
                          'slbktgav46omarsd',
                          {'posts': {'slbktgav46omarsd': ['123']},
                           'revisions': {'456': []}})
        self.assertRaisesRegex(AssertionError,
                               '', Topic.from_topiclist_data, board,
                          'slbktgav46omarsd',
                          {'posts': {'slbktgav46omarsd': ['123']},
                           'revisions': {'123': {'content': 789}}})

        # Post.fromJSON
        self.assertRaisesRegex(ValueError,
                               illegal_post_data_error,
                               Post.fromJSON, real_topic, 'abc', {})
        self.assertRaisesRegex(ValueError,
                               illegal_post_data_error,
                               Post.fromJSON, real_topic, 'abc',
                          {'stuff': 'blah'})
        self.assertRaisesRegex(ValueError,
                               cur_post_rev,
                               Post.fromJSON, real_topic, 'abc',
                          {'posts': {'abc': ['123']},
                           'revisions': {'456': []}})
        self.assertRaisesRegex(AssertionError,
                               '', Post.fromJSON, real_topic, 'abc',
                          {'posts': {'abc': ['123']},
                           'revisions': {'123': {'content': 789}}})
