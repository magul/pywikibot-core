# -*- coding: utf-8 -*-
u"""
Questo script è stato scritto da Pietrodn & Filnik per it.wikipedia.

Serve per sistemare i vari template {{Portale}} presenti nelle voci in uno solo,
riposizionare correttamente il template {{Portale}}, rimuovere i duplicati,
mettere in ordine alfabetico gli argomenti, aggiungerli e toglierli a comando.

È possibile specificare delle regex per aggiungere delle eccezioni, con il comando -except.

Se si decide di aggiungere un argomento e nella pagina non è presente alcun template portale,
questo verrà aggiunto nel posto giusto.
Se si rimuove l'unico argomento presente nel template portale, questo verrà tolto completamente.

Lo script si basa su add_text.py di Filnik.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-always           Do not ask confirmation before editing pages.

-template:foo     Change templates with the name "foo" instead of the default one.

-add:bar          Add "foo" to the arguments.

-remove:baz       Remove "baz" from the arguments, if present.

-except:regex     Do not process pages that match regex.


Examples:

python portale.py -add:foo -remove:bar -add:baz
python portale.py -add:foo
python portale.py

"""

import re
import sys

import mwparserfromhell

import pywikibot
from pywikibot import pagegenerators, Bot

from add_text import add_text

if sys.version_info[0] > 2:
    unicode = str

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class PortaleBot(Bot):

    """Bot to change occurrences of Portale-like templates."""

    def __init__(self, add=[], remove=[], exceptions=[], **kwargs):
        self.availableOptions.update({
            'template': 'Portale',
            'max-params': 6,
            'summary': None,
        })

        super(PortaleBot, self).__init__(**kwargs)
        self.add = set(add)
        self.remove = set(map(unicode.lower, remove))
        self.exceptions = set(exceptions)

    def build_summary(self, page, added, removed, tidy=None, case=False):
        summary = [u'modifiche a [[Template:%(template)s]]'
                   % {'template': self.getOption('template')}]
        concat = lambda x: page.site.list_to_text(['"%s"' % y for y in x])
        if len(added) > 0:
            summary.append(u'aggiungo %s' % concat(added))
        if len(removed) > 0:
            summary.append(u'tolgo %s' % concat(removed))
        if tidy is True:
            summary.append(u'riordino parametri')
        elif isinstance(tidy, int):
            summary.append(u'unisco %d template' % tidy)
        if case is True:
            summary.append(u'cambio maiuscole/minuscole')
        colon = page.site.mediawiki_message('colon-separator')
        summary = '; '.join([colon.join(summary[:2])] + summary[2:])
        return summary

    @staticmethod
    def remove_with_newline(code, element):
        try:
            after = code.get(code.index(element) + 1)
            if isinstance(after, mwparserfromhell.nodes.text.Text):
                after_str = unicode(after)
                if after_str.startswith('\n'):
                    code.replace(after, after_str[1:])
        except IndexError:
            pass
        code.remove(element)

    def run(self):
        for page in self.generator:
            self.current_page = page

            try:
                page.get()
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, I'll ignore it." % page.title())
                continue

            stop = False
            for exception in self.exceptions:
                if re.search(exception, page.text):
                    pywikibot.output('Exception "%s" found! Skipping.' % exception)
                    stop = True
                    break
            if stop:
                continue

            self.treat(page)

    def treat(self, page):
        code = mwparserfromhell.parse(page.text)

        kept = None
        tidy = None
        case = False
        params = []

        for template in code.ifilter_templates():
            if not page.site.sametitle(template.name.strip(),
                                       self.getOption('template')):
                # Select only configured templates
                continue

            for param in template.params:
                if not param.name.strip().isnumeric():
                    return  # named parameter
                if template.get(param.name.strip()).strip() != param.value.strip():
                    return  # duplicate parameters with different values
                stripped = param.value.strip()
                if stripped != '' and stripped not in params:
                    # select only new and non-empty parameters
                    params.append(stripped)

            if kept is None:
                for param in template.params[::-1]:  # remove params from the end
                    template.remove(param, keep_field=False)
                kept = template
            else:
                self.remove_with_newline(code, template)
                if isinstance(tidy, int):
                    tidy += 1
                else:
                    tidy = 2

        if tidy is None:
            old_params = list(params)
            old_params_lower = map(unicode.lower, old_params)
            old_params_lower = [p for p in old_params_lower if p not in self.remove]
            if sorted(old_params_lower) != old_params_lower:
                tidy = True

        # case-insensitive difference
        diff = set(params)
        added = []
        removed = []
        for toAdd in self.add:
            found = False
            for arg in diff.copy():
                if toAdd.lower() == arg.lower():
                    found = True
                    if toAdd != arg:
                        diff.remove(arg)
                        diff.add(toAdd)
                        case = True
            if not found:
                diff.add(toAdd)
                added.append(toAdd)
        for arg in diff.copy():
            if arg.lower() in self.remove:
                diff.remove(arg)
                removed.append(arg)
        params = list(diff)  # Return to an ordered list
        params.sort(key=unicode.lower)  # Case-insensitive sort

        if self.getOption('max-params') and len(params) > self.getOption('max-params'):
            return  # too many arguments

        if kept:
            self.remove_with_newline(code, kept)
        else:
            kept = mwparserfromhell.nodes.template.Template(self.getOption('template'))

        for num, val in enumerate(params):
            # Add arguments one by one
            kept.add(num + 1, val, preserve_spacing=False)

        addText = unicode(kept)
        (text, newtext, always) = add_text(page=page, addText=addText,
                                           putText=False, oldTextGiven=unicode(code),
                                           reorderEnabled=True)

        if newtext == page.text:
            summary = None
        else:
            summary = self.build_summary(page, added, removed,
                                         tidy=tidy, case=case)
        self.userPut(page, page.text, newtext, comment=summary)


def main(*args):
    options = {}
    add = []
    remove = []
    exceptions = []
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-template:') and len(arg) > 10:
            options['template'] = arg[10:]
        elif arg.startswith('-add:') and len(arg) > 5:
            add.append(arg[5:])
        elif arg.startswith('-remove:') and len(arg) > 8:
            remove.append(arg[8:])
        elif arg.startswith('-except:') and len(arg) > 8:
            exceptions.append(arg[8:])
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        bot = PortaleBot(add, remove, exceptions, generator=gen, **options)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == "__main__":
    main()
