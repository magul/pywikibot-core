#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script that adds claims to Wikidata items based on categories.

------------------------------------------------------------------------------

Usage:

python claimit.py [pagegenerators] P1 Q2 P123 Q456

You can use any typical pagegenerator to provide with a list of pages.
Then list the property-->target pairs to add.

------------------------------------------------------------------------------

For geographic coordinates:

python claimit.py [pagegenerators] P625 [lat-dec],[long-dec],[prec]

[lat-dec] and [long-dec] represent the latitude and longitude respectively,
and [prec] represents the precision. All values are in decimal degrees,
not DMS. If [prec] is omitted, the default precision is 0.0001 degrees.

Example:

python claimit.py [pagegenerators] P625 -23.3991,-52.0910,0.0001

------------------------------------------------------------------------------

By default, claimit.py does not add a claim if one with the same property
already exists on the page. To override this behavior, use the 'exists' option:

python claimit.py [pagegenerators] P246 "string example" -exists:p

Suppose the claim you want to add has the same property as an existing claim
and the "-exists:p" argument is used. Now, claimit.py will not add the claim
if it has the same target, source, and/or the existing claim has qualifiers.
To override this behavior, add 't' (target), 's' (sources), or 'q' (qualifiers)
to the 'exists' argument.

For instance, to add the claim to each page even if one with the same
property, target, and qualifiers already exists:

python claimit.py [pagegenerators] P246 "string example" -exists:ptq

Note that the ordering of the letters in the 'exists' argument does not matter,
but 'p' must be included.

