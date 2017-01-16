#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test diff module."""
#
# (C) Pywikibot team, 2016-2017
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

import sys

from pywikibot.diff import cherry_pick, html_comparator, PatchManager, DictPatchManager
from pywikibot.tools import PY2

from tests import join_html_data_path
from tests.aspects import TestCase, require_modules, unittest

if sys.version_info[0] > 2:
    from unittest.mock import patch
else:
    from mock import patch


@require_modules('bs4')
class TestDryHTMLComparator(TestCase):

    """Test html_comparator method with given strings as test cases."""

    net = False

    def test_added_context(self):
        """Test html_comparator's detection of added-context."""
        output = html_comparator('''
<tr>
  <td class="diff-addedline">line 1a</td>
  <td class="diff-addedline">line \n2a</td>
</tr>
<tr>
  <td class="diff-addedline"><span>line 1b</span></td>
  <td class="diff-addedline">line 2b<i><span></i></span></td>
</tr>''')
        self.assertEqual(output['added-context'],
                         ['line 1a', 'line \n2a', 'line 1b', 'line 2b'])

    def test_deleted_context(self):
        """Test html_comparator's detection of deleted-context."""
        output = html_comparator('''
<tr>
  <td class="diff-deletedline">line 1a</td>
  <td class="diff-deletedline">line \n2a</td>
</tr>
<tr>
  <td class="diff-deletedline"><span>line 1b</span></td>
  <td class="diff-deletedline">line 2b<i><span></i></span></td>
</tr>''')
        self.assertEqual(output['deleted-context'],
                         ['line 1a', 'line \n2a', 'line 1b', 'line 2b'])

    def test_run(self):
        """Test html_comparator using examples given in mw-api docs."""
        with open(join_html_data_path('diff.html')) as filed:
            diff_html = filed.read()
        output = html_comparator(diff_html)
        self.assertEqual(
            output,
            {'added-context': ['#REDIRECT [[Template:Unsigned IP]]'],
             'deleted-context': [
                '<small><span class="autosigned">\\u2014&nbsp;Preceding '
                '[[Wikipedia:Signatures|unsigned]] comment added by '
                '[[User:{{{1}}}|{{{1}}}]] ([[User talk:{{{1}}}|talk]] \\u2022 '
                '[[Special:Contributions/{{{1}}}|contribs]]) {{{2|}}}</span>'
                '</small><!-- Template:Unsigned --><noinclude>',
                '{{documentation}} <!-- add categories to the /doc page, '
                'not here --></noinclude>']})


@require_modules('bs4')
class TestHTMLComparator(TestCase):

    """Test html_comparator using api.php in en:wiki."""

    family = 'wikipedia'
    code = 'en'

    def test_wikipedia_rev_139992(self):
        """Test html_comparator with revision 139992 in en:wikipedia."""
        site = self.get_site()
        diff_html = site.compare(139992, 139993)
        output = html_comparator(diff_html)
        self.assertEqual(len(output['added-context']), 1)
        self.assertEqual(len(output['deleted-context']), 1)


@patch('{0}.__import__'.format('__builtin__' if PY2 else 'builtins'),
       side_effect=ImportError, autospec=True)
class TestNoBeautifulSoup(TestCase):

    """Test functions when BeautifulSoup is not installed."""

    net = False

    def test_html_comparator(self, mocked_import):
        """Test html_comparator when bs4 not installed."""
        self.assertRaises(ImportError, html_comparator, '')
        self.assertEqual(mocked_import.call_count, 1)
        self.assertIn('bs4', mocked_import.call_args[0])


