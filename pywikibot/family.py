# -*- coding: utf-8  -*-

#
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: 7997eaa2dc971556a4fc9bbf1e66b7017f50abfb $'
#

import logging
import re
import collections

from . import config2 as config
import pywikibot

logger = logging.getLogger("pywiki.wiki.family")


# Parent class for all wiki families
class Family(object):
    def __init__(self):
        if not hasattr(self, 'name'):
            self.name = None

        # For interwiki sorting order see
        # https://meta.wikimedia.org/wiki/Interwiki_sorting_order

        # The sorting order by language name from meta
        # MediaWiki:Interwiki_config-sorting_order-native-languagename
        self.alphabetic = [
            'ace', 'kbd', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an',
            'arc', 'roa-rup', 'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'bm',
            'bn', 'bjn', 'zh-min-nan', 'nan', 'map-bms', 'ba', 'be', 'be-x-old',
            'bh', 'bcl', 'bi', 'bg', 'bar', 'bo', 'bs', 'br', 'bxr', 'ca', 'cv',
            'ceb', 'cs', 'ch', 'cbk-zam', 'ny', 'sn', 'tum', 'cho', 'co', 'cy',
            'da', 'dk', 'pdc', 'de', 'dv', 'nv', 'dsb', 'dz', 'mh', 'et', 'el',
            'eml', 'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'hif',
            'fo', 'fr', 'fy', 'ff', 'fur', 'ga', 'gv', 'gag', 'gd', 'gl', 'gan',
            'ki', 'glk', 'gu', 'got', 'hak', 'xal', 'ko', 'ha', 'haw', 'hy',
            'hi', 'ho', 'hsb', 'hr', 'io', 'ig', 'ilo', 'bpy', 'id', 'ia', 'ie',
            'iu', 'ik', 'os', 'xh', 'zu', 'is', 'it', 'he', 'jv', 'kl', 'kn',
            'kr', 'pam', 'krc', 'ka', 'ks', 'csb', 'kk', 'kw', 'rw', 'rn', 'sw',
            'kv', 'kg', 'ht', 'ku', 'kj', 'ky', 'mrj', 'lad', 'lbe', 'lez',
            'lo', 'ltg', 'la', 'lv', 'lb', 'lt', 'lij', 'li', 'ln', 'jbo', 'lg',
            'lmo', 'hu', 'mk', 'mg', 'ml', 'mt', 'mi', 'mr', 'xmf', 'arz',
            'mzn', 'ms', 'min', 'cdo', 'mwl', 'mdf', 'mo', 'mn', 'mus', 'my',
            'nah', 'na', 'fj', 'nl', 'nds-nl', 'cr', 'ne', 'new', 'ja', 'nap',
            'ce', 'frr', 'pih', 'no', 'nb', 'nn', 'nrm', 'nov', 'ii', 'oc',
            'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa', 'pi', 'pfl', 'pag',
            'pnb', 'pap', 'ps', 'koi', 'km', 'pcd', 'pms', 'tpi', 'nds', 'pl',
            'tokipona', 'tp', 'pnt', 'pt', 'aa', 'kaa', 'crh', 'ty', 'ksh',
            'ro', 'rmy', 'rm', 'qu', 'rue', 'ru', 'sah', 'se', 'sm', 'sa', 'sg',
            'sc', 'sco', 'stq', 'st', 'nso', 'tn', 'sq', 'scn', 'si', 'simple',
            'sd', 'ss', 'sk', 'sl', 'cu', 'szl', 'so', 'ckb', 'srn', 'sr', 'sh',
            'su', 'fi', 'sv', 'tl', 'ta', 'shi', 'kab', 'roa-tara', 'tt', 'te',
            'tet', 'th', 'ti', 'tg', 'to', 'chr', 'chy', 've', 'tr', 'tk', 'tw',
            'tyv', 'udm', 'bug', 'uk', 'ur', 'ug', 'za', 'vec', 'vep', 'vi',
            'vo', 'fiu-vro', 'wa', 'zh-classical', 'vls', 'war', 'wo', 'wuu',
            'ts', 'yi', 'yo', 'zh-yue', 'diq', 'zea', 'bat-smg', 'zh', 'zh-tw',
            'zh-cn',
        ]

        # The revised sorting order by first word from meta
        # MediaWiki:Interwiki_config-sorting_order-native-languagename-firstword
        self.alphabetic_revised = [
            'ace', 'kbd', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an',
            'arc', 'roa-rup', 'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'bjn',
            'id', 'ms', 'bm', 'bn', 'zh-min-nan', 'nan', 'map-bms', 'jv', 'su',
            'ba', 'min', 'be', 'be-x-old', 'bh', 'bcl', 'bi', 'bar', 'bo', 'bs',
            'br', 'bug', 'bg', 'bxr', 'ca', 'ceb', 'cv', 'cs', 'ch', 'cbk-zam',
            'ny', 'sn', 'tum', 'cho', 'co', 'cy', 'da', 'dk', 'pdc', 'de', 'dv',
            'nv', 'dsb', 'na', 'dz', 'mh', 'et', 'el', 'eml', 'en', 'myv', 'es',
            'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo', 'fr', 'fy', 'ff', 'fur',
            'ga', 'gv', 'sm', 'gag', 'gd', 'gl', 'gan', 'ki', 'glk', 'gu',
            'got', 'hak', 'xal', 'ko', 'ha', 'haw', 'hy', 'hi', 'ho', 'hsb',
            'hr', 'io', 'ig', 'ilo', 'bpy', 'ia', 'ie', 'iu', 'ik', 'os', 'xh',
            'zu', 'is', 'it', 'he', 'kl', 'kn', 'kr', 'pam', 'ka', 'ks', 'csb',
            'kk', 'kw', 'rw', 'ky', 'rn', 'mrj', 'sw', 'kv', 'kg', 'ht', 'ku',
            'kj', 'lad', 'lbe', 'lez', 'lo', 'la', 'ltg', 'lv', 'to', 'lb',
            'lt', 'lij', 'li', 'ln', 'jbo', 'lg', 'lmo', 'hu', 'mk', 'mg', 'ml',
            'krc', 'mt', 'mi', 'mr', 'xmf', 'arz', 'mzn', 'cdo', 'mwl', 'koi',
            'mdf', 'mo', 'mn', 'mus', 'my', 'nah', 'fj', 'nl', 'nds-nl', 'cr',
            'ne', 'new', 'ja', 'nap', 'ce', 'frr', 'pih', 'no', 'nb', 'nn',
            'nrm', 'nov', 'ii', 'oc', 'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa',
            'pi', 'pfl', 'pag', 'pnb', 'pap', 'ps', 'km', 'pcd', 'pms', 'nds',
            'pl', 'pnt', 'pt', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy',
            'rm', 'qu', 'ru', 'rue', 'sah', 'se', 'sa', 'sg', 'sc', 'sco',
            'stq', 'st', 'nso', 'tn', 'sq', 'scn', 'si', 'simple', 'sd', 'ss',
            'sk', 'sl', 'cu', 'szl', 'so', 'ckb', 'srn', 'sr', 'sh', 'fi', 'sv',
            'tl', 'ta', 'shi', 'kab', 'roa-tara', 'tt', 'te', 'tet', 'th', 'vi',
            'ti', 'tg', 'tpi', 'tokipona', 'tp', 'chr', 'chy', 've', 'tr', 'tk',
            'tw', 'tyv', 'udm', 'uk', 'ur', 'ug', 'za', 'vec', 'vep', 'vo',
            'fiu-vro', 'wa', 'zh-classical', 'vls', 'war', 'wo', 'wuu', 'ts',
            'yi', 'yo', 'zh-yue', 'diq', 'zea', 'bat-smg', 'zh', 'zh-tw',
            'zh-cn',
        ]

        # Order for fy: alphabetical by code, but y counts as i
        self.fyinterwiki = self.alphabetic[:]
        self.fyinterwiki.remove('nb')
        self.fyinterwiki.sort(key=lambda x:
                              x.replace("y", "i") + x.count("y") * "!")

        self.langs = {}

        self.namespacesWithSubpage = [2] + list(range(1, 16, 2))

        # letters that can follow a wikilink and are regarded as part of
        # this link
        # This depends on the linktrail setting in LanguageXx.php and on
        # [[MediaWiki:Linktrail]].
        # Note: this is a regular expression.
        self.linktrails = {
            '_default': u'[a-z]*',
            'ab': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'als': u'[äöüßa-z]*',
            'an': u'[a-záéíóúñ]*',
            'ar': u'[a-zء-ي]*',
            'arz': u'[a-zء-ي]*',
            'av': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'ay': u'[a-záéíóúñ]*',
            'bar': u'[äöüßa-z]*',
            'be': u'[абвгґджзеёжзійклмнопрстуўфхцчшыьэюяćčłńśšŭźža-z]*',
            'be-x-old': u'[абвгґджзеёжзійклмнопрстуўфхцчшыьэюяćčłńśšŭźža-z]*',
            'bg': u'[a-zабвгдежзийклмнопрстуфхцчшщъыьэюя]*',
            'bm': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'bs': u'[a-zćčžšđž]*',
            'bxr': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'ca': u'[a-zàèéíòóúç·ïü]*',
            'cbk-zam': u'[a-záéíóúñ]*',
            'ce': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'crh': u'[a-zâçğıñöşüа-яё“»]*',
            'cs': u'[a-záčďéěíňóřšťúůýž]*',
            'csb': u'[a-zęóąśłżźćńĘÓĄŚŁŻŹĆŃ]*',
            'cu': u'[a-zабвгдеєжѕзїіıићклмнопсстѹфхѡѿцчшщъыьѣюѥѧѩѫѭѯѱѳѷѵґѓђёјйљњќуўџэ҄я“»]*',
            'cv': u'[a-zа-яĕçăӳ"»]*',
            'cy': u'[àáâèéêìíîïòóôûŵŷa-z]*',
            'da': u'[a-zæøå]*',
            'de': u'[a-zäöüß]*',
            'dsb': u'[äöüßa-z]*',
            'el': u'[a-zαβγδεζηθικλμνξοπρστυφχψωςΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩάέήίόύώϊϋΐΰΆΈΉΊΌΎΏΪΫ]*',
            'eml': u'[a-zàéèíîìóòúù]*',
            'es': u'[a-záéíóúñ]*',
            'et': u'[äöõšüža-z]*',
            'fa': u'[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
            'ff': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'fi': u'[a-zäö]*',
            'fiu-vro': u'[äöõšüža-z]*',
            'fo': u'[áðíóúýæøa-z]*',
            'fr': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'frp': u'[a-zàâçéèêîœôû·’æäåāăëēïīòöōùü‘]*',
            'frr': u'[a-zäöüßåāđē]*',
            'fur': u'[a-zàéèíîìóòúù]*',
            'fy': u'[a-zàáèéìíòóùúâêîôûäëïöü]*',
            'gag': u'[a-zÇĞçğİıÖöŞşÜüÂâÎîÛû]*',
            'gl': u'[áâãàéêẽçíòóôõq̃úüűũa-z]*',
            'glk': u'[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
            'gn': u'[a-záéíóúñ]*',
            'gu': u'[઀-૿]*',
            'he': u'[a-zא-ת]*',
            'hr': u'[čšžćđßa-z]*',
            'hsb': u'[äöüßa-z]*',
            'ht': u'[a-zàèòÀÈÒ]*',
            'hu': u'[a-záéíóúöüőűÁÉÍÓÚÖÜŐŰ]*',
            'hy': u'[a-zաբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆև«»]*',
            'is': u'[áðéíóúýþæöa-z-–]*',
            'it': u'[a-zàéèíîìóòúù]*',
            'ka': u'[a-zაბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ“»]*',
            'kk': u'[a-zäçéğıïñöşüýʺʹа-яёәғіқңөұүһٴابپتجحدرزسشعفقكلمنڭەوۇۋۆىيچھ“»]*',
            'kl': u'[a-zæøå]*',
            'koi': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'krc': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'ksh': u'[a-zäöüėëĳßəğåůæœç]*',
            'kv': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'lad': u'[a-záéíóúñ]*',
            'lb': u'[äöüßa-z]*',
            'lbe': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюяӀ1“»]*',
            'lez': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'li': u'[a-zäöüïëéèà]*',
            'lij': u'[a-zàéèíîìóòúù]*',
            'lmo': u'[a-zàéèíîìóòúù]*',
            'ln': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'mg': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'mhr': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'mk': u'[a-zабвгдѓежзѕијклљмнњопрстќуфхцчџш]*',
            'ml': u'[a-zം-ൿ]*',
            'mn': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя“»]*',
            'mr': u'[ऀ-ॣॱ-ॿ﻿‍]*',
            'mrj': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'mwl': u'[áâãàéêẽçíòóôõq̃úüűũa-z]*',
            'myv': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'mzn': u'[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
            'nah': u'[a-záéíóúñ]*',
            'nap': u'[a-zàéèíîìóòúù]*',
            'nds': u'[äöüßa-z]*',
            'nds-nl': u'[a-zäöüïëéèà]*',
            'nl': u'[a-zäöüïëéèà]*',
            'nn': u'[æøåa-z]*',
            'no': u'[æøåa-z]*',
            'oc': u'[a-zàâçéèêîôû]*',
            'or': u'[a-z଀-୿]*',
            'pa': u'[ਁਂਃਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟਠਡਢਣਤਥਦਧਨਪਫਬਭਮਯਰਲਲ਼ਵਸ਼ਸਹ਼ਾਿੀੁੂੇੈੋੌ੍ਖ਼ਗ਼ਜ਼ੜਫ਼ੰੱੲੳa-z]*',
            'pcd': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'pdc': u'[äöüßa-z]*',
            'pfl': u'[äöüßa-z]*',
            'pl': u'[a-zęóąśłżźćńĘÓĄŚŁŻŹĆŃ]*',
            'pms': u'[a-zàéèíîìóòúù]*',
            'pt': u'[a-záâãàéêẽçíòóôõq̃úüűũ]*',
            'qu': u'[a-záéíóúñ]*',
            'rmy': u'[a-zăâîşţșțĂÂÎŞŢȘȚ]*',
            'ro': u'[a-zăâîşţșțĂÂÎŞŢȘȚ]*',
            'ru': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'rue': u'[a-zабвгґдеєжзиіїйклмнопрстуфхцчшщьєюяёъы“»]*',
            'sah': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'scn': u'[a-zàéèíîìóòúù]*',
            'sg': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'sh': u'[a-zčćđžš]*',
            'sk': u'[a-záäčďéíľĺňóôŕšťúýž]*',
            'sl': u'[a-zčćđžš]*',
            'sr': u'[abvgdđežzijklljmnnjoprstćufhcčdžšабвгдђежзијклљмнњопрстћуфхцчџш]*',
            'srn': u'[a-zäöüïëéèà]*',
            'stq': u'[äöüßa-z]*',
            'sv': u'[a-zåäöéÅÄÖÉ]*',
            'szl': u'[a-zęóąśłżźćńĘÓĄŚŁŻŹĆŃ]*',
            'ta': u'[஀-௿]*',
            'te': u'[ఁ-౯]*',
            'tg': u'[a-zабвгдеёжзийклмнопрстуфхчшъэюяғӣқўҳҷцщыь]*',
            'tk': u'[a-zÄäÇçĞğŇňÖöŞşÜüÝýŽž]*',
            'tr': u'[a-zÇĞçğİıÖöŞşÜüÂâÎîÛû]*',
            'tt': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюяӘәӨөҮүҖҗҢңҺһ]*',
            'ty': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'tyv': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'udm': u'[a-zа-яёӝӟӥӧӵ“»]*',
            'uk': u'[a-zабвгґдеєжзиіїйклмнопрстуфхцчшщьєюяёъы“»]*',
            'uz': u'[a-zʻʼ“»]*',
            'vec': u'[a-zàéèíîìóòúù]*',
            'vep': u'[äöõšüža-z]*',
            'vi': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'vls': u'[a-zäöüïëéèà]*',
            'wa': u'[a-zåâêîôûçéè]*',
            'wo': u'[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
            'xal': u'[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
            'xmf': u'[a-zაბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ“»]*',
            'yi': u'[a-zא-ת]*',
            'zea': u'[a-zäöüïëéèà]*',
        }

        # Wikimedia wikis all use "bodyContent" as the id of the <div>
        # element that contains the actual page content; change this for
        # wikis that use something else (e.g., mozilla family)
        self.content_id = "bodyContent"

        # A dictionary where keys are family codes that can be used in
        # inter-family interwiki links. Do not use it directly but
        # get_known_families() instead.

        # TODO: replace this with API interwikimap call
        self.known_families = {
            'abbenormal':       'abbenormal',
            'acronym':          'acronym',
            'advisory':         'advisory',
            'advogato':         'advogato',
            'aew':              'aew',
            'airwarfare':       'airwarfare',
            'aiwiki':           'aiwiki',
            'allwiki':          'allwiki',
            'appropedia':       'appropedia',
            'aquariumwiki':     'aquariumwiki',
            'arxiv':            'arxiv',
            'aspienetwiki':     'aspienetwiki',
            'atmwiki':          'atmwiki',
            'b':                'wikibooks',
            'battlestarwiki':   'battlestarwiki',
            'bemi':             'bemi',
            'benefitswiki':     'benefitswiki',
            'betawiki':         'betawiki',
            'betawikiversity':  'betawikiversity',
            'biblewiki':        'biblewiki',
            'bluwiki':          'bluwiki',
            'botwiki':          'botwiki',
            'boxrec':           'boxrec',
            'brickwiki':        'brickwiki',
            'bridgeswiki':      'bridgeswiki',
            'bugzilla':         'bugzilla',
            'buzztard':         'buzztard',
            'bytesmiths':       'bytesmiths',
            'c2':               'c2',
            'c2find':           'c2find',
            'cache':            'cache',
            'canwiki':          'canwiki',
            'canyonwiki':       'canyonwiki',
            'Ĉej':              'Ĉej',
            'cellwiki':         'cellwiki',
            'centralwikia':     'centralwikia',
            'chapter':          'chapter',
            'chej':             'chej',
            'choralwiki':       'choralwiki',
            'ciscavate':        'ciscavate',
            'citizendium':      'citizendium',
            'ckwiss':           'ckwiss',
            'closed-zh-tw':     'closed-zh-tw',
            'cndbname':         'cndbname',
            'cndbtitle':        'cndbtitle',
            'colab':            'colab',
            'comcom':           'comcom',
            'comixpedia':       'comixpedia',
            'commons':          'commons',
            'communityscheme':  'communityscheme',
            'comune':           'comune',
            'consciousness':    'consciousness',
            'corpknowpedia':    'corpknowpedia',
            'crazyhacks':       'crazyhacks',
            'creatureswiki':    'creatureswiki',
            'cxej':             'cxej',
            'dawiki':           'dawiki',
            'dbdump':           'dbdump',
            'dcc':              'dcc',
            'dcdatabase':       'dcdatabase',
            'dcma':             'dcma',
            'dejanews':         'dejanews',
            'delicious':        'delicious',
            'demokraatia':      'demokraatia',
            'devmo':            'devmo',
            'dict':             'dict',
            'dictionary':       'dictionary',
            'disinfopedia':     'disinfopedia',
            'distributedproofreaders': 'distributedproofreaders',
            'distributedproofreadersca': 'distributedproofreadersca',
            'dk':               'dk',
            'dmoz':             'dmoz',
            'dmozs':            'dmozs',
            'docbook':          'docbook',
#            'doi':              'doi',
            'doom_wiki':        'doom_wiki',
            'download':         'download',
            'drae':             'drae',
            'dreamhost':        'dreamhost',
            'drumcorpswiki':    'drumcorpswiki',
            'dwjwiki':          'dwjwiki',
            'eĉei':             'eĉei',
            'echei':            'echei',
            'ecoreality':       'ecoreality',
            'ecxei':            'ecxei',
            'efnetceewiki':     'efnetceewiki',
            'efnetcppwiki':     'efnetcppwiki',
            'efnetpythonwiki':  'efnetpythonwiki',
            'efnetxmlwiki':     'efnetxmlwiki',
            'elibre':           'elibre',
            'emacswiki':        'emacswiki',
            'energiewiki':      'energiewiki',
            'eokulturcentro':   'eokulturcentro',
            'epo':              'epo',
            'ethnologue':       'ethnologue',
            'evowiki':          'evowiki',
            'exotica':          'exotica',
            'fanimutationwiki': 'fanimutationwiki',
            'finalempire':      'finalempire',
            'finalfantasy':     'finalfantasy',
            'finnix':           'finnix',
            'flickruser':       'flickruser',
            'floralwiki':       'floralwiki',
            'flyerwiki-de':     'flyerwiki-de',
            'foldoc':           'foldoc',
            'forthfreak':       'forthfreak',
            'foundation':       'foundation',
            'foxwiki':          'foxwiki',
            'freebio':          'freebio',
            'freebsdman':       'freebsdman',
            'freeculturewiki':  'freeculturewiki',
            'freedomdefined':   'freedomdefined',
            'freefeel':         'freefeel',
            'freekiwiki':       'freekiwiki',
            'ganfyd':           'ganfyd',
            'gausswiki':        'gausswiki',
            'gentoo-wiki':      'gentoo',
            'genwiki':          'genwiki',
            'globalvoices':     'globalvoices',
            'glossarwiki':      'glossarwiki',
            'glossarywiki':     'glossarywiki',
            'golem':            'golem',
            'google':           'google',
            'googledefine':     'googledefine',
            'googlegroups':     'googlegroups',
            'gotamac':          'gotamac',
            'greatlakeswiki':   'greatlakeswiki',
            'guildwiki':        'guildwiki',
            'gutenberg':        'gutenberg',
            'gutenbergwiki':    'gutenbergwiki',
            'h2wiki':           'h2wiki',
            'hammondwiki':      'hammondwiki',
            'heroeswiki':       'heroeswiki',
            'herzkinderwiki':   'herzkinderwiki',
            'hkmule':           'hkmule',
            'holshamtraders':   'holshamtraders',
            'hrfwiki':          'hrfwiki',
            'hrwiki':           'hrwiki',
            'humancell':        'humancell',
            'hupwiki':          'hupwiki',
            'imdbcharacter':    'imdbcharacter',
            'imdbcompany':      'imdbcompany',
            'imdbname':         'imdbname',
            'imdbtitle':        'imdbtitle',
            'incubator':        'incubator',
            'infoanarchy':      'infoanarchy',
            'infosecpedia':     'infosecpedia',
            'infosphere':       'infosphere',
            'iso639-3':         'iso639-3',
            'iuridictum':       'iuridictum',
            'jameshoward':      'jameshoward',
            'javanet':          'javanet',
            'javapedia':        'javapedia',
            'jefo':             'jefo',
            'jiniwiki':         'jiniwiki',
            'jspwiki':          'jspwiki',
            'jstor':            'jstor',
            'kamelo':           'kamelo',
            'karlsruhe':        'karlsruhe',
            'kerimwiki':        'kerimwiki',
            'kinowiki':         'kinowiki',
            'kmwiki':           'kmwiki',
            'kontuwiki':        'kontuwiki',
            'koslarwiki':       'koslarwiki',
            'kpopwiki':         'kpopwiki',
            'linguistlist':     'linguistlist',
            'linuxwiki':        'linuxwiki',
            'linuxwikide':      'linuxwikide',
            'liswiki':          'liswiki',
            'literateprograms': 'literateprograms',
            'livepedia':        'livepedia',
            'lojban':           'lojban',
            'lostpedia':        'lostpedia',
            'lqwiki':           'lqwiki',
            'lugkr':            'lugkr',
            'luxo':             'luxo',
            'lyricwiki':        'lyricwiki',
            'm':                'meta',
            'm-w':              'm-w',
            'mail':             'mail',
            'mailarchive':      'mailarchive',
            'mariowiki':        'mariowiki',
            'marveldatabase':   'marveldatabase',
            'meatball':         'meatball',
            'mediazilla':       'mediazilla',
            'memoryalpha':      'memoryalpha',
            'meta':             'meta',
            'metawiki':         'metawiki',
            'metawikipedia':    'metawikipedia',
            'mineralienatlas':  'mineralienatlas',
            'moinmoin':         'moinmoin',
            'monstropedia':     'monstropedia',
            'mosapedia':        'mosapedia',
            'mozcom':           'mozcom',
            'mozillawiki':      'mozillawiki',
            'mozillazinekb':    'mozillazinekb',
            'musicbrainz':      'musicbrainz',
            'mw':               'mw',
            'mwod':             'mwod',
            'mwot':             'mwot',
            'n':                'wikinews',
            'netvillage':       'netvillage',
            'nkcells':          'nkcells',
            'nomcom':           'nomcom',
            'nosmoke':          'nosmoke',
            'nost':             'nost',
            'oeis':             'oeis',
            'oldwikisource':    'oldwikisource',
            'olpc':             'olpc',
            'onelook':          'onelook',
            'openfacts':        'openfacts',
            'openstreetmap':    'openstreetmap',
            'openwetware':      'openwetware',
            'openwiki':         'openwiki',
            'opera7wiki':       'opera7wiki',
            'organicdesign':    'organicdesign',
            'orgpatterns':      'orgpatterns',
            'orthodoxwiki':     'orthodoxwiki',
            'osi reference model': 'osi reference model',
            'otrs':             'otrs',
            'otrswiki':         'otrswiki',
            'ourmedia':         'ourmedia',
            'paganwiki':        'paganwiki',
            'panawiki':         'panawiki',
            'pangalacticorg':   'pangalacticorg',
            'patwiki':          'patwiki',
            'perlconfwiki':     'perlconfwiki',
            'perlnet':          'perlnet',
            'personaltelco':    'personaltelco',
            'phpwiki':          'phpwiki',
            'phwiki':           'phwiki',
            'planetmath':       'planetmath',
            'pmeg':             'pmeg',
            'pmwiki':           'pmwiki',
            'psycle':           'psycle',
            'purlnet':          'purlnet',
            'pythoninfo':       'pythoninfo',
            'pythonwiki':       'pythonwiki',
            'pywiki':           'pywiki',
            'q':                'wikiquote',
            'qcwiki':           'qcwiki',
            'quality':          'quality',
            'qwiki':            'qwiki',
            'r3000':            'r3000',
            'raec':             'raec',
            'rakwiki':          'rakwiki',
            'reuterswiki':      'reuterswiki',
            'rev':              'rev',
            'revo':             'revo',
            'rfc':              'rfc',
            'rheinneckar':      'rheinneckar',
            'robowiki':         'robowiki',
            'rowiki':           'rowiki',
            's':                'wikisource',
            's23wiki':          's23wiki',
            'scholar':          'scholar',
            'schoolswp':        'schoolswp',
            'scores':           'scores',
            'scoutwiki':        'scoutwiki',
            'scramble':         'scramble',
            'seapig':           'seapig',
            'seattlewiki':      'seattlewiki',
            'seattlewireless':  'seattlewireless',
            'senseislibrary':   'senseislibrary',
            'silcode':          'silcode',
            'slashdot':         'slashdot',
            'slwiki':           'slwiki',
            'smikipedia':       'smikipedia',
            'sourceforge':      'sourceforge',
            'spcom':            'spcom',
            'species':          'species',
            'squeak':           'squeak',
            'stable':           'stable',
            'strategywiki':     'strategywiki',
            'sulutil':          'sulutil',
            'susning':          'susning',
            'svgwiki':          'svgwiki',
            'svn':              'svn',
            'swinbrain':        'swinbrain',
            'swingwiki':        'swingwiki',
            'swtrain':          'swtrain',
            'tabwiki':          'tabwiki',
            'takipedia':        'takipedia',
            'tavi':             'tavi',
            'tclerswiki':       'tclerswiki',
            'technorati':       'technorati',
            'tejo':             'tejo',
            'tesoltaiwan':      'tesoltaiwan',
            'testwiki':         'testwiki',
            'thelemapedia':     'thelemapedia',
            'theopedia':        'theopedia',
            'theppn':           'theppn',
            'thinkwiki':        'thinkwiki',
            'tibiawiki':        'tibiawiki',
            'ticket':           'ticket',
            'tmbw':             'tmbw',
            'tmnet':            'tmnet',
            'tmwiki':           'tmwiki',
            'tokyonights':      'tokyonights',
            'tools':            'tools',
            'translatewiki':    'translatewiki',
            'trash!italia':     'trash!italia',
            'tswiki':           'tswiki',
            'turismo':          'turismo',
            'tviv':             'tviv',
            'tvtropes':         'tvtropes',
            'twiki':            'twiki',
            'twistedwiki':      'twistedwiki',
            'tyvawiki':         'tyvawiki',
            'uncyclopedia':     'uncyclopedia',
            'unreal':           'unreal',
            'urbandict':        'urbandict',
            'usej':             'usej',
            'usemod':           'usemod',
            'v':                'wikiversity',
            'valuewiki':        'valuewiki',
            'veropedia':        'veropedia',
            'vinismo':          'vinismo',
            'vkol':             'vkol',
            'vlos':             'vlos',
            'voipinfo':         'voipinfo',
            'voy':              'wikivoyage',
            'w':                'wikipedia',
            'warpedview':       'warpedview',
            'webdevwikinl':     'webdevwikinl',
            'webisodes':        'webisodes',
            'webseitzwiki':     'webseitzwiki',
            'wg':               'wg',
            'wiki':             'wiki',
            'wikia':            'wikia',
            'wikianso':         'wikianso',
            'wikiasite':        'wikiasite',
            'wikible':          'wikible',
            'wikibooks':        'wikibooks',
            'wikichat':         'wikichat',
            'wikichristian':    'wikichristian',
            'wikicities':       'wikicities',
            'wikicity':         'wikicity',
            'wikif1':           'wikif1',
            'wikifur':          'wikifur',
            'wikihow':          'wikihow',
            'wikiindex':        'wikiindex',
            'wikilemon':        'wikilemon',
            'wikilivres':       'wikilivres',
            'wikimac-de':       'wikimac-de',
            'wikimac-fr':       'wikimac-fr',
            'wikimedia':        'wikimedia',
            'wikinews':         'wikinews',
            'wikinfo':          'wikinfo',
            'wikinurse':        'wikinurse',
            'wikinvest':        'wikinvest',
            'wikipaltz':        'wikipaltz',
            'wikipedia':        'wikipedia',
            'wikipediawikipedia': 'wikipediawikipedia',
            'wikiquote':        'wikiquote',
            'wikireason':       'wikireason',
            'wikischool':       'wikischool',
            'wikisophia':       'wikisophia',
            'wikisource':       'wikisource',
            'wikispecies':      'wikispecies',
            'wikispot':         'wikispot',
            'wikiti':           'wikiti',
            'wikitravel':       'wikitravel',
            'wikitree':         'wikitree',
            'wikiversity':      'wikiversity',
            'wikiwikiweb':      'wikiwikiweb',
            'wikt':             'wiktionary',
            'wiktionary':       'wiktionary',
            'wipipedia':        'wipipedia',
            'wlug':             'wlug',
            'wm2005':           'wm2005',
            'wm2006':           'wm2006',
            'wm2007':           'wm2007',
            'wm2008':           'wm2008',
            'wm2009':           'wm2009',
            'wm2010':           'wm2010',
            'wmania':           'wmania',
            'wmcz':             'wmcz',
            'wmf':              'wmf',
            'wmrs':             'wmrs',
            'wmse':             'wmse',
            'wookieepedia':     'wookieepedia',
            'world66':          'world66',
            'wowwiki':          'wowwiki',
            'wqy':              'wqy',
            'wurmpedia':        'wurmpedia',
            'wznan':            'wznan',
            'xboxic':           'xboxic',
            'zh-cfr':           'zh-cfr',
            'zrhwiki':          'zrhwiki',
            'zum':              'zum',
            'zwiki':            'zwiki',
            'zzz wiki':         'zzz wiki',
        }

        # A list of category redirect template names in different languages
        self.category_redirect_templates = {
            '_default': []
        }

        # A list of languages that use hard (instead of soft) category redirects
        self.use_hard_category_redirects = []

        # A list of disambiguation template names in different languages
        self.disambiguationTemplates = {
            '_default': []
        }

        # A list of projects that share cross-project sessions.
        self.cross_projects = []

        # A list with the name for cross-project cookies.
        # default for wikimedia centralAuth extensions.
        self.cross_projects_cookies = ['centralauth_Session',
                                       'centralauth_Token',
                                       'centralauth_User']
        self.cross_projects_cookie_username = 'centralauth_User'

        # A list with the name in the cross-language flag permissions
        self.cross_allowed = []

        # A list with the name of the category containing disambiguation
        # pages for the various languages. Only one category per language,
        # and without the namespace, so add things like:
        # 'en': "Disambiguation"
        self.disambcatname = {}

        # On most wikis page names must start with a capital letter, but some
        # languages don't use this.
        self.nocapitalize = []

        # attop is a list of languages that prefer to have the interwiki
        # links at the top of the page.
        self.interwiki_attop = []
        # on_one_line is a list of languages that want the interwiki links
        # one-after-another on a single line
        self.interwiki_on_one_line = []
        # String used as separator between interwiki links and the text
        self.interwiki_text_separator = config.line_separator * 2

        # Similar for category
        self.category_attop = []
        # on_one_line is a list of languages that want the category links
        # one-after-another on a single line
        self.category_on_one_line = []
        # String used as separator between category links and the text
        self.category_text_separator = config.line_separator * 2
        # When both at the bottom should categories come after interwikilinks?
        self.categories_last = []

        # Which languages have a special order for putting interlanguage
        # links, and what order is it? If a language is not in
        # interwiki_putfirst, alphabetical order on language code is used.
        # For languages that are in interwiki_putfirst, interwiki_putfirst
        # is checked first, and languages are put in the order given there.
        # All other languages are put after those, in code-alphabetical
        # order.
        self.interwiki_putfirst = {}

        # Languages in interwiki_putfirst_doubled should have a number plus
        # a list of languages. If there are at least the number of interwiki
        # links, all languages in the list should be placed at the front as
        # well as in the normal list.
        self.interwiki_putfirst_doubled = {}  # THIS APPEARS TO BE UNUSED!

        # Some families, e. g. commons and meta, are not multilingual and
        # forward interlanguage links to another family (wikipedia).
        # These families can set this variable to the name of the target
        # family.
        self.interwiki_forward = None

        # Some families, e. g. wikipedia, receive forwarded interlanguage
        # links from other families, e. g. incubator, commons, or meta.
        # These families can set this variable to the names of their source
        # families.
        self.interwiki_forwarded_from = {}

        # Which language codes no longer exist and by which language code
        # should they be replaced. If for example the language with code xx:
        # now should get code yy:, add {'xx':'yy'} to obsolete. If all
        # links to language xx: should be removed, add {'xx': None}.
        self.obsolete = {}

        # Language codes of the largest wikis. They should be roughly sorted
        # by size.
        self.languages_by_size = []

        # Some languages belong to a group where the possibility is high that
        # equivalent articles have identical titles among the group.
        self.language_groups = {
            # languages using the arabic script (incomplete)
            'arab': [
                'ar', 'arz', 'ps', 'sd', 'ur', 'bjn', 'ckb',
                # languages using multiple scripts, including arabic
                'kk', 'ku', 'tt', 'ug', 'pnb'
            ],
            # languages that use chinese symbols
            'chinese': [
                'wuu', 'zh', 'zh-classical', 'zh-yue', 'gan', 'ii',
                # languages using multiple/mixed scripts, including chinese
                'ja', 'za'
            ],
            # languages that use the cyrillic alphabet
            'cyril': [
                'ab', 'av', 'ba', 'be', 'be-x-old', 'bg', 'bxr', 'ce', 'cu',
                'cv', 'kbd', 'koi', 'kv', 'ky', 'mk', 'lbe', 'mdf', 'mn', 'mo',
                'myv', 'mhr', 'mrj', 'os', 'ru', 'rue', 'sah', 'tg', 'tk',
                'udm', 'uk', 'xal',
                # languages using multiple scripts, including cyrillic
                'ha', 'kk', 'sh', 'sr', 'tt'
            ],
            # languages that use a greek script
            'grec': [
                'el', 'grc', 'pnt'
                # languages using multiple scripts, including greek
            ],
            # languages that use the latin alphabet
            'latin': [
                'aa', 'ace', 'af', 'ak', 'als', 'an', 'ang', 'ast', 'ay', 'bar',
                'bat-smg', 'bcl', 'bi', 'bm', 'br', 'bs', 'ca', 'cbk-zam',
                'cdo', 'ceb', 'ch', 'cho', 'chy', 'co', 'crh', 'cs', 'csb',
                'cy', 'da', 'de', 'diq', 'dsb', 'ee', 'eml', 'en', 'eo', 'es',
                'et', 'eu', 'ext', 'ff', 'fi', 'fiu-vro', 'fj', 'fo', 'fr',
                'frp', 'frr', 'fur', 'fy', 'ga', 'gag', 'gd', 'gl', 'gn', 'gv',
                'hak', 'haw', 'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hz', 'ia',
                'id', 'ie', 'ig', 'ik', 'ilo', 'io', 'is', 'it', 'jbo', 'jv',
                'kaa', 'kab', 'kg', 'ki', 'kj', 'kl', 'kr', 'ksh', 'kw', 'la',
                'lad', 'lb', 'lg', 'li', 'lij', 'lmo', 'ln', 'lt', 'ltg', 'lv',
                'map-bms', 'mg', 'mh', 'mi', 'ms', 'mt', 'mus', 'mwl', 'na',
                'nah', 'nap', 'nds', 'nds-nl', 'ng', 'nl', 'nn', 'no', 'nov',
                'nrm', 'nv', 'ny', 'oc', 'om', 'pag', 'pam', 'pap', 'pcd',
                'pdc', 'pfl', 'pih', 'pl', 'pms', 'pt', 'qu', 'rm', 'rn', 'ro',
                'roa-rup', 'roa-tara', 'rw', 'sc', 'scn', 'sco', 'se', 'sg',
                'simple', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'srn', 'ss', 'st',
                'stq', 'su', 'sv', 'sw', 'szl', 'tet', 'tl', 'tn', 'to', 'tpi',
                'tr', 'ts', 'tum', 'tw', 'ty', 'uz', 've', 'vec', 'vi', 'vls',
                'vo', 'wa', 'war', 'wo', 'xh', 'yo', 'zea', 'zh-min-nan', 'zu',
                # languages using multiple scripts, including latin
                'az', 'chr', 'ckb', 'ha', 'iu', 'kk', 'ku', 'rmy', 'sh', 'sr',
                'tt', 'ug', 'za'
            ],
            # Scandinavian languages
            'scand': [
                'da', 'fo', 'is', 'nb', 'nn', 'no', 'sv'
            ],
        }

        # LDAP domain if your wiki uses LDAP authentication,
        # https://www.mediawiki.org/wiki/Extension:LDAP_Authentication
        self.ldapDomain = ()

        # Allows crossnamespace interwiki linking.
        # Lists the possible crossnamespaces combinations
        # keys are originating NS
        # values are dicts where:
        #   keys are the originating langcode, or _default
        #   values are dicts where:
        #     keys are the languages that can be linked to from the lang+ns, or
        #     '_default'; values are a list of namespace numbers
        self.crossnamespace = collections.defaultdict(dict)
        ##
        # Examples :
        #
        # Allowing linking to pt' 102 NS from any other lang' 0 NS is
        #
        #   self.crossnamespace[0] = {
        #       '_default': { 'pt': [102]}
        #   }
        #
        # While allowing linking from pt' 102 NS to any other lang' = NS is
        #
        #   self.crossnamespace[102] = {
        #       'pt': { '_default': [0]}
        #   }

    @property
    def iwkeys(self):
        if self.interwiki_forward:
            return list(pywikibot.Family(self.interwiki_forward).langs.keys())
        return list(self.langs.keys())

    def _addlang(self, code, location, namespaces={}):
        """Add a new language to the langs and namespaces of the family.
           This is supposed to be called in the constructor of the family.

        """
        self.langs[code] = location
