# -*- coding: utf-8 -*-
"""Objects representing Flow entities, like boards, topics, and posts."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import logging

from pywikibot.exceptions import NoPage, UnknownExtension, LockedPage
from pywikibot.page import BasePage, User
from pywikibot.tools import PY2, ComparableMixin

if not PY2:
    unicode = str
    basestring = (str,)
    from urllib.parse import urlparse, parse_qs
else:
    from urlparse import urlparse, parse_qs


logger = logging.getLogger('pywiki.wiki.flow')


# Flow page-like objects (boards and topics)
class FlowPage(BasePage):

    """
    The base page for the Flow extension.

    There should be no need to instantiate this directly.

    Subclasses must provide a _load() method to load and cache
    the object's internal data from the API.
    """

    def __init__(self, source, title=''):
        """Constructor.

        @param source: A Flow-enabled site or a Link or Page on such a site
        @type source: Site, Link, or Page
        @param title: normalized title of the page
        @type title: unicode

        @raises TypeError: incorrect use of parameters
        @raises ValueError: use of non-Flow-enabled Site
        """
        super(FlowPage, self).__init__(source, title)

        if not self.site.has_extension('Flow'):
            raise UnknownExtension('site is not Flow-enabled')

    def _load_uuid(self):
        """Load and save the UUID of the page."""
        self._uuid = self._load()['workflowId']

    @property
    def uuid(self):
        """Return the UUID of the page.

        @return: UUID of the page
        @rtype: unicode
        """
        if not hasattr(self, '_uuid'):
            self._load_uuid()
        return self._uuid

    def get(self, force=False, get_redirect=False, sysop=False):
        """Get the page's content."""
        if get_redirect or force or sysop:
            raise NotImplementedError

        # TODO: Return more useful data
        return self._data


class Board(FlowPage):

    """A Flow discussion board."""

    def _load(self, force=False):
        """Load and cache the Board's data, derived from its topic list."""
        if not hasattr(self, '_data') or force:
            self._data = self.site.load_board(self)
        return self._data

    def _parse_url(self, links):
        """Parse a URL retrieved from the API."""
        rule = links['fwd']
        parsed_url = urlparse(rule['url'])
        params = parse_qs(parsed_url.query)
        new_params = {}
        for key, value in params.items():
            if key != 'title':
                key = key.replace('topiclist_', '').replace('-', '_')
                if key == 'offset_dir':
                    new_params['reverse'] = (value == 'rev')
                else:
                    new_params[key] = value
        return new_params

    def topics(self, format='wikitext', limit=100, sort_by='newest',
               offset=None, offset_uuid='', reverse=False,
               include_offset=False, toc_only=False):
        """Load this board's topics.

        @param format: The content format to request the data in.
        @type format: str (either 'wikitext', 'html', or 'fixed-html')
        @param limit: The number of topics to fetch in each request.
        @type limit: int
        @param sort_by: Algorithm to sort topics by.
        @type sort_by: str (either 'newest' or 'updated')
        @param offset: The timestamp to start at (when sortby is 'updated').
        @type offset: Timestamp or equivalent str
        @param offset_uuid: The UUID to start at (when sortby is 'newest').
        @type offset_uuid: str (in the form of a UUID)
        @param reverse: Whether to reverse the topic ordering.
        @type reverse: bool
        @param include_offset: Whether to include the offset topic.
        @type include_offset: bool
        @param toc_only: Whether to only include information for the TOC.
        @type toc_only: bool
        @return: A generator of this board's topics.
        @rtype: generator of Topic objects
        """
        data = self.site.load_topiclist(self, format=format, limit=limit,
                                        sortby=sort_by, toconly=toc_only,
                                        offset=offset, offset_id=offset_uuid,
                                        reverse=reverse,
                                        include_offset=include_offset)
        while data['roots']:
            for root in data['roots']:
                topic = Topic.from_topiclist_data(self, root, data)
                yield topic
            cont_args = self._parse_url(data['links']['pagination'])
            data = self.site.load_topiclist(self, **cont_args)

    def new_topic(self, title, content, format='wikitext'):
        """Create and return a Topic object for a new topic on this Board.

        @param title: The title of the new topic (must be in plaintext)
        @type title: unicode
        @param content: The content of the topic's initial post
        @type content: unicode
        @param format: The content format of the value supplied for content
        @type format: unicode (either 'wikitext' or 'html')
        @return: The new topic
        @rtype: Topic
        """
        return Topic.create_topic(self, title, content, format)