class TestPatchManager(TestCase):

    """Test PatchManager class with given strings as test cases."""

    net = False

    # each tuple: (before, after, expected hunks
    cases = [(' test',
              '_test',
              {0: '@@ -1 +1 @@\n\n'
                  '-  test\n'
                  '? ^\n'
                  '+ _test\n'
                  '? ^\n'}),
             ('The quick brown fox jumps over the lazy dog.',
              'quick brown dog jumps quickly over the lazy fox.',
              {0: '@@ -1 +1 @@\n\n'
                  '- The quick brown fox jumps over the lazy dog.\n'
                  '? ----            ^ ^                     ^ ^\n'
                  '+ quick brown dog jumps quickly over the lazy fox.\n'
                  '?             ^ ^       ++++++++              ^ ^\n'}),
             ('spam',
              'eggs',
              {0: '@@ -1 +1 @@\n\n'
                  '- spam\n'
                  '+ eggs\n'}),
             ('Lorem\n'
              'ipsum\n'
              'dolor',
              'Quorem\n'
              'ipsum\n'
              'dolom',
              {0: '@@ -1 +1 @@\n\n'
                  '- Lorem\n'
                  '? ^\n'
                  '+ Quorem\n'
                  '? ^^\n',
               1: '@@ -3 +3 @@\n\n'
                  '- dolor\n'
                  '?     ^\n'
                  '+ dolom\n'
                  '?     ^\n'}),
             ('.foola.Pywikipediabot',
              '.foo.Pywikipediabot.foo.',
              {0: '@@ -1 +1 @@\n\n'
                  '- .foola.Pywikipediabot\n'
                  '?     --\n'
                  '+ .foo.Pywikipediabot.foo.\n'
                  '?                    +++++\n'}),
             ('{foola}Pywikipediabot',
              '{foo}Pywikipediabot{foo}',
              {0: '@@ -1 +1 @@\n\n'
                  '- {foola}Pywikipediabot\n'
                  '?     --\n'
                  '+ {foo}Pywikipediabot{foo}\n'
                  '?                    +++++\n'}),
             ('{default}Foo bar Pywikipediabot foo bar',
              '{default}Foo  bar  Pywikipediabot  foo  bar',
              {0: '@@ -1 +1 @@\n\n'
                  '- {default}Foo bar Pywikipediabot foo bar\n'
                  '+ {default}Foo  bar  Pywikipediabot  foo  bar\n'
                  '?              +   +                +    +\n'}),
             ('Pywikipediabot foo',
              'Pywikipediabot  foo',
              {0: '@@ -1 +1 @@\n\n'
                  '- Pywikipediabot foo\n'
                  '+ Pywikipediabot  foo\n'
                  '?                +\n'}),
             ('  Pywikipediabot    ',
              '   Pywikipediabot   ',
              {0: '@@ -1 +1 @@\n\n'
                  '-   Pywikipediabot    \n'
                  '?                    -\n'
                  '+    Pywikipediabot   \n'
                  '? +\n'})]

    def test_patch_manager(self):
        """Test PatchManager."""
        for case in self.cases:
            p = PatchManager(case[0], case[1])
            for key in case[2].keys():  # for each hunk
                self.assertEqual(p.hunks[key].diff_plain_text, case[2][key])


class TestDictPatchManager(TestCase):

    """Test DictPatchManager creating diffs between dictionaries."""

    net = False

    def check_hunks(self, first, second, results):
        """Helper method, used to check if DictPatchManager returned expected results."""
        p = DictPatchManager(first, second)
        self.assertEqual(len(p.hunks), len(results))
        for i in range(0, len(p.hunks)):
            self.assertEqual(p.hunks[i].diff_plain_text, results[i])

    def test_numeric_values(self):
        """Test comparing dictionaries with numeric values."""
        first = {
            'numeric1': 42,
            'numeric2': 124,
            'numeric3': 15,
        }
        second = {
            'numeric1': 42,
            'numeric2': 62,
            'numeric4': 195,
        }
        results = [
            '- numeric2: 124\n'
            '+ numeric2: 62\n',

            '- numeric3: 15\n',
            '+ numeric4: 195\n',
        ]
        self.check_hunks(first, second, results)

    def test_string_values(self):
        """Test comparing dictionaries with values values."""
        first = {
            'string1': 'value1',
            'string2': 'value2',
            'string3': 'value3',
        }
        second = {
            'string1': 'value1',
            'string2': 'changed_value2',
            'string4': 'new_value4',
        }
        results = [
            '- string2: "value2"\n'
            '+ string2: "changed_value2"\n',

            '- string3: "value3"\n',
            '+ string4: "new_value4"\n',
        ]
        self.check_hunks(first, second, results)

    def test_nested_dicts(self):
        """Test comparing dictionaries with nested dictionaries."""
        first = {
            'nested_dict': {
                'nested_key1': 'nested_value1',
                'nested_key2': 'nested_value2',
                'nested_key3': 'nested_value3',
            },
            'nested_dict_2': {
                'foo': 'bar',
            },
        }
        second = {
            'nested_dict': {
                'nested_key1': 'nested_value1',
                'nested_key2': 'nested_changed_value2',
                'nested_key4': 'nested_new_value4',
            },
            'nested_dict_3': {
                'foo': 'bar',
            },
        }
        results = [
            '- nested_dict.nested_key2: "nested_value2"\n'
            '+ nested_dict.nested_key2: "nested_changed_value2"\n'
            '? nested_dict.nested_key2:      ++++++++\n',

            '- nested_dict.nested_key3: "nested_value3"\n',
            '+ nested_dict.nested_key4: "nested_new_value4"\n',
            '- nested_dict_2.foo: "bar"\n',
            '+ nested_dict_3.foo: "bar"\n',
        ]
        self.check_hunks(first, second, results)

    def test_nested_arrays(self):
        """Test comparing dictionaries with nested arrays."""
        first = {
            'array1': [
                42, 124, 15,
            ],
            'array2': [
                {
                    'foo': 'bar',
                },
                1,
                2,
                {
                    'key0': 'value1',
                },
                {
                    'key1a': 'value2a',
                    'key1b': 'value2b',
                },
                {
                    'key3': 'value3',
                },
                {
                    'foo': 'bar',
                },
            ],
            'array3': [
                [0, 1, 2],
                [3, 4, 5],
            ],
            'array4': [
                5,
                6,
                [
                    'value1', 'value2'
                ],
                [
                    'value4', 'value5'
                ],
            ],
        }
        second = {
            'array1': [
                42, 62, 195
            ],
            'array2': [
                {
                    'foo': 'new_value',
                },
                2,
                3,
                4,
                {
                    'key0': 'value1',
                },
                {
                    'key1a': 'changed_value_2a',
                    'key1b': 'value2b',
                },
                {
                    'key4': 'new_value_4',
                },
            ],
            'array3': [
                [0, 1, 2],
                [6, 4, 8],
            ],
            'array4': [
                6,
                7,
                8,
                [
                    'value1', 'value3'
                ],
            ],
        }
        results = [
            '- array1[1]: 124\n',
            '- array1[2]: 15\n',
            '+ array1[1]: 62\n',
            '+ array1[2]: 195\n',
            '- array2[1]: 1\n',
            '+ array2[2]: 3\n',
            '+ array2[3]: 4\n',

            '- array2[0].foo: "bar"\n'
            '+ array2[0].foo: "new_value"\n',

            '- array2[4->5].key1a: "value2a"\n'
            '+ array2[4->5].key1a: "changed_value_2a"\n',

            '- array2[5->6].key3: "value3"\n',
            '+ array2[5->6].key4: "new_value_4"\n',
            '- array2[6].foo: "bar"\n',
            '- array3[1][0]: 3\n',
            '- array3[1][2]: 5\n',
            '+ array3[1][0]: 6\n',
            '+ array3[1][2]: 8\n',
            '- array4[0]: 5\n',
            '+ array4[1]: 7\n',
            '+ array4[2]: 8\n',
            '- array4[2->3][1]: "value2"\n',
            '+ array4[2->3][1]: "value3"\n',
            '- array4[3][0]: "value4"\n',
            '- array4[3][1]: "value5"\n',
        ]
        self.check_hunks(first, second, results)

    @patch('pywikibot.output')
    def test_print_hunks(self, mock):
        """Test printing hunks."""
        first = {
            'foo': 'bar',
            'unicode-test': '\U0001F30E',
        }
        second = {
        }
        diff_messages = [
            '\x03{lightred}- foo: "bar"',
            '\x03{lightred}- unicode-test: "\U0001F30E"',
            '\x03{default}',
        ]

        p = DictPatchManager(first, second)
        p.print_hunks()
        for message in diff_messages:
            mock.assert_any_call(message)


