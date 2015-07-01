# -*- coding: utf-8  -*-
"""Test Bot classes."""
#
# (C) Pywikibot team, 2014-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import sys

import pywikibot
import pywikibot.bot

from tests.aspects import (
    unittest, DefaultSiteTestCase, SiteAttributeTestCase, TestCase,
)


class FakeSaveBotTestCase(TestCase):

    """
    An abstract test case which patches the bot class to not actually write.

    It redirects the bot's _save_page to it's own C{bot_save} method. Currently
    userPut, put_current and user_edit_entity call it. By default it'll call
    the original method but replace the function called to actually save the
    page by C{page_save}. It patches the bot class as soon as this class'
    attribute bot is defined. It also sets the bot's 'always' option to True to
    avoid user interaction.

    The C{bot_save} method compares the save counter before the call and asserts
    that it has increased by one after the call. It also stores locally in
    C{save_called} if C{page_save} has been called. If C{bot_save} or
    C{page_save} are implemented they should call super's method at some point
    to make sure these assertions work. At C{tearDown} it checks that the pages
    are saved often enough. The attribute C{default_assert_saves} defines the
    number of saves which must happen and compares it to the difference using
    the save counter. It is possible to define C{assert_saves} after C{setUp} to
    overwrite the default value for certain tests. By default the number of
    saves it asserts are 1. Additionally C{save_called} increases by 1 on each
    call of C{page_save} and should be equal to C{assert_saves}.

    This means if the bot class actually does other writes, like using
    L{pywikibot.page.Page.save} manually, it'll still write.
    """

    @property
    def bot(self):
        """Get the current bot."""
        return self._bot

    @bot.setter
    def bot(self, value):
        """Set and patch the current bot."""
        assert value._save_page != self.bot_save, 'bot may not be patched.'
        self._bot = value
        self._bot.options['always'] = True
        self._original = self._bot._save_page
        self._bot._save_page = self.bot_save
        self._old_counter = self._bot._save_counter

    def setUp(self):
        """Set up test by reseting the counters."""
        super(FakeSaveBotTestCase, self).setUp()
        self.assert_saves = getattr(self, 'default_assert_saves', 1)
        self.save_called = 0

    def tearDown(self):
        """Tear down by asserting the counters."""
        self.assertEqual(self._bot._save_counter,
                         self._old_counter + self.assert_saves)
        self.assertEqual(self.save_called, self.assert_saves)
        super(FakeSaveBotTestCase, self).tearDown()

    def bot_save(self, page, func, *args, **kwargs):
        """Handle when bot's userPut was called."""
        self.assertGreaterEqual(self._bot._save_counter, 0)
        old_counter = self._bot._save_counter
        old_local_cnt = self.save_called
        result = self._original(page, self.page_save, *args, **kwargs)
        self.assertEqual(self._bot._save_counter, old_counter + 1)
        self.assertEqual(self.save_called, old_local_cnt + 1)
        self.assertGreater(self._bot._save_counter, self._old_counter)
        return result

    def page_save(self, *args, **kwargs):
        """Handle when bot calls the page's save method."""
        self.save_called += 1


class TestBotTreatExit(object):

    """Mixin to provide handling for treat and exit."""

    def _treat(self, pages, post_treat=None):
        """
        Get tests which are executed on each treat.

        It uses pages as an iterator and compares the page given to the page
        returned by pages iterator. It checks that the bot's _site and site
        attributes are set to the page's site. If _treat_site is set with a Site
        it compares it to that one too.

        Afterwards it calls post_treat so it's possible to do additional checks.
        """
        def treat(page):
            self.assertEqual(page, next(self._page_iter))
            if self._treat_site is None:
                self.assertFalse(hasattr(self.bot, 'site'))
                self.assertFalse(hasattr(self.bot, '_site'))
            else:
                self.assertIsNotNone(self.bot._site)
                self.assertEqual(self.bot.site, self.bot._site)
                if self._treat_site:
                    self.assertEqual(self.bot._site, self._treat_site)
                self.assertEqual(page.site, self.bot.site)
            if post_treat:
                post_treat(page)
        self._page_iter = iter(pages)
        return treat

    def _treat_page(self, pages=True, post_treat=None):
        """
        Adjust to CurrentPageBot signature.

        It uses almost the same logic as _treat but returns a wrapper function
        which itself calls the function returned by _treat.

        The pages may be set to True which sill use _treat_generator as the
        source for the pages.
        """
        def treat_page():
            treat(self.bot.current_page)

        if pages is True:
            pages = self._treat_generator()
        treat = self._treat(pages, post_treat)
        return treat_page

    def _exit(self, treated, written=0, exception=None):
        """Get tests which are executed on exit."""
        def exit():
            exc = sys.exc_info()[0]
            if exc is AssertionError:
                # When an AssertionError happened we shouldn't do these
                # assertions as they are invalid anyway and hide the actual
                # failed assertion
                return
            self.assertEqual(self.bot._treat_counter, treated)
            self.assertEqual(self.bot._save_counter, written)
            if exception:
                self.assertIs(exc, exception)
            else:
                self.assertIsNone(exc)
                self.assertRaises(StopIteration, next, self._page_iter)
        return exit