class Topic(FlowPage):

    """A Flow discussion topic."""

    def _load(self, format='wikitext', force=False):
        """Load and cache the Topic's data."""
        if not hasattr(self, '_data') or force:
            self._data = self.site.load_topic(self, format)
        return self._data

    def _reload(self, new_revision=False):
        """Forcibly reload the topic's root post."""
        self.root._load(load_from_topic=True, new_revision=new_revision)

    @classmethod
    def create_topic(cls, board, title, content, format='wikitext'):
        """Create and return a Topic object for a new topic on a Board.

        @param board: The topic's parent board
        @type board: Board
        @param title: The title of the new topic (must be in plaintext)
        @type title: unicode
        @param content: The content of the topic's initial post
        @type content: unicode
        @param format: The content format of the value supplied for content
        @type format: unicode (either 'wikitext' or 'html')
        @return: The new topic
        @rtype: Topic
        """
        data = board.site.create_new_topic(board, title, content, format)
        return cls(board.site, data['topic-page'])

    @classmethod
    def from_topiclist_data(cls, board, root_uuid, topiclist_data):
        """Create a Topic object from API data.

        @param board: The topic's parent Flow board
        @type board: Board
        @param root_uuid: The UUID of the topic and its root post
        @type root_uuid: unicode
        @param topiclist_data: The data returned by view-topiclist
        @type topiclist_data: dict
        @return: A Topic object derived from the supplied data
        @rtype: Topic
        @raises TypeError: any passed parameters have wrong types
        @raises ValueError: the passed topiclist_data is missing required data
        """
        if not isinstance(board, Board):
            raise TypeError('board must be a pywikibot.flow.Board object.')
        if not isinstance(root_uuid, basestring):
            raise TypeError('Topic/root UUID must be a string.')

        topic = cls(board.site, 'Topic:' + root_uuid)
        topic._root = Post.fromJSON(topic, root_uuid, topiclist_data)
        topic._uuid = root_uuid
        return topic

    @property
    def root(self):
        """The root post of this topic."""
        if not hasattr(self, '_root'):
            self._root = Post.fromJSON(self, self.uuid, self._data)
        return self._root

    @property
    def is_locked(self):
        """Whether this topic is locked."""
        return self.root._data['isLocked']

    @property
    def is_moderated(self):
        """Whether this topic is moderated."""
        return self.root.is_moderated

    def flow_revisions(self, format='wikitext', force=False):
        """Return this topic's Flow revisions.

        @param format: Content format to return contents in
        @type format: str ('wikitext', 'html', or 'fixed-html')
        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @return: This topic's revisions
        @rtype: list of FlowRevisions
        """
        if format not in ('wikitext', 'html', 'fixed-html'):
            raise ValueError('Invalid content format.')

        if hasattr(self, '_flow_revisions') and not force:
            return self._flow_revisions

        revision_list = self.site.load_topic_history(self, format)

        self._flow_revisions = [FlowRevision.fromHistoryJSON(self, revision)
                                for revision in revision_list]

        return self._flow_revisions

    def replies(self, format='wikitext', force=False):
        """A list of replies to this topic's root post.

        @param format: Content format to return contents in
        @type format: str ('wikitext', 'html', or 'fixed-html')
        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @return: The replies of this topic's root post
        @rtype: list of Posts
        """
        return self.root.replies(format=format, force=force)

    def reply(self, content, format='wikitext'):
        """A convenience method to reply to this topic's root post.

        @param content: The content of the new post
        @type content: unicode
        @param format: The format of the given content
        @type format: str ('wikitext' or 'html')
        @return: The new reply to this topic's root post
        @rtype: Post
        """
        return self.root.reply(content, format)

    # Moderation
    def lock(self, reason):
        """Lock this topic.

        @param reason: The reason for locking this topic
        @type reason: unicode
        """
        self.site.lock_topic(self, True, reason)
        self._reload(new_revision=True)

    def unlock(self, reason):
        """Unlock this topic.

        @param reason: The reason for unlocking this topic
        @type reason: unicode
        """
        self.site.lock_topic(self, False, reason)
        self._reload(new_revision=True)

    def delete_mod(self, reason):
        """Delete this topic through the Flow moderation system.

        @param reason: The reason for deleting this topic.
        @type reason: unicode
        """
        self.site.delete_topic(self, reason)
        self._reload(new_revision=True)

    def hide(self, reason):
        """Hide this topic.

        @param reason: The reason for hiding this topic.
        @type reason: unicode
        """
        self.site.hide_topic(self, reason)
        self._reload(new_revision=True)

    def suppress(self, reason):
        """Suppress this topic.

        @param reason: The reason for suppressing this topic.
        @type reason: unicode
        """
        self.site.suppress_topic(self, reason)
        self._reload(new_revision=True)

    def restore(self, reason):
        """Restore this topic.

        @param reason: The reason for restoring this topic.
        @type reason: unicode
        """
        self.site.restore_topic(self, reason)
        self._reload(new_revision=True)


