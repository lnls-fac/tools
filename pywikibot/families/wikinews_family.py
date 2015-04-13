# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id: 9e2f2b2f0c5c87b7ce052eb7369328a3a6caf598 $'


# The Wikimedia family that is known as Wikinews
class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'wikinews'

        self.languages_by_size = [
            'sr', 'en', 'fr', 'pl', 'de', 'it', 'es', 'pt', 'ru', 'ca', 'zh',
            'sv', 'ja', 'ta', 'el', 'cs', 'ar', 'uk', 'fa', 'fi', 'ro', 'tr',
            'he', 'bg', 'sq', 'no', 'ko', 'eo', 'bs',
        ]

        self.langs = dict([(lang, '%s.wikinews.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['ca', 'cs', 'en', 'fa', 'ko', ]

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are
        # put after those, in code-alphabetical order.
        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'fi': self.alphabetic,
            'fr': self.alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': self.alphabetic,
        }

        self.obsolete = {
            'hu': None,  # https://bugzilla.wikimedia.org/show_bug.cgi?id=28342
            'jp': 'ja',
            'nb': 'no',
            'nl': None,  # https://bugzilla.wikimedia.org/show_bug.cgi?id=20325
            'sd': None,
            'th': None,  # https://bugzilla.wikimedia.org/show_bug.cgi?id=28341
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }
