#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script that adds claims to Wikidata items based on a tab-separated table of values.

It is heavily influenced by claimit.py.
------------------------------------------------------------------------------

Usage:

    python pwb.py tsv_claims -tsv <tsvFile>

Where
<tsvFile> is a tab-delimited file in this format:
  <Q-number> [<P-number> <Value>]+
<Q-number> := "Q[0-9]+", referring to an existing WD item
<P-number> := "P[0-0]+", referring to an existing WD property
<Value> := "{<coord>|<date>|<quantity>}[@<sourceP>:<sourceQ>]"  is a
  specification for a value for <P-number>, with optional source specification
<sourceP> is the P-number like P143 (imported From)
<sourceQ> is a Q-number like Q465 (DBpedia)
<coord> :=  see 'geographic coordinates', below
<date> := [watch this space]
<quantity> := "<number>:<units of measure Q>"
<units of measure Q> is the Q-number of a unit of measure such as Q25343
  (sq. meters)


------------------------------------------------------------------------------

For geographic coordinates:

    <Q number> P625 [lat-dec],[long-dec],[prec]

[lat-dec] and [long-dec] represent the latitude and longitude respectively,
and [prec] represents the precision. All values are in decimal degrees,
not DMS. If [prec] is omitted, the default precision is 0.0001 degrees.

Example:

    <Q number> P625 -23.3991,-52.0910,0.0001@P143:Q465


------------------------------------------------------------------------------

By default, tsv_claims.py does not add a claim if one with the same property
already exists on the page. To override this behavior, use the 'exists' option:

     <some item>  P246 "string example" -exists:p

Suppose the claim you want to add has the same property as an existing claim
and the "-exists:p" argument is used. Now, tsv_claims.py will not add the claim
if it has the same target, sources, and/or qualifiers as the existing claim.
To override this behavior, add 't' (target), 's' (sources), or 'q' (qualifiers)
to the 'exists' argument.

For instance, to add the claim to each page even if one with the same
property, target, and qualifiers already exists:

    <Q-number>  P246 "string example" -exists:ptq

