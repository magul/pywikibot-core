# -*- coding: utf-8  -*-
"""Tests for threading tools."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from tests.aspects import unittest, TestCase
import pywikibot.tools
from pywikibot.tools import intersect_generators


class BasicThreadedGeneratorTestCase(TestCase):

    """ThreadedGenerator test cases."""

    net = False

    def gen_func(self, iterable):
        for i in iterable:
            yield i

    class TestingThreadedGenerator(pywikibot.tools.ThreadedGeneratorBase):
        def generator(self):
            return self.iterable

    def test_run_old_from_iterable(self):
        iterable = 'abcd'
        thd_gen = pywikibot.tools.ThreadedGenerator(target=iterable)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))

    def test_run_old_from_gen_function(self):
        iterable = 'abcd'
        thd_gen = pywikibot.tools.ThreadedGenerator(target=self.gen_func,
                                                    args=(iterable,))
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))

    def test_run_new_from_iterable(self):
        iterable = 'abcd'
        thd_gen = pywikibot.tools.ThreadedGeneratorProperty(target=iterable)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))

    def test_run_new_from_gen_function(self):
        iterable = 'abcd'
        thd_gen = pywikibot.tools.ThreadedGeneratorMethod(target=self.gen_func,
                                                          args=(iterable,))
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))

    def test_run_new_from_subclass(self):
        iterable = 'abcd'
        thd_gen = BasicThreadedGeneratorTestCase.TestingThreadedGenerator()
        thd_gen.iterable = iterable
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))


class GeneratorIntersectTestCase(TestCase):

    """Base class for intersect_generators test cases."""

    def assertEqualItertools(self, gens):
        # If they are a generator, we need to convert to a list
        # first otherwise the generator is empty the second time.
        datasets = [list(gen) for gen in gens]

        set_result = set(datasets[0]).intersection(*datasets[1:])

        result = list(intersect_generators(datasets))

        self.assertEqual(len(set(result)), len(result))

        self.assertCountEqual(result, set_result)


class BasicGeneratorIntersectTestCase(GeneratorIntersectTestCase):

    """Disconnected intersect_generators test cases."""

    net = False

    def test_intersect_basic(self):
        self.assertEqualItertools(['abc', 'db', 'ba'])

    def test_intersect_with_dups(self):
        self.assertEqualItertools(['aabc', 'dddb', 'baa'])


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
