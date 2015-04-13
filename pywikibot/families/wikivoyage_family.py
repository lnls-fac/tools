# -*- coding: utf-8 -*-

__version__ = '$Id: 4f89641dc44ae270ec38152de0d65c808ee3fa55 $'

# The new wikivoyage family that is hosted at wikimedia

from pywikibot import family


class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'wikivoyage'
        self.languages_by_size = [
            'en', 'de', 'fr', 'it', 'pt', 'nl', 'pl', 'ru', 'es', 'vi', 'sv',
            'zh', 'he', 'ro', 'uk', 'el',
        ]

        self.langs = dict([(lang, '%s.wikivoyage.org' % lang)
                           for lang in self.languages_by_size])
        # Global bot allowed languages on https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['es', 'ru', ]

    def shared_data_repository(self, code, transcluded=False):
        return ('wikidata', 'wikidata')