Note that the ordering of the letters in the 'exists' argument does not matter,
but 'p' must be included.
"""

# NOTE: this code owes heavily to 'claimit.py'
# by Legoktm, 2013 and
# Pywikibot team, 2013-2014
# Adapted to the current application by Eric D. Scott (lisp.hippie)
#
# Distributed under the terms of the MIT license.

# Version 2/3 interoperability...
from __future__ import absolute_import, unicode_literals

from future.builtins.disabled import (reduce)

from future.builtins.iterators import map

from functools import reduce

#__version__ = '$Id$'

import codecs

import pywikibot

from pywikibot import pagegenerators, WikidataBot, config

# This is required for the text that is shown when you run this script
# with the parameter -help or without parameters.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

class TsvClaimRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    def __init__(self, generator, item_to_claim_to_source, exists_arg=''):
        """
        Constructor.

        Arguments:
            * generator    - A tsv generator G =yield=> [<page>, ...]
            * item_to_claim_to_source {<q number> : {<claim> : <source claim>, ...}, ...}
            * exists_arg   - String specifying how to handle duplicate claims

         Where
        <page> is an instance of Page.
        <claim> is an instance of Claim.
        <source claim> is a claim with a predicate like P143 (imported from)
          and a target derived from something like Q465 (DBpedia).
        """
        super(TsvClaimRobot, self).__init__(use_from_page=None)
        self.generator = generator
        self.exists_arg = exists_arg
        self.item_to_claim_to_source = item_to_claim_to_source
        self.cacheSources()
        if self.exists_arg:
            pywikibot.output('\'exists\' argument set to \'%s\'' % self.exists_arg)

    def treat(self, page, item):
        """Treat each page."""
        self.current_page = page

        if item:
            q_number = item.getID()

            for claim in self.item_to_claim_to_source[q_number].keys():
                skip = False
                # If claim with same property already exists...
                if claim.getID() in item.claims:
                    if self.exists_arg is None or 'p' not in self.exists_arg:
                        pywikibot.log(
                            'Skipping %s because claim with same property '
                            'already exists' % (claim.getID(),))
                        pywikibot.log(
                            'Use -exists:p option to override this behavior')
                        skip = True
                    else:
                        # Existing claims on page of same property
                        existing_claims = item.claims[claim.getID()]
                        for existing in existing_claims:
                            skip = True  # Default value
                            # If some attribute of the claim being added
                            # matches some attribute in an existing claim of
                            # the same property, skip the claim, unless the
                            # 'exists' argument overrides it.
                            if (claim.getTarget() == existing.getTarget() and
                                    't' not in self.exists_arg):
                                pywikibot.log(
                                    'Skipping %s because claim with same target already exists'
                                    % (claim.getID(),))
                                pywikibot.log(
                                    'Append \'t\' to -exists argument to override this behavior')
                                break
                            if (listsEqual(claim.getSources(), existing.getSources()) and
                                    's' not in self.exists_arg):
                                pywikibot.log(
                                    'Skipping %s because claim with same sources already exists'
                                    % (claim.getID(),))
                                pywikibot.log(
                                    'Append \'s\' to -exists argument to override this behavior')
                                break
                            if (listsEqual(claim.qualifiers, existing.qualifiers) and
                                    'q' not in self.exists_arg):
                                pywikibot.log(
                                    'Skipping %s because claim with same '
                                    'qualifiers already exists' % (claim.getID(),))
                                pywikibot.log(
                                    'Append \'q\' to -exists argument to override this behavior')
                                break
                            skip = False
                if not skip:
                    pywikibot.output('Adding %s --> %s'
                                     % (claim.getID(), claim.getTarget()))
                    item.addClaim(claim)
                    # A generator might yield pages from multiple languages
                    source = self.getSource(page.site)
                    if source:
                        claim.addSource(source, bot=True)
                    elif claim in self.item_to_claim_to_source[q_number]:
                        claim.addSource(self.item_to_claim_to_source[q_number][claim])
                    # TODO FIXME: We need to check that we aren't adding a
                    # duplicate


def listsEqual(list1, list2):
    """
    Return true if the lists are probably equal, ignoring order.


    Works for lists of unhashable items (like dictionaries).
    """
    if len(list1) != len(list2):
        return False
    if sorted(list1) != sorted(list2):
        return False
    for item in list1:
        if item not in list2:
            return False
    return True

def chunk(sequence, size):
    """
    Return [[<firstItem>, ...<size'th Item>], ...], segments of <sequence>.


    Where:
    <sequence> is a sequence of items
    <size> is the maximum size of each chunk
    """
    def chunker():
        # version compatibility assuming it's either 2 or 3...
        for i in range(0, len(sequence), size):
            yield sequence[i:i + size]
    return list(chunker())

def parse_value_source_spec(valueSourceSpec):
    """Return [<valueSpec>, <sourceSpec>]."""

    atSplit = valueSourceSpec.split('@')
    assert (len(atSplit) < 3)
    return atSplit + ([] if len(atSplit) == 2 else [None])

def get_records(tsvFile):
    """
    Return a generator G => [<record>, ...] parsed from <tsvFile>.


    Where
    <tsvFile> is a pathname to a tab-delimited text file.
    <record> := [<Q>, <P1>, <V1>, <P2>, <V2>, ....]
    """
    f = codecs.open(tsvFile, 'r', config.textfile_encoding)
    linkmatch = None
    for linkmatch in pywikibot.link_regex.finditer(f.read()):
        # If the link is in interwiki format, the Page object may reside
        # on a different Site than the default.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        raise NotImplemented()
        # yield pywikibot.Page(pywikibot.Link(linkmatch.group("title"), site))
    if linkmatch is None:
        f.seek(0)
        for line in f:
            rec = map(lambda x: x.strip(), line.split('\t'))
            yield rec
    f.close()


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    exists_arg = ''
    commandline_claims = list()

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    [arg, tsvFile] = local_args[0].split(':')
    assert tsvFile
    gen = pagegenerators.GeneratorFactory()

    for arg in local_args:
        # Handle args specifying how to handle duplicate claims
        if arg.startswith('-exists:'):
            raise NotImplemented()
            exists_arg = arg.split(':')[1].strip('"')
            continue
        # Handle page generator args
        if gen.handleArg(arg):
            continue
        commandline_claims.append(arg)

    assert not commandline_claims

    repo = pywikibot.Site().data_repository()

    assert repo

    def infer_target(claimType, propertySpec, valueSpec):
        # returns target appropriate to <claimType> and <valueSpec>
        # where
        # <claimType> is a <claim>.type, for some <claim>
        # <valueSpec> should be a string appropriate to <claimType>
        if claimType == 'wikibase-item':
            return pywikibot.ItemPage(repo, valueSpec)
        elif claimType == 'string':
            return propertySpec
        elif claimType == 'globe-coordinate':
            coord_args = [float(c) for c in valueSpec.split(',')]
            if len(coord_args) >= 3:
                precision = coord_args[2]
            else:
                precision = 0.0001  # Default value (~10 m at equator)
            return pywikibot.Coordinate(coord_args[0], coord_args[1], precision=precision)
        elif claimType == "quantity":
            [quantity, unitQ] = valueSpec.split(':')
            # [] TODO: check these formats
            unitUri = "http://www.wikidata.org/entity/%s" % unitQ
            return pywikibot.WbQuantity(quantity, unit=unitUri)
        else:
            raise NotImplementedError(
                "%s datatype is not yet supported by claimit.py"
                % claimType)

    def infer_source_claim(sourceSpec):
        # returns a <source claim> to be asserted as source of the main claim, or None
        # based on <sourceSpec>
        # where
        # <sourceSpec> is a string :~ "<sourceP>:<sourceQ>"
        [sourceP, sourceQ] = sourceSpec.split(':')
        # [] TODO: check these formats and maybe check against a list
        #   of valid values
        if sourceP and sourceQ:
            sourceClaim = pywikibot.Claim(repo, sourceP)
            sourceItem = pywikibot.ItemPage(repo, sourceQ)
            sourceClaim.setTarget(sourceItem)
            return sourceClaim

    def collect_items(accum, nextRecord):
        # Returns {<q number> : {<claim> : <sourceClaim>, ...}, ...}
        # where
        # nextRecord := [<Q>, <p1>, <v1>, <p2>, <v2>, ...]
        #   as parsed from  a line of tab-delimited file
        def collect_claims(accum, nextProperty_value):
            # returns {<claim> : <sourceClaim>, ...}
            # where
            # <nextProperty_value> := [<propertySpec>, <valueSpec>]
            # <sourceClaim> is a claim, or None if there is no spec.
            [propertySpec, valueSourceSpec] = nextProperty_value
            [valueSpec, sourceSpec] = parse_value_source_spec(valueSourceSpec)
            claim = pywikibot.Claim(repo, propertySpec)
            claim.setTarget(infer_target(claim.type, propertySpec, valueSpec))
            sourceClaim = infer_source_claim(sourceSpec)
            accum[claim] = sourceClaim
            return accum
        nextRecord = list(nextRecord)  # unpack imap object
        q_number = nextRecord[0]
        p_spex = nextRecord[1:]
        assert (len(p_spex) >= 2) and (len(p_spex) % 2 == 0)
        itemClaims = accum[q_number] if q_number in accum else {}
        accum[q_number] = reduce(collect_claims,
                                 chunk(p_spex, 2),  # [[p, v], ...]
                                 itemClaims)
        return accum

    item_to_claim_to_source = reduce(collect_items,
                                     get_records(tsvFile),
                                     {})
    generator = gen.getCombinedGenerator()
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False
    bot = TsvClaimRobot(generator, item_to_claim_to_source, exists_arg)
    bot.run()
    return True

if __name__ == "__main__":
    main()
