# -*- coding: utf-8  -*-
"""XML API support."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import itertools
import json

import xmltodict

import pywikibot


# Unused atm
def _to_dict(array, key):
    assert isinstance(array, list), 'not a list: %s' % array
    d = {}
    for item in array:
        assert isinstance(item, dict), 'not a dict: %s' % item
        d[item[key]] = item
    return d


def xml_postprocessor(path, key, value):
    """XML postprocessor to transform the data structures to replicate MediaWiki JSON."""
    if key.startswith('_') or key.startswith('xml:'):
        return None
    if len(path) == 2 and key in ['entities']:
        return key, value
    if len(path) == 3 and key in ['pages', 'userinfo', 'namespaces']:
        return key, value
    elif len(path) == 3 and key in 'extensions':
        values = value.values()
        extensions = [item for item in values if isinstance(item, dict)]
        extras = [item for item in values if isinstance(item, list)]
        extras = list(itertools.chain.from_iterable(extras))
        extensions += extras
        return key, extensions
    elif len(path) == 3 and key in 'modules':
        return key, value.values()
    elif len(path) == 3 and key in ['querymodules', 'namespacealiases']:
        return key, value.values()[0]
    elif len(path) == 3 and key == 'pageids':
        return key, value.values()
    elif ((len(path) == 4 and key in ['aliases', 'claims']) or
            (len(path) == 9 and key == 'snaks')):
        d = {}
        for k in value.keys():
            v = value[k]
            if isinstance(v, dict):
                v = [v]
            d[k] = v
        return key, d
    elif len(path) == 3 and key == 'entity':
        key = value['id']
        return key, value
    elif len(path) == 4 and key == 'module':
        key = value['name']
        return key, value
    elif len(path) == 4 and key == 'page':
        if 'pageid' in value:
            key = value['pageid']
        else:
            key = value['title']
        return key, value
    elif len(path) == 4 and key == 'ext':
        key = value['name']
        return key, value
    elif len(path) == 4 and key == 'ns':
        if path[2][0] != 'namespacealiases':
            if isinstance(value, dict):
                key = value['id']
        if isinstance(value, dict) and '*' not in value:
            value['*'] = u''
        return key, value
    elif len(path) == 5 and key in ['alias', 'label', 'description']:
        key = value['language']
        return key, value
    elif (key == 'property' and len(path) in [5, 10] and
            ('claim' in value or 'snak' in value)):
        key = value['id']
        if 'claim' in value:
            return key, value['claim']
        else:
            return key, value['snak']
    elif len(path) == 5 and key == 'sitelink':
        key = value['site']
        return key, value
    elif len(path) > 3 and isinstance(value, dict) and len(value.keys()) == 1:
        key2 = value.keys()[0]
        if isinstance(value[key2], list):
            return key, value[key2]
        else:
            return key, value.values()
    elif (len(path) > 3 and isinstance(value, list) and len(value) == 1 and
            isinstance(value[0], list)):
        pywikibot.warning('found a list with an inner list')
        return key, value[0]
    elif value is None:
        return None
    else:
        return key, value


def xml_to_json(rawdata):
    """Convert MediaWiki XML to MediaWiki JSON."""
    rawdata = rawdata.encode('utf-8')
    d = xmltodict.parse(
        rawdata,
        attr_prefix='',
        cdata_separator='',
        cdata_key='*',
        postprocessor=xml_postprocessor)

    d = d['api']
    rawdata = json.dumps(d, indent=4)
    return rawdata