#        for num, val in namespaces.items():
#            self.namespaces[num][code] = val

    def get_known_families(self, site):
        return self.known_families

    def linktrail(self, code, fallback='_default'):
        """Return regex for trailing chars displayed as part of a link.

        Returns a string, not a compiled regular expression object.

        This reads from the family file, and ''not'' from
        [[MediaWiki:Linktrail]], because the MW software currently uses a
        built-in linktrail from its message files and ignores the wiki
        value.

        """
        if code in self.linktrails:
            return self.linktrails[code]
        elif fallback:
            return self.linktrails[fallback]
        else:
            raise KeyError(
                "ERROR: linktrail in language %(language_code)s unknown"
                % {'language_code': code})

    def category_redirects(self, code, fallback="_default"):
        if not hasattr(self, "_catredirtemplates") or \
           code not in self._catredirtemplates:
            self.get_cr_templates(code, fallback)
        if code in self._catredirtemplates:
            return self._catredirtemplates[code]
        else:
            raise KeyError("ERROR: title for category redirect template in "
                           "language '%s' unknown" % code)

    def get_cr_templates(self, code, fallback):
        if not hasattr(self, "_catredirtemplates"):
            self._catredirtemplates = {}
        if code in self.category_redirect_templates:
            cr_template_list = self.category_redirect_templates[code]
            cr_list = list(self.category_redirect_templates[code])
        else:
            cr_template_list = self.category_redirect_templates[fallback]
            cr_list = []
        if cr_template_list:
            cr_template = cr_template_list[0]
            # start with list of category redirect templates from family file
            cr_page = pywikibot.Page(pywikibot.Site(code, self),
                                     "Template:" + cr_template)
            # retrieve all redirects to primary template from API,
            # add any that are not already on the list
            for t in cr_page.backlinks(filterRedirects=True, namespaces=10):
                newtitle = t.title(withNamespace=False)
                if newtitle not in cr_list:
                    cr_list.append(newtitle)
        self._catredirtemplates[code] = cr_list

    def disambig(self, code, fallback='_default'):
        if code in self.disambiguationTemplates:
            return self.disambiguationTemplates[code]
        elif fallback:
            return self.disambiguationTemplates[fallback]
        else:
            raise KeyError(
                "ERROR: title for disambig template in language %s unknown"
                % code)

    # Methods
    def protocol(self, code):
        """
        Can be overridden to return 'https'. Other protocols are not supported.

        """
        return 'http'

    def hostname(self, code):
        """The hostname to use for standard http connections."""
        return self.langs[code]

    def ssl_hostname(self, code):
        """The hostname to use for SSL connections."""
        return self.hostname(code)

    def scriptpath(self, code):
        """The prefix used to locate scripts on this wiki.

        This is the value displayed when you enter {{SCRIPTPATH}} on a
        wiki page (often displayed at [[Help:Variables]] if the wiki has
        copied the master help page correctly).

        The default value is the one used on Wikimedia Foundation wikis,
        but needs to be overridden in the family file for any wiki that
        uses a different value.

        """
        return '/w'

    def ssl_pathprefix(self, code):
        """The path prefix for secure HTTP access."""
        # Override this ONLY if the wiki family requires a path prefix
        return ''

    def path(self, code):
        return '%s/index.php' % self.scriptpath(code)

    def querypath(self, code):
        return '%s/query.php' % self.scriptpath(code)

    def apipath(self, code):
        return '%s/api.php' % self.scriptpath(code)

    def nicepath(self, code):
        return '/wiki/'

    def nice_get_address(self, code, title):
        return '%s%s' % (self.nicepath(code), title)

    def dbName(self, code):
        # returns the name of the MySQL database
        return '%s%s' % (code, self.name)

    # Which version of MediaWiki is used?
    def version(self, code):
        """ Return MediaWiki version number as a string.
        Use LooseVersion from distutils.version to compare version strings.

        """
        # Here we return the latest mw release for downloading
        return '1.23.1'

    @pywikibot.deprecated("version()")
    def versionnumber(self, code):
        """ DEPRECATED, use version() instead and use
        distutils.version.LooseVersion to compare version strings.
        Return an int identifying MediaWiki version.

        Currently this is implemented as returning the minor version
        number; i.e., 'X' in version '1.X.Y'

        """
        R = re.compile(r"(\d+).(\d+)")
        M = R.search(self.version(code))
        if not M:
            # Version string malformatted; assume it should have been 1.10
            return 10
        return 1000 * int(M.group(1)) + int(M.group(2)) - 1000

    def code2encoding(self, code):
        """Return the encoding for a specific language wiki"""
        return 'utf-8'

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific language
           wiki"""
        return self.code2encoding(code),

    # aliases
    def encoding(self, code):
        """Return the encoding for a specific language wiki"""
        return self.code2encoding(code)

    def encodings(self, code):
        """Return a list of historical encodings for a specific language
           wiki"""
        return self.code2encodings(code)

    def __cmp__(self, otherfamily):
        try:
            return cmp(self.name, otherfamily.name)
        except AttributeError:
            return cmp(id(self), id(otherfamily))

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Family("%s")' % self.name

    def RversionTab(self, code):
        """Change this to some regular expression that shows the page we
        found is an existing page, in case the normal regexp does not work.

        """
        return None

    def has_query_api(self, code):
        """Is query.php installed in the wiki?"""
        return False

    def shared_image_repository(self, code):
        """Return the shared image repository, if any."""
        return (None, None)

    def shared_data_repository(self, code, transcluded=False):
        """Return the shared Wikibase repository, if any."""
        return (None, None)

    @pywikibot.deprecated("Site.getcurrenttime()")
    def server_time(self, code):
        """
        DEPRECATED, use Site.getcurrenttime() instead
        Return a datetime object representing server time"""
        return pywikibot.Site(code, self).getcurrenttime()

    def isPublic(self, code):
        """Does the wiki require logging in before viewing it?"""
        return True

    def post_get_convert(self, site, getText):
        """Do a conversion on the retrieved text from the wiki
        i.e. Esperanto X-conversion """
        return getText

    def pre_put_convert(self, site, putText):
        """Do a conversion on the text to insert on the wiki
        i.e. Esperanto X-conversion """
        return putText


# Parent class for all wikimedia families
class WikimediaFamily(Family):
    def __init__(self):
        super(WikimediaFamily, self).__init__()

        self.namespacesWithSubpage.extend([4, 12])

        # CentralAuth cross avaliable projects.
        self.cross_projects = [
            'commons', 'incubator', 'mediawiki', 'meta', 'species', 'test',
            'wikibooks', 'wikidata', 'wikinews', 'wikipedia', 'wikiquote',
            'wikisource', 'wikiversity', 'wiktionary',
        ]

    def version(self, code):
        """Return Wikimedia projects version number as a string.
        Use LooseVersion from distutils.version to compate versions.

        """
        # Here we return the latest mw release of wikimedia projects
        return '1.24wmf14'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

    def protocol(self, code):
        return 'https'
