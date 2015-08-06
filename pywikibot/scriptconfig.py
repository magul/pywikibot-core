# -*- coding: utf-8  -*-
"""
Functionality for configuration of script behavior.

Configuration for a given script is created by combining:
    - default configuration passed in initialization
    - Mediawiki:Pywikibot/script.json on the target site
    - override configuration in the PYWIKIBOT2_DIR [not implemented yet]

Configuration is cached in the Configuration object.
"""
#
# (C) Pywikibot team, 2004-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

import json
import logging

import pywikibot
from pywikibot import Error, UnicodeMixin

_logger = logging.getLogger('pywikibot.scriptconfig')

class NoConfigurationException(Exception):
    pass

class Configuration(UnicodeMixin):
    def __init__(self, scriptname, default_config="{}", require_config=False):
        self._cache = {}
        self._fmt = 'Mediawiki:Pywikibot/{}.json'
        self.default_config = default_config
        self.require_config = require_config
        self.scriptname = scriptname

    def __call__(self, site):
        if site not in self._cache:
           self._cache[site] = self._build_config(site)
        return self._cache[site]

    def _build_config(self, site):
        _logger.debug('Building {} configuration for {}'.format(self.scriptname, site))

        config = {}
        config.update(self.default_config)

        page = pywikibot.Page(site, self._fmt.format(self.scriptname))
        _logger.debug('Retrieving {}...'.format(page))
        try:
            config.update(json.loads(page.get()))
        except pywikibot.Error as e:
            if self.require_config:
                raise
            _logger.exception(e)

        return config
