# -*- coding: utf-8  -*-
"""
This module offers a wide variety of page generators. A page generator is an
object that is iterable (see http://legacy.python.org/dev/peps/pep-0255/ ) and
that yields page objects on which other scripts can then work.

Pagegenerators.py cannot be run as script. For testing purposes listpages.py can
be used instead, to print page titles to standard output.

These parameters are supported to specify which pages titles to print:

&params;
"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: aad6df123c3c69e4fbc1e6a4ea9234746ee9ba86 $'
#

import codecs
import itertools
import re
import pywikibot
from pywikibot import date
from pywikibot import config
from pywikibot import deprecate_arg, i18n
from pywikibot.comms import http
import pywikibot.data.wikidataquery as wdquery

# ported from version 1 for backwards-compatibility
# most of these functions just wrap a Site or Page method that returns
# a generator

parameterHelp = u"""\
-cat              Work on all pages which are in a specific category.
                  Argument can also be given as "-cat:categoryname" or
                  as "-cat:categoryname|fromtitle" (using # instead of |
                  is also allowed in this one and the following)

-catr             Like -cat, but also recursively includes pages in
                  subcategories, sub-subcategories etc. of the
                  given category.
                  Argument can also be given as "-catr:categoryname" or
                  as "-catr:categoryname|fromtitle".

-subcats          Work on all subcategories of a specific category.
                  Argument can also be given as "-subcats:categoryname" or
                  as "-subcats:categoryname|fromtitle".

-subcatsr         Like -subcats, but also includes sub-subcategories etc. of
                  the given category.
                  Argument can also be given as "-subcatsr:categoryname" or
                  as "-subcatsr:categoryname|fromtitle".

-uncat            Work on all pages which are not categorised.

-uncatcat         Work on all categories which are not categorised.

-uncatfiles       Work on all files which are not categorised.

-file             Read a list of pages to treat from the named text file.
                  Page titles in the file must be enclosed with [[brackets]].
                  Argument can also be given as "-file:filename".

-filelinks        Work on all pages that use a certain image/media file.
                  Argument can also be given as "-filelinks:filename".

-search           Work on all pages that are found in a MediaWiki search
                  across all namespaces.

-namespace        Filter the page generator to only yield pages in the
-ns               specified namespaces. Separate multiple namespace
                  numbers with commas. Example "-ns:0,2,4"
                  If used with -newpages, -namepace/ns must be provided
                  before -newpages.
                  If used with -recentchanges, efficiency is improved if
                  -namepace/ns is provided before -recentchanges.

-interwiki        Work on the given page and all equivalent pages in other
                  languages. This can, for example, be used to fight
                  multi-site spamming.
                  Attention: this will cause the bot to modify
                  pages on several wiki sites, this is not well tested,
                  so check your edits!

-limit:n          When used with any other argument that specifies a set
                  of pages, work on no more than n pages in total

-links            Work on all pages that are linked from a certain page.
                  Argument can also be given as "-links:linkingpagetitle".

-imagesused       Work on all images that contained on a certain page.
                  Argument can also be given as "-imagesused:linkingpagetitle".

-newimages        Work on the 100 newest images. If given as -newimages:x,
                  will work on the x newest images.

-newpages         Work on the most recent new pages. If given as -newpages:x,
                  will work on the x newest pages.

-recentchanges    Work on the pages with the most recent changes. If
                  given as -recentchanges:x, will work on the x most recently
                  changed pages.

-ref              Work on all pages that link to a certain page.
                  Argument can also be given as "-ref:referredpagetitle".

-start            Specifies that the robot should go alphabetically through
                  all pages on the home wiki, starting at the named page.
                  Argument can also be given as "-start:pagetitle".

                  You can also include a namespace. For example,
                  "-start:Template:!" will make the bot work on all pages
                  in the template namespace.

-prefixindex      Work on pages commencing with a common prefix.

-step:n           When used with any other argument that specifies a set
                  of pages, only retrieve n pages at a time from the wiki
                  server

-titleregex       Work on titles that match the given regular expression.

-transcludes      Work on all pages that use a certain template.
                  Argument can also be given as "-transcludes:Title".

-unusedfiles      Work on all description pages of images/media files that are
                  not used anywhere.
                  Argument can be given as "-unusedfiles:n" where
                  n is the maximum number of articles to work on.

-lonelypages      Work on all articles that are not linked from any other article.
                  Argument can be given as "-lonelypages:n" where
                  n is the maximum number of articles to work on.

-unwatched        Work on all articles that are not watched by anyone.
                  Argument can be given as "-unwatched:n" where
                  n is the maximum number of articles to work on.

-usercontribs     Work on all articles that were edited by a certain user :
                  Example : -usercontribs:DumZiBoT

-weblink          Work on all articles that contain an external link to
                  a given URL; may be given as "-weblink:url"

-withoutinterwiki Work on all pages that don't have interlanguage links.
                  Argument can be given as "-withoutinterwiki:n" where
                  n is some number (??).

-wikidataquery    Takes a WikidataQuery query string like claim[31:12280]
                  and works on the resulting pages.

-random           Work on random pages returned by [[Special:Random]].
                  Can also be given as "-random:n" where n is the number
                  of pages to be returned, otherwise the default is 10 pages.

-randomredirect   Work on random redirect pages returned by
                  [[Special:RandomRedirect]]. Can also be given as
                  "-randomredirect:n" where n is the number of pages to be
                  returned, else 10 pages are returned.

