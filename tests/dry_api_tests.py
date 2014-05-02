# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2012-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import datetime
import pywikibot
from pywikibot.data.api import CachedRequest, QueryGenerator
from tests.utils import unittest


class DryAPITests(unittest.TestCase):

    def setUp(self):
        self.parms = {'site': pywikibot.Site('en'),
                      'action': 'query',
                      'meta': 'userinfo'}
        self.req = CachedRequest(expiry=1, **self.parms)
        self.expreq = CachedRequest(expiry=0, **self.parms)
        self.diffreq = CachedRequest(expiry=1, site=pywikibot.Site('en'), action='query', meta='siteinfo')
        self.diffsite = CachedRequest(expiry=1, site=pywikibot.Site('de'), action='query', meta='userinfo')

    def test_expiry_formats(self):
        self.assertEqual(self.req.expiry, CachedRequest(datetime.timedelta(days=1), **self.parms).expiry)

    def test_create_file_name(self):
        self.assertEqual(self.req._cache_key(), self.req._cache_key())
        self.assertEqual(self.req._cache_key(), self.expreq._cache_key())
        self.assertNotEqual(self.req._cache_key(), self.diffreq._cache_key())

    def test_expired(self):
        self.assertFalse(self.req._expired(datetime.datetime.now()))
        self.assertTrue(self.req._expired(datetime.datetime.now() - datetime.timedelta(days=2)))

    def test_query_constructor(self):
        qGen1 = QueryGenerator(action="query", meta="siteinfo")
        qGen2 = QueryGenerator(meta="siteinfo")
        self.assertEqual(str(qGen1.request), str(qGen2.request))

if __name__ == '__main__':
    unittest.main()