# Flow non-page-like objects
class FlowObject(ComparableMixin):

    """A non-Page Flow object."""

    def __init__(self, page, uuid):
        """Constructor.

        @param page: Flow topic
        @type page: Topic
        @param uuid: UUID of a Flow object
        @type uuid: unicode

        @raises TypeError: incorrect types of parameters
        @raises NoPage: topic does not exist
        """
        if not isinstance(page, Topic):
            raise TypeError('Page must be a Topic object')
        if not page.exists():
            raise NoPage(page, 'Topic must exist: %s')
        if not isinstance(uuid, basestring):
            raise TypeError('Flow object UUID must be a string')

        self._page = page
        self._uuid = uuid

    def _cmpkey(self):
        return (self.uuid)

    @property
    def uuid(self):
        """Return the UUID of the object.

        @return: UUID of the object
        @rtype: unicode
        """
        return self._uuid

    @property
    def site(self):
        """Return the site associated with the object.

        @return: Site associated with the object
        @rtype: Site
        """
        return self._page.site

    @property
    def page(self):
        """Return the page associated with the object.

        @return: Page associated with the object
        @rtype: FlowPage
        """
        return self._page


class Post(FlowObject):

    """A post to a Flow discussion topic."""

    @classmethod
    def fromJSON(cls, page, post_uuid, data):
        """
        Create a Post object using the data returned from the API call.

        @param page: A Flow topic
        @type page: Topic
        @param post_uuid: The UUID of the post
        @type post_uuid: unicode
        @param data: The JSON data returned from the API
        @type data: dict

        @return: A Post object
        @raises TypeError: data is not a dict
        @raises ValueError: data is missing required entries
        """
        post = cls(page, post_uuid)
        post._set_data(data)

        return post

    def _set_data(self, data, new_revision=False):
        """Set internal data and cache content.

        @param data: The data to store internally
        @type data: dict
        @param new_revision: Whether there is a new revision
        @type new_revision: bool
        @raises TypeError: data is not a dict
        @raises ValueError: missing data entries or post/revision not found
        """
        if not isinstance(data, dict):
            raise TypeError('Illegal post data (must be a dictionary).')
        if ('posts' not in data) or ('revisions' not in data):
            raise ValueError('Illegal post data (missing required data).')
        if self.uuid not in data['posts']:
            raise ValueError('Post not found in supplied data.')

        if hasattr(self, '_current_revision') and not new_revision:
            self._current_revision._set_data(data)
        else:
            current_revision_id = data['posts'][self.uuid][0]
            if current_revision_id not in data['revisions']:
                raise ValueError('Current revision of post'
                                 'not found in supplied data.')

            self._data = data['revisions'][current_revision_id]
            self._current_revision = FlowRevision.fromJSON(self.page,
                                                           current_revision_id,
                                                           data)

    def _load(self, format='wikitext', load_from_topic=False, new_revision=False):
        """Load and cache the Post's data using the given content format."""
        if load_from_topic:
            data = self.page._load(format=format, force=True)
        else:
            data = self.site.load_post_current_revision(self.page, self.uuid,
                                                        format)
        self._set_data(data, new_revision=new_revision)
        return self._data

    @property
    def _content(self):
        """Mirror of the post FlowRevision content dict."""
        if hasattr(self, '_current_revision'):
            return self._current_revision._content
        else:
            return {}

    @property
    def current_revision(self):
        """The FlowRevision corresponding to this post's current revision."""
        if not hasattr(self, '_current_revision'):
            self._load()
        return self._current_revision

    @property
    def is_moderated(self):
        """Whether this post is moderated."""
        return self.current_revision.is_moderated

    @property
    def creator(self):
        """The creator of this post."""
        return self.current_revision.creator

    def get(self, format='wikitext', force=False, sysop=False):
        """Return the contents of the post in the given format.

        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @param sysop: Whether to load using sysop rights. Implies force.
        @type sysop: bool
        @param format: Content format to return contents in
        @type format: unicode
        @return: The contents of the post in the given content format
        @rtype: unicode
        @raises NotImplementedError: use of 'sysop'
        """
        if sysop:
            raise NotImplementedError

        if format not in self._content or force:
            self._load(format)
        return self._current_revision.get(format=format)

    def revisions(self, format='wikitext', force=False):
        """Return this post's revisions.

        @param format: Content format to return contents in
        @type format: str ('wikitext', 'html', or 'fixed-html')
        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @return: This post's revisions
        @rtype: list of FlowRevisions
        """
        if format not in ('wikitext', 'html', 'fixed-html'):
            raise ValueError('Invalid content format.')

        if hasattr(self, '_revisions') and not force:
            return self._revisions

        revision_list = self.site.load_post_history(self, format)

        self._revisions = [FlowRevision.fromHistoryJSON(self.page, revision)
                           for revision in revision_list]

        return self._revisions

    def replies(self, format='wikitext', force=False):
        """Return this post's replies.

        @param format: Content format to return contents in
        @type format: str ('wikitext', 'html', or 'fixed-html')
        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @return: This post's replies
        @rtype: list of Posts
        """
        if format not in ('wikitext', 'html', 'fixed-html'):
            raise ValueError('Invalid content format.')

        if hasattr(self, '_replies') and not force:
            return self._replies

        # load_from_topic workaround due to T106733
        # (replies not returned by view-post)
        if not hasattr(self, '_data') or force:
            self._load(format, load_from_topic=True)

        reply_uuids = self.current_revision._data['replies']
        self._replies = [Post(self.page, uuid) for uuid in reply_uuids]

        return self._replies

    def reply(self, content, format='wikitext'):
        """Reply to this post.

        @param content: The content of the new post
        @type content: unicode
        @param format: The format of the given content
        @type format: str ('wikitext' or 'html')
        @return: The new reply post
        @rtype: Post
        """
        self._load()
        if self.page.is_locked:
            raise LockedPage(self.page, 'Topic %s is locked.')

        reply_url = self._data['actions']['reply']['url']
        parsed_url = urlparse(reply_url)
        params = parse_qs(parsed_url.query)
        reply_to = params['topic_postId']
        if self.uuid == reply_to:
            del self._data
            del self._replies
        data = self.site.reply_to_post(self.page, reply_to, content, format)
        self._load()
        post = Post(self.page, data['post-id'])
        return post

    # Moderation
    def delete(self, reason):
        """Delete this post through the Flow moderation system.

        @param reason: The reason for deleting this post.
        @type reason: unicode
        """
        self.site.delete_post(self, reason)
        self._load(new_revision=True)

    def hide(self, reason):
        """Hide this post.

        @param reason: The reason for hiding this post.
        @type reason: unicode
        """
        self.site.hide_post(self, reason)
        self._load(new_revision=True)

    def suppress(self, reason):
        """Suppress this post.

        @param reason: The reason for suppressing this post.
        @type reason: unicode
        """
        self.site.suppress_post(self, reason)
        self._load(new_revision=True)

    def restore(self, reason):
        """Restore this post.

        @param reason: The reason for restoring this post.
        @type reason: unicode
        """
        self.site.restore_post(self, reason)
        self._load(new_revision=True)

    def thank(self):
        """Thank the user who made this post."""
        self.site.thank_post(self)


