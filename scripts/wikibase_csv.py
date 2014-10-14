#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Robot to import a CSV file into a Wikibase repository.

Requires an input CSV using tabs as delimiter (TSV), containing a table where
the first row is the header of the columns and each column is one of:
* title (label or alias), description, id (e.g. 'Q42'), uselang (e.g. 'fr'),
* property id, e.g. 'P31',
* property used as reference for a previous property, in the form 'P31_R_P854',
* same for qualifiers: 'P31_Q_P#', or,
* if they apply to all statements in the row, just 'Q_P#' or 'R_P#' (careful!).

Each row must be about a single item, though an item may have multiple rows
about it. Within a row, each column applies to all the others where possible:
* title and/or id define the item for which all other columns are used;
* uselang applies to the label, alias and description [anything else?],
* references and qualifiers if specified as above.

Empty cell means lack of information.
In certain circumstances, the program may fill blanks with information retrieved
from Wikibase while interacting with it.

As for dates, precision is guessed by pywikibot.WbTime.fromTimestr.

"""
# (C) Pywikibot team and Fondazione BEIC, 2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.0.1'

from collections import namedtuple
import re
import sys

if sys.version_info[0] > 2:
    import csv
else:
    try:
        import unicodecsv as csv
    except ImportError:
        print('%s: unicodecsv package required for Python 2' % __name__)
        sys.exit(1)

import pywikibot
from pywikibot import pagegenerators, WikidataBot
from pywikibot.page import ItemPage, Property, Claim
# TODO: Decide what/how to reuse code with other import scripts.
# from scripts.harvest_template import HarvestRobot
# from scripts.claimit import ClaimRobot


class WikibaseCSVBot(WikidataBot):

    """A bot to create new items."""

    def __init__(self, generator, **kwargs):
        """Only accepts options defined in availableOptions."""
        self.availableOptions.update({
            'csv': 'input.csv',
        })

        super(WikibaseCSVBot, self).__init__(**kwargs)
        self.generator = pagegenerators.PreloadingGenerator(generator)
        # FIXME: will not work if the repo is not client of itself.
        # Force the user to start from an actual client, and use that
        # client in get_current_entity() as well?
        self.repo = pywikibot.Site().data_repository()
        self.filename = self.getOption('csv')
        self.summary = u'Import CSV data'

        [store, header] = self.read_CSV(self.filename)
        # TODO: Normalise the header to lowercase or uppercase?
        if not store or not header:
            pywikibot.error(u'Cannot import CSV')
            sys.exit(1)
            return

        for row in store:
            pywikibot.output(u'Now doing "%s"' % row.title)
            current = self.get_current_entity(row)
            self.prepare_entity(current, header, row)
            # Save the updated item into the wiki.
            # item.editEntity(data=item.toJSON(), summary=self.summary)
            # TODO: Also output/merge the updated data to CSV?

    def read_CSV(self, filename):
        """Read the CSV."""
        if self.filename.endswith('.bz2'):
            import bz2
            f = bz2.BZ2File(self.filename)
        elif self.filename.endswith('.gz'):
            import gzip
            f = gzip.open(self.filename)
        else:
            # Assume it's an uncompressed CSV file
            f = open(self.filename, 'r')

        # FIXME: f itself should be properly encoded, no "encoding" in py3 csv
        source = csv.reader(f, delimiter='\t', encoding='utf-8')
        header = source.next()
        store = None
        if self.validate_header(header):
            store = namedtuple(u'store', u', '.join(header))
            store = [store(*row) for row in source]
            f.close()
            return store, header
        else:
            f.close()
            return None, None

    def validate_header(self, header):
        """Check the CSV has columns as we need them."""
        if 'id' not in header:
            pywikibot.error(u'We need Q# in column "id". Empty to create from scratch.')
            return False
        if ('title' in header or 'aliases' in header) and 'uselang' not in header:
            pywikibot.error(u'You specified title or alias, but not uselang.')
            return False

        for cell in header:
            if cell in ['title', 'aliases', 'uselang', 'id']:
                continue
            isprop = re.match(r'P\d+', cell, re.I)
            isrefqual = re.match(r'(P\d+_)?[QR]_P\d+', cell, re.I)
            if isprop:
                continue
            elif isrefqual:
                if not isrefqual.group(1):
                    continue
                elif isrefqual.group(1).lower() in [i.lower() for i in header]:
                    continue
                else:
                    pywikibot.error(u'Column %s: %s is not defined' %
                                    (cell, isrefqual.group(1)))
                    return False

            pywikibot.error(u'Column %s was not recognised' % cell)
            return False

        return True

    def get_current_entity(self, row):
        """Return any existing item matching this CSV row."""
        # TODO: should also use label or perhaps sitelink,
        # to find existing items and merge data into them.
        # May require pywikibot to implement wbsearchentities
        item = None
        if row.id:
            item = pywikibot.ItemPage(self.repo, 'Q%d' % row.id)
        elif row.title and row.uselang:
            item = self.guess_item(row.title, row.uselang)

        if item and item.exists():
            pywikibot.output(u'Found an item for "%s": %s.' % (row.title, item.getID()))
            item.get()
            # TODO: if the item exists, we might want to fetch
            # some or all of the statements and write them back
            # into the source CSV or a clone CSV, to allow syncs.
        else:
            pywikibot.output(u'No item found for "%s", will create.' % row.title)
            item = None
        return item

    def guess_item(self, title, uselang):
        # FIXME: replace with proper search or don't hardcode Wikipedia
        pywikibot.output(u'Looking for item via %s.wikipedia' % uselang)
        wikipedia = pywikibot.Site(uselang, u'wikipedia')
        article = pywikibot.Page(wikipedia, title)
        if article.isRedirectPage():
            article = article.getRedirectTarget()
        if article.isDisambig():
            pywikibot.output(u'"%s" is a disambig, will create new item.' % title)
            return None
        if article.exists():
            item = ItemPage.fromPage(article)
        else:
            item = None
        return item

    def prepare_entity(self, item, header, row):
        """Take any current data and merge CSV row into it."""
        if item and item.exists():
            if row.title and row.uselang:
                # If the item exists, it must have at least one label.
                # It may have none in our language, though.
                if row.uselang not in item._content['labels'].keys():
                    item._content['labels'][row.uselang] = [row.title]
                elif item._content['labels'][row.uselang]['value'] != row.title:
                    alias = {'language': row.uselang, 'value': row.title}
                    if not hasattr(item._content, 'aliases'):
                        item._content['aliases'] = {}
                    if row.uselang not in item._content['aliases'].keys():
                        item._content['aliases'][row.uselang] = alias
                    elif row.title not in item._content['aliases'][row.uselang]:
                        item._content['aliases'][row.uselang].append(alias)
        else:
            if row.title and row.uselang:
                # Anything to borrow from NewItemRobot? Seems not, that's only
                # to create new items from existing pages (sitelinks).
                pywikibot.output(u'Create item: %s' % row.title)
                # FIXME: avoid creating duplicates
                item = ItemPage(self.repo, '-1')
                data = {'labels': {row.uselang: {'language': row.uselang, 'value': row.title}}}
                # Return the data and edit in __init__?
                item.editEntity(data, summary=self.summary)
                # item.editLabels({row.uselang: row.title})
            else:
                pywikibot.output(u'Cannot create item for this row: label or language missing')
                return

        for cell in header:
            # FIXME: duplicate regex matching
            isprop = None
            isrefqual = None
            isprop = re.match(r'(P\d+)', cell, re.I)
            isrefqual = re.match(r'(?:P\d+_)?[QR]_(P\d+)', cell, re.I)
            val = getattr(row, cell)
            if cell in ['title', 'aliases', 'uselang', 'id']:
                continue
            if val == u'':
                pywikibot.output(u'Empty string, skip %s for this row.' % cell)
                continue
            if isrefqual:
                # Was hopefully already added as part of previous claims.
                continue
            elif isprop:
                pid = isprop.group(1)
                claim = self.make_claim(pid=pid, val=val, uselang=row.uselang)
                # TODO: figure out how to integrate existing statements.
                # Reuse ClaimRobot.treat() functionality?
                try:
                    if pid in item.claims.keys():
                        pywikibot.output(u'Property already used, skipping...')
                        continue
                except AttributeError:
                    # No claims at all, all good.
                    pass
                item.addClaim(claim, bot=True)

                # Look for references and qualifiers set in other columns
                # for this column's statements.
                for cell_son in header:
                    p = isprop.group(1)
                    isref = re.match(u'(?:%s_)?R_(P\d+)' % p, cell_son, re.I)
                    isqual = re.match(u'(?:%s_)?Q_(P\d+)' % p, cell_son, re.I)
                    # TODO: figure out whether to allow multi-statement
                    # references (e.g. item+url), which would use addSources
                    if isref:
                        ref = self.make_claim(pid=isref.group(1),
                                              val=getattr(row, cell_son),
                                              uselang=row.uselang)
                        claim.addSource(ref, bot=True)
                    elif isqual:
                        qual = self.make_claim(pid=isqual.group(1),
                                               val=getattr(row, cell_son),
                                               uselang=row.uselang)
                        claim.addQualifier(qual, bot=True)

                # We should be done with this statement and its accessories

        return item

    def make_claim(self, pid=None, val=None, uselang=None):
        """Produce a claim object from two strings, property ID and value."""
        prop = Property(self.repo, id=pid)
        claim = Claim(self.repo, prop.getID())
        pywikibot.output(u'Making claim: %s → %s' % (pid, val))

        if prop.type == 'time':
            # We let WbTime guess precision, but autodetection
            # looks for None which fromTimestr never sets.
            # TODO: tell about WbTime.FORMATSTR
            pywikibot.output(u'The property wants a WbTime.')
            value = pywikibot.WbTime.fromTimestr(val,
                                                 precision=None)
        elif prop.type == 'wikibase-item':
            pywikibot.output(u'The property wants an item.')
            try:
                value = ItemPage(self.repo, title=val)
            except pywikibot.exceptions.InvalidTitle:
                value = self.guess_item(val, uselang)
        else:
            pywikibot.output(u'The property wants whatever?')
            value = val

        try:
            claim.setTarget(value)
            return claim
        except ValueError:
            # TODO: more actionable error message
            pywikibot.error(u'Incorrect value %s' % val)
            return


def main():
    """Process global args and prepare generator args parser."""
    local_args = pywikibot.handle_args()
    # TODO: figure out whether/how to allow passing a generator and other options.
    gen = pagegenerators.GeneratorFactory()

    options = {}
    for arg in local_args:
        if arg.startswith('-csv:'):
            options['csv'] = arg[len('-csv:'):]
        elif not gen.handleArg(arg):
            options[arg[1:].lower()] = True

    generator = gen.getCombinedGenerator()
    # If not generator:
    if not options.get('csv'):
        pywikibot.error(u'You need to specify a CSV -csv. See -help for more.')
        return False

    bot = WikibaseCSVBot(generator, **options)
    bot.run()

if __name__ == '__main__':
    main()