class TestDrySiteBot(TestBotTreatExit, SiteAttributeTestCase):

    """Tests for the BaseBot subclasses."""

    dry = True

    sites = {
        'de': {
            'family': 'wikipedia',
            'code': 'de'
        },
        'en': {
            'family': 'wikipedia',
            'code': 'en'
        }
    }

    def _generator(self):
        """Generic generator."""
        yield pywikibot.Page(self.de, 'Page 1')
        yield pywikibot.Page(self.en, 'Page 2')
        yield pywikibot.Page(self.de, 'Page 3')
        yield pywikibot.Page(self.en, 'Page 4')

    def test_SingleSiteBot_automatic(self):
        """Test SingleSiteBot class with no predefined site."""
        self._treat_site = self.de
        self.bot = pywikibot.bot.SingleSiteBot(site=None,
                                               generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.de, 'Page 1'),
                                      pywikibot.Page(self.de, 'Page 3')])
        self.bot.exit = self._exit(2)
        self.bot.run()
        self.assertEqual(self.bot.site, self._treat_site)

    def test_SingleSiteBot_specific(self):
        """Test SingleSiteBot class with predefined site."""
        self._treat_site = self.en
        self.bot = pywikibot.bot.SingleSiteBot(site=self.en,
                                               generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.en, 'Page 2'),
                                      pywikibot.Page(self.en, 'Page 4')])
        self.bot.exit = self._exit(2)
        self.bot.run()
        self.assertEqual(self.bot.site, self._treat_site)

    def test_MultipleSitesBot(self):
        """Test MultipleSitesBot class."""
        # Assert no specific site
        self._treat_site = False
        self.bot = pywikibot.bot.MultipleSitesBot(generator=self._generator())
        with self.assertRaises(AttributeError):
            self.bot.site = self.de
        with self.assertRaises(ValueError):
            self.bot.site
        if sys.version_info[0] == 2:
            # The exc_info still contains the AttributeError :/
            sys.exc_clear()
        self.bot.treat = self._treat(self._generator())
        self.bot.exit = self._exit(4)
        self.bot.run()
        with self.assertRaises(ValueError):
            self.bot.site
        if sys.version_info[0] == 2:
            # The exc_info still contains the AttributeError :/
            sys.exc_clear()

    def test_Bot(self):
        """Test normal Bot class."""
        # Assert no specific site
        self._treat_site = False
        self.bot = pywikibot.bot.Bot(generator=self._generator())
        self.bot.treat = self._treat(self._generator())
        self.bot.exit = self._exit(4)
        self.bot.run()

    def test_CurrentPageBot(self):
        """Test normal Bot class."""
        def post_treat(page):
            self.assertIs(self.bot.current_page, page)
        # Assert no specific site
        self._treat_site = None
        self.bot = pywikibot.bot.CurrentPageBot(generator=self._generator())
        self.bot.treat_page = self._treat_page(self._generator(), post_treat)
        self.bot.exit = self._exit(4)
        self.bot.run()

    def test_Bot_ValueError(self):
        """Test normal Bot class with a ValueError in treat."""
        def post_treat(page):
            if page.title() == 'Page 3':
                raise ValueError('Whatever')

        self._treat_site = False
        self.bot = pywikibot.bot.Bot(generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.de, 'Page 1'),
                                      pywikibot.Page(self.en, 'Page 2'),
                                      pywikibot.Page(self.de, 'Page 3')],
                                     post_treat)
        self.bot.exit = self._exit(2, exception=ValueError)
        self.assertRaises(ValueError, self.bot.run)

    def test_Bot_KeyboardInterrupt(self):
        """Test normal Bot class with a KeyboardInterrupt in treat."""
        def post_treat(page):
            if page.title() == 'Page 3':
                raise KeyboardInterrupt('Whatever')

        self._treat_site = False
        self.bot = pywikibot.bot.Bot(generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.de, 'Page 1'),
                                      pywikibot.Page(self.en, 'Page 2'),
                                      pywikibot.Page(self.de, 'Page 3')],
                                     post_treat)

        # TODO: sys.exc_info is empty in Python 3
        if sys.version_info[0] > 2:
            exc = None
        else:
            exc = KeyboardInterrupt
        self.bot.exit = self._exit(2, exception=exc)
        self.bot.run()


