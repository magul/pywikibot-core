#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script generates a family file from a given URL.

Hackish, etc. Regexps, yes. Sorry, jwz.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
#
# (C) Merlijn van Deen, 2010-2013
# (C) Pywikibot team, 2010-2015
#
# Distributed under the terms of the MIT license
#
__version__ = '$Id$'
#

# system imports
import codecs
import os
import sys

# creating & retrieving urls
if sys.version_info[0] > 2:
    from urllib.parse import urlparse
    raw_input = input
else:
    from urlparse import urlparse

# Disable user-config checks so the family can be created first,
# and then used when generating the user-config
_orig_no_user_config = os.environ.get('PYWIKIBOT2_NO_USER_CONFIG')  # noqa
os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = '2'  # noqa

from pywikibot.site_detect import MWSite as Wiki

# Reset this flag in case another script is run by pwb after this script
if not _orig_no_user_config:
    del os.environ['PYWIKIBOT2_NO_USER_CONFIG']
else:
    os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = _orig_no_user_config


class FamilyFileGenerator(object):

    """Family file creator."""

    def __init__(self, url=None, name=None, dointerwiki=None):
        """Constructor."""
        if url is None:
            url = raw_input("Please insert URL to wiki: ")
        if name is None:
            name = raw_input("Please insert a short name (eg: freeciv): ")
        self.dointerwiki = dointerwiki
        self.base_url = url
        self.name = name

        self.wikis = {}  # {'https://wiki/$1': Wiki('https://wiki/$1'), ...}
        self.langs = []  # [Wiki('https://wiki/$1'), ...]

    def run(self):
        """Run generator."""
        print("Generating family file from %s" % self.base_url)

        w = Wiki(self.base_url)
        print()
        print("==================================")
        print("api url: %s" % w.api)
        print("MediaWiki version: %s" % w.version)
        print("==================================")
        print()

        if not w.articlepath:
            print('article path not found; skipping interwikis')
            self.wikis[w.api] = w
        else:
            self.wikis[w.iwpath] = w
            self.getlangs(w)

        self.getapis()
        self.writefile()

    def getlangs(self, w):
        """Populate langs from interwikimap."""
        print("Determining other languages...", end="")
        try:
            self.langs = w.langs
            print(u' '.join(sorted([wiki[u'prefix'] for wiki in self.langs])))
        except Exception as e:
            self.langs = []
            print(e, "; continuing...")

        if len([lang for lang in self.langs if lang['url'] == w.iwpath]) == 0:
            print('Interwiki matrix doesnt include this site; '
                  'manually adding as code %s' % w.lang)
            self.langs.append({u'language': w.lang,
                               u'local': u'',
                               u'prefix': w.lang,
                               u'url': w.iwpath})

        if len(self.langs) > 1:
            if self.dointerwiki is None:
                makeiw = raw_input(
                    "\nThere are %i languages available."
                    "\nDo you want to generate interwiki links?"
                    "This might take a long time. ([y]es/[N]o/[e]dit)"
                    % len(self.langs)).lower()
            else:
                makeiw = self.dointerwiki

            if makeiw == "y":
                pass
            elif makeiw == "e":
                for wiki in self.langs:
                    print(wiki['prefix'], wiki['url'])
                do_langs = raw_input("Which languages do you want: ")
                self.langs = [wiki for wiki in self.langs
                              if wiki['prefix'] in do_langs or
                              wiki['url'] == w.iwpath]
            else:
                self.langs = [wiki for wiki in self.langs
                              if wiki[u'url'] == w.iwpath]

    def getapis(self):
        """Populate wikis from langs."""
        print("Loading wikis... ")
        for lang in self.langs:
            print("  * %s... " % (lang[u'prefix']), end="")
            if lang[u'url'] not in self.wikis:
                try:
                    self.wikis[lang[u'url']] = Wiki(lang[u'url'])
                    print("downloaded")
                except Exception as e:
                    print(e)
            else:
                print("in cache")

    def writefile(self):
        """Write family module."""
        fn = "pywikibot/families/%s_family.py" % self.name
        print("Writing %s... " % fn)
        try:
            open(fn)
            if raw_input("%s already exists. Overwrite? (y/n)"
                         % fn).lower() == 'n':
                print("Terminating.")
                sys.exit(1)
        except IOError:  # file not found
            pass
        f = codecs.open(fn, 'w', 'utf-8')

        f.write("""
# -*- coding: utf-8 -*-
\"\"\"
This family file was auto-generated by $Id$
Configuration parameters:
  url = %(url)s
  name = %(name)s

Please do not commit this to the Git repository!
\"\"\"

from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = '%(name)s'
        self.langs = {
""".lstrip() % {'url': self.base_url, 'name': self.name})

        for w in self.wikis.values():
            f.write("            '%(lang)s': '%(hostname)s',\n"
                    % {'lang': w.lang, 'hostname': urlparse(w.server).netloc})

        f.write("        }\n\n")

        f.write("    def scriptpath(self, code):\n")
        f.write("        return {\n")

        for w in self.wikis.values():
            f.write("            '%(lang)s': '%(path)s',\n"
                    % {'lang': w.lang, 'path': w.scriptpath})
        f.write("        }[code]\n")
        f.write("\n")

        f.write("    @deprecated('APISite.version()')\n")
        f.write("    def version(self, code):\n")
        f.write("        return {\n")
        for w in self.wikis.values():
            if w.version is None:
                f.write("            '%(lang)s': None,\n" % {'lang': w.lang})
            else:
                f.write("            '%(lang)s': u'%(ver)s',\n"
                        % {'lang': w.lang, 'ver': w.version})
        f.write("        }[code]\n")

        f.write("\n")
        f.write("    def protocol(self, code):\n")
        f.write("        return {\n")
        for w in self.wikis.values():
            f.write("            '%(lang)s': u'%(protocol)s',\n"
                    % {'lang': w.lang, 'protocol': urlparse(w.server).scheme})
        f.write("        }[code]\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <url> <short name>" % sys.argv[0])
        print("Example: %s https://www.mywiki.bogus/wiki/Main_Page mywiki"
              % sys.argv[0])
        print("This will create the file families/mywiki_family.py")

    FamilyFileGenerator(*sys.argv[1:]).run()
