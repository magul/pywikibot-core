# -*- coding: utf-8  -*-
"""Tests for XML API support."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot.data.api import Request

from tests import TestRequest

from tests.aspects import unittest

from tests.api_tests import (
    # TestAPIMWException as _APIMWExceptionBase, requires json -> xml first
    TestApiFunctions as _ApiFunctionsBase,
    TestParamInfo as _ParamInfoBase,
)
from tests.page_tests import (
    TestPageObject as _PageObjectTestBase,
    TestPageObjectEnglish as _PageObjectEnglishTestBase,
)


class XmlApiTestBase(object):

    """Base class for XML API testing."""

    def setUp(self):
        """Set up XML test."""
        Request._FORMAT = 'xml'
        TestRequest._FORMAT = 'xml'
        super(XmlApiTestBase, self).setUp()

    def tearDown(self):
        """Restore XML as the API format."""
        Request._FORMAT = 'json'
        TestRequest._FORMAT = 'json'
        super(XmlApiTestBase, self).tearDown()


class TestXmlApiFunctions(XmlApiTestBase, _ApiFunctionsBase):

    """Test the XML API on basic functions."""


class TestXmlApiParamInfo(XmlApiTestBase, _ParamInfoBase):

    """Test the XML API with ParamInfo."""


class _TestXmlPageObject(XmlApiTestBase, _PageObjectTestBase):

    """Test the Page object using XML API."""


class _TestXmlPageObjectEnglish(XmlApiTestBase, _PageObjectEnglishTestBase):

    """Test the Page object using XML API."""


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
