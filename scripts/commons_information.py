# -*- coding: utf-8  -*-
"""Insert a language template into the Description field."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#

import copy

import mwparserfromhell

import pywikibot
from pywikibot import i18n, pagegenerators, Bot

try:
    import langdetect
except ImportError:
    langdetect = None


class InformationBot(Bot):

    """Bot for the Information template on Commons."""

    lang_tmp_cat = 'Language templates'
    desc_params = ('Description', 'description')

    comment = {
        'en': u'wrap the Description parameter of Information in the appropriate language template'
    }

    def __init__(self, site, **kwargs):
        super(InformationBot, self).__init__(**kwargs)
        self.site = site
        lang_tmp_cat = pywikibot.Category(self.site, self.lang_tmp_cat)
        self.lang_tmps = lang_tmp_cat.articles(namespaces=[10])

    def get_description(self, template):
        params = [param for param in template.params
                  if param.name.strip() in self.desc_params]
        if len(params) > 1:
            pywikibot.warning(u'multiple description parameters found')
        elif len(params) == 1 and params[0].value.strip() != '':
            return params[0]

    @staticmethod
    def detect_langs(text):
        if langdetect:
            return langdetect.detect_langs(text)

    def process_desc_template(self, template):
        tmp_page = pywikibot.Page(self.site, template.name.strip(), ns=10)
        if tmp_page in self.lang_tmps and len(template.params) == 1 and template.has('1'):
            lang_tmp_val = template.get('1').value.strip()
            langs = self.detect_langs(lang_tmp_val)
            if langs and langs[0].prob > 0.9:
                tmp_page2 = pywikibot.Page(self.site, langs[0].lang, ns=10)
                if tmp_page2 != tmp_page:
                    pywikibot.output(u'\03{{lightblue}}The language template "{before}" '
                                     u'was found, but langdetect thinks "{after}" is the '
                                     u'most appropriate with a probability of {prob}:'
                                     u'\03{{default}}\n{text}'.format(
                                         before=tmp_page.title(withNamespace=False),
                                         after=tmp_page2.title(withNamespace=False),
                                         prob=langs[0].prob,
                                         text=lang_tmp_val))
                    choice = pywikibot.input_choice(u'What to do?',
                                                    [('Replace it', 'y'),
                                                     ('Do not replace it', 'n'),
                                                     ('Choose another', 'c')])
                    if choice == 'y':
                        template.name = langs[0].lang
                        return True
                    elif choice == 'c':
                        newlang = pywikibot.input(u'Enter the language of the displayed text:')
                        if newlang and newlang != template.name:
                            template.name = newlang
                            return True

    @staticmethod
    def replace_value(param, value):
        lstrip = param.value.lstrip()
        lspaces = param.value[:len(param.value) - len(lstrip)]
        rspaces = lstrip[len(lstrip.rstrip()):]
        param.value = u'{0}{1}{2}'.format(lspaces, value, rspaces)

    def treat(self, page):
        self.current_page = page
        code = mwparserfromhell.parse(page.text)
        edited = False  # to prevent unwanted changes
        for template in code.ifilter_templates():
            if not page.site.sametitle(template.name.strip(), 'Information'):
                continue
            desc = self.get_description(template)
            if desc is None:
                continue
            for tmp in desc.value.filter_templates(recursive=False):
                if self.process_desc_template(tmp):
                    edited = True
            desc_clean = copy.deepcopy(desc.value)
            for tmp in desc_clean.filter_templates(recursive=False):
                # TODO: emit a debug item?
                desc_clean.remove(tmp)
            value = desc_clean.strip()
            if value == '':
                pywikibot.output(u'Empty description')
                continue
            pywikibot.output(value)
            langs = self.detect_langs(value)
            if langs:
                pywikibot.output(u'\03{lightblue}Hints from langdetect:\03{default}')
                for language in langs:
                    pywikibot.output(u'\03{{lightblue}}{obj.lang}: {obj.prob}'
                                     u'\03{{default}}'.format(obj=language))
            lang = pywikibot.input(u'Enter the language of the displayed text:').strip()
            if lang != '':
                tmp_page = pywikibot.Page(page.site, lang, ns=10)
                if tmp_page not in self.lang_tmps:
                    pywikibot.warning(u'"{lang}" is not a valid language template on {site}'.format(
                        lang=lang, site=page.site))
                new = mwparserfromhell.nodes.template.Template(lang, [value])
                self.replace_value(desc, new)
                edited = True
        if edited:
            text = unicode(code)
            comment = i18n.translate(page.site.lang, self.comment, fallback=True)
            self.userPut(page, page.text, text, comment=comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        bot = InformationBot(site=pywikibot.Site(), generator=gen)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == '__main__':
    main()
