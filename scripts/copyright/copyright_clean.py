# -*- coding: utf-8  -*-
"""Script taking care of cleaning requirements on page based on copyright inspection."""
#
# (C) Francesco Cosoleto, 2006
# (c) Pywikibot team 2006-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re

import pywikibot

from pywikibot import pagegenerators
from copyright import mysplit, put, reports_cat, join_family_data


summary_msg = {
    'ar': u'إزالة',
    'en': u'Removing',
    'fa': u'حذف',
    'fr': u'Retiré',
    'it': u'Rimozione',
    'ru': u'Удаление',
    'uk': u'Видалення',
}

headC = re.compile(
    '(?m)^=== (?:<strike>)?(?:<s>)?(?:<del>)?\[\[(?::)?(.*?)\]\]')
separatorC = re.compile('(?m)^== +')
next_headC = re.compile("(?m)^=+.*?=+")


# {{botbox|title|newid|oldid|author|...}}
rev_templateC = re.compile(
    '(?m)^(?:{{/t\|.*?}}\n?)?{{(?:/box|botbox)\|.*?\|(.*?)\|')


class CopyrightCleanBot(pywikibot.Bot):

    """Bot initiating cleaning requirements on page based on copyright inspection."""

    query_results_titles = list()
    query_results_revids = list()

    def __init__(self, generator):
        super(CopyrightCleanBot, self).__init__(generator=generator)

    def query_api(self, data):
        predata = {
            'action': 'query',
            'prop': 'revisions',
        }
        predata = self.CombineParams(predata, data)
        return pywikibot.data.api.Request(**predata).submit()

    def query_old_api(self, data):

        predata = {
            'what': 'revisions',
            'rvlimit': '1',
        }
        predata = self.CombineParams(predata, data)
        return pywikibot.data.api.Request(**predata).submit()

    def old_page_exist(self, title):
        for pageobjs in self.query_results_titles:
            for key in pageobjs['pages']:
                if pageobjs['pages'][key]['title'] == title:
                    if int(key) >= 0:
                        return True
        pywikibot.output('* ' + title)
        return False

    def old_revid_exist(self, revid):
        for pageobjs in self.query_results_revids:
            for id in pageobjs['pages']:
                for rv in range(len(pageobjs['pages'][id]['revisions'])):
                    if pageobjs['pages'][id]['revisions'][rv]['revid'] == \
                       int(revid):
                        # print rv
                        return True
        pywikibot.output('* ' + revid)
        return False

    def page_exist(self, title):
        for pageobjs in self.query_results_titles:
            for key in pageobjs['query']['pages']:
                if pageobjs['query']['pages'][key]['title'] == title:
                    if 'missing' in pageobjs['query']['pages'][key]:
                        pywikibot.output('* ' + title)
                        return False
        return True

    def revid_exist(self, revid):
        for pageobjs in self.query_results_revids:
            if 'badrevids' in pageobjs['query']:
                for id in pageobjs['query']['badrevids']:
                    if id == int(revid):
                        # print rv
                        pywikibot.output('* ' + revid)
                        return False
        return True

    def treat(self, page):
        data = page.get()
        pywikibot.output(page.title(asLink=True))
        output = ''

        #
        # Preserve text before of the sections
        #

        m = re.search('(?m)^==\s*[^=]*?\s*==', data)
        if m:
            output = data[:m.end() + 1]
        else:
            m = re.search('(?m)^===\s*[^=]*?', data)
            if m:
                output = data[:m.start()]

        titles = headC.findall(data)
        titles = [re.sub('#.*', '', item) for item in titles]
        revids = rev_templateC.findall(data)

        # No more of 50 titles at a time using API
        for s in mysplit(self.ListToParam(titles), 50, '|'):
            self.query_results_titles.append(self.query_api({'titles': s}))
        for s in mysplit(self.ListToParam(revids), 50, '|'):
            self.query_results_revids.append(self.query_api({'revids': s}))

        comment_entry = list()
        add_separator = False
        index = 0

        while True:
            head = headC.search(data, index)
            if not head:
                break
            index = head.end()
            title = re.sub('#.*', '', head.group(1))
            next_head = next_headC.search(data, index)
            if next_head:
                if separatorC.search(data[next_head.start():next_head.end()]):
                    add_separator = True
                stop = next_head.start()
            else:
                stop = len(data)

            exist = True
            if self.page_exist(title):
                # check {{botbox}}
                revid = re.search('{{(?:/box|botbox)\|.*?\|(.*?)\|',
                                  data[head.end():stop])
                if revid:
                    if not self.revid_exist(revid.group(1)):
                        exist = False
            else:
                exist = False

            if exist:
                ctitle = re.sub(u'(?i)=== \[\[%s:'
                                % join_family_data('Image', 6),
                                u'=== [[:\1:', title)
                ctitle = re.sub(u'(?i)=== \[\[%s:'
                                % join_family_data('Category', 14),
                                u'=== [[:\1:', ctitle)
                output += '=== [[' + ctitle + ']]' + data[head.end():stop]
            else:
                comment_entry.append('[[%s]]' % title)

            if add_separator:
                output += data[next_head.start():next_head.end()] + '\n'
                add_separator = False

        add_comment = u'%s: %s' % (pywikibot.translate(pywikibot.Site(),
                                                       summary_msg),
                                   ', '.join(comment_entry))

        # remove useless newlines
        output = re.sub('(?m)^\n', '', output)

        if comment_entry:
            pywikibot.output(add_comment)
            if pywikibot.config.verbose_output:
                pywikibot.showDiff(page.get(), output)

            choice = pywikibot.input_yn(u'Do you want to clean the page?',
                                        automatic_quit=False)
            if choice:
                try:
                    put(page, output, add_comment)
                except pywikibot.PageNotSaved:
                    raise

    pywikibot.stopme()

    #
    #
    # Helper utilities
    #
    #

    def CleanParams(self, params):
        """Param may be either a tuple, a list of tuples or a dictionary.

        This method will convert it into a dictionary
        """
        if params is None:
            return {}
        pt = type(params)
        if pt == dict:
            return params
        elif pt == tuple:
            if len(params) != 2:
                raise 'Tuple size must be 2'
            return {params[0]: params[1]}
        elif pt == list:
            for p in params:
                if p != tuple or len(p) != 2:
                    raise 'Every list element must be a 2 item tuple'
            return dict(params)
        else:
            raise 'Unknown param type %s' % pt

    def CombineParams(self, params1, params2):
        """Merge two dictionaries.

        If they have the same keys, their values will be appended one after
        another separated by the '|' symbol.
        """
        params1 = self.CleanParams(params1)
        if params2 is None:
            return params1
        params2 = self.CleanParams(params2)

        for k, v2 in params2.iteritems():
            if k in params1:
                v1 = params1[k]
                if len(v1) == 0:
                    params1[k] = v2
                elif len(v2) > 0:
                    if str in [type(v1), type(v2)]:
                        raise "Both merged values must be of type 'str'"
                    params1[k] = v1 + '|' + v2
                # else ignore
            else:
                params1[k] = v2
        return params1

    def ConvToList(self, item):
        """Ensure the output is a list."""
        if item is None:
            return []
        elif isinstance(item, str):
            return [item]
        else:
            return item

    def ListToParam(self, list):
        """Convert list of unicode strings into a UTF8 string separated by '|' symbol."""
        list = self.ConvToList(list)
        if len(list) == 0:
            return ''

        encList = ''
        # items may not have one symbol - '|'
        for item in list:
            if isinstance(item, str):
                if u'|' in item:
                    raise pywikibot.Error(u"item '%s' contains '|' symbol" % item)
                encList += self.ToUtf8(item) + u'|'
            elif type(item) == int:
                encList += self.ToUtf8(item) + u'|'
            elif isinstance(item, pywikibot.Page):
                encList += self.ToUtf8(item.title()) + u'|'
            elif item.__class__.__name__ == 'User':
                # delay loading this until it is needed
                encList += self.ToUtf8(item.name()) + u'|'
            else:
                raise pywikibot.Error(u'unknown item class %s'
                                      % item.__class__.__name__)

        # strip trailing '|' before returning
        return encList[:-1]

    def ToUtf8(self, s):
        if isinstance(s, type(u'')):
            try:
                s = s.decode(encoding='utf-8')
            except UnicodeDecodeError:
                s = s.decode(pywikibot.config.console_encoding)
        return s


def main(*args):
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        genFactory.handleArg(arg)
    gen = genFactory.getCombinedGenerator()

    if not gen:
        cat = pywikibot.Category(pywikibot.Site(), 'Category:%s' %
                                 pywikibot.translate(pywikibot.Site(),
                                                     reports_cat))
        gen = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
    bot = CopyrightCleanBot(gen)
    bot.run()

if __name__ == '__main__':
    main()
