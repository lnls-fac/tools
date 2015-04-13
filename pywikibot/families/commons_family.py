# -*- coding: utf-8  -*-

__version__ = '$Id: 39375c9252beca882e3114c5aca2c5c3653c7acd $'

from pywikibot import family


# The Wikimedia Commons family
class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'commons'
        self.langs = {
            'commons': 'commons.wikimedia.org',
        }

        self.interwiki_forward = 'wikipedia'

        self.category_redirect_templates = {
            'commons': (
                u'Category redirect',
                u'Categoryredirect',
                u'Catredirect',
                u'Cat redirect',
                u'Catredir',
                u'Cat-red',
                u'See cat',
                u'Seecat',
                u'See category',
                u'Redirect category',
                u'Redirect cat',
                u'Redir cat',
                u'Synonym taxon category redirect',
                u'Invalid taxon category redirect',
                u'Monotypic taxon category redirect',
            ),
        }

        self.disambcatname = {
            'commons':  u'Disambiguation'
        }

    def shared_data_repository(self, code, transcluded=False):
        return ('wikidata', 'wikidata')