class TestCherryPick(TestCase):
    """Test cherry_pick method."""

    net = False

    # texts used during testing
    oldtext = 'old'
    newtext = 'new'

    # output messages expected during testing
    diff_message = '\x03{lightred}- old\n\x03{default}\x03{lightgreen}+ new\n\x03{default}'
    none_message = '\x03{{lightpurple}}{0: ^50}\x03{{default}}'.format('None.')
    header_base = '\n\x03{{lightpurple}}{0:*^50}\x03{{default}}\n'
    headers = ['  ALL CHANGES  ', '  REVIEW CHANGES  ', '  APPROVED CHANGES  ']
    diff_by_letter_message = ("\x03{lightred}- o\n\x03{default}"
                              "\x03{lightred}- l\n\x03{default}"
                              "\x03{lightred}- d\n\x03{default}"
                              "\x03{lightgreen}+ n\n\x03{default}"
                              "\x03{lightgreen}+ e\n\x03{default}"
                              "\x03{lightgreen}+ w\n\x03{default}")

    def check_headers(self, mock):
        """Check if all headers were added to ouput."""
        for header in self.headers:
            mock.assert_any_call(self.header_base.format(header))

    @patch('pywikibot.output')
    @patch('pywikibot.userinterfaces.terminal_interface_base.UI.input', return_value='y')
    def test_accept(self, input, mock):
        """Check output of cherry_pick if changes accepted."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext), self.newtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_message)

    @patch('pywikibot.output')
    @patch('pywikibot.userinterfaces.terminal_interface_base.UI.input', return_value='n')
    def test_reject(self, input, mock):
        """Check output of cherry_pick if changes rejected."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext), self.oldtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_message)
        mock.assert_any_call(self.none_message)

    @patch('pywikibot.output')
    @patch('pywikibot.userinterfaces.terminal_interface_base.UI.input', return_value='q')
    def test_quit(self, input, mock):
        """Check output of cherry_pick if quitted."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext), self.oldtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_message)
        mock.assert_any_call(self.none_message)

    @patch('pywikibot.output')
    @patch('pywikibot.userinterfaces.terminal_interface_base.UI.input', return_value='y')
    def test_by_letter_accept(self, input, mock):
        """Check output of cherry_pick if by_letter diff is enabled and changes accepted."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext, by_letter=True), self.newtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_by_letter_message)

    @patch('pywikibot.output')
    @patch('pywikibot.userinterfaces.terminal_interface_base.UI.input', return_value='q')
    def test_by_letter_quit(self, input, mock):
        """Check output of cherry_pick if by_letter diff is enabled and quitted during review."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext, by_letter=True), self.oldtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_by_letter_message)
        mock.assert_any_call(self.none_message)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
