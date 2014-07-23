# -*- coding: utf-8 -*-
"""
Help sysops to quickly check and/or delete pages listed for speedy deletion.

This bot trawls through candidates for speedy deletion in a fast and
semi-automated fashion.  It displays the contents of each page one at a time
and provides a prompt for the user to skip or delete the page.
Of course, this will require a sysop account.

Future upcoming options include the ability to untag a page as not being
eligible for speedy deletion, as well as the option to commute its sentence to
Proposed Deletion (see [[en:WP:PROD]] for more details).  Also, if the article
text is long, to prevent terminal spamming, it might be a good idea to truncate
it just to the first so many bytes.

WARNING: This tool shows the contents of the top revision only.  It is possible
that a vandal has replaced a perfectly good article with nonsense, which has
subsequently been tagged by someone who didn't realize it was previously a good
article.  The onus is on you to avoid making these mistakes.

NOTE: This script currently only works for the Wikipedia project.

"""

#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, pagegenerators, Bot
import time


class SpeedyBot(Bot):
    """
    This bot will load a list of pages from the category of candidates for
    speedy deletion on the language's wiki and give the user an interactive
    prompt to decide whether each should be deleted or not.
    """

    csd_cat_item = pywikibot.ItemPage(
        pywikibot.Site('wikidata', 'wikidata').data_repository(), 'Q5964')

    csd_cat_title = {
        'wikiversity': {
            'beta': u'Category:Candidates for speedy deletion',
            'cs': u'Kategorie:Stránky ke smazání',
            'de': u'Kategorie:Wikiversity:Löschen',
            'el': u'Κατηγορία:Σελίδες για γρήγορη διαγραφή',
            'en': u'Category:Candidates for speedy deletion',
            'es': u'Categoría:Wikiversidad:Borrar (definitivo)',
            'it': u'Categoria:Da cancellare subito',
            'ja': u'Category:Candidates for speedy deletion',
            'pt': u'Categoria:!Páginas para eliminação rápida',
        },
        'wiktionary': {
            'ar': u'تصنيف:صفحات حذف سريع',
            'en': u'Category:Candidates for speedy deletion',
            'fi': u'Luokka:Roskaa',
            'fr': u'Catégorie:Pages à supprimer rapidement',
            'ja': u'Category:即時削除',
            'simple': u'Category:Quick deletion requests',
            'tt': u'Törkem:Candidates for speedy deletion',
            'zh': u'Category:快速删除候选',
        },
        'wikibooks': {
            'ar': u'تصنيف:صفحات حذف سريع',
            'ca': u'Categoria:Elements a eliminar',
            'en': u'Category:Candidates for speedy deletion',
            'es': u'Categoría:Wikilibros:Borrar',
            'it': u'Categoria:Da cancellare subito',
            'ja': u'Category:即時削除',
            'pl': u'Kategoria:Ekspresowe kasowanko',
            'zh': u'Category:快速删除候选',
        },
        'meta': {'meta': u'Category:Deleteme'},
        'incubator': {'incubator': u'Category:Maintenance:Delete'},
        'mediawiki': {'mediawiki': u'Category:Candidates for deletion'},
    }

    # If the site has several templates for speedy deletion, it might be
    # possible to find out the reason for deletion by the template used.
    # _default will be used if no such semantic template was used.
    deletion_messages = {
        'wikipedia': {
            'ar': {
                '_default': u'حذف مرشح للحذف السريع حسب [[وProject:حذف سريع|معايير الحذف السريع]]',
            },
            'cs': {
                '_default': u'Bylo označeno k [[Wikipedie:Rychlé smazání|rychlému smazání]]',
            },
            'de': {
                '_default': u'Lösche Artikel mit [[Wikipedia:Schnelllöschantrag|Schnelllöschantrag]]',
            },
            'en': {
                '_default':      u'Deleting candidate for speedy deletion per [[WP:CSD|CSD]]',
                'db-author':     u'Deleting page per [[WP:CSD|CSD]] G7: Author requests deletion and is its only editor.',
                'db-nonsense':   u'Deleting page per [[WP:CSD|CSD]] G1: Page is patent nonsense or gibberish.',
                'db-test':       u'Deleting page per [[WP:CSD|CSD]] G2: Test page.',
                'db-nocontext':  u'Deleting page per [[WP:CSD|CSD]] A1: Short article that provides little or no context.',
                'db-empty':      u'Deleting page per [[WP:CSD|CSD]] A1: Empty article.',
                'db-attack':     u'Deleting page per [[WP:CSD|CSD]] G10: Page that exists solely to attack its subject.',
                'db-catempty':   u'Deleting page per [[WP:CSD|CSD]] C1: Empty category.',
                'db-band':       u'Deleting page per [[WP:CSD|CSD]] A7: Article about a non-notable band.',
                'db-banned':     u'Deleting page per [[WP:CSD|CSD]] G5: Page created by a banned user.',
                'db-bio':        u'Deleting page per [[WP:CSD|CSD]] A7: Article about a non-notable person.',
                'db-notenglish': u'Deleting page per [[WP:CSD|CSD]] A2: Article isn\'t written in English.',
                'db-copyvio':    u'Deleting page per [[WP:CSD|CSD]] G12: Page is a blatant copyright violation.',
                'db-repost':     u'Deleting page per [[WP:CSD|CSD]] G4: Recreation of previously deleted material.',
                'db-vandalism':  u'Deleting page per [[WP:CSD|CSD]] G3: Blatant vandalism.',
                'db-talk':       u'Deleting page per [[WP:CSD|CSD]] G8: Talk page of a deleted or non-existent page.',
                'db-spam':       u'Deleting page per [[WP:CSD|CSD]] G11: Blatant advertising.',
                'db-disparage':  u'Deleting page per [[WP:CSD|CSD]] T1: Divisive or inflammatory template.',
                'db-r1':         u'Deleting page per [[WP:CSD|CSD]] R1: Redirect to a deleted or non-existent page.',
                'db-experiment': u'Deleting page per [[WP:CSD|CSD]] G2: Page was created as an experiment.',
            },
            'fa': {
                '_default': u'حذف مرشَّح للحذف السريع حسب [[ويكيبيديا:حذف سريع|معايير الحذف السريع]]',
            },
            'he': {
                '_default': u'מחיקת מועמד למחיקה מהירה לפי [[ויקיפדיה:מדיניות המחיקה|מדיניות המחיקה]]',
                u'גם בוויקישיתוף': u'הקובץ זמין כעת בוויקישיתוף.',
            },
            'ja': {
                '_default': u'[[WP:CSD|即時削除の方針]]に基づい削除',
            },
            'pt': {
                '_default': u'Apagando página por [[Wikipedia:Páginas para eliminar|eliminação rápida]]',
            },
            'pl': {
                '_default': u'Usuwanie artykułu zgodnie z zasadami [[Wikipedia:Ekspresowe kasowanko|ekspresowego kasowania]]',
            },
            'it': {
                '_default': u'Rimuovo pagina che rientra nei casi di [[Wikipedia:IMMEDIATA|cancellazione immediata]].',
            },
            'zh': {
                '_default': u'[[WP:CSD]]',
                'advert': 'ad',
                'db-blanked': 'auth',
                'db-spam': u'[[WP:CSD#G11|CSD G11]]: 廣告、宣傳頁面',
                'db-rediruser': u'[[WP:CSD#O1|CSD O6]] 沒有在使用的討論頁',
                'notchinese': u'[[WP:CSD#G7|CSD G7]]: 非中文條目且長時間未翻譯',
                'db-vandalism': 'vand',
                u'翻译': 'oprj',
                u'翻譯': 'oprj',
                'notchinese': 'oprj',
                'notmandarin': 'oprj',
                'no source': u'[[WP:CSD#I3|CSD I3]]: 沒有來源連結，無法確認來源與版權資訊',
                'no license': u'[[WP:CSD#I3|CSD I3]]: 沒有版權模板，無法確認版權資訊',
                'unknown': u'[[WP:CSD#I3|CSD I3]]: 沒有版權模板，無法確認版權資訊',
                'temppage': u'[[WP:CSD]]: 臨時頁面',
                'nowcommons': 'commons',
                'roughtranslation': 'mactra',
            },
        },
        'wikinews': {
            'en': {
                '_default': u'[[WN:CSD]]',
            },
            'zh': {
                '_default': u'[[WN:CSD]]',
            },
        },
    }

    # Default reason for deleting a talk page.
    talk_deletion_msg = {
        'wikipedia': {
            'ar': u'صفحة نقاش يتيمة',
            'cs': u'Osiřelá diskusní stránka',
            'de': u'Verwaiste Diskussionsseite',
            'en': u'Orphaned talk page',
            'fa': u'بحث یتیم',
            'fr': u'Page de discussion orpheline',
            'he': u'דף שיחה של ערך שנמחק',
            'it': u'Rimuovo pagina di discussione di una pagina già cancellata',
            'pl': u'Osierocona strona dyskusji',
            'pt': u'Página de discussão órfã',
            'zh': u'[[WP:CSD#O1|CSD O1 O2 O6]] 沒有在使用的討論頁',
        },
        'wikinews': {
            'en': u'Orphaned talk page',
            'zh': u'[[WN:CSD#O1|CSD O1 O2 O6]] 沒有在使用的討論頁',
        }
    }

    # A list of often-used reasons for deletion. Shortcuts are keys, and
    # reasons are values. If the user enters a shortcut, the associated reason
    # will be used.
    delete_reasons = {
        'wikipedia': {
            'de': {
                'asdf':  u'Tastaturtest',
                'egal':  u'Eindeutig irrelevant',
                'ka':    u'Kein Artikel',
                'mist':  u'Unsinn',
                'move':  u'Redirectlöschung, um Platz für Verschiebung zu schaffen',
                'nde':   u'Nicht in deutscher Sprache verfasst',
                'pfui':  u'Beleidigung',
                'redir': u'Unnötiger Redirect',
                'spam':  u'Spam',
                'web':   u'Nur ein Weblink',
                'wg':    u'Wiedergänger (wurde bereits zuvor gelöscht)',
            },
            'it': {
                'test': u'Si tratta di un test',
                'vandalismo': u'Caso di vandalismo',
                'copyviol': 'Violazione di copyright',
                'redirect': 'Redirect rotto o inutile',
                'spam': 'Spam',
                'promo': 'Pagina promozionale',
            },
            'ja': {
                'cont': u'[[WP:CSD]] 全般1 意味不明な内容のページ',
                'test': u'[[WP:CSD]] 全般2 テスト投稿',
                'vand': u'[[WP:CSD]] 全般3 荒らしand/orいたずら',
                'ad': u'[[WP:CSD]] 全般4 宣伝',
                'rep': u'[[WP:CSD]] 全般5 削除されたページの改善なき再作成',
                'cp': u'[[WP:CSD]] 全般6 コピペ移動or分割',
                'sh': u'[[WP:CSD]] 記事1 短すぎ',
                'nd': u'[[WP:CSD]] 記事1 定義なし',
                'auth': u'[[WP:CSD]] 記事3 投稿者依頼or初版立項者による白紙化',
                'nr': u'[[WP:CSD]] リダイレクト1 無意味なリダイレクト',
                'nc': u'[[WP:CSD]] リダイレクト2 [[WP:NC]]違反',
                'ren': u'[[WP:CSD]] リダイレクト3 改名提案を経た曖昧回避括弧付きの移動の残骸',
                'commons': u'[[WP:CSD]] マルチメディア7 コモンズの画像ページ',
                'tmp': u'[[WP:CSD]] テンプレート1 初版投稿者依頼',
                'uau': u'[[WP:CSD]] 利用者ページ1 本人希望',
                'nuu': u'[[WP:CSD]] 利用者ページ2 利用者登録されていない利用者ページ',
                'ipu': u'[[WP:CSD]] 利用者ページ3 IPユーザの利用者ページ',
            },
            'zh': {
                'empty': u'[[WP:CSD#G1]]: 沒有實際內容或歷史記錄的文章。',
                'test': u'[[WP:CSD#G2]]: 測試頁',
                'vand': u'[[WP:CSD#G3]]: 純粹破壞',
                'rep': u'[[WP:CSD#G5]]: 經討論被刪除後又重新創建的內容',
                'repa': u'[[WP:CSD#G5]]: 重複的文章',
                'oprj': u'[[WP:CSD#G7]]: 內容來自其他中文計劃',
                'move': u'[[WP:CSD#G8]]: 依[[Wikipedia:移動請求|移動請求]]暫時刪除以進行移動或合併頁面之工作',
                'auth': u'[[WP:CSD#G10]]: 原作者請求',
                'ad': u'[[WP:CSD#G11]]: 明顯的以廣告宣傳為目而建立的頁面',
                'adc': u'[[WP:CSD#G11]]: 只有條目名稱中的人物或團體之聯絡資訊',
                'bio': u'[[WP:CSD#G12]]: 未列明來源及語調負面的生者傳記',
                'mactra': u'[[WP:CSD#G13]]: 明顯的機器翻譯',
                'notrans': u'[[WP:CSD#G14]]: 未翻譯的頁面',
                'isol': u'[[WP:CSD#G15]]: 孤立頁面',
                'isol-f': u'[[WP:CSD#G15]]: 孤立頁面-沒有對應檔案的檔案頁面',
                'isol-sub': u'[[WP:CSD#G15]]: 孤立頁面-沒有對應母頁面的子頁面',
                'tempcp': u'[[WP:CSD#G16]]: 臨時頁面依然侵權',
                'cont': u'[[WP:CSD#A1]]: 非常短，而且沒有定義或內容。',
                'nocont': u'[[WP:CSD#A2]]: 內容只包括外部連接、參見、圖書參考、類別標籤、模板標籤、跨語言連接的條目',
                'nc': u'[[WP:CSD#A3]]: 跨計劃內容',
                'cn': u'[[WP:CSD#R2]]: 跨空間重定向',
                'wr': u'[[WP:CSD#R3]]: 錯誤重定向',
                'slr': u'[[WP:CSD#R5]]: 指向本身的重定向或循環的重定向',
                'repi': u'[[WP:CSD#F1]]: 重複的檔案',
                'lssd': u'[[WP:CSD#F3]]: 沒有版權或來源資訊，無法確認圖片是否符合方針要求',
                'nls': u'[[WP:CSD#F3]]: 沒有版權模板，無法確認版權資訊',
                'svg': u'[[WP:CSD#F5]]: 被高解析度與SVG檔案取代的圖片',
                'ui': u'[[WP:CSD#F6]]: 圖片未使用且不自由',
                'commons': u'[[WP:CSD#F7]]: 此圖片已存在於[[:commons:|維基共享資源]]',
                'urs': u'[[WP:CSD#O1]]: 用戶請求刪除自己的用戶頁子頁面',
                'anou': u'[[WP:CSD#O3]]: 匿名用戶的用戶討論頁，其中的內容不再有用',
                'uc': u'[[WP:CSD#O4]]: 空類別',
                'tmp': u'[[WP:CSD]]: 臨時頁面',
            },
        },
    }

    def __init__(self, site):
        """
        Constructor.

        @param site: the site to work on
        @type  site: pywikibot.APISite

        """
        self.site = site
        csd_cat = i18n.translate(self.site, self.csd_cat_title,
                                 fallback=False)
        if csd_cat is None and \
        self.csd_cat_item.site is self.site.data_repository():
            # try to get the category title from the Wikibase item
            self.csd_cat_item.get()
            csd_cat = self.csd_cat_item.sitelinks.get(self.site.dbName(), None)

        if csd_cat is None:
            raise pywikibot.Error(u'No category for speedy deletion found '
                                  u'for %s' % self.site)

        self.csd_cat = pywikibot.Category(self.site, csd_cat)
        self.saved_progress = None
        self.preloadingGen = None

    def guess_reason_for_deletion(self, page):
        reason = None
        # TODO: The following check loads the page 2 times. Find a better way to
        # do it.
        if page.isTalkPage() and (page.toggleTalkPage().isRedirectPage() or
                                  not page.toggleTalkPage().exists()):
            # This is probably a talk page that is orphaned because we
            # just deleted the associated article.
            reason = i18n.translate(self.site, self.talk_deletion_msg)
        else:
            # Try to guess reason by the template used
            templateNames = page.templatesWithParams()
            reasons = i18n.translate(self.site, self.deletion_messages)

            for templateName in templateNames:
                if templateName[0].lower() in reasons:
                    if type(reasons[templateName[0].lower()]) is not unicode:
                        # Make alias to delete_reasons
                        reason = i18n.translate(
                            self.site,
                            self.delete_reasons)[reasons[templateName[0].lower()]]
                    else:
                        reason = reasons[templateName[0].lower()]
                    break
        if not reason:
            # Unsuccessful in guessing the reason. Use a default message.
            reason = reasons['_default']
        return reason

    def get_reason_for_deletion(self, page):
        suggested_reason = self.guess_reason_for_deletion(page)
        pywikibot.output(
            u'The suggested reason is: \03{lightred}%s\03{default}'
            % suggested_reason)

        # We don't use i18n.translate() here because for some languages the
        # entry is intentionally left out.
        if self.site.family.name in self.delete_reasons and \
        page.site.lang in self.delete_reasons[self.site.family.name]:
            local_reasons = i18n.translate(page.site.lang,
                                           self.delete_reasons)
            pywikibot.output(u'')
            local_reasone_key = local_reasons.keys()
            local_reasone_key.sort()
            for key in local_reasone_key:
                pywikibot.output((key + ':').ljust(8) + local_reasons[key])
            pywikibot.output(u'')
            reason = pywikibot.input(
                u'Please enter the reason for deletion, choose a default '
                u'reason,\nor press enter for the suggested message:')
            if reason.strip() in local_reasons:
                reason = local_reasons[reason]
        else:
            reason = pywikibot.input(
                u'Please enter the reason for deletion,\n'
                u'or press enter for the suggested message:')

        return reason or suggested_reason

    def run(self):
        """
        Start the bot's action.
        """

        start_from_beginning = True
        while True:
            if start_from_beginning:
                self.saved_progress = None
            self.refresh_generator()
            count = 0
            for page in self.preloading_gen:
                try:
                    page_text = page.get(get_redirect=True).split("\n")
                    count += 1
                except pywikibot.NoPage:
                    pywikibot.output(u'Page %s does not exist or has already '
                                     u'been deleted, skipping.'
                                     % page.title(asLink=True))
                    continue
                self.current_page = page
                pywikibot.output(u'-  -  -  -  -  -  -  -  -  ')
                if len(page_text) > 75:
                    pywikibot.output('The page detail is too many lines, '
                                     u'only output first 50 lines:')
                    pywikibot.output(u'-  ' * 9)
                    pywikibot.output(u'\n'.join(page_text[:50]))
                else:
                    pywikibot.output(u'\n'.join(page_text))
                pywikibot.output(u'-  -  -  -  -  -  -  -  -  ')
                choice = pywikibot.inputChoice(u'Input action?',
                                               ['delete', 'skip', 'update',
                                                'quit'],
                                               ['d', 'S', 'u', 'q'], 'S')
                if choice == 'q':
                    self.quit()
                elif choice == 'u':
                    pywikibot.output(u'Updating from CSD category.')
                    self.saved_progress = page.title()
                    start_from_beginning = False
                    self.quit()
                elif choice == 'd':
                    reason = self.get_reason_for_deletion(page)
                    pywikibot.output(
                        u'The chosen reason is: \03{lightred}%s\03{default}'
                        % reason)
                    page.delete(reason, prompt=False)
                else:
                    pywikibot.output(u'Skipping page %s' % page.title())
                start_from_beginning = True
            if count == 0:
                if start_from_beginning:
                    pywikibot.output(
                        u'There are no pages to delete.\n'
                        u'Waiting for 30 seconds or press Ctrl+C to quit...')
                    time.sleep(30)
                else:
                    start_from_beginning = True

    def refresh_generator(self):
        generator = pagegenerators.CategorizedPageGenerator(
            self.csd_cat, start=self.saved_progress)
        # wrap another generator around it so that we won't produce orphaned
        # talk pages.
        generator2 = pagegenerators.PageWithTalkPageGenerator(generator)
        self.preloading_gen = pagegenerators.PreloadingGenerator(generator2,
                                                                 pageNumber=20)


def main():
    # read command line parameters
    for arg in pywikibot.handleArgs():
        pass  # No args yet

    bot = SpeedyBot(site=pywikibot.Site())
    bot.run()

if __name__ == "__main__":
    main()
