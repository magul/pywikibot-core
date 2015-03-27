#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
A bot to do some simple over categorization filtering.

Now it uses the strategy to loop over all articles in all the subcategories.
That might be a very good strategy when the parent category is very full, but
later on it will become very inefficient.

Can be used with:
&params;
"""
#
# (C) Pywikibot team, 2013-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ExistingPageBot


class OverCatBot(ExistingPageBot):

    """Bot to provoke bot operations."""

    def treat_page(self):
        """Process one page from the generator."""
        self.filterCategory(self.current_page)

    def filterCategory(self, page):
        """Loop over all subcategories of page and filter them."""
        category = pywikibot.Category(page)

        for subcat in category.subcategories():
            self.filterSubCategory(subcat, category)

    def filterSubCategory(self, subcat, category):
        """Filter and remove category from all articles and files in subcat.

        The details are then updated on corresponding articles and files.
        """
        for article in subcat.articles(content=True):
            pywikibot.output(u'Working on %s' % (article.title))
            articleCategories = list(article.categories())
            if category in articleCategories:
                articleCategories.remove(category)
                newtext = pywikibot.replaceCategoryLinks(article.text, articleCategories)
                comment = (u'Removing [[%s]]: Is already in the subcategory [[%s]]'
                           % (category.title(), subcat.title()))
                self.userPut(article, article.text, newtext, comment=comment, show_diff=True)


def main(*args):
    """Process command line arguments and invoke OverCatBot."""
    genFactory = pagegenerators.GeneratorFactory(predefined_namespaces=14)

    for arg in pywikibot.handle_args(*args):
        genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if not generator:
        return pywikibot.showHelp()

    bot = OverCatBot(generator=generator)
    bot.run()

if __name__ == '__main__':
    main()
