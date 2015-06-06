# -*- coding: utf-8  -*-
"""
Objects representing objects used with ProofreadPage Extension.

The extension is supported by MW 1.21+.

This module includes objects:
* ProofreadPage(Page)
* FullHeader

"""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import re
import json

import pywikibot


class ProofreadPage(pywikibot.Page):

    """ProofreadPage page used in Mediawiki ProofreadPage extension."""

    WITHOUT_TEXT = 0
    NOT_PROOFREAD = 1
    PROBLEMATIC = 2
    PROOFREAD = 3
    VALIDATED = 4

    open_tag = '<noinclude>'
    close_tag = '</noinclude>'
    p_open = re.compile(r'<noinclude>')
    p_close = re.compile(r'(</div>|\n\n\n)?</noinclude>')
    p_header = re.compile(
        r'<pagequality level="(?P<level>\d)" user="(?P<user>.*?)" />'
        r'<div class="pagetext">(?P<header>.*)',
        re.DOTALL)

    KEYS = ['header', 'body', 'footer', 'level', 'user']

    def __init__(self, source, title=''):
        """Instantiate a ProofreadPage object.

        Raises UnknownExtension if source Site has no ProofreadPage Extension.
        """
        if not isinstance(source, pywikibot.site.BaseSite):
            site = source.site
        else:
            site = source
        ns = site.proofread_page_ns
        super(ProofreadPage, self).__init__(source, title, ns=ns)
        if self.namespace() != site.proofread_page_ns:
            raise ValueError('Page %s must belong to %s namespace'
                             % (self.title(), ns))

        self._page_dict = RestrictedDict(ProofreadPage.KEYS)

    def load_text_and_apply(fn):
        """Decorator.

        Load text if needed and recompose text after change.
        """
        def wrapper(obj, *args, **kwargs):
            if not hasattr(obj, '_text'):
                obj.text  # Property force page text loading.
            _res = fn(obj, *args, **kwargs)
            obj._compose_page()
            return _res
        return wrapper

    @property
    @load_text_and_apply
    def level(self):
        """Return page quality level."""
        return self._page_dict['level']

    @level.setter
    @load_text_and_apply
    def level(self, value):
        """Set page quality level."""
        if value not in self.site.proofread_levels:
            raise ValueError('Not valid Quality Level: %s (legal values: %s)'
                             % (value, self.site.proofread_levels))
        # TODO: add logic to validate level value change, considering
        # site.proofread_levels.
        self._page_dict['level'] = value

    @property
    @load_text_and_apply
    def user(self):
        """Return user in page header."""
        return self._page_dict['user']

    @user.setter
    @load_text_and_apply
    def user(self, value):
        """Set user in page header."""
        self._page_dict['user'] = value

    @property
    @load_text_and_apply
    def status(self):
        """Return Proofread Page status."""
        try:
            return self.site.proofread_levels[self.level]
        except KeyError:
            pywikibot.warning('Not valid status set for %s: quality level = %s'
                              % (self.title(asLink=True), self.level))
            return None

    def without_text(self):
        """Set Page Quality Level to "Without text"."""
        self.level = self.WITHOUT_TEXT

    def problematic(self):
        """Set Page Quality Level to "Problematic"."""
        self.level = self.PROBLEMATIC

    def not_proofread(self):
        """Set Page Quality Level to "Not Proofread"."""
        self.level = self.NOT_PROOFREAD

    def proofread(self):
        """Set Page Quality Level to "Proofread"."""
        # TODO: check should be made to be consistent with Proofread Extension
        self.level = self.PROOFREAD

    def validate(self):
        """Set Page Quality Level to "Validated"."""
        # TODO: check should be made to be consistent with Proofread Extension
        self.level = self.VALIDATED

    @property
    @load_text_and_apply
    def header(self):
        """Return editable part of Page header."""
        return self._page_dict['header']

    @header.setter
    @load_text_and_apply
    def header(self, value):
        """Set editable part of Page header."""
        self._page_dict['header'] = value

    @property
    @load_text_and_apply
    def body(self):
        """Return Page body."""
        return self._page_dict['body']

    @body.setter
    @load_text_and_apply
    def body(self, value):
        """Set Page body."""
        self._page_dict['body'] = value

    @property
    @load_text_and_apply
    def footer(self):
        """Return Page footer."""
        return self._page_dict['footer']

    @footer.setter
    @load_text_and_apply
    def footer(self, value):
        """Set Page footer."""
        self._page_dict['footer'] = value

    def _create_empty_page(self):
        """Create empty page."""
        self.user = self.site.username()  # Fill user field in empty header.
        self._compose_page()

    @property
    def text(self):
        """Override text property.

        Load text if needed and fill self._page_dict if needed.

        Preload text returned by EditFormPreloadText to preload non-existing
        pages.
        """
        # Text is already cached.
        if hasattr(self, '_text'):
            return self._text
        if self.exists():
            # If page exists, load it in 'application/json' format and
            # convert it in 'text/x-wiki' format.
            self._text = self.get(get_redirect=True, contentformat='application/json')
            self._json_to_dict()  # Fill page dictionary structure.
            self._compose_page()  # Update text in 'text/x-wiki' format.
        else:
            # If page does not exist, preload it
            self._text = self.preloadText()
            self._decompose_page()  # Fill page dictionary structure.
            self.user = self.site.username()  # Fill user field in empty header.
        return self._text

    @text.setter
    def text(self, value):
        """Update current text.

        Mainly for use within the class, called by other methods.
        Use self.header, self.body and self.footer to set page content,

        @param value: New value or None
        @param value: basestring

        Raises:
        exception Error:   the page is not formatted according to ProofreadPage
                           extension.
        """


        old_text, self._text = self._text, value

        e_1, e_2 = None, None
        try:
            self._json_to_dict()
            self._compose_page()
        except ValueError as e_1:
            pass

        try:
            self._decompose_page()
        except pywikibot.Error as e_2:
            pass

        if all([e_1, e_2]):
            self._text = old_text
            raise pywikibot.Error('ProofreadPage %s: invalid format'
                      % self.title())


    @text.deleter
    def text(self):
        """Delete current text."""
        if hasattr(self, '_text'):
            del self._text

    def _decompose_page(self):
        """Split Proofread Page text in header, body and footer.

        Raises:
        exception Error:   the page is not formatted according to ProofreadPage
                           extension.
        """

        open_queue = list(self.p_open.finditer(self._text))
        close_queue = list(self.p_close.finditer(self._text))

        len_oq = len(open_queue)
        len_cq = len(close_queue)
        if (len_oq != len_cq) or (len_oq < 2 or len_cq < 2):
            raise pywikibot.Error('ProofreadPage %s: invalid "text/x-wiki" format'
                                  % self.title())

        f_open, f_close = open_queue[0], close_queue[0]
        m = self.p_header.search(self._text[f_open.end():f_close.start()])
        if m:
            self._page_dict['level'] = int(m.group('level'))
            self._page_dict['user'] = m.group('user')
            self._page_dict['header'] = m.group('header')
        else:
            self._page_dict['level'] = ProofreadPage.NOT_PROOFREAD
            self._page_dict['user'] = ''
            self._page_dict['header'] = ''

        l_open, l_close = open_queue[-1], close_queue[-1]
        self._page_dict['footer'] = self._text[l_open.end():l_close.start()]

        self._page_dict['body'] = self._text[f_close.end():l_open.start()]

    def _compose_page(self):
        """Compose Proofread Page text from header, body and footer."""
        fmt = ('{open_tag}'
               '<pagequality level="{level}" user="{user}" />'
               '<div class="pagetext">{header}\n\n\n'
               '{close_tag}'
               '{body}'
               '{open_tag}{footer}</div>{close_tag}')
        value = dict(self._page_dict)
        value.update({'open_tag': self.open_tag, 'close_tag': self.close_tag})
        self._text = fmt.format(**value)
        return self._text

    def _json_to_dict(self):
        """Convert page json format to dict.

        This is the format accepted by action=edit specifying
        contentformat=application/json. This format is recommended to save the
        page, as it is not subject to possible errors done in composing the
        wikitext header and footer of the page or changes in the ProofreadPage
        extension format.
        """
        try:
            page_dict = json.loads(self.text)
        except ValueError as e:
            raise ValueError(e.args[0] + ' - text: %s' % self.text)

        self._page_dict.update(page_dict)
        self._page_dict.update(page_dict['level'])
        return self._page_dict

    def _page_to_json(self):
        """Convert page text to json format.

        This is the format accepted by action=edit specifying
        contentformat=application/json. This format is recommended to save the
        page, as it is not subject to possible errors done in composing the
        wikitext header and footer of the page or changes in the ProofreadPage
        extension format.
        """
        page_dict = {'header': self.header,
                     'body': self.body,
                     'footer': self.footer,
                     'level': {'level': self.level, 'user': self.user},
                     }
        # ensure_ascii=False returns a unicode
        return json.dumps(page_dict, ensure_ascii=False)

    def save(self, *args, **kwargs):  # see Page.save()
        """Save page content after recomposing the page."""
        summary = kwargs.pop('summary', '')
        summary = self.pre_summary + summary
        # Save using contentformat='application/json'
        kwargs['contentformat'] = 'application/json'
        kwargs['contentmodel'] = 'proofread-page'
        text = self._page_to_json()
        super(ProofreadPage, self).save(*args, text=text, summary=summary,
                                        **kwargs)

    @property
    def pre_summary(self):
        """Return trailing part of edit summary.

        The edit summary shall be appended to pre_summary to highlight
        Status in the edit summary on wiki.
        """
        return '/* {0.status} */ '.format(self)


