#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to remove EDP images in non-article namespaces.

This script is currently used on the Chinese wikipedia.

Way:
* [[Image:logo.jpg]] --> [[:Image:logo.jpg]]
* [[:Image:logo.jpg]] pass
* Image:logo.jpg in gallery --> [[:Image:logo.jpg]] in gallery end
* logo.jpg(like used in template) --> hide(used <!--logo.jpg-->)

command:
python pwb.py deledpimage.py

"""
#
# (c) Shizhao, 2008
# (c) Pywikibot team, 2009-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import re
import pywikibot

from pywikibot import i18n, pagegenerators


def DATA(site, name):
    """Tool to process wikidata."""
    dp = pywikibot.ItemPage(site.data_repository(), name)
    try:
        title = dp.getSitelink(site)
    except pywikibot.NoPage:
        return
    yield pywikibot.Category(site, title)

cat = {
    'wikidata': (DATA, u'Q6547698'),
}

content = {
    'ar': u'هذه الصورة غير الحرة غير مستخدمة في نطاق المقالات، انظر ' +
          u'[[Wikipedia:Non-free content#Policy]]',
    'en': u'This Non-free image NOT used in non-article namespaces,' +
          u' see[[Wikipedia:Non-free content#Policy]]',
    'zh': u'不是使用在条目中的非自由版权图像，根据[[Wikipedia:合理使用]]' +
          u'，不能在非条目名字空间展示：\n',
}


def find_site(site):
    """Function for site codes to be processed."""
    image_no = cat['wikidata'][1]
    repo = site.data_repository()
    dp = pywikibot.ItemPage(repo, image_no)
    dp.get()
    for key in sorted(dp.sitelinks.keys()):
        try:
            s = site.fromDBName(key)
        except pywikibot.SiteDefinitionError:
            pywikibot.output('"%s" is not a valid site. Skipping...'
                                % key)
        if s.family == site.family:
            method = cat['wikidata'][0]
            name = cat['wikidata'][1]
            for p in method(site, name):
                if p.site.lang == s.lang:
                    return p


def main(*args):
    """Process command line arguments."""
    genFactory = pagegenerators.GeneratorFactory()
    for arg in pywikibot.handle_args(args):
        genFactory.handleArg(arg)

    site = pywikibot.Site()
    lcontent = i18n.translate(site, content)
    category = i18n.translate(site, find_site(site).title())
    putmsg = i18n.twtranslate(site.lang, 'remove_edp_images-edit-summary')

    # Checking if lcontent and category exists and then proceeding
    if lcontent and category:
        # from non-free copyright tag category get all EDPtemplate
        templatecat = pywikibot.Category(site, category)
        templatelist = list(templatecat.articles())

        # from References of EDP template get all non-free images
        for template in templatelist:
            for page in pagegenerators.ReferringPageGenerator(template):
                images = pagegenerators.ImagesPageGenerator(page)

                for image in images:
                    imagetitle = image.title()
                    imagepage = pywikibot.FilePage(site, imagetitle)
                    # from imagepage get all usingPages of non-articles
                    pimages = [puseimage for puseimage in imagepage.usingPages() if
                               puseimage.namespace() != 0]
                    for pimage in pimages:
                        ns = pimage.namespace()
                        pimagetitle = pimage.title()
                        c = u'\nFound an used image [[%s]] in [[%s]]: ' \
                            % (imagetitle, pimagetitle)
                        text = pimage.get()
                        m = re.search('<!--(.*?)' + imagetitle + '(.*?)-->', text, re.I)
                        if not m:
                            try:
                                if imagetitle not in text:
                                    # Not namespace eg.[[Image:]]
                                    imagetitlenons = image.title(withNamespace=False)
                                    if imagetitlenons in text:
                                        imagetext = re.search(imagetitlenons + '(.*?)(|)',
                                                              text, re.I).group(0)
                                        text = re.sub(imagetitlenons + '(.*?)(|)',
                                                      '<!--' + lcontent + imagetext + ' \n-->',
                                                      text, re.I)
                                        pywikibot.output(c + u'remove!!!')
                                        pimage.put(text, putmsg % {'title': imagetitle})

                                # used [[Image:wiki.png]] or [[File:B]]  image
                                else:
                                    if '[[' + imagetitle in text:

                                        # Image in userpage, imagepage, and all talkpage
                                        # [[Image:wiki.png]] --> [[:Image:wiki.png]]
                                        if (ns % 2 == 1) or ns == 2 or ns == 6:
                                            text = re.sub('\[\[' + imagetitle + '(.*?)\]\]',
                                                          '<!--' + lcontent + '\n-->' +
                                                          '[[' + ':' + imagetitle + ']]',
                                                          text, re.I)
                                            pywikibot.output(c + u'FIX!')
                                            pimage.put(text, putmsg % {'title': imagetitle})

                                        # Image in template, categorypage,  remove
                                        elif ns in (10, 14):
                                            text = re.sub(
                                                '\[\[' + imagetitle + '(.*?)(|)\]\]',
                                                '<!--' + lcontent + imagetext + '\n-->',
                                                text, re.I)
                                            pywikibot.output(
                                                c + u'Remove!!!')
                                            pimage.put(text, putmsg % {'title': imagetitle})
                                    # Image in <gallery></gallery>
                                    else:
                                        text = re.sub(imagetitle + '(.*?)', '', text, re.I)
                                        text = re.sub('</gallery>\n',
                                                      '</gallery>\n' + '<!--' +
                                                      lcontent + imagetext + '\n-->\n' +
                                                      '[[:' + imagetitle + ']]\n',
                                                      text, re.I)
                                        pywikibot.output(
                                            c + u'FIX <gallery>!')
                                        pimage.put(text, putmsg % {'title': imagetitle})
                            except Exception as e:
                                pywikibot.output('An error of {0} occured.\n'.format(type(e)))
    else:
        pywikibot.showHelp()

if __name__ == '__main__':
    main()