class FlowRevision(FlowObject):

    """A revision of a Flow object."""

    def __init__(self, page, uuid):
        """Constructor.

        @param page: Flow topic
        @type page: Topic
        @param uuid: UUID of a Flow revision
        @type uuid: unicode

        @raises TypeError: incorrect types of parameters
        @raises NoPage: topic does not exist
        """
        super(FlowRevision, self).__init__(page, uuid)

        self._content = {}

    @classmethod
    def fromJSON(cls, page, uuid, data):
        """
        Create a FlowRevision object using the data returned from the API call.

        @param page: A Flow topic
        @type page: Topic
        @param uuid: The UUID of the revision
        @type uuid: unicode
        @param data: The JSON data returned from the API
        @type data: dict

        @return: A FlowRevision object
        @raises TypeError: data is not a dict
        @raises ValueError: data is missing required entries
        """
        revision = cls(page, uuid)
        revision._set_data(data)

        return revision

    @classmethod
    def fromHistoryJSON(cls, page, data):
        """
        Create a FlowRevision object using data from the history API calls.

        @param page: A Flow topic
        @type page: Topic
        @param data: The JSON data returned from the API
        @type data: dict

        @return: A FlowRevision object
        @raises TypeError: data is not a dict
        @raises ValueError: data is missing required entries
        """
        if not isinstance(page, Topic):
            raise TypeError('Page must be a Topic object')
        if not isinstance(data, dict):
            raise TypeError('Illegal revision data (must be a dictionary).')
        if 'revisionId' not in data:
            raise ValueError('Illegal revision data (missing required data).')
        uuid = data['revisionId']
        full_data = {'revisions': {uuid: data}}

        return cls.fromJSON(page, uuid, full_data)

    def _set_data(self, data):
        """Set internal data and cache content.

        @param data: The data to store internally
        @type data: dict
        @raises TypeError: data is not a dict
        @raises ValueError: missing data entries or revision not found
        """
        if not isinstance(data, dict):
            raise TypeError('Illegal revision data (must be a dictionary).')
        if 'revisions' not in data:
            raise ValueError('Illegal revision data (missing required data).')
        if self.uuid not in data['revisions']:
            raise ValueError('Revision not found in supplied data.')

        self._data = data['revisions'][self.uuid]
        if 'content' in self._data:
            content = self._data.pop('content')
            assert isinstance(content, dict)
            assert isinstance(content['content'], unicode)
            self._content[content['format']] = content['content']

    def _load(self, format='wikitext', load_from_topic=True):
        """Load and cache the revision's data using the given content format."""
        if load_from_topic:
            history_data = self.site.load_topic_history(page=self.page,
                                                        format=format)
            revision_data = None
            for rev in history_data:
                if rev['revisionId'] == self.uuid:
                    revision_data = rev
                    break
            data = {'revisions': {self.uuid: revision_data}}
        else:
            # TODO: Load single revision (T103055)
            # data = self.site.load_flow_revision(self.page, self.uuid,
            #                                     format)
            raise NotImplementedError
        try:
            self._set_data(data)
            return self._data
        except ValueError:
            raise NotImplementedError('Revision not current (see T103055)')

    @property
    def change_type(self):
        """The type of change this revision made."""
        return self._data['changeType']

    @property
    def is_moderated(self):
        """Whether this revision is moderated."""
        return self._data['isModerated']

    @property
    def moderation_state(self):
        """The moderation state for this revision."""
        if self.is_moderated:
            return self._data['moderateState']
        else:
            return False

    @property
    def moderation_reason(self):
        """The moderation reason for this revision."""
        if self.is_moderated:
            return self._data['moderateReason']['content']
        else:
            return False

    @property
    def creator(self):
        """The creator of the post this revision belongs to."""
        if not hasattr(self, '_creator'):
            self._creator = User(self.site, self._data['creator']['name'])
        return self._creator

    @property
    def author(self):
        """The author of this revision."""
        if not hasattr(self, '_author'):
            self._author = User(self.site, self._data['author']['name'])
        return self._author

    @property
    def previous_revision(self):
        """The previous Flow revision."""
        if not hasattr(self, '_previous_revision'):
            self._previous_revision = FlowRevision(self.page,
                                                   self._data['previousRevisionId'])
        return self._previous_revision

    def get(self, format='wikitext', sysop=False):
        """Return the contents of the post in the given format.

        @param sysop: Whether to load using sysop rights.
        @type sysop: bool
        @param format: Content format to return contents in
        @type format: unicode
        @return: The contents of the post in the given content format
        @rtype: unicode
        @raises NotImplementedError: use of 'sysop'
        """
        if sysop:
            raise NotImplementedError

        if format not in self._content:
            self._load(format)
        if format not in self._content:
            raise NotImplementedError('Content format probably not supported.')
        return self._content[format]
