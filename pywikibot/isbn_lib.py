#!/usr/bin/python
# -*- coding: utf-8  -*-
"""ISBN rules library."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
import inspect
import os
from xml.etree.ElementTree import parse

from pywikibot import Error

# try foreign libraries
try:
    import stdnum.isbn
except ImportError:
    try:
        import isbnlib
    except ImportError:
        pass


class ValidationError(Error):

    """
    Invalid ISBN.

    This is for compatibility purpose with stdnum library.
    """


class InvalidIsbnException(ValidationError):

    """Invalid ISBN."""


class RangeMessage(object):

    """
    ISBN range message table from International ISBN Agency.

    source: https://www.isbn-international.org/range_file_generation
    """

    SOURCEFILE = 'RangeMessage.xml'
    ROOTTAG = 'ISBNRangeMessage'

    def __init__(self):
        """Constructor."""
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        source = parse(os.path.join(currentdir, self.SOURCEFILE))
        tree = source.getroot()
        assert tree.tag == self.ROOTTAG, (
            '{0} does not contain {1}'.format(self.SOURCEFILE, self.ROOTTAG))

        self.ranges = {}
        self.agency = {}
        self.prefix_lookup = {}
        for elem in tree:
            if elem.tag.startswith('Message'):
                setattr(self, elem.tag[len('Message'):], elem.text)
            elif elem.tag == 'EAN.UCCPrefixes':
                self.uccprefixes = [Prefix.text
                                    for Prefix, Agency, Rules in elem]
            elif elem.tag == 'RegistrationGroups':
                for Prefix, Agency, Rules in elem:
                    rules = []
                    for Range, Length in Rules:
                        length = int(Length.text)
                        if length:
                            low, high = Range.text.split('-')
                            low = low[:length]
                            high = high[:length]
                            rules.append((low, high))
                    p13, p10 = Prefix.text.split('-')
                    self.ranges[p10] = rules
                    self.prefix_lookup[p10] = p13
                    self.agency[Prefix.text] = Agency.text

_range_message = RangeMessage()  # global range message structure


class ISBN(object):

    """Abstract superclass."""

    def __init__(self):
        """Constructor."""
        self.range_message = _range_message

    def format(self):
        """Put hyphens into this ISBN number."""
        result = ''
        rest = ''
        prefix = '978'
        for digit in self.digits():
            rest += str(digit)
        # Determine the prefix (if any)
        for prefix in self.possiblePrefixes():
            if rest.startswith(prefix):
                result += prefix + '-'
                rest = rest[len(prefix):]
                break

        # Determine the group
        for groupNumber in self.range_message.ranges.keys():
            if self.range_message.prefix_lookup[groupNumber] != prefix:
                continue
            if rest.startswith(groupNumber):
                result += groupNumber + '-'
                rest = rest[len(groupNumber):]
                publisherRanges = self.range_message.ranges[groupNumber]
                break
        else:
            raise InvalidIsbnException('ISBN %s: group number unknown.'
                                       % self.code)

        # Determine the publisher
        for (start, end) in publisherRanges:
            length = len(start)  # NOTE: start and end always have equal length
            if rest[:length] >= start and rest[:length] <= end:
                result += rest[:length] + '-'
                rest = rest[length:]
                break
        else:
            raise InvalidIsbnException('ISBN %s: publisher number unknown.'
                                       % self.code)

        # The rest is the item number and the 1-digit checksum.
        result += rest[:-1] + '-' + rest[-1]
        self.code = result


class ISBN13(ISBN):

    """ISBN 13."""

    def __init__(self, code, checksumMissing=False):
        """Constructor."""
        super(ISBN13, self).__init__()
        self.code = code
        if checksumMissing or len(self.digits()) == 12:
            self.code += str(self.calculateChecksum())
        self.checkValidity()

    def possiblePrefixes(self):
        """Return possible prefixes."""
        return self.range_message.uccprefixes

    def digits(self):
        """Return a list of the digits in the ISBN code."""
        result = []
        for c in self.code:
            if c.isdigit():
                result.append(int(c))
            elif c != '-':
                raise InvalidIsbnException(
                    'The ISBN %s contains invalid characters.' % self.code)
        return result

    def checkValidity(self):
        """Check validity of ISBN."""
        if len(self.digits()) != 13:
            raise InvalidIsbnException('The ISBN %s is not 13 digits long.'
                                       % self.code)
        if self.calculateChecksum() != self.digits()[-1]:
            raise InvalidIsbnException('The ISBN checksum of %s is incorrect.'
                                       % self.code)

    def calculateChecksum(self):
        """
        Calculate checksum.

        See https://en.wikipedia.org/wiki/ISBN#Check_digit_in_ISBN_13
        """
        sum = 0
        for i in range(0, 13 - 1, 2):
            sum += self.digits()[i]
        for i in range(1, 13 - 1, 2):
            sum += 3 * self.digits()[i]
        return (10 - (sum % 10)) % 10


class ISBN10(ISBN):

    """ISBN 10."""

    def __init__(self, code):
        """Constructor."""
        super(ISBN10, self).__init__()
        self.code = code
        self.checkValidity()

    def possiblePrefixes(self):
        """Return possible prefixes."""
        return []

    def digits(self):
        """Return a list of the digits and Xs in the ISBN code."""
        result = []
        for c in self.code:
            if c.isdigit() or c in 'Xx':
                result.append(c)
            elif c != '-':
                raise InvalidIsbnException(
                    'The ISBN %s contains invalid characters.' % self.code)
        return result

    def checkChecksum(self):
        """Raise an InvalidIsbnException if the ISBN checksum is incorrect."""
        # See https://en.wikipedia.org/wiki/ISBN#Check_digit_in_ISBN_10
        sum = 0
        for i in range(0, 9):
            sum += (i + 1) * int(self.digits()[i])
        checksum = sum % 11
        lastDigit = self.digits()[-1]
        if not ((checksum == 10 and lastDigit in 'Xx') or
                (lastDigit.isdigit() and checksum == int(lastDigit))):
            raise InvalidIsbnException('The ISBN checksum of %s is incorrect.'
                                       % self.code)

    def checkValidity(self):
        """Check validity of ISBN."""
        if len(self.digits()) != 10:
            raise InvalidIsbnException('The ISBN %s is not 10 digits long.'
                                       % self.code)
        if 'X' in self.digits()[:-1] or 'x' in self.digits()[:-1]:
            raise InvalidIsbnException(
                'ISBN %s: X is only allowed at the end of the ISBN.'
                % self.code)
        self.checkChecksum()

    def toISBN13(self):
        """
        Create a 13-digit ISBN from this 10-digit ISBN.

        Adds the UCC prefix and recalculates the checksum.
        The hyphenation structure is taken from the format of the original
        ISBN number.

        @rtype: L{ISBN13}
        """
        old_code = self.code
        self.format()
        code = self.code[:-1]
        self.code = old_code
        agency = code.split('-')[0]
        prefix = self.range_message.prefix_lookup[agency]
        code = '{0}-{1}'.format(prefix, code)
        return ISBN13(code, checksumMissing=True)

    def format(self):
        """Format ISBN number."""
        # load overridden superclass method
        ISBN.format(self)
        # capitalize checksum
        if self.code[-1] == 'x':
            self.code = self.code[:-1] + 'X'


def validate(isbn):
    """Check whether an ISBN 10 or 13 is valid."""
    # isbnlib marks any ISBN10 with lowercase 'X' as invalid
    isbn = isbn.upper()
    try:
        stdnum.isbn
    except NameError:
        pass
    else:
        try:
            stdnum.isbn.validate(isbn)
        except stdnum.isbn.InvalidFormat as e:
            raise InvalidIsbnException(str(e))
        except stdnum.isbn.InvalidChecksum as e:
            raise InvalidIsbnException(str(e))
        except stdnum.isbn.InvalidLength as e:
            raise InvalidIsbnException(str(e))
        return True

    try:
        isbnlib
    except NameError:
        pass
    else:
        if isbnlib.notisbn(isbn):
            raise InvalidIsbnException('Invalid ISBN found')
        return True

    get_isbn(isbn)
    return True


def get_isbn(code):
    """Return an ISBN object for the code."""
    try:
        i = ISBN13(code)
    except InvalidIsbnException as e13:
        try:
            i = ISBN10(code)
        except InvalidIsbnException as e10:
            raise InvalidIsbnException(u'ISBN-13: %s / ISBN-10: %s'
                                       % (e13, e10))
    return i