-untagged         Work on image pages that don't have any license template on a
                  site given in the format "<language>.<project>.org, e.g.
                  "ja.wikipedia.org" or "commons.wikimedia.org".
                  Using an external Toolserver tool.

-google           Work on all pages that are found in a Google search.
                  You need a Google Web API license key. Note that Google
                  doesn't give out license keys anymore. See google_key in
                  config.py for instructions.
                  Argument can also be given as "-google:searchstring".

-yahoo            Work on all pages that are found in a Yahoo search.
                  Depends on python module pYsearch.  See yahoo_appid in
                  config.py for instructions.

-page             Work on a single page. Argument can also be given as
                  "-page:pagetitle".

-grep             A regular expression that needs to match the article
                  otherwise the page won't be returned.
"""

docuReplacements = {'&params;': parameterHelp}

# if a bot uses GeneratorFactory, the module should include the line
#   docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}
# and include the marker &params; in the module's docstring
#
# We manually include it so the parameters show up in the auto-generated
# module documentation:

__doc__ = __doc__.replace("&params;", parameterHelp)


class GeneratorFactory(object):

    """Process command line arguments and return appropriate page generator.
    This factory is responsible for processing command line arguments
    that are used by many scripts and that determine which pages to work on.
    """
    def __init__(self, site=None):
        self.gens = []
        self.namespaces = []
        self.step = None
        self.limit = None
        self.articlefilter = None
        self.site = site
        if self.site is None:
            self.site = pywikibot.Site()

    def getCombinedGenerator(self, gen=None):
        """Return the combination of all accumulated generators.

        Only call this after all arguments have been parsed.
        """

        if gen:
            self.gens.insert(0, gen)

        namespaces = [int(n) for n in self.namespaces]
        for i in range(len(self.gens)):
            if isinstance(self.gens[i], pywikibot.data.api.QueryGenerator):
                if self.namespaces:
                    self.gens[i].set_namespace(namespaces)
                if self.step:
                    self.gens[i].set_query_increment(self.step)
                if self.limit:
                    self.gens[i].set_maximum_items(self.limit)
            else:
                if self.namespaces:
                    self.gens[i] = NamespaceFilterPageGenerator(self.gens[i],
                                                                namespaces)
                if self.limit:
                    self.gens[i] = itertools.islice(self.gens[i], self.limit)
        if len(self.gens) == 0:
            return None
        elif len(self.gens) == 1:
            gensList = self.gens[0]
        else:
            gensList = CombinedPageGenerator(self.gens)

        dupfiltergen = DuplicateFilterPageGenerator(gensList)

        if self.articlefilter:
            return RegexBodyFilterPageGenerator(
                PreloadingGenerator(dupfiltergen), self.articlefilter)
        else:
            return dupfiltergen

    def getCategoryGen(self, arg, length, recurse=False, content=False):
        if len(arg) == length:
            categoryname = i18n.input('pywikibot-enter-category-name')
        else:
            categoryname = arg[length + 1:]
        categoryname = categoryname.replace('#', '|')
        ind = categoryname.find('|')
        startfrom = None
        if ind > 0:
            startfrom = categoryname[ind + 1:]
            categoryname = categoryname[:ind]

        cat = pywikibot.Category(pywikibot.Link(categoryname,
                                                defaultNamespace=14))
        # Link constructor automatically prepends localized namespace
        # if not included in user's input
        return CategorizedPageGenerator(cat, start=startfrom,
                                        recurse=recurse, content=content)

    def setSubCategoriesGen(self, arg, length, recurse=False, content=False):
        if len(arg) == length:
            categoryname = i18n.input('pywikibot-enter-category-name')
        else:
            categoryname = arg[length + 1:]

        ind = categoryname.find('|')
        if ind > 0:
            startfrom = categoryname[ind + 1:]
            categoryname = categoryname[:ind]
        else:
            startfrom = None

        cat = pywikibot.Category(pywikibot.Link(categoryname,
                                                defaultNamespace=14))
        return SubCategoriesPageGenerator(cat, start=startfrom,
                                          recurse=recurse, content=content)

    def handleArg(self, arg):
        """Parse one argument at a time.

        If it is recognized as an argument that specifies a generator, a
        generator is created and added to the accumulation list, and the
        function returns true.  Otherwise, it returns false, so that caller
        can try parsing the argument. Call getCombinedGenerator() after all
        arguments have been parsed to get the final output generator.

        """
        gen = None
        if arg.startswith('-filelinks'):
            fileLinksPageTitle = arg[11:]
            if not fileLinksPageTitle:
                fileLinksPageTitle = i18n.input(
                    'pywikibot-enter-file-links-processing')
            if fileLinksPageTitle.startswith(self.site.namespace(6)
                                             + ":"):
                fileLinksPage = pywikibot.ImagePage(self.site,
                                                    fileLinksPageTitle)
            else:
                fileLinksPage = pywikibot.ImagePage(self.site,
                                                    'Image:' +
                                                    fileLinksPageTitle)
            gen = FileLinksGenerator(fileLinksPage)
        elif arg.startswith('-unusedfiles'):
            if len(arg) == 12:
                gen = UnusedFilesGenerator()
            else:
                gen = UnusedFilesGenerator(total=int(arg[13:]))
        elif arg.startswith('-lonelypages'):
            if len(arg) == 12:
                gen = LonelyPagesPageGenerator()
            else:
                gen = LonelyPagesPageGenerator(total=int(arg[13:]))
        elif arg.startswith('-unwatched'):
            if len(arg) == 10:
                gen = UnwatchedPagesPageGenerator()
            else:
                gen = UnwatchedPagesPageGenerator(total=int(arg[11:]))
        elif arg.startswith('-usercontribs'):
            gen = UserContributionsGenerator(arg[14:])
        elif arg.startswith('-withoutinterwiki'):
            if len(arg) == 17:
                gen = WithoutInterwikiPageGenerator()
            else:
                gen = WithoutInterwikiPageGenerator(total=int(arg[18:]))
        elif arg.startswith('-interwiki'):
            title = arg[11:]
            if not title:
                title = i18n.input('pywikibot-enter-page-processing')
            page = pywikibot.Page(pywikibot.Link(title,
                                                 self.site))
            gen = InterwikiPageGenerator(page)
        elif arg.startswith('-randomredirect'):
            if len(arg) == 15:
                gen = RandomRedirectPageGenerator()
            else:
                gen = RandomRedirectPageGenerator(total=int(arg[16:]))
        elif arg.startswith('-random'):
            if len(arg) == 7:
                gen = RandomPageGenerator()
            else:
                gen = RandomPageGenerator(total=int(arg[8:]))
        elif arg.startswith('-recentchanges'):
            namespaces = [int(n) for n in self.namespaces] or None
            if len(arg) >= 15:
                gen = RecentChangesPageGenerator(namespaces=namespaces, total=int(arg[15:]))
            else:
                gen = RecentChangesPageGenerator(namespaces=namespaces, total=60)
            gen = DuplicateFilterPageGenerator(gen)
        elif arg.startswith('-file'):
            textfilename = arg[6:]
            if not textfilename:
                textfilename = pywikibot.input(
                    u'Please enter the local file name:')
            gen = TextfilePageGenerator(textfilename)
        elif arg.startswith('-namespace'):
            if len(arg) == len('-namespace'):
                self.namespaces.append(
                    pywikibot.input(u'What namespace are you filtering on?'))
            else:
                self.namespaces.extend(arg[len('-namespace:'):].split(","))
            return True
        elif arg.startswith('-ns'):
            if len(arg) == len('-ns'):
                self.namespaces.append(
                    pywikibot.input(u'What namespace are you filtering on?'))
            else:
                self.namespaces.extend(arg[len('-ns:'):].split(","))
            return True
        elif arg.startswith('-step'):
            if len(arg) == len('-step'):
                self.step = int(pywikibot.input("What is the step value?"))
            else:
                self.step = int(arg[len('-step:'):])
            return True
        elif arg.startswith('-limit'):
            if len(arg) == len('-limit'):
                self.limit = int(pywikibot.input("What is the limit value?"))
            else:
                self.limit = int(arg[len('-limit:'):])
            return True
        elif arg.startswith('-catr'):
            gen = self.getCategoryGen(arg, len('-catr'), recurse=True)
        elif arg.startswith('-category'):
            gen = self.getCategoryGen(arg, len('-category'))
        elif arg.startswith('-cat'):
            gen = self.getCategoryGen(arg, len('-cat'))
        elif arg.startswith('-subcatsr'):
            gen = self.setSubCategoriesGen(arg, 9, recurse=True)
        elif arg.startswith('-subcats'):
            gen = self.setSubCategoriesGen(arg, 8)
        elif arg.startswith('-page'):
            if len(arg) == len('-page'):
                gen = [pywikibot.Page(
                    pywikibot.Link(
                        pywikibot.input(
                            u'What page do you want to use?'),
                        self.site)
                )]
            else:
                gen = [pywikibot.Page(pywikibot.Link(arg[len('-page:'):],
                                                     self.site)
                                      )]
        elif arg.startswith('-uncatfiles'):
            gen = UnCategorizedImageGenerator()
        elif arg.startswith('-uncatcat'):
            gen = UnCategorizedCategoryGenerator()
        elif arg.startswith('-uncat'):
            gen = UnCategorizedPageGenerator()
        elif arg.startswith('-ref'):
            referredPageTitle = arg[5:]
            if not referredPageTitle:
                referredPageTitle = pywikibot.input(
                    u'Links to which page should be processed?')
            referredPage = pywikibot.Page(pywikibot.Link(referredPageTitle,
                                                         self.site))
            gen = ReferringPageGenerator(referredPage)
        elif arg.startswith('-links'):
            linkingPageTitle = arg[7:]
            if not linkingPageTitle:
                linkingPageTitle = pywikibot.input(
                    u'Links from which page should be processed?')
            linkingPage = pywikibot.Page(pywikibot.Link(linkingPageTitle,
                                                        self.site))
            gen = LinkedPageGenerator(linkingPage)
        elif arg.startswith('-weblink'):
            url = arg[9:]
            if not url:
                url = pywikibot.input(
                    u'Pages with which weblink should be processed?')
            gen = LinksearchPageGenerator(url)
        elif arg.startswith('-transcludes'):
            transclusionPageTitle = arg[len('-transcludes:'):]
            if not transclusionPageTitle:
                transclusionPageTitle = pywikibot.input(
                    u'Pages that transclude which page should be processed?')
            transclusionPage = pywikibot.Page(
                pywikibot.Link(transclusionPageTitle,
                               defaultNamespace=10,
                               source=self.site))
            gen = ReferringPageGenerator(transclusionPage,
                                         onlyTemplateInclusion=True)
        elif arg.startswith('-start'):
            firstPageTitle = arg[7:]
            if not firstPageTitle:
                firstPageTitle = pywikibot.input(
                    u'At which page do you want to start?')
            firstpagelink = pywikibot.Link(firstPageTitle,
                                           self.site)
            namespace = firstpagelink.namespace
            firstPageTitle = firstpagelink.title
            gen = AllpagesPageGenerator(firstPageTitle, namespace,
                                        includeredirects=False)
        elif arg.startswith('-prefixindex'):
            prefix = arg[13:]
            namespace = None
            if not prefix:
                prefix = pywikibot.input(
                    u'What page names are you looking for?')
            gen = PrefixingPageGenerator(prefix=prefix)
        elif arg.startswith('-newimages'):
            limit = arg[11:] or pywikibot.input(
                u'How many images do you want to load?')
            gen = NewimagesPageGenerator(total=int(limit))
        elif arg.startswith('-newpages'):
            # partial workaround for bug 67249
            # to use -namespace/ns with -newpages, -ns must be given before -newpages
            # otherwise default namespace is 0
            namespaces = [int(n) for n in self.namespaces] or 0
            if len(arg) >= 10:
                gen = NewpagesPageGenerator(namespaces=namespaces, total=int(arg[10:]))
            else:
                gen = NewpagesPageGenerator(namespaces=namespaces, total=60)
        elif arg.startswith('-imagesused'):
            imagelinkstitle = arg[len('-imagesused:'):]
            if not imagelinkstitle:
                imagelinkstitle = pywikibot.input(
                    u'Images on which page should be processed?')
            imagelinksPage = pywikibot.Page(pywikibot.Link(imagelinkstitle,
                                                           self.site))
            gen = ImagesPageGenerator(imagelinksPage)
        elif arg.startswith('-search'):
            mediawikiQuery = arg[8:]
            if not mediawikiQuery:
                mediawikiQuery = pywikibot.input(
                    u'What do you want to search for?')
            # In order to be useful, all namespaces are required
            gen = SearchPageGenerator(mediawikiQuery, namespaces=[])
        elif arg.startswith('-google'):
            gen = GoogleSearchPageGenerator(arg[8:])
        elif arg.startswith('-titleregex'):
            if len(arg) == 11:
                regex = pywikibot.input(u'What page names are you looking for?')
            else:
                regex = arg[12:]
            gen = RegexFilterPageGenerator(self.site.allpages(), regex)
        elif arg.startswith('-grep'):
            if len(arg) == 5:
                self.articlefilter = pywikibot.input(
                    u'Which pattern do you want to grep?')
            else:
                self.articlefilter = arg[6:]
            return True
        elif arg.startswith('-yahoo'):
            gen = YahooSearchPageGenerator(arg[7:])
        elif arg.startswith('-untagged'):
            gen = UntaggedPageGenerator(arg[10:])
        elif arg.startswith('-wikidataquery'):
            query = arg[len('-wikidataquery:'):]
            if not query:
                query = pywikibot.input(
                    u'WikidataQuery string:')
            gen = WikidataQueryPageGenerator(query)

        if gen:
            self.gens.append(gen)
            return True
        else:
            return False


def AllpagesPageGenerator(start='!', namespace=0, includeredirects=True,
                          site=None, step=None, total=None, content=False):
    """
    Iterate Page objects for all titles in a single namespace.

    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.

    @param step: Maximum number of pages to retrieve per API query
    @param total: Maxmum number of pages to retrieve in total
    @param content: If True, load current version of each page (default False)

    """
    if site is None:
        site = pywikibot.Site()
    if includeredirects:
        if includeredirects == 'only':
            filterredir = True
        else:
            filterredir = None
    else:
        filterredir = False
    return site.allpages(start=start, namespace=namespace,
                         filterredir=filterredir, step=step, total=total,
                         content=content)


def PrefixingPageGenerator(prefix, namespace=None, includeredirects=True,
                           site=None, step=None, total=None, content=False):
    if site is None:
        site = pywikibot.Site()
    prefixlink = pywikibot.Link(prefix, site)
    if namespace is None:
        namespace = prefixlink.namespace
    title = prefixlink.title
    if includeredirects:
        if includeredirects == 'only':
            filterredir = True
        else:
            filterredir = None
    else:
        filterredir = False
    return site.allpages(prefix=title, namespace=namespace,
                         filterredir=filterredir, step=step, total=total,
                         content=content)


@deprecate_arg("number", "total")
@deprecate_arg("namespace", "namespaces")
@deprecate_arg("repeat", None)
def NewpagesPageGenerator(get_redirect=False, site=None,
                          namespaces=[0, ], step=None, total=None):
    """
    Iterate Page objects for all new titles in a single namespace.
    """
    # API does not (yet) have a newpages function, so this tries to duplicate
    # it by filtering the recentchanges output
    # defaults to namespace 0 because that's how Special:Newpages defaults
    if site is None:
        site = pywikibot.Site()
    for item in site.recentchanges(showRedirects=get_redirect,
                                   changetype="new", namespaces=namespaces,
                                   step=step, total=total):
        yield pywikibot.Page(pywikibot.Link(item["title"], site))


def RecentChangesPageGenerator(start=None, end=None, reverse=False,
                               namespaces=None, pagelist=None,
                               changetype=None, showMinor=None,
                               showBot=None, showAnon=None,
                               showRedirects=None, showPatrolled=None,
                               topOnly=False, step=None, total=None,
                               user=None, excludeuser=None, site=None):

    """
    Generate pages that are in the recent changes list.

    @param start: Timestamp to start listing from
    @type start: pywikibot.Timestamp
    @param end: Timestamp to end listing at
    @type end: pywikibot.Timestamp
    @param reverse: if True, start with oldest changes (default: newest)
    @type reverse: bool
    @param pagelist: iterate changes to pages in this list only
    @param pagelist: list of Pages
    @param changetype: only iterate changes of this type ("edit" for
        edits to existing pages, "new" for new pages, "log" for log
        entries)
    @type changetype: basestring
    @param showMinor: if True, only list minor edits; if False, only list
        non-minor edits; if None, list all
    @type showMinor: bool or None
    @param showBot: if True, only list bot edits; if False, only list
        non-bot edits; if None, list all
    @type showBot: bool or None
    @param showAnon: if True, only list anon edits; if False, only list
        non-anon edits; if None, list all
    @type showAnon: bool or None
    @param showRedirects: if True, only list edits to redirect pages; if
        False, only list edits to non-redirect pages; if None, list all
    @type showRedirects: bool or None
    @param showPatrolled: if True, only list patrolled edits; if False,
        only list non-patrolled edits; if None, list all
    @type showPatrolled: bool or None
    @param topOnly: if True, only list changes that are the latest revision
        (default False)
    @type topOnly: bool
    @param user: if not None, only list edits by this user or users
    @type user: basestring|list
    @param excludeuser: if not None, exclude edits by this user or users
    @type excludeuser: basestring|list

    """

    if site is None:
        site = pywikibot.Site()
    for item in site.recentchanges(start=start, end=end, reverse=reverse,
                                   namespaces=namespaces, pagelist=pagelist,
                                   changetype=changetype, showMinor=showMinor,
                                   showBot=showBot, showAnon=showAnon,
                                   showRedirects=showRedirects,
                                   showPatrolled=showPatrolled,
                                   topOnly=topOnly, step=step, total=total,
                                   user=user, excludeuser=excludeuser):
        yield pywikibot.Page(pywikibot.Link(item["title"], site))


def FileLinksGenerator(referredImagePage, step=None, total=None, content=False):
    return referredImagePage.usingPages(step=step, total=total, content=content)


def ImagesPageGenerator(pageWithImages, step=None, total=None, content=False):
    return pageWithImages.imagelinks(step=step, total=total, content=content)


def InterwikiPageGenerator(page):
    """Iterator over all interwiki (non-language) links on a page."""
    for link in page.interwiki():
        yield pywikibot.Page(link)


def LanguageLinksPageGenerator(page, step=None, total=None):
    """Iterator over all interwiki language links on a page."""
    for link in page.iterlanglinks(step=step, total=total):
        yield pywikibot.Page(link)


def ReferringPageGenerator(referredPage, followRedirects=False,
                           withTemplateInclusion=True,
                           onlyTemplateInclusion=False,
                           step=None, total=None, content=False):
    '''Yields all pages referring to a specific page.'''
    return referredPage.getReferences(
        follow_redirects=followRedirects,
        withTemplateInclusion=withTemplateInclusion,
        onlyTemplateInclusion=onlyTemplateInclusion,
        step=step, total=total, content=content)


def CategorizedPageGenerator(category, recurse=False, start=None,
                             step=None, total=None, content=False):
    """Yield all pages in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).

    If start is a string value, only pages whose sortkey comes after start
    alphabetically are included.

    If content is True (default is False), the current page text of each
    retrieved page will be downloaded.

    """
    kwargs = dict(recurse=recurse, step=step, total=total,
                  content=content)
    if start:
        kwargs['sortby'] = 'sortkey'
        kwargs['startsort'] = start
    for a in category.articles(**kwargs):
        yield a


def SubCategoriesPageGenerator(category, recurse=False, start=None,
                               step=None, total=None, content=False):
    """Yield all subcategories in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).

    If start is a string value, only categories whose sortkey comes after
    start alphabetically are included.

    If content is True (default is False), the current page text of each
    category description page will be downloaded.

    """
    # TODO: page generator could be modified to use cmstartsortkey ...
    for s in category.subcategories(recurse=recurse, step=step,
                                    total=total, content=content):
        if start is None or s.title(withNamespace=False) >= start:
            yield s


def LinkedPageGenerator(linkingPage, step=None, total=None, content=False):
    """Yield all pages linked from a specific page."""
    return linkingPage.linkedPages(step=step, total=total, content=content)


def TextfilePageGenerator(filename=None, site=None):
    """Iterate pages from a list in a text file.

    The file must contain page links between double-square-brackets or, in
    alternative, separated by newlines. The generator will yield each
    corresponding Page object.

    @param filename: the name of the file that should be read. If no name is
                     given, the generator prompts the user.
    @param site: the default Site for which Page objects should be created

    """
    if filename is None:
        filename = pywikibot.input(u'Please enter the filename:')
    if site is None:
        site = pywikibot.Site()
    f = codecs.open(filename, 'r', config.textfile_encoding)
    linkmatch = None
    for linkmatch in pywikibot.link_regex.finditer(f.read()):
        # If the link is in interwiki format, the Page object may reside
        # on a different Site than the default.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        yield pywikibot.Page(pywikibot.Link(linkmatch.group("title"), site))
    if linkmatch is None:
        f.seek(0)
        for title in f:
            title = title.strip()
            if '|' in title:
                title = title[:title.index('|')]
            if title:
                yield pywikibot.Page(site, title)
    f.close()


def PagesFromTitlesGenerator(iterable, site=None):
    """Generate pages from the titles (unicode strings) yielded by iterable."""
    if site is None:
        site = pywikibot.Site()
    for title in iterable:
        if not isinstance(title, basestring):
            break
        yield pywikibot.Page(pywikibot.Link(title, site))


@deprecate_arg("number", "total")
def UserContributionsGenerator(username, namespaces=None, site=None,
                               step=None, total=None):
    """Yield unique pages edited by user:username

    @param namespaces: list of namespace numbers to fetch contribs from

    """
    if site is None:
        site = pywikibot.Site()
    return DuplicateFilterPageGenerator(
        pywikibot.Page(pywikibot.Link(contrib["title"], source=site))
        for contrib in site.usercontribs(user=username, namespaces=namespaces,
                                         step=step, total=total)
    )


def NamespaceFilterPageGenerator(generator, namespaces, site=None):
    """
    Wraps around another generator. Yields only those pages that are in one
    of the given namespaces.

    The namespace list can contain both integers (namespace numbers) and
    strings/unicode strings (namespace names).

    NOTE: API-based generators that have a "namespaces" parameter perform
    namespace filtering more efficiently than this generator.

    """
    if site is None:
        site = pywikibot.Site()
    if isinstance(namespaces, (int, basestring)):
        namespaces = [namespaces]
    # convert namespace names to namespace numbers
    for i in range(len(namespaces)):
        ns = namespaces[i]
        if isinstance(ns, basestring):
            try:
                # namespace might be given as str representation of int
                index = int(ns)
            except ValueError:
                index = site.getNamespaceIndex(ns)
                if index is None:
                    raise ValueError(u'Unknown namespace: %s' % ns)
            namespaces[i] = index
    for page in generator:
        if page.namespace() in namespaces:
            yield page


def RedirectFilterPageGenerator(generator, no_redirects=True):
    """Yield pages from another generator that are redirects or not."""
    for page in generator:
        if not page.isRedirectPage() and no_redirects:
            yield page
        elif page.isRedirectPage() and not no_redirects:
            yield page


def DuplicateFilterPageGenerator(generator):
    """Yield all unique pages from another generator, omitting duplicates."""
    seenPages = {}
    for page in generator:
        if page not in seenPages:
            seenPages[page] = True
            yield page


class RegexFilter(object):

    @classmethod
    def __filter_match(cls, regex, string, quantifier):
        """ return True if string matches precompiled regex list with depending
        on the quantifier parameter (see below).

        """
        if quantifier == 'all':
            match = all(r.search(string) for r in regex)
        else:
            match = any(r.search(string) for r in regex)
        return (quantifier == 'none') ^ match

    @classmethod
    def __precompile(cls, regex, flag):
        """ precompile the regex list if needed """
        # Enable multiple regexes
        if not isinstance(regex, list):
            regex = [regex]
        # Test if regex is already compiled.
        # We assume that all list componets have the same type
        if isinstance(regex[0], basestring):
            regex = [re.compile(r, flag) for r in regex]
        return regex

    @classmethod
    @deprecate_arg("inverse", "quantifier")
    def titlefilter(cls, generator, regex, quantifier='any',
                    ignore_namespace=True):
        """ Yield pages from another generator whose title matches regex with
        options re.IGNORECASE dependig on the quantifier parameter.
        If ignore_namespace is False, the whole page title is compared.
        NOTE: if you want to check for a match at the beginning of the title,
        you have to start the regex with "^"

        @param generator: another generator
        @type generator: any generator or iterator
        @param regex: a regex which should match the page title
        @type regex: a single regex string or a list of regex strings or a
            compiled regex or a list of compiled regexes
        @param quantifier: must be one of the following values:
            'all' - yields page if title is matched by all regexes
            'any' - yields page if title is matched by any regexes
            'none' - yields page if title is NOT matched by any regexes
        @type quantifier: string of ('all', 'any', 'none')
        @param ignore_namespace: ignore the namespace when matching the title
        @type ignore_namespace: bool
        @return: return a page depending on the matching parameters

        """
        # for backwards compatibility with compat for inverse parameter
        if quantifier is False:
            quantifier = 'any'
        elif quantifier is True:
            quantifier = 'none'
        reg = cls.__precompile(regex, re.I)
        for page in generator:
            title = page.title(withNamespace=not ignore_namespace)
            if cls.__filter_match(reg, title, quantifier):
                yield page

    @classmethod
    def contentfilter(cls, generator, regex, quantifier='any'):
        """Yield pages from another generator whose body matches regex with
        options re.IGNORECASE|re.DOTALL dependig on the quantifier parameter.

        For parameters see titlefilter above

        """
        reg = cls.__precompile(regex, re.IGNORECASE | re.DOTALL)
        return (page for page in generator
                if cls.__filter_match(reg, page.text, quantifier))

# name the generator methods
RegexFilterPageGenerator = RegexFilter.titlefilter
RegexBodyFilterPageGenerator = RegexFilter.contentfilter


def CombinedPageGenerator(generators):
    return itertools.chain(*generators)


def CategoryGenerator(generator):
    """Yield pages from another generator as Category objects.

    Makes sense only if it is ascertained that only categories are being
    retrieved.

    """
    for page in generator:
        yield pywikibot.Category(page)


def ImageGenerator(generator):
    """
    Wraps around another generator. Yields the same pages, but as ImagePage
    objects instead of Page objects. Makes sense only if it is ascertained
    that only images are being retrieved.
    """
    for page in generator:
        yield pywikibot.ImagePage(page)


def PageWithTalkPageGenerator(generator):
    """Yield pages and associated talk pages from another generator.

    Only yields talk pages if the original generator yields a non-talk page,
    and does not check if the talk page in fact exists.

    """
    for page in generator:
        yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()


@deprecate_arg("pageNumber", "step")
@deprecate_arg("lookahead", None)
def PreloadingGenerator(generator, step=50):
    """Yield preloaded pages taken from another generator."""

    # pages may be on more than one site, for example if an interwiki
    # generator is used, so use a separate preloader for each site
    sites = {}
    # build a list of pages for each site found in the iterator
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= step:
            # if this site is at the step, process it
            group = sites[site]
            sites[site] = []
            for i in site.preloadpages(group, step):
                yield i
    for site in sites:
        if sites[site]:
            # process any leftover sites that never reached the step
            for i in site.preloadpages(sites[site], step):
                yield i


def PreloadingItemGenerator(generator, step=50):
    """
    Yield preloaded pages taken from another generator.

    Function basically is copied from above, but for ItemPage's

    @param generator: pages to iterate over
    @param step: how many pages to preload at once
    """
    sites = {}
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= step:
            # if this site is at the step, process it
            group = sites[site]
            sites[site] = []
            for i in site.preloaditempages(group, step):
                yield i
    for site in sites:
        if sites[site]:
            # process any leftover sites that never reached the step
            for i in site.preloaditempages(sites[site], step):
                yield i


@deprecate_arg("number", "total")
def NewimagesPageGenerator(step=None, total=None, site=None):
    if site is None:
        site = pywikibot.Site()
    for entry in site.logevents(logtype="upload", step=step, total=total):
        # entry is an UploadEntry object
        # entry.title() returns a Page object
        yield entry.title()


def WikidataItemGenerator(gen):
    """
    A wrapper generator used to take another generator
    and yield their relevant Wikidata items
    """
    for page in gen:
        if isinstance(page, pywikibot.ItemPage):
            yield page
        elif page.site.data_repository() == page.site:
            # These are already items, just not item pages
            # FIXME: If we've already fetched content, we should retain it
            yield pywikibot.ItemPage(page.site, page.title())
        else:
            yield pywikibot.ItemPage.fromPage(page)


# TODO below
@deprecate_arg("extension", None)
@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def UnusedFilesGenerator(total=100, site=None, extension=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.unusedfiles(total=total):
        yield pywikibot.ImagePage(page.site, page.title())


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def WithoutInterwikiPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.withoutinterwiki(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def UnCategorizedCategoryGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedcategories(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def UnCategorizedImageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedimages(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def UnCategorizedPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedpages(total=total):
        yield page


def UnCategorizedTemplateGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedtemplates(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def LonelyPagesPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.lonelypages(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def UnwatchedPagesPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.unwatchedpages(total=total):
        yield page


def WantedPagesPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.wantedpages(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def AncientPagesPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page, timestamp in site.ancientpages(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def DeadendPagesPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.deadendpages(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def LongPagesPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page, length in site.longpages(total=total):
        yield page


@deprecate_arg("number", "total")
@deprecate_arg("repeat", None)
def ShortPagesPageGenerator(total=100, site=None):
    if site is None:
        site = pywikibot.Site()
    for page, length in site.shortpages(total=total):
        yield page


@deprecate_arg("number", "total")
def RandomPageGenerator(total=10, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.randompages(total=total):
        yield page


@deprecate_arg("number", "total")
def RandomRedirectPageGenerator(total=10, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.randompages(total=total, redirects=True):
        yield page


def LinksearchPageGenerator(link, namespaces=None, step=None, total=None,
                            site=None):
    """Yield all pages that include a specified link, according to
    [[Special:Linksearch]].

    """
    if site is None:
        site = pywikibot.Site()
    return site.exturlusage(link, namespaces=namespaces, step=step,
                                 total=total, content=False)


def SearchPageGenerator(query, step=None, total=None, namespaces=None,
                        site=None):
    """
    Provides a list of results using the internal MediaWiki search engine
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.search(query, step=step, total=total,
                            namespaces=namespaces):
        yield page