# TODO: This could be written as dry tests probably by faking the important
# properties
class LiveBotTestCase(TestBotTreatExit, DefaultSiteTestCase):

    """Test bot classes which need to check the Page object live."""

    def _treat_generator(self):
        """Yield the current page until it's None."""
        while self._current_page:
            yield self._current_page

    def _missing_generator(self):
        """Yield pages and the last one does not exist."""
        self._count = 1
        self._current_page = list(self.site.allpages(total=1))[0]
        yield self._current_page
        while self._current_page.exists():
            self._count += 1
            self._current_page = pywikibot.Page(
                self.site, self._current_page.title() + 'X')
            yield self._current_page
        self._current_page = None

    def _exit(self, treated=None, written=0, exception=None):
        """Set the number of treated pages to _count."""
        def exit():
            t = self._count if treated is None else treated
            super(LiveBotTestCase, self)._exit(t, written, exception)()
        return exit

    def test_ExistingPageBot(self):
        """Test ExistingPageBot class."""
        def post_treat(page):
            """Verify the page exists."""
            self.assertTrue(page.exists())

        self._treat_site = None
        self.bot = pywikibot.bot.ExistingPageBot(
            generator=self._missing_generator())
        self.bot.treat_page = self._treat_page(post_treat=post_treat)
        self.bot.exit = self._exit()
        self.bot.run()

    def test_CreatingPageBot(self):
        """Test CreatingPageBot class."""
        # This doesn't verify much (e.g. it could yield the first existing page)
        # but the assertion in post_treat should verify that the page is valid
        def treat_generator():
            """Yield just one current page (the last one)."""
            yield self._current_page

        def post_treat(page):
            """Verify the page is missing."""
            self.assertFalse(page.exists())

        self._treat_site = None
        self.bot = pywikibot.bot.CreatingPageBot(
            generator=self._missing_generator())
        self.bot.treat_page = self._treat_page(treat_generator(), post_treat)
        self.bot.exit = self._exit()
        self.bot.run()


class BotOptionTest(TestCase):

    """Test Bot options."""

    net = False

    def setUp(self):
        self.parameter = pywikibot.bot.BotOption(True, 'Testing parameter')
        self.stringparam = pywikibot.bot.BotOption('some string', 'string parameter')

        class BotOptionHolder(object):
            parameter = self.parameter
            stringparam = self.stringparam

            def __init__(self):
                self._options = {}

        self.BotOptionHolder = BotOptionHolder

        super(BotOptionTest, self).setUp()

    def test_get_in_class(self):
        self.assertIs(self.BotOptionHolder.parameter, self.parameter)

    def test_get_defaults_in_object(self):
        obj1 = self.BotOptionHolder()
        self.assertEqual(obj1.parameter, True)
        self.assertEqual(obj1.stringparam, 'some string')

    def test_get_set_in_object(self):
        obj1 = self.BotOptionHolder()
        self.assertEqual(obj1.parameter, True)
        obj1.parameter = False
        self.assertEqual(obj1.parameter, False)

    def test_parameters_are_independent(self):
        obj1 = self.BotOptionHolder()
        obj1.parameter = False
        obj1.stringparam = 'blah'
        self.assertEqual(obj1.parameter, False)
        self.assertEqual(obj1.stringparam, 'blah')

    def test_objects_are_independent(self):
        obj1 = self.BotOptionHolder()
        obj2 = self.BotOptionHolder()
        obj1.parameter = False
        self.assertEqual(obj1.parameter, False)
        self.assertEqual(obj2.parameter, True)
        obj3 = self.BotOptionHolder()
        self.assertEqual(obj3.parameter, True)


class BotMetaTest(TestCase):

    """Test Bot metaclass."""

    net = False

    def setUp(self):
        class BotOptionHolder(object):
            parameter = pywikibot.bot.BotOption(True, 'Testing parameter')
            stringparam = pywikibot.bot.BotOption('some string', 'string parameter')

            def __init__(self):
                self._options = {}

        self.BotOptionHolder = BotOptionHolder
        super(BotMetaTest, self).setUp()

    def test_docstring_builder(self):
        self.assertEqual(pywikibot.bot.BotMeta.build_docstring(self.BotOptionHolder), """
@param parameter=True: Testing parameter
@param stringparam='some string': string parameter
        """.strip())


