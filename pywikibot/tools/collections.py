# -*- coding: utf-8 -*-
"""Miscellaneous collections classes."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, print_function, unicode_literals
__version__ = '$Id$'

import collections
import types

from pywikibot.tools import PY2, UnicodeMixin

if not PY2:
    unicode = str


class ProxyDict(collections.Mapping, UnicodeMixin):

    """
    Mapping providing read only access to it.

    The default constructor will not create a copy of the dict, so changes in
    it are reflected by this dict. The C{create} classmethod will copy the data.

    Copying this dict will always return a new dict instance which won't reflect
    changes. When the iterator is returned, it creates an iterator of the
    underlying dict. So when that underlying dict changes it may be reflected in
    the iterator or cause the iterator to fail.
    """

    def __init__(self, mapping):
        """Create a mapping proxy with the given data which is a dict."""
        super(ProxyDict, self).__init__()
        self.__data = mapping

    @classmethod
    def create(cls, *args, **data):
        """Create a copy without proxing."""
        if not args:
            arg_data = {}
        elif len(args) == 1:
            arg_data = dict(args[0])
        else:
            raise TypeError('{0} expected at most 1 arguments, got '
                            '{1}'.format(cls.__class__.__name__, len(args)))
        if data:
            arg_data.update(data)
        return cls(arg_data)

    def __getitem__(self, key):
        """Get the item from the underlying dict."""
        return self.__data[key]

    def __iter__(self):
        """Get an iterator from the underlying dict."""
        return iter(self.__data)

    def __len__(self):
        """Get the length of the underlying dict."""
        return len(self.__data)

    def __contains__(self, value):
        """Return whether value is in the proxied data."""
        return value in self.__data

    def keys(self):
        """Return the keys of the data."""
        return self.__data.keys()

    def values(self):
        """Return the values of the data."""
        return self.__data.values()

    def items(self):
        """Return the items of the data."""
        return self.__data.items()

    if PY2:
        def iterkeys(self):
            """Return the data's iterkeys result."""
            return self.__data.iterkeys()

        def itervalues(self):
            """Return the data's itervalues result."""
            return self.__data.itervalues()

        def iteritems(self):
            """Return the data's iteritems result."""
            return self.__data.iteritems()

    def __unicode__(self):
        """Return unicode text as if it were a dict."""
        return unicode(self.copy())

    def __repr__(self):
        """Return representation using the class name and content as dict."""
        return str('{0}({1!r})'.format(self.__class__.__name__, self.copy()))

    def copy(self):
        """Shallowly copy the underlying dict."""
        return dict(self.__data)


if PY2:
    # Not exactly the same, but close enough. MappingProxyType in Python 3
    # does not support subclasses.
    def MappingProxyType(mapping):
        """Return a mappingproxy instance."""
        class mappingproxy(ProxyDict):
            pass

        return mappingproxy(mapping)
else:
    MappingProxyType = types.MappingProxyType
