#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Script to determine the Pywikibot version (tag, revision and date)."""
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2008
# (C) xqt, 2010-2014
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import sys
import os
import codecs

try:
    import pywikibot
    from pywikibot.version import getversion
except ImportError as e:
    pywikibot = e

try:
    import requests
except ImportError:
    requests = {'__version__': 'n/a'}

WMF_CACERT = 'MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs'


def output(text):
    """Output the text via print in an error."""
    if isinstance(pywikibot, ImportError):
        print(text)
    else:
        pywikibot.output(text)


def check_environ(environ_name):
    """Print environment variable."""
    output('{0}: {1}'.format(environ_name, os.environ.get(environ_name, 'Not set')))


if __name__ == '__main__':
    if not isinstance(pywikibot, ImportError):
        pywikibot.output('Pywikibot: %s' % getversion())
        pywikibot.output('Release version: %s' % pywikibot.__release__)
    else:
        output('Pywikibot: Unavailable ({0})'.format(pywikibot))
    output('requests version: %s' % requests.__version__)

    has_wikimedia_cert = False
    if (not hasattr(requests, 'certs') or
            not hasattr(requests.certs, 'where') or
            not callable(requests.certs.where)):
        output('  cacerts: not defined')
    elif not os.path.isfile(requests.certs.where()):
        output('  cacerts: %s (missing)' % requests.certs.where())
    else:
        output('  cacerts: %s' % requests.certs.where())

        with codecs.open(requests.certs.where(), 'r', 'utf-8') as cert_file:
            text = cert_file.read()
            if WMF_CACERT in text:
                has_wikimedia_cert = True
        output(u'    certificate test: %s'
                         % ('ok' if has_wikimedia_cert else 'not ok'))
    if not has_wikimedia_cert:
        output(
            '  Please reinstall requests!')

    output('Python: %s' % sys.version)
    normalize_text = u'\u092e\u093e\u0930\u094d\u0915 \u091c\u093c\u0941\u0915\u0947\u0930\u092c\u0930\u094d\u0917'

    if normalize_text != __import__('unicodedata').normalize(
            'NFC', normalize_text):
        output(u'  unicode test: triggers problem #3081100')
    else:
        output(u'  unicode test: ok')
    check_environ('PYWIKIBOT2_DIR')
    check_environ('PYWIKIBOT2_DIR_PWB')
    check_environ('PYWIKIBOT2_NO_USER_CONFIG')
    if not isinstance(pywikibot, ImportError):
        pywikibot.output('Config base dir: {0}'.format(pywikibot.config2.base_dir))
        for family, usernames in pywikibot.config2.usernames.items():
            if usernames:
                pywikibot.output('Usernames for family "{0}":'.format(family))
                for lang, username in usernames.items():
                    sysop_name = pywikibot.config2.sysopnames.get(family, {}).get(lang)
                    if not sysop_name:
                        sysop_name = 'no sysop configured'
                    elif sysop_name == username:
                        sysop_name = 'also sysop'
                    pywikibot.output('\t{0}: {1} ({2})'.format(lang, username, sysop_name))
    else:
        output('pywikibot could not be loaded: unknown base dir.')
