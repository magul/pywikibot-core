# -*- coding: utf-8 -*-
"""Wikibase diff module."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import re
import sys

if sys.version_info[0] > 2:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

try:
    from pycountry import languages
except ImportError:
    languages = None

from pywikibot.diff import DictPatchManager
from pywikibot.page import ItemPage, PropertyPage


class WikibasePatchManager(DictPatchManager):
    """Similar to DictPatchManagers, but generates diffs in more friendly format."""

    iso8601 = re.compile((r"^(?P<full>(\+?(?P<year>-?\d*)([/-]?(?P<mon>(0[0-9])|(1[012]))"
                          "([/-]?(?P<mday>(0[0-9])|([12]\d)|(3[01])))?)?(?:T(?P<hour>([01][0-9])"
                          "|(?:2[0123]))(\:?(?P<min>[0-5][0-9])(\:?(?P<sec>[0-5][0-9]"
                          "([\,\.]\d{1,10})?))?)?(?:Z|([\-+](?:([01][0-9])|(?:2[0123]))"
                          "(\:?(?:[0-5][0-9]))?))?)?))$"))

    def __init__(self, dict_a, dict_b, site):
        """
        Constructor.

        @param dict_a: first wikibase item to compare.
        @param dict_b: second wikibase item to compare.
        @param site: DataSite used to gather additional information while generating diffs.
        """
        self.site = site
        DictPatchManager.__init__(self, dict_a, dict_b)

    def add_dict_hunks(self, a, b, key_prefix=None, key_parts=[], sort_keys=True):
        """
        Generate friendly formatted diff between two dicts.

        @param a: first dict.
        @param b: second dict.
        @param key_prefix: prefix to add to each key (used when displayed).
        @param key_parts: list of keys, indicating location of dictionaries relative to the root.
        @param sort_keys: whether to sort keys when creating diff.
        """
        if a != b:
            a_text = b_text = None

            if len(key_parts) == 3 and key_parts[0] == 'claims':
                property_id = key_parts[1]
                label = self.get_property_label(property_id)
                key_prefix = '%s.%s (%s)[%i]' % (key_parts[0], property_id, label, key_parts[2])
                a_text = self.get_property_description(a)
                b_text = self.get_property_description(b)

            if ((len(key_parts) == 3 and key_parts[0] == 'aliases') or
               (len(key_parts) == 2 and key_parts[0] == 'labels')):
                a_text = self.get_label_description(a)
                b_text = self.get_label_description(b)
                key_prefix = key_parts[0]

            if a_text != b_text:
                self.add_hunk(a_text, b_text, key_prefix, add_quotes=False)
                return

        DictPatchManager.add_dict_hunks(self, a, b, key_prefix, key_parts, sort_keys)

    @staticmethod
    def format_timestamp(timestamp):
        """
        Convert timestamp to a friendly format.

        Converts only iso8601 timestamps.
        If provided timestamp doesn't match iso8601, then does not change anything.

        @param timestamp: timestamp to convert
        @returns converted timestamp.
        @rtype str
        """
        try:
            date = WikibasePatchManager.iso8601.match(timestamp).groupdict()
        except AttributeError:
            return timestamp

        if date['year'][0] == '-':
            return '%s BC' % date['year'][1:]

        if date['mon'] == '00':
            date['mon'] = '01'

        if date['mday'] == '00':
            date['mday'] = '01'

        year = int(date['year'])
        month = int(date['mon'])
        day = int(date['mday'])
        hour = int(date['hour'])
        minute = int(date['min'])
        second = int(date['sec'])

        if hour == 0 and minute == 0 and second == 0:
            if month == 1 and day == 1:
                return '%s AD' % year
            else:
                return '%02i/%02i/%i' % (month, day, year)
        else:
            return timestamp

    @staticmethod
    def get_label_description(label):
        """
        Generate description for entity label.

        @param label: label of entity.
        @rtype str or None, if label is None
        """
        if not label:
            return None

        value = label['value']
        lang_code = label['language']

        if languages:
            try:
                lang = languages.get(alpha_2=lang_code).name
            except KeyError:
                lang = '[Unknown language: %s]' % lang_code
        else:
            lang = lang_code

        return '%s (in %s)' % (value, lang)

    def get_property_description(self, property):
        """
        Generate description for entity property.

        @param property: property of entity.
        @rtype str or None, if property is None
        """
        if not property:
            return None

        if 'mainsnak' in property:
            mainsnak = property['mainsnak']
        else:
            mainsnak = property

        if mainsnak['snaktype'] == 'novalue':
            return 'No data'

        if 'datavalue' not in mainsnak:
            return 'No data'

        datatype = mainsnak['datatype']
        datavalue = mainsnak['datavalue']
        value = datavalue['value']

        description = None

        if datatype == 'commonsMedia':
            description = '%s (Commons Media)' % value

        elif datatype in ('string', 'external-id'):
            description = value

        elif datatype == 'quantity':
            description = value['amount']
            if 'lowerBound' in value and 'upperBound' in value:
                lower_bound = value['lowerBound']
                upper_bound = value['upperBound']
                description += ' [%s...%s]' % (lower_bound, upper_bound)

        elif datatype == 'globe-coordinate':
            longitude = value['longitude']
            latitude = value['latitude']
            description = 'lat: %d long: %d' % (latitude, longitude)
            if 'altitude' in value:
                altitude = value['altitude']
                if altitude:
                    description += ' alt: %d' % altitude
            if 'precision' in value:
                precision = value['precision']
                if precision > 0:
                    description += ' ±%s' % format(value['precision'], 'g')
            description += ' (on %s)' % self.get_entity_label_by_url(value['globe'])

        elif datatype == 'wikibase-item':
            if 'id' in value:
                item_id = value['id']
            else:
                item_id = 'Q%i' % value['numeric-id']

            description = self.get_item_title(item_id)

        elif datatype == 'time':
            time = self.format_timestamp(value['time'])
            calendarmodel = self.get_entity_label_by_url(value['calendarmodel'])
            description = '%s (%s)' % (time, calendarmodel)

        if not description:
            return '[Unknown property type: %s]' % datatype

        qualifiers_text = []
        if 'qualifiers' in property:
            for qid in property['qualifiers']:
                for element in property['qualifiers'][qid]:
                    qualifiers_text.append(self.get_property_description(element))

        if len(qualifiers_text) > 0:
            description += ' (%s)' % (', '.join(qualifiers_text))

        return description

    def get_entity_label_by_url(self, url):
        """
        Return entity label (in English) by provided entity url.

        @param url: url of entity
        @rtype str
        """
        return self.get_item_title(urlparse(url).path.replace('/entity/', ''))

    def get_property_label(self, id):
        """
        Return property label (in English), requested from wikibase site.

        @param id: id of property
        @rtype str
        """
        try:
            labels = PropertyPage(self.site, id).labels
            if 'en' in labels:
                return labels['en']['value']
            else:
                return '[No English label]'
        except KeyError:
            return '[Unknown Property]'

    def get_item_title(self, id):
        """
        Return item title (in English), requested from wikibase site.

        @param id: id of item
        @rtype str
        """
        try:
            labels = ItemPage(self.site, id).get()['labels']
            if 'en' in labels:
                return labels['en']
            else:
                return '[No English label]'
        except KeyError:
            return '[Unknown Item]'