"""
#
# (C) Legoktm, 2013
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import copy
import sys

import pywikibot

from pywikibot import pagegenerators, WikidataBot

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

if sys.version_info[0] > 2:
    unicode = str

# This is required for the text that is shown when you run this script
# with the parameter -help or without parameters.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

EXISTS_HELP_MSG = ("Append '%s' to the -exists: argument "
                   "to override this behavior.")


class ClaimRobot(WikidataBot):

    """
    A bot to add Wikidata claims with a client page as a source.

    FIXME: Only the claim target and page source are properly checked in the
    'exists' algorithm.  Qualifiers and other sources on the claims are added,
    but are not used in the 'exists' checking algorithm. T76547.
    """

    def __init__(self, generator, claims, exists_arg=None):
        """
        Constructor.

        @param generator: A generator that yields Page objects.
        @param claims: A list of wikidata claims
        @param exists_arg: String specifying how to handle duplicate claims

        """
        super(ClaimRobot, self).__init__()
        self.generator = generator
        self.claims = claims
        self.cacheSources()
        if not exists_arg:
            self.exists_arg = set()
        else:
            self.exists_arg = set(exists_arg)
            pywikibot.output('\'exists\' argument set to \'%s\''
                             % ','.join(sorted(self.exists_arg)))
            if set(['s', 'q']) & self.exists_arg:
                for claim in self.claims:
                    if claim.sources or claim.qualifiers:
                        pywikibot.warning("%s 'exists' detection does not support claims with sources or qualifiers.")

    def treat(self, page, item):
        """Treat each page."""
        self.current_page = page

        if not item:
            return

        # A generator might yield pages from multiple languages
        source = self.getSource(page.site)

        # getSource may not know about the site of this page.
        if not source and 's' not in self.exists_arg:
            pywikibot.log(
                ('Skipping %s because the source could not be determined for '
                 '%s.\n' + EXISTS_HELP_MSG)
                % (item.title(), page.title(), 's'))
            return

        for claim in self.claims:
            # Clone, so attributes modified are not retained.
            claim = copy.deepcopy(claim)

            if source:
                claim.sources.append(
                    OrderedDict({source.getID(): [source]}))

            # Check if claim with same property is desired
            exists_result = self.check_exists(item, claim)
            if exists_result:
                pywikibot.output(
                    'Failed exists checks. Use -exists:%s to override.'
                    % ''.join(sorted(self.exists_arg | exists_result)))
            else:
                pywikibot.output('Adding %s --> %s'
                                 % (claim.getID(), claim.getTarget()))

                item.addClaim(claim)
                if source:
                    claim.addSource(source)

    def check_exists(self, item, claim):
        """
        Check the exists options to determine whether additional claim allowed.

        @param item: The item to add the claim to
        @type item: ItemPage
        @param claim: A potential claim to add to item with the same property
        @type claim: Claim
        @rtype: True or set of exists flags
        """
        if 'p' not in self.exists_arg:
            if claim.getID() in item.claims:
                pywikibot.log('Skipping %s because claim with same property already exists' % (claim.getID(),))
                pywikibot.log('Use the -exists:p option to override this behavior')
                return set(['p'])
            else:
                return set()

        existing_claims = item.claims[claim.getID()]

        # Checking existing claims of same property on the item
        exists_result = set()
        dup = False
        for existing in existing_claims:
            # If some attribute of the claim being added matches some
            # attribute in an existing claim of the same property, skip
            # the claim, unless the 'exists' argument overrides it.
            if claim.getTarget() == existing.getTarget():
                dup = True
                if 't' not in self.exists_arg:
                    pywikibot.log('Skipping %s because claim with same target already exists' % (claim.getID(),))
                    pywikibot.log('Append \'t\' to the -exists argument to override this behavior')
                    exists_result.add('t')

            # FIXME: exists options 's' and 'q' only work correctly for the
            # page source and no qualifiers respectively, which is all the
            # command line parameters currently permit.

            # The claim may already have sources if instantiated from another
            # script.  If run via the command line, the claim has no sources,
            # other than the last item in sources which is the is page.site.

            if 's' not in self.exists_arg and not existing.getSources():
                pywikibot.log('Skipping %s because claim without source already exists' % (claim.getID(),))
                pywikibot.log('Append \'s\' to the -exists argument to override this behavior')
                exists_result.add('s')

            elif ('s' not in self.exists_arg
                    and claim.sources[-1].values()[0][0].getTarget()
                       in get_item_targets(existing.getSources())):
                pywikibot.log('Skipping %s because claim with the same page site already exists' % (claim.getID(),))
                pywikibot.log('Append \'s\' to the -exists argument to override this behavior')
                exists_result.add('s')

            # If run via the command line, the claim has no qualifiers.
            if ('q' not in self.exists_arg and not existing.qualifiers):
                pywikibot.log('Skipping %s because claim without qualifiers already exists' % (claim.getID(),))
                pywikibot.log('Append \'q\' to the -exists argument to override this behavior')
                exists_result.add('q')

        if dup and not exists_result:
            pywikibot.warning('Adding duplicate value to %s.' % claim.getID())

        return exists_result


def listsEqual(list1, list2):
    """
    Return true if the lists are probably equal, ignoring order.

    Works for lists of unhashable items (like dictionaries).
    Does not currently work, as it depends on a __eq__ operator
    being created for Claim. T76615
    """
    if len(list1) != len(list2):
        return False
    if sorted(list1) != sorted(list2):
        return False
    for item in list1:
        if item not in list2:
            return False
    return True


def get_item_targets(sources):
    """Return a list of all wikibase-item claim targets in sources."""
    return [claim.getTarget() for source in sources
            for claims in source.values()
            for claim in claims
            if claim.type == 'wikibase-item']


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
    gen = pagegenerators.GeneratorFactory()

    for arg in local_args:
        # Handle args specifying how to handle duplicate claims
        if arg.startswith('-exists:'):
            exists_arg = arg.split(':')[1].strip('"')
            continue
        # Handle page generator args
        if gen.handleArg(arg):
            continue
        commandline_claims.append(arg)
    if len(commandline_claims) % 2:
        raise ValueError  # or something.

    claims = list()
    repo = pywikibot.Site().data_repository()
    for i in range(0, len(commandline_claims), 2):
        claim = pywikibot.Claim(repo, commandline_claims[i])
        if claim.type == 'wikibase-item':
            target = pywikibot.ItemPage(repo, commandline_claims[i + 1])
        elif claim.type == 'string':
            target = commandline_claims[i + 1]
        elif claim.type == 'globe-coordinate':
            coord_args = [float(c) for c in commandline_claims[i + 1].split(',')]
            if len(coord_args) >= 3:
                precision = coord_args[2]
            else:
                precision = 0.0001  # Default value (~10 m at equator)
            target = pywikibot.Coordinate(coord_args[0], coord_args[1], precision=precision)
        else:
            raise NotImplementedError(
                "%s datatype is not yet supported by claimit.py"
                % claim.type)
        claim.setTarget(target)
        claims.append(claim)

    generator = gen.getCombinedGenerator()
    if not generator:
        # show help text from the top of this file
        pywikibot.showHelp()
        return

    bot = ClaimRobot(generator, claims, exists_arg)
    bot.run()

if __name__ == "__main__":
    main()