class BotTest(TestCase):

    """Test Bot class."""

    net = False

    def test_new_Bot_docstring(self):
        self.assertEqual(pywikibot.bot.BaseBot.__init__.__doc__, """
        Instantiate a new Bot.

        Available parameters are:
        @param always=False: Always save, even if normally the user is asked to confirm
        """)

    def test_init_function(self):
        newbot = pywikibot.bot.BaseBot()
        self.assertEqual(newbot.always, False)

        newbot = pywikibot.bot.BaseBot(always=True)
        self.assertEqual(newbot.always, True)

    def test_deprecated_API(self):
        bot = pywikibot.bot.BaseBot()
        self.assertEqual(bot.getOption("always"), False)

        bot.options["always"] = True
        self.assertEqual(bot.getOption("always"), True)

        bot = pywikibot.bot.BaseBot()
        bot.options = {'always': True}
        self.assertEqual(bot.getOption("always"), True)

    def test_extend_bot(self):
        class MyBot(pywikibot.bot.BaseBot):
            comment = pywikibot.bot.BotOption('Random comment here', 'Edit comment')

        self.assertEqual(MyBot.__init__.__doc__, """
        Instantiate a new Bot.

        Available parameters are:
        @param always=False: Always save, even if normally the user is asked to confirm
        @param comment='Random comment here': Edit comment
        """)

        bot = MyBot()
        self.assertEqual(bot.comment, "Random comment here")
        self.assertEqual(bot.always, False)

        bot = MyBot(always=True, comment="Some other comment")
        self.assertEqual(bot.comment, "Some other comment")
        self.assertEqual(bot.always, True)

    def test_extend_bot_new_init_no_docstring(self):
        class MyBotWithInitWithoutDocstring(pywikibot.bot.BaseBot):
            comment = pywikibot.bot.BotOption('Random comment here', 'Edit comment')

            def __init__(self, **kwargs):
                super(MyBotWithInitWithoutDocstring, self).__init__(**kwargs)

        self.assertEqual(MyBotWithInitWithoutDocstring.__init__.__doc__, None)

    def test_extend_bot_new_init_with_docstring(self):
        class MyBotWithInitWithDocstring(pywikibot.bot.BaseBot):
            comment = pywikibot.bot.BotOption('Random comment here', 'Edit comment')

            def __init__(self, **kwargs):  # noqa
                """Some awesomer bot.
&botparameters;"""
                super(MyBotWithInitWithDocstring, self).__init__(**kwargs)

        self.assertEqual(MyBotWithInitWithDocstring.__init__.__doc__, """Some awesomer bot.
@param always=False: Always save, even if normally the user is asked to confirm
@param comment='Random comment here': Edit comment""")

    def test_extend_bot_deprecated_method_1(self):
        class MyAncientBot(pywikibot.bot.BaseBot):
            availableOptions = {'jetzer': 'meuk'}

        self.assertEqual(MyAncientBot.__init__.__doc__, """
        Instantiate a new Bot.

        Available parameters are:
        @param always=False: Always save, even if normally the user is asked to confirm
        @param jetzer='meuk': (this option has no description)
        """)

        bot = MyAncientBot()
        self.assertEqual(bot.jetzer, 'meuk')
        self.assertEqual(bot.getOption('jetzer'), 'meuk')

        bot = MyAncientBot(jetzer='andere meuk')
        self.assertEqual(bot.jetzer, 'andere meuk')
        self.assertEqual(bot.getOption('jetzer'), 'andere meuk')

    def test_extend_bot_deprecated_method_2(self):
        class MyAncientDynamicBot(pywikibot.bot.BaseBot):
            def __init__(self, **kwargs):  # noqa
                """Some awesomer bot.
&botparameters;"""
                self.availableOptions = {'jetzer': 'meuk'}
                super(MyAncientDynamicBot, self).__init__(**kwargs)

        # we cannot generate the docstring based on what's in __init__ without
        # running it, so we will ignore parameters added there. They can still
        # be in the __init__ docstring, of course.
        self.assertEqual(MyAncientDynamicBot.__init__.__doc__, """Some awesomer bot.
@param always=False: Always save, even if normally the user is asked to confirm""")

        bot = MyAncientDynamicBot()
        self.assertEqual(bot.jetzer, 'meuk')
        self.assertEqual(bot.getOption('jetzer'), 'meuk')

        bot = MyAncientDynamicBot(jetzer='andere meuk')
        self.assertEqual(bot.jetzer, 'andere meuk')
        self.assertEqual(bot.getOption('jetzer'), 'andere meuk')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