def UntaggedPageGenerator(untaggedProject, limit=500):
    """ Function to get the pages returned by this tool:
    https://toolserver.org/~daniel/WikiSense/UntaggedImages.php
    """
    URL = "https://toolserver.org/~daniel/WikiSense/UntaggedImages.php?"
    REGEXP = r"<td valign='top' title='Name'><a href='http[s]?://.*?" \
             "\.org/w/index\.php\?title=(.*?)'>.*?</a></td>"
    lang, project = untaggedProject.split('.', 1)
    if lang == 'commons':
        wiki = 'wikifam=commons.wikimedia.org'
    else:
        wiki = 'wikilang=%s&wikifam=.%s' % (lang, project)
    link = '%s&%s&max=%d&order=img_timestamp' % (URL, wiki, limit)
    results = re.findall(REGEXP, http.request(site=None, uri=link))
    if not results:
        raise pywikibot.Error(
            u'Nothing found at %s! Try to use the tool by yourself to be sure '
            u'that it works!' % link)
    else:
        for result in results:
            yield pywikibot.Page(pywikibot.Site(), result)


# following classes just ported from version 1 without revision; not tested


class YahooSearchPageGenerator:

    """
    Page generator using Yahoo! search results.

    To use this generator, you need to install the package 'pYsearch'.
    https://pypi.python.org/pypi/pYsearch

    To use this generator, install pYsearch
    """

    # values larger than 100 fail
    def __init__(self, query=None, count=100, site=None):
        self.query = query or pywikibot.input(u'Please enter the search query:')
        self.count = count
        if site is None:
            site = pywikibot.Site()
        self.site = site

    def queryYahoo(self, query):
        """ Perform a query using python package 'pYsearch'. """
        try:
            from yahoo.search.web import WebSearch
        except ImportError:
            pywikibot.error("ERROR: generator YahooSearchPageGenerator "
                            "depends on package 'pYsearch'.\n"
                            "To install, please run: pip install pYsearch")
            exit(1)

        srch = WebSearch(config.yahoo_appid, query=query, results=self.count)
        dom = srch.get_results()
        results = srch.parse_results(dom)
        for res in results:
            url = res.Url
            yield url

    def __iter__(self):
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(),
                                self.site.nice_get_address(''))
        for url in self.queryYahoo(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(pywikibot.Link(title, pywikibot.Site()))
                yield page


class GoogleSearchPageGenerator:

    """
    Page generator using Google search results.

    To use this generator, you need to install the package 'google'.
    https://pypi.python.org/pypi/google

    This package has been available since 2010, hosted on github
    since 2012, and provided by pypi since 2013.

    As there are concerns about Google's Terms of Service, this
    generator prints a warning for each query.
    """

    def __init__(self, query=None, site=None):
        self.query = query or pywikibot.input(u'Please enter the search query:')
        if site is None:
            site = pywikibot.Site()
        self.site = site

    def queryGoogle(self, query):
        """
        Perform a query using python package 'google'.

        The terms of service as at June 2014 give two conditions that
        may apply to use of search:
            1. Dont access [Google Services] using a method other than
               the interface and the instructions that [they] provide.
            2. Don't remove, obscure, or alter any legal notices
               displayed in or along with [Google] Services.

        Both of those issues should be managed by the package 'google',
        however pywikibot will at least ensure the user sees the TOS
        in order to comply with the second condition.
        """
        try:
            import google
        except ImportError:
            pywikibot.error("ERROR: generator GoogleSearchPageGenerator "
                            "depends on package 'google'.\n"
                            "To install, please run: pip install google.")
            exit(1)
        pywikibot.warning('Please read http://www.google.com/accounts/TOS')
        for url in google.search(query):
            yield url

    def __iter__(self):
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(),
                                self.site.nice_get_address(''))
        for url in self.queryGoogle(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(pywikibot.Link(title, self.site))
                # Google contains links in the format
                # https://de.wikipedia.org/wiki/en:Foobar
                if page.site == self.site:
                    yield page


def MySQLPageGenerator(query, site=None):
    """
    Requires oursql <https://pythonhosted.org/oursql/> or
    MySQLdb <https://sourceforge.net/projects/mysql-python/>
    Yields a list of pages based on a MySQL query. Each query
    should provide the page namespace and page title. An example
    query that yields all ns0 pages might look like:
        SELECT
         page_namespace,
         page_title,
        FROM page
        WHERE page_namespace = 0;
    @param query: MySQL query to execute
    @param site: Site object or raw database name
    @type site: pywikibot.Site|str
    @return: iterator of pywikibot.Page
    """
    try:
        import oursql as mysqldb
    except ImportError:
        import MySQLdb as mysqldb
    if site is None:
        site = pywikibot.Site()
    if isinstance(site, pywikibot.site.Site):
        # We want to let people to set a custom dbname
        # since the master dbname might not be exactly
        # equal to the name on the replicated site
        site = site.dbName()
    conn = mysqldb.connect(config.db_hostname, db=site,
                           user=config.db_username,
                           passwd=config.db_password)
    cursor = conn.cursor()
    pywikibot.output(u'Executing query:\n%s' % query)
    query = query.encode(site.encoding())
    cursor.execute(query)
    while True:
        try:
            namespaceNumber, pageName = cursor.fetchone()
        except TypeError:
            # Limit reached or no more results
            break
        if pageName:
            namespace = site.namespace(namespaceNumber)
            pageName = unicode(pageName, site.encoding())
            if namespace:
                pageTitle = '%s:%s' % (namespace, pageName)
            else:
                pageTitle = pageName
            page = pywikibot.Page(site, pageTitle)
            yield page


def YearPageGenerator(start=1, end=2050, site=None):
    if site is None:
        site = pywikibot.Site()
    pywikibot.output(u"Starting with year %i" % start)
    for i in range(start, end + 1):
        if i % 100 == 0:
            pywikibot.output(u'Preparing %i...' % i)
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(site.lang, i)
            yield pywikibot.Page(pywikibot.Link(current_year, site))


def DayPageGenerator(startMonth=1, endMonth=12, site=None):
    if site is None:
        site = pywikibot.Site()
    fd = date.FormatDate(site)
    firstPage = pywikibot.Page(site, fd(startMonth, 1))
    pywikibot.output(u"Starting with %s" % firstPage.title(asLink=True))
    for month in range(startMonth, endMonth + 1):
        for day in range(1, date.getNumberOfDaysInMonth(month) + 1):
            yield pywikibot.Page(pywikibot.Link(fd(month, day), site))


def WikidataQueryPageGenerator(query, site=None):
    """Generate pages that result from the given WikidataQuery.

    @param query: the WikidataQuery query string.

    """
    if site is None:
        site = pywikibot.Site()
    repo = site.data_repository()

    wd_queryset = wdquery.QuerySet(query)

    wd_query = wdquery.WikidataQuery(cacheMaxAge=0)
    data = wd_query.query(wd_queryset)

    pywikibot.output(u'retrieved %d items' % data[u'status'][u'items'])
    for item in data[u'items']:
        page = pywikibot.ItemPage(repo, u'Q' + unicode(item))
        try:
            link = page.getSitelink(site)
        except pywikibot.NoPage:
            continue
        yield pywikibot.Page(pywikibot.Link(link, site))


if __name__ == "__main__":
    pywikibot.output(u'Pagegenerators cannot be run as script - are you '
                     u'looking for listpages.py?')