# TODO: this could go in tools.
class RestrictedDict(dict):
    """
    Stores the properties of an object. It's a dictionary that's
    restricted to a tuple of allowed keys. Any attempt to set an invalid
    key raises an error.

    Based on http://code.activestate.com/recipes/578042-restricted-dictionary
    """

    def __init__(self, allowed_keys, seq=(), **kwargs):
        """Class constructor."""
        super(RestrictedDict, self).__init__()
        self._allowed_keys = tuple(allowed_keys)
        # normalize arguments to a (key, value) iterable
        if hasattr(seq, 'keys'):
            get = seq.__getitem__
            seq = ((k, get(k)) for k in seq.keys())
        if kwargs:
            from itertools import chain
            seq = chain(seq, kwargs.iteritems())
        # scan the items keeping track of the keys' order
        for k, v in seq:
            self.__setitem__(k, v)

    def __setitem__(self, key, value):
        """Checks if the key is allowed before setting the value"""
        if key in self._allowed_keys:
            super(RestrictedDict, self).__setitem__(key, value)
        else:
            raise KeyError("%s is not allowed as key" % key)

    def update(self, e=None, **kwargs):
        """
        Equivalent to dict.update(), but it was needed to call
        RestrictedDict.__setitem__() instead of dict.__setitem__
        """
        try:
            for k in e:
                self.__setitem__(k, e[k])
        except AttributeError:
            for (k, v) in e:
                self.__setitem__(k, v)
        for k in kwargs:
            self.__setitem__(k, kwargs[k])

    def __repr__(self):
        """Representation of the RestrictedDict"""
        return 'RestrictedDict(%s, %s)' % (self._allowed_keys.__repr__(),
                                     super(RestrictedDict, self).__repr__())
