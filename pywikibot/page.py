# -*- coding: utf-8  -*-
"""
Objects representing various types of MediaWiki, including Wikibase, pages.

This module also includes objects:
* Link: an internal or interwiki link in wikitext.
* Revision: a single change to a wiki page.
* Property: a type of semantic data.
* Claim: an instance of a semantic assertion.

"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: 2232a49a9173638fadfeeffa7dcbfce0f6cd6ff1 $'
#

import pywikibot
from pywikibot import deprecate_arg
from pywikibot import deprecated
from pywikibot import config
import pywikibot.site
from pywikibot.exceptions import AutoblockUser, UserActionRefuse
from pywikibot.tools import ComparableMixin
import hashlib

try:
    import htmlentitydefs
    from urllib import quote as quote_from_bytes, unquote as unquote_to_bytes
except ImportError:
    unicode = str
    from html import entities as htmlentitydefs
    from urllib.parse import quote_from_bytes, unquote_to_bytes

import logging
import re
import sys
import unicodedata
import collections

import urllib

logger = logging.getLogger("pywiki.wiki.page")

# Pre-compile re expressions
reNamespace = re.compile("^(.+?) *: *(.*)$")


# Note: Link objects (defined later on) represent a wiki-page's title, while
# Page objects (defined here) represent the page itself, including its contents.

class Page(pywikibot.UnicodeMixin, ComparableMixin):

    """Page: A MediaWiki page.

    This object only implements internally methods that do not require
    reading from or writing to the wiki.  All other methods are delegated
    to the Site object.

    """

    @deprecate_arg("insite", None)
    @deprecate_arg("defaultNamespace", "ns")
    def __init__(self, source, title=u"", ns=0):
        """Instantiate a Page object.

        Three calling formats are supported:

          - If the first argument is a Page, create a copy of that object.
            This can be used to convert an existing Page into a subclass
            object, such as Category or ImagePage.  (If the title is also
            given as the second argument, creates a copy with that title;
            this is used when pages are moved.)
          - If the first argument is a Site, create a Page on that Site
            using the second argument as the title (may include a section),
            and the third as the namespace number. The namespace number is
            mandatory, even if the title includes the namespace prefix. This
            is the preferred syntax when using an already-normalized title
            obtained from api.php or a database dump.  WARNING: may produce
            invalid objects if page title isn't in normal form!
          - If the first argument is a Link, create a Page from that link.
            This is the preferred syntax when using a title scraped from
            wikitext, URLs, or another non-normalized source.

        @param source: the source of the page
        @type source: Link, Page (or subclass), or Site
        @param title: normalized title of the page; required if source is a
            Site, ignored otherwise
        @type title: unicode
        @param ns: namespace number; required if source is a Site, ignored
            otherwise
        @type ns: int

        """
        if isinstance(source, pywikibot.site.BaseSite):
            self._link = Link(title, source=source, defaultNamespace=ns)
            self._revisions = {}
        elif isinstance(source, Page):
            # copy all of source's attributes to this object
            # without overwriting non-None values
            self.__dict__.update((k, v) for k, v in source.__dict__.items()
                                 if k not in self.__dict__ or
                                 self.__dict__[k] is None)
            if title:
                # overwrite title
                self._link = Link(title, source=source.site,
                                  defaultNamespace=ns)
        elif isinstance(source, Link):
            self._link = source
            self._revisions = {}
        else:
            raise pywikibot.Error(
                "Invalid argument type '%s' in Page constructor: %s"
                % (type(source), source))

    @property
    def site(self):
        """Return the Site object for the wiki on which this Page resides."""
        return self._link.site

    @property
    def image_repository(self):
        """Return the Site object for the image repository."""
        return self.site.image_repository()

    @property
    def data_repository(self):
        """Return the Site object for the data repository."""
        return self.site.data_repository()

    def namespace(self):
        """Return the number of the namespace of the page.

        @return: int
        """
        return self._link.namespace

    @deprecate_arg("decode", None)
    @deprecate_arg("savetitle", "asUrl")
    def title(self, underscore=False, withNamespace=True,
              withSection=True, asUrl=False, asLink=False,
              allowInterwiki=True, forceInterwiki=False, textlink=False,
              as_filename=False, insite=None):
        """Return the title of this Page, as a Unicode string.

        @param underscore: (not used with asLink) if true, replace all ' '
            characters with '_'
        @param withNamespace: if false, omit the namespace prefix. If this
            option is false and used together with asLink return a labeled
            link like [[link|label]]
        @param withSection: if false, omit the section
        @param asUrl: (not used with asLink) if true, quote title as if in an
            URL
        @param asLink: if true, return the title in the form of a wikilink
        @param allowInterwiki: (only used if asLink is true) if true, format
            the link as an interwiki link if necessary
        @param forceInterwiki: (only used if asLink is true) if true, always
            format the link as an interwiki link
        @param textlink: (only used if asLink is true) if true, place a ':'
            before Category: and Image: links
        @param as_filename: (not used with asLink) if true, replace any
            characters that are unsafe in filenames
        @param insite: (only used if asLink is true) a site object where the
            title is to be shown. default is the current family/lang given by
            -family and -lang option i.e. config.family and config.mylang

        """
        title = self._link.canonical_title()
        label = self._link.title
        if withSection and self._link.section:
            section = u"#" + self._link.section
        else:
            section = u''
        if asLink:
            if insite:
                target_code = insite.code
                target_family = insite.family.name
            else:
                target_code = config.mylang
                target_family = config.family
            if forceInterwiki or \
               (allowInterwiki and
                (self.site.family.name != target_family
                 or self.site.code != target_code)):
                if self.site.family.name != target_family \
                   and self.site.family.name != self.site.code:
                    title = u'%s:%s:%s' % (self.site.family.name,
                                           self.site.code,
                                           title)
                else:
                    # use this form for sites like commons, where the
                    # code is the same as the family name
                    title = u'%s:%s' % (self.site.code, title)
            elif textlink and (self.isImage() or self.isCategory()):
                title = u':%s' % title
            elif self.namespace() == 0 and not section:
                withNamespace = True
            if withNamespace:
                return u'[[%s%s]]' % (title, section)
            else:
                return u'[[%s%s|%s]]' % (title, section, label)
        if not withNamespace and self.namespace() != 0:
            title = label + section
        else:
            title += section
        if underscore or asUrl:
            title = title.replace(u' ', u'_')
        if asUrl:
            encodedTitle = title.encode(self.site.encoding())
            title = quote_from_bytes(encodedTitle)
        if as_filename:
            # Replace characters that are not possible in file names on some
            # systems.
            # Spaces are possible on most systems, but are bad for URLs.
            for forbidden in ':*?/\\ ':
                title = title.replace(forbidden, '_')
        return title

    @deprecate_arg("decode", None)
    @deprecate_arg("underscore", None)
    def section(self):
        """Return the name of the section this Page refers to.

        The section is the part of the title following a '#' character, if
        any. If no section is present, return None.

        """
        return self._link.section

    def __unicode__(self):
        """Return a unicode string representation."""
        return self.title(asLink=True, forceInterwiki=True)

    def __repr__(self):
        """Return a more complete string representation."""
        return "%s(%s)" % (self.__class__.__name__,
                           self.title().encode(config.console_encoding))

    def _cmpkey(self):
        """
        Key for comparison of Page objects.

        Page objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        Page objects are sortable by site, namespace then title.
        """
        return (self.site, self.namespace(), self.title())

    def __hash__(self):
        """
        A stable identifier to be used as a key in hash-tables.

        This relies on the fact that the string
        representation of an instance can not change after the construction.
        """
        return hash(unicode(self))

    def autoFormat(self):
        """Return L{date.autoFormat} dictName and value, if any.

        Value can be a year, date, etc., and dictName is 'YearBC',
        'Year_December', or another dictionary name. Please note that two
        entries may have exactly the same autoFormat, but be in two
        different namespaces, as some sites have categories with the
        same names. Regular titles return (None, None).

        """
        if not hasattr(self, '_autoFormat'):
            from pywikibot import date
            self._autoFormat = date.getAutoFormat(
                self.site.code,
                self.title(withNamespace=False)
            )
        return self._autoFormat

    def isAutoTitle(self):
        """Return True if title of this Page is in the autoFormat dictionary."""
        return self.autoFormat()[0] is not None

    @deprecate_arg("throttle", None)
    @deprecate_arg("change_edit_time", None)
    def get(self, force=False, get_redirect=False, sysop=False):
        """Return the wiki-text of the page.

        This will retrieve the page from the server if it has not been
        retrieved yet, or if force is True. This can raise the following
        exceptions that should be caught by the calling code:

        @exception NoPage         The page does not exist
        @exception IsRedirectPage The page is a redirect. The argument of the
                                  exception is the title of the page it
                                  redirects to.
        @exception SectionError   The section does not exist on a page with
                                  a # link

        @param force:           reload all page attributes, including errors.
        @param get_redirect:    return the redirect text, do not follow the
                                redirect, do not raise an exception.
        @param sysop:           if the user has a sysop account, use it to
                                retrieve this page

        """
        if force:
            # When forcing, we retry the page no matter what:
            # * Old exceptions do not apply any more
            # * Deleting _revid to force reload
            # * Deleting _redirtarget, that info is now obsolete.
            for attr in ['_redirtarget', '_getexception', '_revid']:
                if hasattr(self, attr):
                    delattr(self, attr)
        try:
            self._getInternals(sysop)
        except pywikibot.IsRedirectPage:
            if not get_redirect:
                raise

        return self._revisions[self._revid].text

    def _getInternals(self, sysop):
        """Helper function for get().

        Stores latest revision in self if it doesn't contain it, doesn't think.
        * Raises exceptions from previous runs.
        * Stores new exceptions in _getexception and raises them.

        """
        # Raise exceptions from previous runs
        if hasattr(self, '_getexception'):
            raise self._getexception

        # If not already stored, fetch revision
        if not hasattr(self, "_revid") \
                or self._revid not in self._revisions \
                or self._revisions[self._revid].text is None:
            try:
                self.site.loadrevisions(self, getText=True, sysop=sysop)
            except (pywikibot.NoPage, pywikibot.SectionError) as e:
                self._getexception = e
                raise

        # self._isredir is set by loadrevisions
        if self._isredir:
            self._getexception = pywikibot.IsRedirectPage(self)
            raise self._getexception

    @deprecate_arg("throttle", None)
    @deprecate_arg("change_edit_time", None)
    def getOldVersion(self, oldid, force=False, get_redirect=False,
                      sysop=False):
        """Return text of an old revision of this page; same options as get().

        @param oldid: The revid of the revision desired.

        """
        if force or oldid not in self._revisions \
                or self._revisions[oldid].text is None:
            self.site.loadrevisions(self,
                                    getText=True,
                                    revids=oldid,
                                    sysop=sysop)
        # TODO: what about redirects, errors?
        return self._revisions[oldid].text

    def permalink(self, oldid=None):
        """Return the permalink URL of an old revision of this page.

        @param oldid: The revid of the revision desired.

        """
        return "//%s%s/index.php?title=%s&oldid=%s" \
               % (self.site.hostname(),
                  self.site.scriptpath(),
                  self.title(asUrl=True),
                  (oldid if oldid is not None else self.latestRevision()))

    def latestRevision(self):
        """Return the current revision id for this page."""
        if not hasattr(self, '_revid'):
            self.site.loadrevisions(self)
        return self._revid

    @property
    def text(self):
        """Return the current (edited) wikitext, loading it if necessary.

        @return: unicode
        """
        if not hasattr(self, '_text') or self._text is None:
            try:
                self._text = self.get(get_redirect=True)
            except pywikibot.NoPage:
                # TODO: what other exceptions might be returned?
                self._text = u""
        return self._text

    @text.setter
    def text(self, value):
        """Update the current (edited) wikitext.

        @param value: New value or None
        @param value: basestring
        """
        self._text = None if value is None else unicode(value)

    @text.deleter
    def text(self):
        """Delete the current (edited) wikitext."""
        if hasattr(self, "_text"):
            del self._text

    def preloadText(self):
        """The text returned by EditFormPreloadText.

        See API module "info".

        Application: on Wikisource wikis, text can be preloaded even if
        a page does not exist, if an Index page is present.

        @return: unicode
        """
        self.site.loadpageinfo(self, preload=True)
        return self._preloadedtext

    def properties(self, force=False):
        """
        Return the properties of the page.

        @param force: force updating from the live site

        @return: dict
        """
        if not hasattr(self, '_pageprops') or force:
            self._pageprops = {}  # page may not have pageprops (see bug 54868)
            self.site.loadpageprops(self)
        return self._pageprops

    def defaultsort(self, force=False):
        """
        Extract value of the {{DEFAULTSORT:}} magic word from the page.

        @param force: force updating from the live site

        @return: unicode or None
        """
        return self.properties(force=force).get('defaultsort')

    @deprecate_arg('refresh', 'force')
    def expand_text(self, force=False, includecomments=False):
        """Return the page text with all templates and parser words expanded.

        @param force: force updating from the live site
        @param includecomments: Also strip comments if includecomments
            parameter is not True.

        @return: unicode or None
        """
        if not hasattr(self, '_expanded_text') or (
                self._expanded_text is None) or force:
            self._expanded_text = self.site.expand_text(
                self.text,
                title=self.title(withSection=False),
                includecomments=includecomments)
        return self._expanded_text

    def userName(self):
        """Return name or IP address of last user to edit page.

        @return: unicode
        """
        rev = self.latestRevision()
        if rev not in self._revisions:
            self.site.loadrevisions(self)
        return self._revisions[rev].user

    def isIpEdit(self):
        """Return True if last editor was unregistered.

        @return: bool
        """
        rev = self.latestRevision()
        if rev not in self._revisions:
            self.site.loadrevisions(self)
        return self._revisions[rev].anon

    def lastNonBotUser(self):
        """Return name or IP address of last human/non-bot user to edit page.

        Determine the most recent human editor out of the last revisions.
        If it was not able to retrieve a human user, returns None.

        If the edit was done by a bot which is no longer flagged as 'bot',
        i.e. which is not returned by Site.botusers(), it will be returned
        as a non-bot edit.

        @return: unicode
        """
        if hasattr(self, '_lastNonBotUser'):
            return self._lastNonBotUser

        self._lastNonBotUser = None
        for vh in self.getVersionHistory():
            (revid, timestmp, username, comment) = vh[:4]

            if username and (not self.site.isBot(username)):
                self._lastNonBotUser = username
                break

        return self._lastNonBotUser

    def editTime(self):
        """Return timestamp of last revision to page.

        @return: pywikibot.Timestamp
        """
        rev = self.latestRevision()
        if rev not in self._revisions:
            self.site.loadrevisions(self)
        return self._revisions[rev].timestamp

    def previousRevision(self):
        """Return the revision id for the previous revision of this Page.

        @return: long
        """
        self.getVersionHistory(total=2)
        revkey = sorted(self._revisions, reverse=True)[1]
        return revkey

    def exists(self):
        """Return True if page exists on the wiki, even if it's a redirect.

        If the title includes a section, return False if this section isn't
        found.

        @return: bool
        """
        return self.site.page_exists(self)

    def isRedirectPage(self):
        """Return True if this is a redirect, False if not or not existing."""
        return self.site.page_isredirect(self)

    def isStaticRedirect(self, force=False):
        """
        Determine whether the page is a static redirect.

        A static redirect must be a valid redirect, and contain the magic word
        __STATICREDIRECT__.

        @param force: Bypass local caching
        @type force: bool

        @return: bool
        """
        found = False
        if self.isRedirectPage():
            staticKeys = self.site.getmagicwords('staticredirect')
            text = self.get(get_redirect=True, force=force)
            if staticKeys:
                for key in staticKeys:
                    if key in text:
                        found = True
                        break
        return found

    def isCategoryRedirect(self):
        """Return True if this is a category redirect page, False otherwise.

        @return: bool
        """
        if not self.isCategory():
            return False
        if not hasattr(self, "_catredirect"):
            catredirs = self.site.category_redirects()
            for (template, args) in self.templatesWithParams():
                if template.title(withNamespace=False) in catredirs:
                    # Get target (first template argument)
                    try:
                        p = pywikibot.Page(self.site, args[0].strip(), ns=14)
                        if p.namespace() == 14:
                            self._catredirect = p.title()
                        else:
                            pywikibot.warning(
                                u"Target %s on %s is not a category"
                                % (p.title(asLink=True),
                                   self.title(asLink=True)))
                            self._catredirect = False
                    except IndexError:
                        pywikibot.warning(
                            u"No target for category redirect on %s"
                            % self.title(asLink=True))
                        self._catredirect = False
                    break
            else:
                self._catredirect = False
        return bool(self._catredirect)

    def getCategoryRedirectTarget(self):
        """If this is a category redirect, return the target category title.

        @return: Category
        """
        if self.isCategoryRedirect():
            return Category(Link(self._catredirect, self.site))
        raise pywikibot.IsNotRedirectPage(self.title())

    def isEmpty(self):
        """Return True if the page text has less than 4 characters.

        Character count ignores language links and category links.
        Can raise the same exceptions as get().

        @return bool
        """
        txt = self.get()
        txt = pywikibot.removeLanguageLinks(txt, site=self.site)
        txt = pywikibot.removeCategoryLinks(txt, site=self.site)
        return len(txt) < 4

    def isTalkPage(self):
        """Return True if this page is in any talk namespace."""
        ns = self.namespace()
        return ns >= 0 and ns % 2 == 1

    def toggleTalkPage(self):
        """Return other member of the article-talk page pair for this Page.

        If self is a talk page, returns the associated content page;
        otherwise, returns the associated talk page.  The returned page need
        not actually exist on the wiki.

        @return: Page or None if self is a special page.
        """
        ns = self.namespace()
        if ns < 0:  # Special page
            return
        if self.isTalkPage():
            if self.namespace() == 1:
                return Page(self.site, self.title(withNamespace=False))
            else:
                return Page(self.site,
                            "%s:%s" % (self.site.namespace(ns - 1),
                                       self.title(withNamespace=False)))
        else:
            return Page(self.site,
                        "%s:%s" % (self.site.namespace(ns + 1),
                                   self.title(withNamespace=False)))

    def isCategory(self):
        """Return True if the page is a Category, False otherwise."""
        return self.namespace() == 14

    def isImage(self):
        """Return True if this is an image description page, False otherwise."""
        return self.namespace() == 6

    def isDisambig(self, get_Index=True):
        """Return True if this is a disambiguation page, False otherwise.

        Relies on the presence of specific templates, identified in
        the Family file or on a wiki page, to identify disambiguation
        pages.

        By default, loads a list of template names from the Family file;
        if the value in the Family file is None no entry was made, looks for
        the list on [[MediaWiki:Disambiguationspage]]. If this page does not
        exist, take the MediaWiki message.

        If get_Index is True then also load the templates for index articles
        which are given on en-wiki

        'Template:Disambig' is always assumed to be default, and will be
        appended regardless of its existence.

        @return: bool
        """
        if self.site.hasExtension('Disambiguator', False):
            # If the Disambiguator extension is loaded, use it
            return 'disambiguation' in self.properties()

        if not hasattr(self.site, "_disambigtemplates"):
            try:
                default = set(self.site.family.disambig('_default'))
            except KeyError:
                default = set([u'Disambig'])
            try:
                distl = self.site.family.disambig(self.site.code,
                                                  fallback=False)
            except KeyError:
                distl = None
            if distl is None:
                disambigpages = Page(self.site,
                                     "MediaWiki:Disambiguationspage")
                indexes = set()
                if disambigpages.exists():
                    disambigs = set(link.title(withNamespace=False)
                                    for link in disambigpages.linkedPages()
                                    if link.namespace() == 10)
                    # cache index article templates separately
                    if self.site.sitename() == 'wikipedia:en':
                        regex = re.compile('\(\((.+?)\)\)')
                        content = disambigpages.get()
                        for index in regex.findall(content):
                            indexes.add(index[:1].upper() + index[1:])
                        self.site._indextemplates = indexes
                else:
                    message = self.site.mediawiki_message(
                        'disambiguationspage').split(':', 1)[1]
                    # add the default template(s) for default mw message
                    # only
                    disambigs = set([message[:1].upper() +
                                     message[1:]]) | default
                self.site._disambigtemplates = disambigs
            else:
                # Normalize template capitalization
                self.site._disambigtemplates = set(
                    t[:1].upper() + t[1:] for t in distl
                )
        templates = set(tl.title(withNamespace=False)
                        for tl in self.templates())
        disambigs = set()
        # always use cached disambig templates
        disambigs.update(self.site._disambigtemplates)
        # if get_Index is True, also use cached index templates
        if get_Index and hasattr(self.site, '_indextemplates'):
            disambigs.update(self.site._indextemplates)
        # see if any template on this page is in the set of disambigs
        disambigInPage = disambigs.intersection(templates)
        return self.namespace() != 10 and len(disambigInPage) > 0

    def getReferences(self, follow_redirects=True, withTemplateInclusion=True,
                      onlyTemplateInclusion=False, redirectsOnly=False,
                      namespaces=None, step=None, total=None, content=False):
        """Return an iterator all pages that refer to or embed the page.

        If you need a full list of referring pages, use
        C{pages = list(s.getReferences())}

        @param follow_redirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        @param withTemplateInclusion: if True, also iterate pages where self
            is used as a template.
        @param onlyTemplateInclusion: if True, only iterate pages where self
            is used as a template.
        @param redirectsOnly: if True, only iterate redirects to self.
        @param namespaces: only iterate pages in these namespaces
        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param content: if True, retrieve the content of the current version
            of each referring page (default False)

        """
        # N.B.: this method intentionally overlaps with backlinks() and
        # embeddedin(). Depending on the interface, it may be more efficient
        # to implement those methods in the site interface and then combine
        # the results for this method, or to implement this method and then
        # split up the results for the others.
        return self.site.pagereferences(
            self,
            followRedirects=follow_redirects,
            filterRedirects=redirectsOnly,
            withTemplateInclusion=withTemplateInclusion,
            onlyTemplateInclusion=onlyTemplateInclusion,
            namespaces=namespaces,
            step=step,
            total=total,
            content=content
        )

    def backlinks(self, followRedirects=True, filterRedirects=None,
                  namespaces=None, step=None, total=None, content=False):
        """Return an iterator for pages that link to this page.

        @param followRedirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        @param filterRedirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        @param namespaces: only iterate pages in these namespaces
        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param content: if True, retrieve the content of the current version
            of each referring page (default False)

        """
        return self.site.pagebacklinks(
            self,
            followRedirects=followRedirects,
            filterRedirects=filterRedirects,
            namespaces=namespaces,
            step=step,
            total=total,
            content=content
        )

    def embeddedin(self, filter_redirects=None, namespaces=None, step=None,
                   total=None, content=False):
        """Return an iterator for pages that embed this page as a template.

        @param filterRedirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        @param namespaces: only iterate pages in these namespaces
        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param content: if True, retrieve the content of the current version
            of each embedding page (default False)

        """
        return self.site.page_embeddedin(
            self,
            filterRedirects=filter_redirects,
            namespaces=namespaces,
            step=step,
            total=total,
            content=content
        )

    def protection(self):
        """Return a dictionary reflecting page protections.

        @return: dict
        """
        return self.site.page_restrictions(self)

    def canBeEdited(self):
        """Determine whether the page may be edited.

        This returns True if and only if:
          - page is unprotected, and bot has an account for this site, or
          - page is protected, and bot has a sysop account for this site.

        @return: bool
        """
        return self.site.page_can_be_edited(self)

    def botMayEdit(self):
        """Determine whether the active bot is allowed to edit the page.

        This will be True if the page doesn't contain {{bots}} or
        {{nobots}}, or it contains them and the active bot is allowed to
        edit this page. (This method is only useful on those sites that
        recognize the bot-exclusion protocol; on other sites, it will always
        return True.)

        The framework enforces this restriction by default. It is possible
        to override this by setting ignore_bot_templates=True in
        user-config.py, or using page.put(force=True).

        @return: bool
        """
        # TODO: move this to Site object?
        if config.ignore_bot_templates:  # Check the "master ignore switch"
            return True
        username = self.site.user()
        try:
            templates = self.templatesWithParams()
        except (pywikibot.NoPage,
                pywikibot.IsRedirectPage,
                pywikibot.SectionError):
            return True

        # go through all templates and look for any restriction
        # multiple bots/nobots templates are allowed
        for template in templates:
            title = template[0].title(withNamespace=False)
            if title == 'Nobots':
                if len(template[1]) == 0:
                    return False
                else:
                    bots = template[1][0].split(',')
                    if 'all' in bots or pywikibot.calledModuleName() in bots \
                       or username in bots:
                        return False
            elif title == 'Bots':
                if len(template[1]) == 0:
                    return True
                else:
                    (ttype, bots) = template[1][0].split('=', 1)
                    bots = bots.split(',')
                    if ttype == 'allow':
                        return 'all' in bots or username in bots
                    if ttype == 'deny':
                        return not ('all' in bots or username in bots)
                    if ttype == 'allowscript':
                        return 'all' in bots or pywikibot.calledModuleName() in bots
                    if ttype == 'denyscript':
                        return not ('all' in bots or pywikibot.calledModuleName() in bots)
        # no restricting template found
        return True

    @deprecate_arg('sysop', None)
    def save(self, comment=None, watch=None, minor=True, botflag=None,
             force=False, async=False, callback=None, **kwargs):
        """Save the current contents of page's text to the wiki.

        @param comment: The edit summary for the modification (optional, but
            most wikis strongly encourage its use)
        @type comment: unicode
        @param watch: if True, add or if False, remove this Page to/from bot
            user's watchlist; if None (default), follow bot account's default
            settings
        @type watch: bool or None
        @param minor: if True, mark this edit as minor
        @type minor: bool
        @param botflag: if True, mark this edit as made by a bot (default:
            True if user has bot status, False if not)
        @param force: if True, ignore botMayEdit() setting
        @type force: bool
        @param async: if True, launch a separate thread to save
            asynchronously
        @param callback: a callable object that will be called after the
            page put operation. This object must take two arguments: (1) a
            Page object, and (2) an exception instance, which will be None
            if the page was saved successfully. The callback is intended for
            use by bots that need to keep track of which saves were
            successful.

        """
        if not comment:
            comment = config.default_edit_summary
        if watch is None:
            watchval = None
        elif watch:
            watchval = "watch"
        else:
            watchval = "unwatch"
        if not force and not self.botMayEdit():
            raise pywikibot.PageNotSaved(
                "Page %s not saved; editing restricted by {{bots}} template"
                % self.title(asLink=True))
        if botflag is None:
            botflag = ("bot" in self.site.userinfo["rights"])
        if async:
            pywikibot.async_request(self._save, comment=comment, minor=minor,
                                    watchval=watchval, botflag=botflag,
                                    async=async, callback=callback, **kwargs)
        else:
            self._save(comment=comment, minor=minor, watchval=watchval,
                       botflag=botflag, async=async, callback=callback,
                       **kwargs)

    def _save(self, comment, minor, watchval, botflag, async, callback,
              **kwargs):
        """Helper function for save()."""
        err = None
        link = self.title(asLink=True)
        if config.cosmetic_changes:
            comment = self._cosmetic_changes_hook(comment) or comment
        try:
            done = self.site.editpage(self, summary=comment, minor=minor,
                                      watch=watchval, bot=botflag, **kwargs)
            if not done:
                pywikibot.warning(u"Page %s not saved" % link)
                raise pywikibot.PageNotSaved(link)
            else:
                pywikibot.output(u"Page %s saved" % link)
        except pywikibot.LockedPage as err:
            # re-raise the LockedPage exception so that calling program
            # can re-try if appropriate
            if not callback and not async:
                raise
        # TODO: other "expected" error types to catch?
        except pywikibot.Error as err:
            pywikibot.log(u"Error saving page %s (%s)\n" % (link, err),
                          exc_info=True)
            if not callback and not async:
                raise pywikibot.PageNotSaved("%s: %s" % (link, err))
        if callback:
            callback(self, err)

    def _cosmetic_changes_hook(self, comment):
        if self.isTalkPage() or \
           pywikibot.calledModuleName() in config.cosmetic_changes_deny_script:
            return
        family = self.site.family.name
        config.cosmetic_changes_disable.update({'wikidata': ('repo', )})
        if config.cosmetic_changes_mylang_only:
            cc = ((family == config.family and
                   self.site.lang == config.mylang) or
                  family in list(config.cosmetic_changes_enable.keys()) and
                  self.site.lang in config.cosmetic_changes_enable[family])
        else:
            cc = True
        cc = (cc and not
              (family in list(config.cosmetic_changes_disable.keys()) and
               self.site.lang in config.cosmetic_changes_disable[family]))
        if not cc:
            return
        old = self.text
        pywikibot.log(u'Cosmetic changes for %s-%s enabled.'
                      % (family, self.site.lang))
        from scripts.cosmetic_changes import CosmeticChangesToolkit
        from pywikibot import i18n
        ccToolkit = CosmeticChangesToolkit(self.site,
                                           redirect=self.isRedirectPage(),
                                           namespace=self.namespace(),
                                           pageTitle=self.title())
        self.text = ccToolkit.change(old)
        if comment and \
           old.strip().replace('\r\n',
                               '\n') != self.text.strip().replace('\r\n', '\n'):
            comment += i18n.twtranslate(self.site, 'cosmetic_changes-append')
            return comment

    def put(self, newtext, comment=u'', watchArticle=None, minorEdit=True,
            botflag=None, force=False, async=False, callback=None, **kwargs):
        """Save the page with the contents of the first argument as the text.

        This method is maintained primarily for backwards-compatibility.
        For new code, using Page.save() is preferred.  See save() method
        docs for all parameters not listed here.

        @param newtext: The complete text of the revised page.
        @type newtext: unicode

        """
        self.text = newtext
        self.save(comment=comment, watch=watchArticle, minor=minorEdit,
                  botflag=botflag, force=force, async=async, callback=callback,
                  **kwargs)

    def put_async(self, newtext, comment=u'', watchArticle=None,
                  minorEdit=True, botflag=None, force=False, callback=None,
                  **kwargs):
        """Put page on queue to be saved to wiki asynchronously.

        Asynchronous version of put (takes the same arguments), which places
        pages on a queue to be saved by a daemon thread. All arguments are
        the same as for .put().  This version is maintained solely for
        backwards-compatibility.

        """
        self.put(newtext, comment=comment, watchArticle=watchArticle,
                 minorEdit=minorEdit, botflag=botflag, force=force, async=True,
                 callback=callback, **kwargs)

    def watch(self, unwatch=False):
        """Add or remove this page to/from bot account's watchlist.

        @param unwatch: True to unwatch, False (default) to watch.
        @type unwatch: bool

        @return: bool; True if successful, False otherwise.
        """
        return self.site.watchpage(self, unwatch)

    def purge(self, **kwargs):
        """Purge the server's cache for this page.

        @return: bool
        """
        return self.site.purgepages([self], **kwargs)

    def linkedPages(self, namespaces=None, step=None, total=None,
                    content=False):
        """Iterate Pages that this Page links to.

        Only returns pages from "normal" internal links. Image and category
        links are omitted unless prefixed with ":". Embedded templates are
        omitted (but links within them are returned). All interwiki and
        external links are omitted.

        @param namespaces: only iterate links in these namespaces
        @param namespaces: int, or list of ints
        @param step: limit each API call to this number of pages
        @type step: int
        @param total: iterate no more than this number of pages in total
        @type total: int
        @param content: if True, retrieve the content of the current version
            of each linked page (default False)
        @type content: bool

        @return: a generator that yields Page objects.
        """
        return self.site.pagelinks(self, namespaces=namespaces, step=step,
                                   total=total, content=content)

    def interwiki(self, expand=True):
        """Iterate interwiki links in the page text, excluding language links.

        @param expand: if True (default), include interwiki links found in
            templates transcluded onto this page; if False, only iterate
            interwiki links found in this page's own wikitext
        @type expand: bool

        @return: a generator that yields Link objects
        """
        # This function does not exist in the API, so it has to be
        # implemented by screen-scraping
        if expand:
            text = self.expand_text()
        else:
            text = self.text
        for linkmatch in pywikibot.link_regex.finditer(
                pywikibot.removeDisabledParts(text)):
            linktitle = linkmatch.group("title")
            link = Link(linktitle, self.site)
            # only yield links that are to a different site and that
            # are not language links
            try:
                if link.site != self.site:
                    if linktitle.lstrip().startswith(":"):
                        # initial ":" indicates not a language link
                        yield link
                    elif link.site.family != self.site.family:
                        # link to a different family is not a language link
                        yield link
            except pywikibot.Error:
                # ignore any links with invalid contents
                continue

    def langlinks(self, include_obsolete=False):
        """Return a list of all inter-language Links on this page.

        @param include_obsolete: if true, return even Link objects whose site
                                 is obsolete
        @type include_obsolete: bool

        @return: list of Link objects.
        """
        # Note: We preload a list of *all* langlinks, including links to
        # obsolete sites, and store that in self._langlinks. We then filter
        # this list if the method was called with include_obsolete=False
        # (which is the default)
        if not hasattr(self, '_langlinks'):
            self._langlinks = list(self.iterlanglinks(include_obsolete=True))

        if include_obsolete:
            return self._langlinks
        else:
            return filter(lambda i: not i.site.obsolete, self._langlinks)

    def iterlanglinks(self, step=None, total=None, include_obsolete=False):
        """Iterate all inter-language links on this page.

        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param include_obsolete: if true, yield even Link object whose site
                                 is obsolete
        @type include_obsolete: bool

        @return: a generator that yields Link objects.
        """
        if hasattr(self, '_langlinks'):
            return iter(self.langlinks(include_obsolete=include_obsolete))
        # XXX We might want to fill _langlinks when the Site
        # method is called. If we do this, we'll have to think
        # about what will happen if the generator is not completely
        # iterated upon.
        return self.site.pagelanglinks(self, step=step, total=total,
                                       include_obsolete=include_obsolete)

    def data_item(self):
        """
        Convenience function to get the Wikibase item of a page.

        @return: ItemPage
        """
        return ItemPage.fromPage(self)

    @deprecate_arg('tllimit', None)
    @deprecated("Page.templates()")
    def getTemplates(self):
        """DEPRECATED. Use templates()."""
        return self.templates()

    def templates(self, content=False):
        """Return a list of Page objects for templates used on this Page.

        Template parameters are ignored.  This method only returns embedded
        templates, not template pages that happen to be referenced through
        a normal link.

        @param content: if True, retrieve the content of the current version
            of each template (default False)
        @param content: bool
        """
        # Data might have been preloaded
        if not hasattr(self, '_templates'):
            self._templates = list(self.itertemplates(content=content))

        return self._templates

    def itertemplates(self, step=None, total=None, content=False):
        """Iterate Page objects for templates used on this Page.

        Template parameters are ignored.  This method only returns embedded
        templates, not template pages that happen to be referenced through
        a normal link.

        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param content: if True, retrieve the content of the current version
            of each template (default False)
        @param content: bool

        """
        if hasattr(self, '_templates'):
            return iter(self._templates)
        return self.site.pagetemplates(self, step=step, total=total,
                                       content=content)

    @deprecate_arg("followRedirects", None)
    @deprecate_arg("loose", None)
    def imagelinks(self, step=None, total=None, content=False):
        """Iterate ImagePage objects for images displayed on this Page.

        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param content: if True, retrieve the content of the current version
            of each image description page (default False)
        @return: a generator that yields ImagePage objects.

        """
        return self.site.pageimages(self, step=step, total=total,
                                    content=content)

    @deprecate_arg("get_redirect", None)
    def templatesWithParams(self):
        """Iterate templates used on this Page.

        @return: a generator that yields a tuple for each use of a template
        in the page, with the template Page as the first entry and a list of
        parameters as the second entry.

        """
        # WARNING: may not return all templates used in particularly
        # intricate cases such as template substitution
        titles = list(t.title() for t in self.templates())
        templates = pywikibot.extract_templates_and_params(self.text)
        # backwards-compatibility: convert the dict returned as the second
        # element into a list in the format used by old scripts
        result = []
        for template in templates:
            link = pywikibot.Link(template[0], self.site,
                                  defaultNamespace=10)
            try:
                if link.canonical_title() not in titles:
                    continue
            except pywikibot.Error:
                # this is a parser function or magic word, not template name
                continue
            args = template[1]
            intkeys = {}
            named = {}
            positional = []
            for key in sorted(args):
                try:
                    intkeys[int(key)] = args[key]
                except ValueError:
                    named[key] = args[key]
            for i in range(1, len(intkeys) + 1):
                # only those args with consecutive integer keys can be
                # treated as positional; an integer could also be used
                # (out of order) as the key for a named argument
                # example: {{tmp|one|two|5=five|three}}
                if i in intkeys:
                    positional.append(intkeys[i])
                else:
                    for k in intkeys:
                        if k < 1 or k >= i:
                            named[str(k)] = intkeys[k]
                    break
            for name in named:
                positional.append("%s=%s" % (name, named[name]))
            result.append((pywikibot.Page(link, self.site), positional))
        return result

    @deprecate_arg("nofollow_redirects", None)
    @deprecate_arg("get_redirect", None)
    def categories(self, withSortKey=False, step=None, total=None,
                   content=False):
        """Iterate categories that the article is in.

        @param withSortKey: if True, include the sort key in each Category.
        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param content: if True, retrieve the content of the current version
            of each category description page (default False)
        @return: a generator that yields Category objects.

        """
        return self.site.pagecategories(self, withSortKey=withSortKey,
                                        step=step, total=total, content=content)

    def extlinks(self, step=None, total=None):
        """Iterate all external URLs (not interwiki links) from this page.

        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @return: a generator that yields unicode objects containing URLs.

        """
        return self.site.page_extlinks(self, step=step, total=total)

    def coordinates(self, primary_only=False):
        """Return a list of Coordinate objects for points on the page.

        Uses the MediaWiki extension GeoData.

        @param primary_only: Only return the coordinate indicated to be primary
        @return: A list of Coordinate objects
        """
        if not hasattr(self, '_coords'):
            self._coords = []
            self.site.loadcoordinfo(self)
        if primary_only:
            return self._coords[0] if len(self._coords) > 0 else None
        else:
            return self._coords

    def getRedirectTarget(self):
        """Return a Page object for the target this Page redirects to.

        If this page is not a redirect page, will raise an IsNotRedirectPage
        exception. This method also can raise a NoPage exception.

        @return: Page
        """
        return self.site.getredirtarget(self)

    # BREAKING CHANGE: in old framework, default value for getVersionHistory
    #                  returned no more than 500 revisions; now, it iterates
    #                  all revisions unless 'total' argument is used
    @deprecate_arg("forceReload", None)
    @deprecate_arg("revCount", "total")
    @deprecate_arg("getAll", None)
    def getVersionHistory(self, reverseOrder=False, step=None,
                          total=None):
        """Load the version history page and return history information.

        Return value is a list of tuples, where each tuple represents one
        edit and is built of revision id, edit date/time, user name, and
        edit summary. Starts with the most current revision, unless
        reverseOrder is True.

        @param step: limit each API call to this number of revisions
        @param total: iterate no more than this number of revisions in total

        """
        self.site.loadrevisions(self, getText=False, rvdir=reverseOrder,
                                step=step, total=total)
        return [(self._revisions[rev].revid,
                 self._revisions[rev].timestamp,
                 self._revisions[rev].user,
                 self._revisions[rev].comment
                 ) for rev in sorted(self._revisions,
                                     reverse=not reverseOrder)
                ]

    def getVersionHistoryTable(self, forceReload=False, reverseOrder=False,
                               step=None, total=None):
        """Return the version history as a wiki table."""
        result = '{| class="wikitable"\n'
        result += '! oldid || date/time || username || edit summary\n'
        for oldid, time, username, summary \
                in self.getVersionHistory(forceReload=forceReload,
                                          reverseOrder=reverseOrder,
                                          step=step, total=total):
            result += '|----\n'
            result += '| %s || %s || %s || <nowiki>%s</nowiki>\n'\
                      % (oldid, time, username, summary)
        result += '|}\n'
        return result

    def fullVersionHistory(self, reverseOrder=False, step=None,
                           total=None, rollback=False):
        """Iterate previous versions including wikitext.

        Takes same arguments as getVersionHistory.

        @param rollback: Returns rollback token.
        @return: A generator that yields tuples consisting of revision ID,
            edit date/time, user name and content

        """
        self.site.loadrevisions(self, getText=True,
                                rvdir=reverseOrder,
                                step=step, total=total, rollback=rollback)
        return [(self._revisions[rev].revid,
                 self._revisions[rev].timestamp,
                 self._revisions[rev].user,
                 self._revisions[rev].text,
                 self._revisions[rev].rollbacktoken
                 ) for rev in sorted(self._revisions,
                                     reverse=not reverseOrder)
                ]

    def contributingUsers(self, step=None, total=None):
        """Return a set of usernames (or IPs) of users who edited this page.

        @param step: limit each API call to this number of revisions
        @param total: iterate no more than this number of revisions in total

        """
        edits = self.getVersionHistory(step=step, total=total)
        users = set([edit[2] for edit in edits])
        return users

    @deprecate_arg("throttle", None)
    def move(self, newtitle, reason=None, movetalkpage=True, sysop=False,
             deleteAndMove=False, safe=True):
        """Move this page to a new title.

        @param newtitle: The new page title.
        @param reason: The edit summary for the move.
        @param movetalkpage: If true, move this page's talk page (if it exists)
        @param sysop: Try to move using sysop account, if available
        @param deleteAndMove: if move succeeds, delete the old page
            (usually requires sysop privileges, depending on wiki settings)
        @param safe: If false, attempt to delete existing page at newtitle
            (if there is one) and then move this page to that title

        """
        if reason is None:
            pywikibot.output(u'Moving %s to [[%s]].'
                             % (self.title(asLink=True), newtitle))
            reason = pywikibot.input(u'Please enter a reason for the move:')
        # TODO: implement "safe" parameter (Is this necessary ?)
        # TODO: implement "sysop" parameter
        return self.site.movepage(self, newtitle, reason,
                                  movetalk=movetalkpage,
                                  noredirect=deleteAndMove)

    @deprecate_arg("throttle", None)
    def delete(self, reason=None, prompt=True, mark=False):
        """Delete the page from the wiki. Requires administrator status.

        @param reason: The edit summary for the deletion, or rationale
            for deletion if requesting. If None, ask for it.
        @param prompt: If true, prompt user for confirmation before deleting.
        @param mark: If true, and user does not have sysop rights, place a
            speedy-deletion request on the page instead. If false, non-sysops
            will be asked before marking pages for deletion.

        """
        if reason is None:
            pywikibot.output(u'Deleting %s.' % (self.title(asLink=True)))
            reason = pywikibot.input(u'Please enter a reason for the deletion:')

        # If user is a sysop, delete the page
        if self.site.username(sysop=True):
            answer = u'y'
            if prompt and not hasattr(self.site, '_noDeletePrompt'):
                answer = pywikibot.inputChoice(
                    u'Do you want to delete %s?' % self.title(
                        asLink=True, forceInterwiki=True),
                    ['Yes', 'No', 'All'],
                    ['Y', 'N', 'A'],
                    'N')
                if answer in ['a', 'A']:
                    answer = 'y'
                    self.site._noDeletePrompt = True
            if answer in ['y', 'Y']:
                return self.site.deletepage(self, reason)
        else:  # Otherwise mark it for deletion
            if mark or hasattr(self.site, '_noMarkDeletePrompt'):
                answer = 'y'
            else:
                answer = pywikibot.inputChoice(
                    u"Can't delete %s; do you want to mark it "
                    "for deletion instead?" % self.title(asLink=True,
                                                         forceInterwiki=True),
                    ['Yes', 'No', 'All'],
                    ['Y', 'N', 'A'],
                    'N')
                if answer in ['a', 'A']:
                    answer = 'y'
                    self.site._noMarkDeletePrompt = True
            if answer in ['y', 'Y']:
                template = '{{delete|1=%s}}\n' % reason
                self.text = template + self.text
                return self.save(comment=reason)

    # all these DeletedRevisions methods need to be reviewed and harmonized
    # with the new framework; they do not appear functional
    def loadDeletedRevisions(self, step=None, total=None):
        """Retrieve all deleted revisions for this Page from Special/Undelete.

        Stores all revisions' timestamps, dates, editors and comments in
        self._deletedRevs attribute.

        @return: iterator of timestamps (which can be used to retrieve
            revisions later on).

        """
        if not hasattr(self, "_deletedRevs"):
            self._deletedRevs = {}
        for item in self.site.deletedrevs(self, step=step, total=total):
            for rev in item.get("revisions", []):
                self._deletedRevs[rev['timestamp']] = rev
                yield rev['timestamp']

    def getDeletedRevision(self, timestamp, retrieveText=False):
        """Return a particular deleted revision by timestamp.

        @return: a list of [date, editor, comment, text, restoration
            marker]. text will be None, unless retrieveText is True (or has
            been retrieved earlier). If timestamp is not found, returns
            None.

        """
        if hasattr(self, "_deletedRevs"):
            if timestamp in self._deletedRevs and (
                    (not retrieveText)
                    or "content" in self._deletedRevs[timestamp]):
                return self._deletedRevs[timestamp]
        for item in self.site.deletedrevs(self, start=timestamp,
                                          get_text=retrieveText, total=1):
            # should only be one item with one revision
            if item['title'] == self.title:
                if "revisions" in item:
                    return item["revisions"][0]

    def markDeletedRevision(self, timestamp, undelete=True):
        """Mark the revision identified by timestamp for undeletion.

        @param undelete: if False, mark the revision to remain deleted.

        """
        if not hasattr(self, "_deletedRevs"):
            self.loadDeletedRevisions()
        if timestamp not in self._deletedRevs:
            # TODO: Throw an exception?
            return
        self._deletedRevs[timestamp][4] = undelete
        self._deletedRevsModified = True

    @deprecate_arg("throttle", None)
    def undelete(self, comment=None):
        """Undelete revisions based on the markers set by previous calls.

        If no calls have been made since loadDeletedRevisions(), everything
        will be restored.

        Simplest case:
            Page(...).undelete('This will restore all revisions')

        More complex:
            pg = Page(...)
            revs = pg.loadDeletedRevsions()
            for rev in revs:
                if ... #decide whether to undelete a revision
                    pg.markDeletedRevision(rev) #mark for undeletion
            pg.undelete('This will restore only selected revisions.')

        @param comment: The undeletion edit summary.

        """
        if comment is None:
            pywikibot.output(u'Preparing to undelete %s.'
                             % (self.title(asLink=True)))
            comment = pywikibot.input(
                u'Please enter a reason for the undeletion:')
        return self.site.undelete(self, comment)

    @deprecate_arg("throttle", None)
    def protect(self, edit='sysop', move='sysop', create=None, upload=None,
                unprotect=False, reason=None, prompt=True, expiry=None):
        """(Un)protect a wiki page. Requires administrator status.

        Valid protection levels (in MediaWiki 1.12) are '' (equivalent to
        'none'), 'autoconfirmed', and 'sysop'. If None is given, however,
        that protection will be skipped.

        @param edit: Level of edit protection
        @param move: Level of move protection
        @param create: Level of create protection
        @param upload: Level of upload protection
        @param unprotect: If true, unprotect page editing and moving
            (equivalent to set both edit and move to '')
        @param reason: Edit summary.
        @param prompt: If true, ask user for confirmation.
        @param expiry: When the block should expire. This expiry will be
            applied to all protections.
            None, 'infinite', 'indefinite', 'never', and '' mean no expiry.
        @type expiry: pywikibot.Timestamp, string in GNU timestamp format
            (including ISO 8601).
        """
        if reason is None:
            if unprotect:
                un = u'un'
            else:
                un = u''
            pywikibot.output(u'Preparing to %sprotect %s.'
                             % (un, self.title(asLink=True)))
            reason = pywikibot.input(u'Please enter a reason for the action:')
        if unprotect:
            edit = move = ""
            # Apply to only edit and move for backward compatibility.
            # To unprotect article creation, for example,
            # create must be set to '' and the rest must be None
        answer = 'y'
        if prompt and not hasattr(self.site, '_noProtectPrompt'):
            answer = pywikibot.inputChoice(
                u'Do you want to change the protection level of %s?'
                % self.title(asLink=True, forceInterwiki=True),
                ['Yes', 'No', 'All'],
                ['Y', 'N', 'A'],
                'N')
            if answer in ['a', 'A']:
                answer = 'y'
                self.site._noProtectPrompt = True
        if answer in ['y', 'Y']:
            protections = {
                'edit': edit,
                'move': move,
                'create': create,
                'upload': upload,
            }
            return self.site.protect(self, protections, reason, expiry)

    def change_category(self, oldCat, newCat, comment=None, sortKey=None,
                        inPlace=True):
        """
        Remove page from oldCat and add it to newCat.

        @param oldCat and newCat: should be Category objects.
            If newCat is None, the category will be removed.

        @param comment: string to use as an edit summary

        @param sortKey: sortKey to use for the added category.
            Unused if newCat is None, or if inPlace=True

        @param inPlace: if True, change categories in place rather than
                      rearranging them.
        @return: True if page was saved changed, otherwise False.

        """
        # get list of Category objects the article is in and remove possible
        # duplicates
        cats = []
        for cat in pywikibot.textlib.getCategoryLinks(self.text,
                                                      site=self.site):
            if cat not in cats:
                cats.append(cat)

        site = self.site

        if not sortKey:
            sortKey = oldCat.sortKey

        if not self.canBeEdited():
            pywikibot.output(u"Can't edit %s, skipping it..."
                             % self.title(asLink=True))
            return False

        if oldCat not in cats:
            pywikibot.error(u'%s is not in category %s!'
                            % (self.title(asLink=True), oldCat.title()))
            return False

        # This prevents the bot from adding newCat if it is already present.
        if newCat in cats:
            newCat = None

        if inPlace or self.namespace() == 10:
            oldtext = self.get(get_redirect=True)
            newtext = pywikibot.replaceCategoryInPlace(oldtext, oldCat, newCat,
                                                       site=self.site)
        else:
            if newCat:
                cats[cats.index(oldCat)] = Category(site, newCat.title(),
                                                    sortKey=sortKey,
                                                    site=self.site)
            else:
                cats.pop(cats.index(oldCat))
            oldtext = self.get(get_redirect=True)
            try:
                newtext = pywikibot.replaceCategoryLinks(oldtext, cats)
            except ValueError:
                # Make sure that the only way replaceCategoryLinks() can return
                # a ValueError is in the case of interwiki links to self.
                pywikibot.output(u'Skipping %s because of interwiki link to '
                                 u'self' % self.title())
                return False

        if oldtext != newtext:
            try:
                self.put(newtext, comment)
                return True
            except pywikibot.EditConflict:
                pywikibot.output(u'Skipping %s because of edit conflict'
                                 % self.title())
            except pywikibot.SpamfilterError as e:
                pywikibot.output(u'Skipping %s because of blacklist entry %s'
                                 % (self.title(), e.url))
            except pywikibot.LockedPage:
                pywikibot.output(u'Skipping %s because page is locked'
                                 % self.title())
            except pywikibot.NoUsername:
                pywikibot.output(u'Page %s not saved; sysop privileges '
                                 u'required.' % self.title(asLink=True))
            except pywikibot.PageNotSaved as error:
                pywikibot.output(u'Saving page %s failed: %s'
                                 % (self.title(asLink=True), error.message))
        return False

    def isFlowPage(self):
        """Whether the given title is a Flow page.

        @return: bool
        """
        if not self.site.hasExtension('Flow', False):
            return False
        if not hasattr(self, '_flowinfo'):
            self.site.loadflowinfo(self)
        return 'enabled' in self._flowinfo

# ####### DEPRECATED METHODS ########

    @deprecated("Site.encoding()")
    def encoding(self):
        """DEPRECATED: use self.site.encoding instead."""
        return self.site.encoding()

    @deprecated("Page.title(withNamespace=False)")
    def titleWithoutNamespace(self, underscore=False):
        """DEPRECATED: use self.title(withNamespace=False) instead."""
        return self.title(underscore=underscore, withNamespace=False,
                          withSection=False)

    @deprecated("Page.title(as_filename=True)")
    def titleForFilename(self):
        """DEPRECATED: use self.title(as_filename=True) instead."""
        return self.title(as_filename=True)

    @deprecated("Page.title(withSection=False)")
    def sectionFreeTitle(self, underscore=False):
        """DEPRECATED: use self.title(withSection=False) instead."""
        return self.title(underscore=underscore, withSection=False)

    @deprecated("Page.title(asLink=True)")
    def aslink(self, forceInterwiki=False, textlink=False, noInterwiki=False):
        """DEPRECATED: use self.title(asLink=True) instead."""
        return self.title(asLink=True, forceInterwiki=forceInterwiki,
                          allowInterwiki=not noInterwiki, textlink=textlink)

    @deprecated("Page.title(asUrl=True)")
    def urlname(self):
        """Return the Page title encoded for use in an URL.

        DEPRECATED: use self.title(asUrl=True) instead.

        """
        return self.title(asUrl=True)

# ###### DISABLED METHODS (warnings provided) ######
    # these methods are easily replaced by editing the page's text using
    # textlib methods and then using put() on the result.

    def removeImage(self, image, put=False, summary=None, safe=True):
        """Old method to remove all instances of an image from page."""
        pywikibot.warning(u"Page.removeImage() is no longer supported.")

    def replaceImage(self, image, replacement=None, put=False, summary=None,
                     safe=True):
        """Old method to replace all instances of an image with another."""
        pywikibot.warning(u"Page.replaceImage() is no longer supported.")


class ImagePage(Page):

    """A subclass of Page representing an image descriptor wiki page.

    Supports the same interface as Page, with the following added methods:

    getImagePageHtml          : Download image page and return raw HTML text.
    fileURL                   : Return the URL for the image described on this
                                page.
    fileIsShared              : Return True if image stored on a shared
                                repository like Wikimedia Commons or Wikitravel.
    getFileMd5Sum             : Return image file's MD5 checksum.
    getFileVersionHistory     : Return the image file's version history.
    getFileVersionHistoryTable: Return the version history in the form of a
                                wiki table.
    usingPages                : Iterate Pages on which the image is displayed.

    """

    @deprecate_arg("insite", None)
    def __init__(self, source, title=u""):
        """Constructor."""
        Page.__init__(self, source, title, 6)
        if self.namespace() != 6:
            raise ValueError(u"'%s' is not in the image namespace!" % title)

    def getImagePageHtml(self):
        """
        Download the image page, and return the HTML, as a unicode string.

        Caches the HTML code, so that if you run this method twice on the
        same ImagePage object, the page will only be downloaded once.
        """
        if not hasattr(self, '_imagePageHtml'):
            from pywikibot.comms import http
            path = "%s/index.php?title=%s" \
                   % (self.site.scriptpath(), self.title(asUrl=True))
            self._imagePageHtml = http.request(self.site, path)
        return self._imagePageHtml

    def fileUrl(self):
        """Return the URL for the image described on this page."""
        # TODO add scaling option?
        if not hasattr(self, '_imageinfo'):
            self._imageinfo = self.site.loadimageinfo(self)
        return self._imageinfo['url']

    @deprecated("fileIsShared")
    def fileIsOnCommons(self):
        """DEPRECATED. Check if the image is stored on Wikimedia Commons.

        @return: bool
        """
        return self.fileIsShared()

    def fileIsShared(self):
        """Check if the image is stored on any known shared repository.

        @return: bool
        """
        # as of now, the only known repositories are commons and wikitravel
        # TODO: put the URLs to family file
        if not self.site.has_image_repository:
            return False
        elif 'wikitravel_shared' in self.site.shared_image_repository():
            return self.fileUrl().startswith(
                u'http://wikitravel.org/upload/shared/')
        else:
            return self.fileUrl().startswith(
                'https://upload.wikimedia.org/wikipedia/commons/')

    @deprecated("ImagePage.getFileSHA1Sum()")
    def getFileMd5Sum(self):
        """Return image file's MD5 checksum."""
# FIXME: MD5 might be performed on incomplete file due to server disconnection
# (see bug #1795683).
        f = urllib.urlopen(self.fileUrl())
        # TODO: check whether this needs a User-Agent header added
        h = hashlib.md5()
        h.update(f.read())
        md5Checksum = h.hexdigest()
        f.close()
        return md5Checksum

    def getFileSHA1Sum(self):
        """Return image file's SHA1 checksum."""
        if not hasattr(self, '_imageinfo'):
            self._imageinfo = self.site.loadimageinfo(self)
        return self._imageinfo['sha1']

    def getFileVersionHistory(self):
        """Return the image file's version history.

        @return: An iterator yielding tuples containing (timestamp,
            username, resolution, filesize, comment).

        """
        return self.site.loadimageinfo(self, history=True)

    def getFileVersionHistoryTable(self):
        """Return the version history in the form of a wiki table."""
        lines = []
        for info in self.getFileVersionHistory():
            datetime = info['timestamp']
            username = info['user']
            resolution = '%dx%d' % (info['height'], info['width'])
            size = info['size']
            comment = info['comment']
            lines.append(u'| %s || %s || %s || %s || <nowiki>%s</nowiki>'
                         % (datetime, username, resolution, size, comment))
        return u'{| border="1"\n! date/time || username || resolution || size || edit summary\n|----\n' + \
               u'\n|----\n'.join(lines) + '\n|}'

    def usingPages(self, step=None, total=None, content=False):
        """Yield Pages on which the image is displayed.

        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in total
        @param content: if True, load the current content of each iterated page
            (default False)

        """
        return self.site.imageusage(
            self, step=step, total=total, content=content)


class Category(Page):

    """A page in the Category: namespace."""

    @deprecate_arg("insite", None)
    def __init__(self, source, title=u"", sortKey=None):
        """
        Constructor.

        All parameters are the same as for Page() constructor.

        """
        self.sortKey = sortKey
        Page.__init__(self, source, title, ns=14)
        if self.namespace() != 14:
            raise ValueError(u"'%s' is not in the category namespace!"
                             % title)

    @deprecate_arg("forceInterwiki", None)
    @deprecate_arg("textlink", None)
    @deprecate_arg("noInterwiki", None)
    def aslink(self, sortKey=None):
        """Return a link to place a page in this Category.

        Use this only to generate a "true" category link, not for interwikis
        or text links to category pages.

        @param sortKey: The sort key for the article to be placed in this
            Category; if omitted, default sort key is used.
        @type sortKey: (optional) unicode

        """
        key = sortKey or self.sortKey
        if key is not None:
            titleWithSortKey = '%s|%s' % (self.title(withSection=False),
                                          key)
        else:
            titleWithSortKey = self.title(withSection=False)
        return '[[%s]]' % titleWithSortKey

    @deprecate_arg("startFrom", None)
    @deprecate_arg("cacheResults", None)
    def subcategories(self, recurse=False, step=None, total=None,
                      content=False):
        """Iterate all subcategories of the current category.

        @param recurse: if not False or 0, also iterate subcategories of
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate direct subcats and
            first-level sub-sub-cats, but no deeper.)
        @type recurse: int or bool
        @param step: limit each API call to this number of categories
        @param total: iterate no more than this number of
            subcategories in total (at all levels)
        @param content: if True, retrieve the content of the current version
            of each category description page (default False)

        """
        if not isinstance(recurse, bool) and recurse:
            recurse = recurse - 1
        if not hasattr(self, "_subcats"):
            self._subcats = []
            for member in self.site.categorymembers(
                    self, namespaces=[14], step=step,
                    total=total, content=content):
                subcat = Category(member)
                self._subcats.append(subcat)
                yield subcat
                if total is not None:
                    total -= 1
                    if total == 0:
                        return
                if recurse:
                    for item in subcat.subcategories(
                            recurse, step=step, total=total, content=content):
                        yield item
                        if total is not None:
                            total -= 1
                            if total == 0:
                                return
        else:
            for subcat in self._subcats:
                yield subcat
                if total is not None:
                    total -= 1
                    if total == 0:
                        return
                if recurse:
                    for item in subcat.subcategories(
                            recurse, step=step, total=total, content=content):
                        yield item
                        if total is not None:
                            total -= 1
                            if total == 0:
                                return

    @deprecate_arg("startFrom", "startsort")
    def articles(self, recurse=False, step=None, total=None,
                 content=False, namespaces=None, sortby="",
                 starttime=None, endtime=None, startsort=None,
                 endsort=None):
        """
        Yield all articles in the current category.

        By default, yields all *pages* in the category that are not
        subcategories!

        @param recurse: if not False or 0, also iterate articles in
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate articles in first-level
            subcats, but no deeper.)
        @type recurse: int or bool
        @param step: limit each API call to this number of pages
        @param total: iterate no more than this number of pages in
            total (at all levels)
        @param namespaces: only yield pages in the specified namespaces
        @type namespace: int or list of ints
        @param content: if True, retrieve the content of the current version
            of each page (default False)
        @param sortby: determines the order in which results are generated,
            valid values are "sortkey" (default, results ordered by category
            sort key) or "timestamp" (results ordered by time page was
            added to the category). This applies recursively.
        @type sortby: str
        @param starttime: if provided, only generate pages added after this
            time; not valid unless sortby="timestamp"
        @type starttime: pywikibot.Timestamp
        @param endtime: if provided, only generate pages added before this
            time; not valid unless sortby="timestamp"
        @type endtime: pywikibot.Timestamp
        @param startsort: if provided, only generate pages >= this title
            lexically; not valid if sortby="timestamp"
        @type startsort: str
        @param endsort: if provided, only generate pages <= this title
            lexically; not valid if sortby="timestamp"
        @type endsort: str

        """
        if namespaces is None:
            namespaces = [x for x in self.site.namespaces()
                          if x >= 0 and x != 14]
        for member in self.site.categorymembers(self,
                                                namespaces=namespaces,
                                                step=step, total=total,
                                                content=content, sortby=sortby,
                                                starttime=starttime,
                                                endtime=endtime,
                                                startsort=startsort,
                                                endsort=endsort
                                                ):
            yield member
            if total is not None:
                total -= 1
                if total == 0:
                    return
        if recurse:
            if not isinstance(recurse, bool) and recurse:
                recurse = recurse - 1
            for subcat in self.subcategories(step=step):
                for article in subcat.articles(recurse, step=step, total=total,
                                               content=content,
                                               namespaces=namespaces,
                                               sortby=sortby,
                                               starttime=starttime,
                                               endtime=endtime,
                                               startsort=startsort,
                                               endsort=endsort
                                               ):
                    yield article
                    if total is not None:
                        total -= 1
                        if total == 0:
                            return

    def members(self, recurse=False, namespaces=None, step=None, total=None,
                content=False):
        """Yield all category contents (subcats, pages, and files)."""
        for member in self.site.categorymembers(
                self, namespaces, step=step, total=total, content=content):
            yield member
            if total is not None:
                total -= 1
                if total == 0:
                    return
        if recurse:
            if not isinstance(recurse, bool) and recurse:
                recurse = recurse - 1
            for subcat in self.subcategories(step=step):
                for article in subcat.members(
                        recurse, namespaces, step=step,
                        total=total, content=content):
                    yield article
                    if total is not None:
                        total -= 1
                        if total == 0:
                            return

    def isEmptyCategory(self):
        """Return True if category has no members (including subcategories)."""
        for member in self.site.categorymembers(self, total=1):
            return False
        return True

    def isHiddenCategory(self):
        """Return True if the category is hidden."""
        # FIXME
        # This should use action=query&list=allcategories
        # setting acfrom and acto to the category title and adding
        # acprop=hidden but currently fails  in some cases
        # (see bug 48824)
        return '__HIDDENCAT__' in self.expand_text()

    def copyTo(self, cat, message):
        """
        Copy text of category page to a new page.  Does not move contents.

        @param cat: New category title (without namespace) or Category object
        @type cat: unicode or Category
        @param message: message to use for category creation message
        If two %s are provided in message, will be replaced
        by (self.title, authorsList)
        @type message: unicode
        @return: True if copying was successful, False if target page
            already existed.

        """
        # This seems far too specialized to be in the top-level framework
        # move to category.py? (Although it doesn't seem to be used there,
        # either)
        if not isinstance(cat, Category):
            cat = self.site.category_namespace() + ':' + cat
            targetCat = Category(self.site, cat)
        else:
            targetCat = cat
        if targetCat.exists():
            pywikibot.output(u'Target page %s already exists!'
                             % targetCat.title(),
                             level=pywikibot.WARNING)
            return False
        else:
            pywikibot.output('Moving text from %s to %s.'
                             % (self.title(), targetCat.title()))
            authors = ', '.join(self.contributingUsers())
            try:
                creationSummary = message % (self.title(), authors)
            except TypeError:
                creationSummary = message
            targetCat.put(self.get(), creationSummary)
            return True

    def copyAndKeep(self, catname, cfdTemplates, message):
        """Copy partial category page text (not contents) to a new title.

        Like copyTo above, except this removes a list of templates (like
        deletion templates) that appear in the old category text.  It also
        removes all text between the two HTML comments BEGIN CFD TEMPLATE
        and END CFD TEMPLATE. (This is to deal with CFD templates that are
        substituted.)

        Returns true if copying was successful, false if target page already
        existed.

        @param catname: New category title (without namespace)
        @param cfdTemplates: A list (or iterator) of templates to be removed
            from the page text
        @return: True if copying was successful, False if target page
            already existed.

        """
        # I don't see why we need this as part of the framework either
        # move to scripts/category.py?
        catname = self.site.category_namespace() + ':' + catname
        targetCat = Category(self.site, catname)
        if targetCat.exists():
            pywikibot.warning(u'Target page %s already exists!'
                              % targetCat.title())
            return False
        else:
            pywikibot.output(
                'Moving text from %s to %s.'
                % (self.title(), targetCat.title()))
            authors = ', '.join(self.contributingUsers())
            creationSummary = message % (self.title(), authors)
            newtext = self.get()
        for regexName in cfdTemplates:
            matchcfd = re.compile(r"{{%s.*?}}" % regexName, re.IGNORECASE)
            newtext = matchcfd.sub('', newtext)
            matchcomment = re.compile(
                r"<!--BEGIN CFD TEMPLATE-->.*?<!--END CFD TEMPLATE-->",
                re.IGNORECASE | re.MULTILINE | re.DOTALL)
            newtext = matchcomment.sub('', newtext)
            pos = 0
            while (newtext[pos:pos + 1] == "\n"):
                pos = pos + 1
            newtext = newtext[pos:]
            targetCat.put(newtext, creationSummary)
            return True

    @property
    def categoryinfo(self):
        """Return a dict containing information about the category.

        The dict contains values for:

        Numbers of pages, subcategories, files, and total contents.

        @return: dict
        """
        return self.site.categoryinfo(self)

# ### DEPRECATED METHODS ####
    @deprecated("list(Category.subcategories(...))")
    def subcategoriesList(self, recurse=False):
        """DEPRECATED: Equivalent to list(self.subcategories(...))."""
        return sorted(list(set(self.subcategories(recurse))))

    @deprecated("list(Category.articles(...))")
    def articlesList(self, recurse=False):
        """DEPRECATED: equivalent to list(self.articles(...))."""
        return sorted(list(set(self.articles(recurse))))

    @deprecated("Category.categories()")
    def supercategories(self):
        """DEPRECATED: equivalent to self.categories()."""
        return self.categories()

    @deprecated("list(Category.categories(...))")
    def supercategoriesList(self):
        """DEPRECATED: equivalent to list(self.categories(...))."""
        return sorted(list(set(self.categories())))


ip_regexp = re.compile(r'^(?:(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                       r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|'
                       r'(((?=(?=(.*?(::)))\3(?!.+\4)))\4?|[\dA-F]{1,4}:)'
                       r'([\dA-F]{1,4}(\4|:\b)|\2){5}'
                       r'(([\dA-F]{1,4}(\4|:\b|$)|\2){2}|'
                       r'(((2[0-4]|1\d|[1-9])?\d|25[0-5])\.?\b){4}))\Z',
                       re.IGNORECASE)


class User(Page):

    """A class that represents a Wiki user.

    This class also represents the Wiki page User:<username>
    """

    @deprecate_arg("site", "source")
    @deprecate_arg("name", "title")
    def __init__(self, source, title=u''):
        """Initializer for a User object.

        All parameters are the same as for Page() constructor.
        """
        if len(title) > 1 and title[0] == u'#':
            self._isAutoblock = True
            title = title[1:]
        else:
            self._isAutoblock = False
        Page.__init__(self, source, title, ns=2)
        if self.namespace() != 2:
            raise ValueError(u"'%s' is not in the user namespace!"
                             % title)
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock.
            pywikibot.output(
                "This is an autoblock ID, you can only use to unblock it.")

    def name(self):
        """
        The username.

        @return: unicode
        """
        return self.username

    @property
    def username(self):
        """ The username.

        Convenience method that returns the title of the page with
        namespace prefix omitted, which is the username.

        @return: unicode
        """
        if self._isAutoblock:
            return u'#' + self.title(withNamespace=False)
        else:
            return self.title(withNamespace=False)

    def isRegistered(self, force=False):
        """ Determine if the user is registered on the site.

        It is possible to have a page named User:xyz and not have
        a corresponding user with username xyz.

        The page does not need to exist for this method to return
        True.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: bool
        """
        if self.isAnonymous():
            return False
        else:
            return self.getprops(force).get('missing') is None

    def isAnonymous(self):
        """ Determine if the user is editing as an IP address.

        @return: bool
        """
        return ip_regexp.match(self.username) is not None

    def getprops(self, force=False):
        """ Return a properties about the user.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: dict
        """
        if force:
            del self._userprops
        if not hasattr(self, '_userprops'):
            self._userprops = list(self.site.users([self.username, ]))[0]
            if self.isAnonymous():
                r = list(self.site.blocks(users=self.username))
                if r:
                    self._userprops['blockedby'] = r[0]['by']
                    self._userprops['blockreason'] = r[0]['reason']
        return self._userprops

    @deprecated('User.registration()')
    def registrationTime(self, force=False):
        """ DEPRECATED. Fetch registration date for this user.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: long (MediaWiki's internal timestamp format) or 0
        """
        if self.registration():
            return long(self.registration().strftime('%Y%m%d%H%M%S'))
        else:
            return 0

    def registration(self, force=False):
        """ Fetch registration date for this user.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: pywikibot.Timestamp or None
        """
        reg = self.getprops(force).get('registration')
        if reg:
            return pywikibot.Timestamp.fromISOformat(reg)

    def editCount(self, force=False):
        """ Return edit count for a registered user.

        Always returns 0 for 'anonymous' users.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: long
        """
        if 'editcount' in self.getprops(force):
            return self.getprops()['editcount']
        else:
            return 0

    def isBlocked(self, force=False):
        """ Determine whether the user is currently blocked.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: bool
        """
        return 'blockedby' in self.getprops(force)

    def isEmailable(self, force=False):
        """ Determine whether emails may be send to this user through MediaWiki.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: bool
        """
        return 'emailable' in self.getprops(force)

    def groups(self, force=False):
        """ Return a list of groups to which this user belongs.

        The list of groups may be empty.

        @param force: if True, forces reloading the data from API
        @type force: bool

        @return: list
        """
        if 'groups' in self.getprops(force):
            return self.getprops()['groups']
        else:
            return []

    def getUserPage(self, subpage=u''):
        """ Return a Page object relative to this user's main page.

        @param subpage: subpage part to be appended to the main
                            page title (optional)
        @type subpage: unicode
        """
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock, so has no user pages per se.
            raise AutoblockUser(
                "This is an autoblock ID, you can only use to unblock it.")
        if subpage:
            subpage = u'/' + subpage
        return Page(Link(self.title() + subpage, self.site))

    def getUserTalkPage(self, subpage=u''):
        """ Return a Page object relative to this user's main talk page.

        @param subpage: subpage part to be appended to the main
                            talk page title (optional)
        @type subpage: unicode
        """
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock, so has no user talk pages per se.
            raise AutoblockUser(
                "This is an autoblock ID, you can only use to unblock it.")
        if subpage:
            subpage = u'/' + subpage
        return Page(Link(self.title(withNamespace=False) + subpage,
                         self.site, defaultNamespace=3))

    def sendMail(self, subject, text, ccme=False):
        """ Send an email to this user via MediaWiki's email interface.

        Return True on success, False otherwise.
        This method can raise an UserActionRefuse exception in case this user
        doesn't allow sending email to him or the currently logged in bot
        doesn't have the right to send emails.

        @param subject: the subject header of the mail
        @type subject: unicode
        @param text: mail body
        @type text: unicode
        @param ccme: if True, sends a copy of this email to the bot
        @type ccme: bool
        """
        if not self.isEmailable():
            raise UserActionRefuse('This user is not mailable')

        if not self.site.has_right('sendemail'):
            raise UserActionRefuse('You don\'t have permission to send mail')

        params = {
            'action': 'emailuser',
            'target': self.username,
            'token': self.site.token(self, 'email'),
            'subject': subject,
            'text': text,
        }
        if ccme:
            params['ccme'] = 1
        mailrequest = pywikibot.data.api.Request(**params)
        maildata = mailrequest.submit()

        if 'error' in maildata:
            code = maildata['error']['code']
            if code == u'usermaildisabled ':
                pywikibot.output(u'User mail has been disabled')
        elif 'emailuser' in maildata:
            if maildata['emailuser']['result'] == u'Success':
                pywikibot.output(u'Email sent.')
                return True
        return False

    def block(self, expiry, reason, anononly=True, nocreate=True,
              autoblock=True, noemail=False, reblock=False):
        """
        Block user.

        @param expiry: When the block should expire
        @type expiry: pywikibot.Timestamp|str
        @param reason: Block reason
        @type reason: basestring
        @param anononly: Whether block should only affect anonymous users
        @type anononly: bool
        @param nocreate: Whether to block account creation
        @type nocreate: bool
        @param autoblock: Whether to enable autoblock
        @type autoblock: bool
        @param noemail: Whether to disable email access
        @type noemail: bool
        @param reblock: Whether to reblock if a block already is set
        @type reblock: bool
        @return: None
        """
        try:
            self.site.blockuser(self, expiry, reason, anononly, nocreate,
                                autoblock, noemail, reblock)
        except pywikibot.data.api.APIError as err:
            if err.code == 'invalidrange':
                raise ValueError("%s is not a valid IP range." % self.username)
            else:
                raise err

    @deprecated("contributions")
    @deprecate_arg("limit", "total")  # To be consistent with rest of framework
    def editedPages(self, total=500):
        """ DEPRECATED. Use contributions().

        Yields pywikibot.Page objects that this user has
        edited, with an upper bound of 'total'. Pages returned are not
        guaranteed to be unique.

        @param total: limit result to this number of pages.
        @type total: int.
        """
        for item in self.contributions(total=total):
            yield item[0]

    @deprecate_arg("limit", "total")  # To be consistent with rest of framework
    @deprecate_arg("namespace", "namespaces")
    def contributions(self, total=500, namespaces=[]):
        """ Yield tuples describing this user edits.

        Each tuple is composed of a pywikibot.Page object,
        the revision id (int), the edit timestamp (as a pywikibot.Timestamp
        object), and the comment (unicode).
        Pages returned are not guaranteed to be unique.

        @param total: limit result to this number of pages
        @type total: int
        @param namespaces: only iterate links in these namespaces
        @type namespaces: list
        """
        for contrib in self.site.usercontribs(
                user=self.username, namespaces=namespaces, total=total):
            ts = pywikibot.Timestamp.fromISOformat(contrib['timestamp'])
            yield (Page(self.site, contrib['title'], contrib['ns']),
                   contrib['revid'],
                   ts,
                   contrib.get('comment', None)
                   )

    @deprecate_arg("number", "total")
    def uploadedImages(self, total=10):
        """ Yield tuples describing files uploaded by this user.

        Each tuple is composed of a pywikibot.Page, the timestamp (str in
        ISO8601 format), comment (unicode) and a bool for pageid > 0.
        Pages returned are not guaranteed to be unique.

        @param total: limit result to this number of pages
        @type total: int
        """
        if not self.isRegistered():
            raise StopIteration
        for item in self.site.logevents(
                logtype='upload', user=self.username, total=total):
            yield (ImagePage(self.site, item.title().title()),
                   unicode(item.timestamp()),
                   item.comment(),
                   item.pageid() > 0
                   )


class WikibasePage(Page):

    """
    The base page for the Wikibase extension.

    There should be no need to instantiate this directly.
    """

    def __init__(self, site, title=u"", **kwargs):
        """ Constructor. """
        if not isinstance(site, pywikibot.site.DataSite):
            raise TypeError("site must be a pywikibot.site.DataSite object")
        Page.__init__(self, site, title, **kwargs)
        self.repo = self.site
        self._isredir = False  # Wikibase pages cannot be a redirect

    def title(self, **kwargs):
        """ Page title.

        If the item was instantiated without an ID,
        fetch the ID and reparse the title.
        """
        if self.namespace() == 0:
            self.getID()
            if self._link._text != self.id:
                self._link._text = self.id
                del self._link._title
        return Page(self).title(**kwargs)

    @deprecated("_defined_by")
    def __defined_by(self, singular=False):
        """ DEPRECATED. """
        return self._defined_by(singular=singular)

    def _defined_by(self, singular=False):
        """
        Internal function to provide the API parameters to identify the entity.

        Once an item's "p/q##" is looked up, that will be used for all future
        requests.

        @param singular: Whether the parameter names should use the singular
                         form
        @type singular: bool
        """
        params = {}
        if singular:
            id = 'id'
            site = 'site'
            title = 'title'
        else:
            id = 'ids'
            site = 'sites'
            title = 'titles'
        # id overrides all
        if hasattr(self, 'id'):
            params[id] = self.id
            return params

        # the rest only applies to ItemPages, but is still needed here.
        if hasattr(self, '_site') and hasattr(self, '_title'):
            params[site] = self._site.dbName()
            params[title] = self._title
        else:
            quit()
            params[id] = self.getID()

        return params

    def exists(self):
        """
        Determine if an entity exists in the data repository.

        @return: bool
        """
        if not hasattr(self, '_content'):
            try:
                self.get()
                return True
            except pywikibot.NoPage:
                return False
        return 'lastrevid' in self._content

    def get(self, force=False, *args, **kwargs):
        """
        Fetch all page data, and cache it.

        @param force: override caching
        @type force: bool
        @param args: may be used to specify custom props.
        """
        lazy_loading_id = not hasattr(self, 'id') and hasattr(self, '_site')
        if force or not hasattr(self, '_content'):
            data = self.repo.loadcontent(self._defined_by(), *args)
            self.id = list(data.keys())[0]
            self._content = data[self.id]
        if 'lastrevid' in self._content:
            self.lastrevid = self._content['lastrevid']
        else:
            if lazy_loading_id:
                p = Page(self._site, self._title)
                if not p.exists():
                    raise pywikibot.NoPage(p)
            raise pywikibot.NoPage(self)

        # aliases
        self.aliases = {}
        if 'aliases' in self._content:
            for lang in self._content['aliases']:
                self.aliases[lang] = list()
                for value in self._content['aliases'][lang]:
                    self.aliases[lang].append(value['value'])

        # labels
        self.labels = {}
        if 'labels' in self._content:
            for lang in self._content['labels']:
                if 'removed' not in self._content['labels'][lang]:  # Bug 54767
                    self.labels[lang] = self._content['labels'][lang]['value']

        # descriptions
        self.descriptions = {}
        if 'descriptions' in self._content:
            for lang in self._content['descriptions']:
                self.descriptions[lang] = self._content[
                    'descriptions'][lang]['value']

        return {'aliases': self.aliases,
                'labels': self.labels,
                'descriptions': self.descriptions,
                }

    def getID(self, numeric=False, force=False):
        """
        Get the entity identifier.

        @param numeric: Strip the first letter and return an int
        @type numeric: bool
        @param force: Force an update of new data
        @type force: bool
        """
        if not hasattr(self, 'id') or force:
            self.get(force=force)
        if numeric:
            return int(self.id[1:])
        return self.id

    def latestRevision(self):
        """
        Get the revision identifier for the most recent revision of the entity.

        @return: long
        """
        if not hasattr(self, 'lastrevid'):
            self.get()
        return self.lastrevid

    def __normalizeLanguages(self, data):
        """
        Helper function to replace site objects with their language codes.

        @param data: The dict to check
        @type data: dict

        @return: dict
        """
        for key in data:
            if isinstance(key, pywikibot.site.BaseSite):
                data[key.language()] = data[key]
                del data[key]
        return data

    def getdbName(self, site):
        """
        Helper function to obtain a dbName for a Site.

        @param site: The site to look up.
        @type site: Site
        """
        if isinstance(site, pywikibot.site.BaseSite):
            return site.dbName()
        return site

    def editEntity(self, data, **kwargs):
        """
        Edit an entity using Wikibase wbeditentity API.

        This function is wrapped around by:
         *editLabels
         *editDescriptions
         *editAliases
         *ItemPage.setSitelinks

        @param data: Data to be saved
        @type data: dict
        """
        if hasattr(self, 'lastrevid'):
            baserevid = self.lastrevid
        else:
            baserevid = None
        updates = self.repo.editEntity(self._defined_by(singular=True), data,
                                       baserevid=baserevid, **kwargs)
        self.lastrevid = updates['entity']['lastrevid']

    def editLabels(self, labels, **kwargs):
        """
        Edit entity labels.

        Labels should be a dict, with the key
        as a language or a site object. The
        value should be the string to set it to.
        You can set it to '' to remove the label.
        """
        labels = self.__normalizeLanguages(labels)
        for key in labels:
            labels[key] = {'language': key, 'value': labels[key]}
        data = {'labels': labels}
        self.editEntity(data, **kwargs)

    def editDescriptions(self, descriptions, **kwargs):
        """
        Edit entity descriptions.

        Descriptions should be a dict, with the key
        as a language or a site object. The
        value should be the string to set it to.
        You can set it to '' to remove the description.
        """
        descriptions = self.__normalizeLanguages(descriptions)
        for key in descriptions:
            descriptions[key] = {'language': key, 'value': descriptions[key]}
        data = {'descriptions': descriptions}
        self.editEntity(data, **kwargs)

    def editAliases(self, aliases, **kwargs):
        """
        Edit entity aliases.

        Aliases should be a dict, with the key
        as a language or a site object. The
        value should be a list of strings.
        """
        aliases = self.__normalizeLanguages(aliases)
        for (key, strings) in list(aliases.items()):
            aliases[key] = [{'language': key, 'value': i} for i in strings]
        data = {'aliases': aliases}
        self.editEntity(data, **kwargs)


class ItemPage(WikibasePage):

    """ A Wikibase item.

    A Wikibase item may be defined by either a 'Q' id (qid),
    or by a site & title.

    If an item is defined by site & title, once an item's qid has
    been looked up, the item is then defined by the qid.
    """

    def __init__(self, site, title=None):
        """
        Constructor.

        @param site: data repository
        @type site: pywikibot.site.DataSite
        @param title: id number of item, "Q###"
        """
        super(ItemPage, self).__init__(site, title, ns=0)
        self.id = title.upper()  # This might cause issues if not ns0?

    @classmethod
    def fromPage(cls, page):
        """
        Get the ItemPage for a Page that links to it.

        @param page: Page
        @return: ItemPage
        """
        if not page.site.has_transcluded_data:
            raise pywikibot.WikiBaseError(u'%s has no transcluded data'
                                          % page.site)
        repo = page.site.data_repository()
        if hasattr(page,
                   '_pageprops') and page.properties().get('wikibase_item'):
            # If we have already fetched the pageprops for something else,
            # we already have the id, so use it
            return cls(repo, page.properties().get('wikibase_item'))
        i = cls(repo, 'null')
        del i.id
        i._site = page.site
        i._title = page.title()
        return i

    def get(self, force=False, *args, **kwargs):
        """
        Fetch all item data, and cache it.

        @param force: override caching
        @type force: bool
        @param args: values of props
        """
        super(ItemPage, self).get(force=force, *args, **kwargs)

        # claims
        self.claims = {}
        if 'claims' in self._content:
            for pid in self._content['claims']:
                self.claims[pid] = list()
                for claim in self._content['claims'][pid]:
                    c = Claim.fromJSON(self.repo, claim)
                    c.on_item = self
                    self.claims[pid].append(c)

        # sitelinks
        self.sitelinks = {}
        if 'sitelinks' in self._content:
            for dbname in self._content['sitelinks']:
                self.sitelinks[dbname] = self._content[
                    'sitelinks'][dbname]['title']

        return {'aliases': self.aliases,
                'labels': self.labels,
                'descriptions': self.descriptions,
                'sitelinks': self.sitelinks,
                'claims': self.claims
                }

    def iterlinks(self, family=None):
        """
        Iterate through all the sitelinks.

        @param family: string/Family object which represents what family of
                       links to iterate
        @type family: str|pywikibot.family.Family
        @return: iterator of pywikibot.Page objects
        """
        if not hasattr(self, 'sitelinks'):
            self.get()
        if family is not None and not isinstance(family,
                                                 pywikibot.family.Family):
            family = pywikibot.site.Family(family)
        for dbname in self.sitelinks:
            pg = Page(pywikibot.site.APISite.fromDBName(dbname),
                      self.sitelinks[dbname])
            if family is None or family == pg.site.family:
                yield pg

    def getSitelink(self, site, force=False):
        """
        Return the title for the specific site.

        If the item doesn't have that language, raise NoPage.

        @param site: Site to find the linked page of.
        @type site: pywikibot.Site or database name
        @param force: override caching

        @return: unicode
        """
        if force or not hasattr(self, '_content'):
            self.get(force=force)
        dbname = self.getdbName(site)
        if dbname not in self.sitelinks:
            raise pywikibot.NoPage(self)
        else:
            return self.sitelinks[dbname]

    def setSitelink(self, sitelink, **kwargs):
        """
        Set sitelinks. Calls setSitelinks().

        A sitelink can either be a Page object,
        or a {'site':dbname,'title':title} dictionary.
        """
        self.setSitelinks([sitelink], **kwargs)

    def removeSitelink(self, site, **kwargs):
        """
        Remove a sitelink.

        A site can either be a Site object, or it can be a dbName.
        """
        self.removeSitelinks([site], **kwargs)

    def removeSitelinks(self, sites, **kwargs):
        """
        Remove sitelinks.

        Sites should be a list, with values either
        being Site objects, or dbNames.
        """
        data = list()
        for site in sites:
            site = self.getdbName(site)
            data.append({'site': site, 'title': ''})
        self.setSitelinks(data, **kwargs)

    def setSitelinks(self, sitelinks, **kwargs):
        """
        Set sitelinks.

        Sitelinks should be a list. Each item in the
        list can either be a Page object, or a dict
        with a value for 'site' and 'title'.
        """
        data = {}
        for obj in sitelinks:
            if isinstance(obj, Page):
                dbName = self.getdbName(obj.site)
                data[dbName] = {'site': dbName, 'title': obj.title()}
            else:
                # TODO: Do some verification here
                dbName = obj['site']
                data[dbName] = obj
        data = {'sitelinks': data}
        self.editEntity(data, **kwargs)

    def addClaim(self, claim, bot=True, **kwargs):
        """
        Add a claim to the item.

        @param claim: The claim to add
        @type claim: Claim
        @param bot: Whether to flag as bot (if possible)
        @type bot: bool
        """
        self.repo.addClaim(self, claim, bot=bot, **kwargs)
        claim.on_item = self

    def removeClaims(self, claims, **kwargs):
        """
        Remove the claims from the item.

        @type claims: list

        """
        # this check allows single claims to be removed by pushing them into a
        # list of length one.
        if isinstance(claims, pywikibot.Claim):
            claims = [claims]
        self.repo.removeClaims(claims, **kwargs)

    def mergeInto(self, item, **kwargs):
        """
        Merge the item into another item.

        @param item: The item to merge into
        @type item: pywikibot.ItemPage
        """
        self.repo.mergeItems(fromItem=self, toItem=item, **kwargs)


class Property():

    """
    A Wikibase property.

    While every Wikibase property has a Page on the data repository,
    this object is for when the property is used as part of another concept
    where the property is not _the_ Page of the property.

    For example, a claim on an ItemPage has many property attributes, and so
    it subclasses this Property class, but a claim does not have Page like
    behaviour and semantics.
    """

    types = {'wikibase-item': ItemPage,
             'string': basestring,
             'commonsMedia': ImagePage,
             'globe-coordinate': pywikibot.Coordinate,
             'url': basestring,
             'time': pywikibot.WbTime,
             'quantity': pywikibot.WbQuantity,
             }

    value_types = {'wikibase-item': 'wikibase-entityid',
                   'commonsMedia': 'string',
                   'url': 'string',
                   'globe-coordinate': 'globecoordinate',
                   }

    def __init__(self, site, id=None, datatype=None):
        """
        Constructor.

        @param datatype: datatype of the property;
            if not given, it will be queried via the API
        @type datatype: basestring
        """
        self.repo = site
        self.id = id.upper()
        if datatype:
            self._type = datatype

    @property
    def type(self):
        """
        Return the type of this property.

        @return: str
        """
        if not hasattr(self, '_type'):
            self._type = self.repo.getPropertyType(self)
        return self._type

    @deprecated("Property.type")
    def getType(self):
        """
        Return the type of this property.

        It returns 'globecoordinate' for type 'globe-coordinate'
        in order to be backwards compatible.  See
        https://gerrit.wikimedia.org/r/#/c/135405/ for background.
        """
        if self.type == 'globe-coordinate':
            return 'globecoordinate'
        else:
            return self._type

    def getID(self, numeric=False):
        """
        Get the identifier of this property.

        @param numeric: Strip the first letter and return an int
        @type numeric: bool
        """
        if numeric:
            return int(self.id[1:])
        else:
            return self.id


class PropertyPage(WikibasePage, Property):

    """
    A Wikibase entity in the property namespace.

    Should be created as:
        PropertyPage(DataSite, 'Property:P21')
    """

    def __init__(self, source, title=u""):
        """
        Constructor.

        @param source: data repository property is on
        @type source: pywikibot.site.DataSite
        @param title: page name of property, like "Property:P##"
        """
        WikibasePage.__init__(self, source, title, ns=120)
        Property.__init__(self, source, title)
        self.id = self.title(withNamespace=False).upper()
        if not self.id.startswith(u'P'):
            raise ValueError(u"'%s' is not a property page!" % self.title())

    def get(self, force=False, *args):
        """
        Fetch the property entity, and cache it.

        @param force: override caching
        @param args: values of props
        """
        if force or not hasattr(self, '_content'):
            WikibasePage.get(self, force=force, *args)
        self.type = self._content['datatype']

    def newClaim(self, *args, **kwargs):
        """
        Helper function to create a new claim object for this property.

        @return: Claim
        """
        return Claim(self.site, self.getID(), *args, **kwargs)


class QueryPage(WikibasePage):

    """
    A Wikibase Query entity.

    For future usage, not implemented yet.
    """

    def __init__(self, site, title):
        """Constructor."""
        WikibasePage.__init__(self, site, title, ns=122)
        self.id = self.title(withNamespace=False).upper()
        if not self.id.startswith(u'U'):
            raise ValueError(u"'%s' is not a query page!" % self.title())


class Claim(Property):

    """
    A Claim on a Wikibase entity.

    Claims are standard claims as well as references.
    """

    def __init__(self, site, pid, snak=None, hash=None, isReference=False,
                 isQualifier=False, **kwargs):
        """
        Constructor.

        Defined by the "snak" value, supplemented by site + pid

        @param site: repository the claim is on
        @type site: pywikibot.site.DataSite
        @param pid: property id, with "P" prefix
        @param snak: snak identifier for claim
        @param hash: hash identifier for references
        @param isReference: whether specified claim is a reference
        @param isQualifier: whether specified claim is a qualifier
        """
        Property.__init__(self, site, pid, **kwargs)
        self.snak = snak
        self.hash = hash
        self.isReference = isReference
        self.isQualifier = isQualifier
        if self.isQualifier and self.isReference:
            raise ValueError(u'Claim cannot be both a qualifier and reference.')
        self.sources = []
        self.qualifiers = collections.defaultdict(list)
        self.target = None
        self.snaktype = 'value'
        self.rank = 'normal'
        self.on_item = None  # The item it's on

    @staticmethod
    def fromJSON(site, data):
        """
        Create a claim object from JSON returned in the API call.

        @param data: JSON containing claim data
        @type data: dict

        @return: Claim
        """
        claim = Claim(site, data['mainsnak']['property'],
                      datatype=data['mainsnak'].get('datatype', None))
        if 'id' in data:
            claim.snak = data['id']
        elif 'hash' in data:
            claim.isReference = True
            claim.hash = data['hash']
        else:
            claim.isQualifier = True
        claim.snaktype = data['mainsnak']['snaktype']
        if claim.getSnakType() == 'value':
            value = data['mainsnak']['datavalue']['value']
            if claim.type == 'wikibase-item':
                claim.target = ItemPage(site, 'Q' + str(value['numeric-id']))
            elif claim.type == 'commonsMedia':
                claim.target = ImagePage(site.image_repository(), value)
            elif claim.type == 'globe-coordinate':
                claim.target = pywikibot.Coordinate.fromWikibase(value, site)
            elif claim.type == 'time':
                claim.target = pywikibot.WbTime.fromWikibase(value)
            elif claim.type == 'quantity':
                claim.target = pywikibot.WbQuantity.fromWikibase(value)
            else:
                # This covers string, url types
                claim.target = value
        if 'rank' in data:  # References/Qualifiers don't have ranks
            claim.rank = data['rank']
        if 'references' in data:
            for source in data['references']:
                claim.sources.append(Claim.referenceFromJSON(site, source))
        if 'qualifiers' in data:
            for prop in data['qualifiers']:
                for qualifier in data['qualifiers'][prop]:
                    qual = Claim.qualifierFromJSON(site, qualifier)
                    claim.qualifiers[prop].append(qual)
        return claim

    @staticmethod
    def referenceFromJSON(site, data):
        """
        Create a dict of claims from reference JSON returned in the API call.

        Reference objects are represented a
        bit differently, and require some
        more handling.

        @return: dict
        """
        source = collections.defaultdict(list)
        for prop in list(data['snaks'].values()):
            for claimsnak in prop:
                claim = Claim.fromJSON(site, {'mainsnak': claimsnak,
                                              'hash': data['hash']})
                source[claim.getID()].append(claim)
        return source

    @staticmethod
    def qualifierFromJSON(site, data):
        """
        Create a Claim for a qualifier from JSON.

        Qualifier objects are represented a bit
        differently like references, but I'm not
        sure if this even requires it's own function.

        @return: Claim
        """
        wrap = {'mainsnak': data}
        return Claim.fromJSON(site, wrap)

    def setTarget(self, value):
        """
        Set the target value in the local object.

        @param value: The new target value.
        @type value: object

        Raises ValueError if value is not of the type
               required for the Claim type.
        """
        value_class = self.types[self.type]
        if not isinstance(value, value_class):
            raise ValueError("%s is not type %s."
                                 % (value, value_class))
        self.target = value

    def changeTarget(self, value=None, snaktype='value', **kwargs):
        """
        Set the target value in the data repository.

        @param value: The new target value.
        @type value: object
        @param snaktype: The new snak type.
        @type value: str ('value', 'somevalue', or 'novalue')
        """
        if value:
            self.setTarget(value)

        data = self.repo.changeClaimTarget(self, snaktype=snaktype,
                                           **kwargs)
        # TODO: Re-create the entire item from JSON, not just id
        self.snak = data['claim']['id']

    def getTarget(self):
        """
        Return the target value of this Claim.

        None is returned if no target is set

        @return: object
        """
        return self.target

    def getSnakType(self):
        """
        Return the type of snak.

        @return: str ('value', 'somevalue' or 'novalue')
        """
        return self.snaktype

    def setSnakType(self, value):
        """Set the type of snak.

        @param value: Type of snak
        @type value: str ('value', 'somevalue', or 'novalue')
        """
        if value in ['value', 'somevalue', 'novalue']:
            self.snaktype = value
        else:
            raise ValueError(
                "snaktype must be 'value', 'somevalue', or 'novalue'.")

    def getRank(self):
        """Return the rank of the Claim."""
        return self.rank

    def setRank(self):
        """
        Set the rank of the Claim.

        Has not been implemented in the Wikibase API yet
        """
        raise NotImplementedError

    def changeSnakType(self, value=None, **kwargs):
        """
        Save the new snak value.

        TODO: Is this function really needed?
        """
        if value:
            self.setSnakType(value)
        self.changeTarget(snaktype=self.getSnakType(), **kwargs)

    def getSources(self):
        """
        Return a list of sources, each being a list of Claims.

        @return: list
        """
        return self.sources

    def addSource(self, claim, **kwargs):
        """
        Add the claim as a source.

        @param claim: the claim to add
        @type claim: pywikibot.Claim
        """
        self.addSources([claim], **kwargs)

    def addSources(self, claims, **kwargs):
        """
        Add the claims as one source.

        @param claims: the claims to add
        @type claims: list of pywikibot.Claim
        """
        data = self.repo.editSource(self, claims, new=True, **kwargs)
        source = collections.defaultdict(list)
        for claim in claims:
            claim.hash = data['reference']['hash']
            self.on_item.lastrevid = data['pageinfo']['lastrevid']
            source[claim.getID()].append(claim)
        self.sources.append(source)

    def removeSource(self, source, **kwargs):
        """
        Remove the source.  Calls removeSources().

        @param source: the source to remove
        @type source: pywikibot.Claim
        """
        self.removeSources([source], **kwargs)

    def removeSources(self, sources, **kwargs):
        """
        Remove the sources.

        @param sources: the sources to remove
        @type sources: list of pywikibot.Claim
        """
        self.repo.removeSources(self, sources, **kwargs)
        for source in sources:
            source_dict = collections.defaultdict(list)
            source_dict[source.getID()].append(source)
            self.sources.remove(source_dict)

    def addQualifier(self, qualifier, **kwargs):
        """Add the given qualifier.

        @param qualifier: the qualifier to add
        @type qualifier: Claim
        """
        data = self.repo.editQualifier(self, qualifier, **kwargs)
        qualifier.isQualifier = True
        self.on_item.lastrevid = data['pageinfo']['lastrevid']
        self.qualifiers[qualifier.getID()].append(qualifier)

    def _formatValue(self):
        """
        Format the target into the proper JSON value that Wikibase wants.

        @return: dict
        """
        if self.type == 'wikibase-item':
            value = {'entity-type': 'item',
                     'numeric-id': self.getTarget().getID(numeric=True)}
        elif self.type in ('string', 'url'):
            value = self.getTarget()
        elif self.type == 'commonsMedia':
            value = self.getTarget().title(withNamespace=False)
        elif self.type in ('globe-coordinate', 'time', 'quantity'):
            value = self.getTarget().toWikibase()
        else:
            raise NotImplementedError('%s datatype is not supported yet.'
                                      % self.type)
        return value

    def _formatDataValue(self):
        """
        Format the target into the proper JSON datavalue that Wikibase wants.
        """
        return {'value': self._formatValue(),
                'type': self.value_types.get(self.type, self.type)
                }


class Revision(object):

    """A structure holding information about a single revision of a Page."""

    def __init__(self, revid, timestamp, user, anon=False, comment=u"",
                 text=None, minor=False, rollbacktoken=None):
        """
        Constructor.

        All parameters correspond to object attributes (e.g., revid
        parameter is stored as self.revid)

        @param revid: Revision id number
        @type revid: int
        @param text: Revision wikitext.
        @type text: unicode, or None if text not yet retrieved
        @param timestamp: Revision time stamp
        @type timestamp: pywikibot.Timestamp
        @param user: user who edited this revision
        @type user: unicode
        @param anon: user is unregistered
        @type anon: bool
        @param comment: edit comment text
        @type comment: unicode
        @param minor: edit flagged as minor
        @type minor: bool

        """
        self.revid = revid
        self.text = text
        self.timestamp = timestamp
        self.user = user
        self.anon = anon
        self.comment = comment
        self.minor = minor
        self.rollbacktoken = rollbacktoken


class Link(ComparableMixin):

    """A MediaWiki link (local or interwiki).

    Has the following attributes:

      - site:  The Site object for the wiki linked to
      - namespace: The namespace of the page linked to (int)
      - title: The title of the page linked to (unicode); does not include
        namespace or section
      - section: The section of the page linked to (unicode or None); this
        contains any text following a '#' character in the title
      - anchor: The anchor text (unicode or None); this contains any text
        following a '|' character inside the link

    """

    illegal_titles_pattern = re.compile(
        # Matching titles will be held as illegal.
        r'''[\x00-\x1f\x23\x3c\x3e\x5b\x5d\x7b\x7c\x7d\x7f]'''
        # URL percent encoding sequences interfere with the ability
        # to round-trip titles -- you can't link to them consistently.
        u'|%[0-9A-Fa-f]{2}'
        # XML/HTML character references produce similar issues.
        u'|&[A-Za-z0-9\x80-\xff]+;'
        u'|&#[0-9]+;'
        u'|&#x[0-9A-Fa-f]+;'
    )

    def __init__(self, text, source=None, defaultNamespace=0):
        """Constructor.

        @param text: the link text (everything appearing between [[ and ]]
            on a wiki page)
        @type text: unicode
        @param source: the Site on which the link was found (not necessarily
            the site to which the link refers)
        @type source: Site
        @param defaultNamespace: a namespace to use if the link does not
            contain one (defaults to 0)
        @type defaultNamespace: int

        """
        assert source is None or isinstance(source, pywikibot.site.BaseSite), \
            "source parameter should be a Site object"

        self._text = text
        self._source = source or pywikibot.Site()
        self._defaultns = defaultNamespace

        # preprocess text (these changes aren't site-dependent)
        # First remove anchor, which is stored unchanged, if there is one
        if u"|" in self._text:
            self._text, self._anchor = self._text.split(u"|", 1)
        else:
            self._anchor = None

        # Clean up the name, it can come from anywhere.
        # Convert HTML entities to unicode
        t = html2unicode(self._text)

        # Convert URL-encoded characters to unicode
        t = url2unicode(t, site=self._source)

        # Normalize unicode string to a NFC (composed) format to allow
        # proper string comparisons. According to
        # https://svn.wikimedia.org/viewvc/mediawiki/branches/REL1_6/phase3/includes/normal/UtfNormal.php?view=markup
        # the MediaWiki code normalizes everything to NFC, not NFKC
        # (which might result in information loss).
        t = unicodedata.normalize('NFC', t)

        # This code was adapted from Title.php : secureAndSplit()
        #
        if u'\ufffd' in t:
            raise pywikibot.Error(
                "Title contains illegal char (\\uFFFD 'REPLACEMENT CHARACTER')")

        # Replace underscores by spaces
        t = t.replace(u"_", u" ")
        # replace multiple spaces with a single space
        while u"  " in t:
            t = t.replace(u"  ", u" ")
        # Strip spaces at both ends
        t = t.strip()
        # Remove left-to-right and right-to-left markers.
        t = t.replace(u"\u200e", u"").replace(u"\u200f", u"")
        self._text = t

    def __repr__(self):
        """Return a more complete string representation."""
        return "pywikibot.page.Link(%r, %r)" % (self.title, self.site)

    def parse_site(self):
        """Parse only enough text to determine which site the link points to.

        This method does not parse anything after the first ":"; links
        with multiple interwiki prefixes (such as "wikt:fr:Parlais") need
        to be re-parsed on the first linked wiki to get the actual site.

        @return: tuple of (family-name, language-code) for the linked site.

        """
        t = self._text
        fam = self._source.family
        code = self._source.code
        while u":" in t:
            # Initial colon
            if t.startswith(u":"):
                # remove the colon but continue processing
                # remove any subsequent whitespace
                t = t.lstrip(u":").lstrip(u" ")
                continue
            prefix = t[:t.index(u":")].lower()  # part of text before :
            ns = self._source.ns_index(prefix)
            if ns:
                # The prefix is a namespace in the source wiki
                return (fam.name, code)
            if prefix in fam.langs:
                # prefix is a language code within the source wiki family
                return (fam.name, prefix)
            known = fam.get_known_families(site=self._source)
            if prefix in known:
                if known[prefix] == fam.name:
                    # interwiki prefix links back to source family
                    t = t[t.index(u":") + 1:].lstrip(u" ")
                    # strip off the prefix and retry
                    continue
                # prefix is a different wiki family
                return (known[prefix], code)
            break
        return (fam.name, code)  # text before : doesn't match any known prefix

    def parse(self):
        """Parse wikitext of the link.

        Called internally when accessing attributes.
        """
        self._site = self._source
        self._namespace = self._defaultns
        t = self._text

        # This code was adapted from Title.php : secureAndSplit()
        #
        firstPass = True
        while u":" in t:
            # Initial colon indicates main namespace rather than default
            if t.startswith(u":"):
                self._namespace = 0
                # remove the colon but continue processing
                # remove any subsequent whitespace
                t = t.lstrip(u":").lstrip(u" ")
                continue

            fam = self._site.family
            prefix = t[:t.index(u":")].lower()
            ns = self._site.ns_index(prefix)
            if ns:
                # Ordinary namespace
                t = t[t.index(u":"):].lstrip(u":").lstrip(u" ")
                self._namespace = ns
                break
            if prefix in list(fam.langs.keys())\
                    or prefix in fam.get_known_families(site=self._site):
                # looks like an interwiki link
                if not firstPass:
                    # Can't make a local interwiki link to an interwiki link.
                    raise pywikibot.Error(
                        "Improperly formatted interwiki link '%s'"
                        % self._text)
                t = t[t.index(u":"):].lstrip(u":").lstrip(u" ")
                if prefix in list(fam.langs.keys()):
                    newsite = pywikibot.Site(prefix, fam)
                else:
                    otherlang = self._site.code
                    familyName = fam.get_known_families(site=self._site)[prefix]
                    if familyName in ['commons', 'meta']:
                        otherlang = familyName
                    try:
                        newsite = pywikibot.Site(otherlang, familyName)
                    except ValueError:
                        raise pywikibot.Error(
                            """\
%s is not a local page on %s, and the %s family is
not supported by PyWikiBot!"""
                            % (self._text, self._site, familyName))

                # Redundant interwiki prefix to the local wiki
                if newsite == self._site:
                    if not t:
                        # Can't have an empty self-link
                        raise pywikibot.InvalidTitle(
                            "Invalid link title: '%s'" % self._text)
                    firstPass = False
                    continue
                self._site = newsite
            else:
                break   # text before : doesn't match any known prefix

        if u"#" in t:
            t, sec = t.split(u'#', 1)
            t, self._section = t.rstrip(), sec.lstrip()
        else:
            self._section = None

        # Reject illegal characters.
        m = Link.illegal_titles_pattern.search(t)
        if m:
            raise pywikibot.InvalidTitle(
                u"%s contains illegal char(s) %s" % (repr(t), repr(m.group(0))))

        # Pages with "/./" or "/../" appearing in the URLs will
        # often be unreachable due to the way web browsers deal
        # * with 'relative' URLs. Forbid them explicitly.

        if u'.' in t and (
                t == u'.' or t == u'..'
                or t.startswith(u"./")
                or t.startswith(u"../")
                or u"/./" in t
                or u"/../" in t
                or t.endswith(u"/.")
                or t.endswith(u"/..")
        ):
            raise pywikibot.InvalidTitle(
                "(contains . / combinations): '%s'"
                % self._text)

        # Magic tilde sequences? Nu-uh!
        if u"~~~" in t:
            raise pywikibot.InvalidTitle("(contains ~~~): '%s'" % self._text)

        if self._namespace != -1 and len(t) > 255:
            raise pywikibot.InvalidTitle("(over 255 bytes): '%s'" % t)

        if self._site.case() == 'first-letter':
            t = t[:1].upper() + t[1:]

        # Can't make a link to a namespace alone...
        # "empty" local links can only be self-links
        # with a fragment identifier.
        if not t and self._site == self._source and self._namespace != 0:
            raise pywikibot.Error("Invalid link (no page title): '%s'"
                                  % self._text)

        self._title = t

    # define attributes, to be evaluated lazily

    @property
    def site(self):
        """Return the site of the link.

        @return: unicode
        """
        if not hasattr(self, "_site"):
            self.parse()
        return self._site

    @property
    def namespace(self):
        """Return the namespace of the link.

        @return: unicode
        """
        if not hasattr(self, "_namespace"):
            self.parse()
        return self._namespace

    @property
    def title(self):
        """Return the title of the link.

        @return: unicode
        """
        if not hasattr(self, "_title"):
            self.parse()
        return self._title

    @property
    def section(self):
        """Return the section of the link.

        @return: unicode
        """
        if not hasattr(self, "_section"):
            self.parse()
        return self._section

    @property
    def anchor(self):
        """Return the anchor of the link.

        @return: unicode
        """
        if not hasattr(self, "_anchor"):
            self.parse()
        return self._anchor

    def canonical_title(self):
        """Return full page title, including localized namespace."""
        if self.namespace:
            return "%s:%s" % (self.site.namespace(self.namespace),
                              self.title)
        else:
            return self.title

    def astext(self, onsite=None):
        """Return a text representation of the link.

        @param onsite: if specified, present as a (possibly interwiki) link
            from the given site; otherwise, present as an internal link on
            the source site.

        """
        if onsite is None:
            onsite = self._source
        title = self.title
        if self.namespace:
            title = onsite.namespace(self.namespace) + ":" + title
        if self.section:
            title = title + "#" + self.section
        if onsite == self.site:
            return u'[[%s]]' % title
        if onsite.family == self.site.family:
            return u'[[%s:%s]]' % (self.site.code, title)
        if self.site.family.name == self.site.code:
            # use this form for sites like commons, where the
            # code is the same as the family name
            return u'[[%s:%s]]' % (self.site.code,
                                   title)
        return u'[[%s:%s:%s]]' % (self.site.family.name,
                                  self.site.code,
                                  title)

    def __str__(self):
        """Return a string representation."""
        return self.astext().encode("ascii", "backslashreplace")

    def _cmpkey(self):
        """
        Key for comparison of Link objects.

        Link objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        Link objects are sortable by site, then namespace, then title.
        """
        return (self.site, self.namespace, self.title)

    def __unicode__(self):
        """Return a unicode string representation.

        @return unicode
        """
        return self.astext()

    def __hash__(self):
        """A stable identifier to be used as a key in hash-tables."""
        return hash(u'%s:%s:%s' % (self.site.family.name,
                                   self.site.code,
                                   self.title))

    @staticmethod
    def fromPage(page, source=None):
        """
        Create a Link to a Page.

        @param page: target Page
        @type page: Page
        @param source: Link from site source
        @param source: Site

        @return: Link
        """
        link = Link.__new__(Link)
        link._site = page.site
        link._section = page.section()
        link._namespace = page.namespace()
        link._title = page.title(withNamespace=False,
                                 allowInterwiki=False,
                                 withSection=False)
        link._anchor = None
        link._source = source or pywikibot.Site()

        return link

    @staticmethod
    def langlinkUnsafe(lang, title, source):
        """
        Create a "lang:title" Link linked from source.

        Assumes that the lang & title come clean, no checks are made.

        @param lang: target site code (language)
        @type lang: str
        @param title: target Page
        @type title: unicode
        @param source: Link from site source
        @param source: Site

        @return: Link
        """
        link = Link.__new__(Link)
        if source.family.interwiki_forward:
            link._site = pywikibot.Site(lang, source.family.interwiki_forward)
        else:
            link._site = pywikibot.Site(lang, source.family.name)
        link._section = None
        link._source = source

        link._namespace = 0

        if ':' in title:
            ns, t = title.split(':', 1)
            ns = link._site.ns_index(ns.lower())
            if ns:
                link._namespace = ns
                title = t
        if u"#" in title:
            t, sec = title.split(u'#', 1)
            title, link._section = t.rstrip(), sec.lstrip()
        else:
            link._section = None
        link._title = title
        return link


# Utility functions for parsing page titles


def html2unicode(text, ignore=None):
    """Replace HTML entities with equivalent unicode.

    @param ignore: HTML entities to ignore
    @param ignore: list of int

    @return: unicode
    """
    if ignore is None:
        ignore = []
    # This regular expression will match any decimal and hexadecimal entity and
    # also entities that might be named entities.
    entityR = re.compile(
        r'&(?:amp;)?(#(?P<decimal>\d+)|#x(?P<hex>[0-9a-fA-F]+)|(?P<name>[A-Za-z]+));')
    # These characters are Html-illegal, but sadly you *can* find some of
    # these and converting them to unichr(decimal) is unsuitable
    convertIllegalHtmlEntities = {
        128: 8364,  # €
        130: 8218,  # ‚
        131: 402,   # ƒ
        132: 8222,  # „
        133: 8230,  # …
        134: 8224,  # †
        135: 8225,  # ‡
        136: 710,   # ˆ
        137: 8240,  # ‰
        138: 352,   # Š
        139: 8249,  # ‹
        140: 338,   # Œ
        142: 381,   # Ž
        145: 8216,  # ‘
        146: 8217,  # ’
        147: 8220,  # “
        148: 8221,  # ”
        149: 8226,  # •
        150: 8211,  # –
        151: 8212,  # —
        152: 732,   # ˜
        153: 8482,  # ™
        154: 353,   # š
        155: 8250,  # ›
        156: 339,   # œ
        158: 382,   # ž
        159: 376    # Ÿ
    }
    # ensuring that illegal &#129; &#141; and &#157, which have no known values,
    # don't get converted to unichr(129), unichr(141) or unichr(157)
    ignore = set(ignore) | set([129, 141, 157])
    result = u''
    i = 0
    found = True
    while found:
        text = text[i:]
        match = entityR.search(text)
        if match:
            unicodeCodepoint = None
            if match.group('decimal'):
                unicodeCodepoint = int(match.group('decimal'))
            elif match.group('hex'):
                unicodeCodepoint = int(match.group('hex'), 16)
            elif match.group('name'):
                name = match.group('name')
                if name in htmlentitydefs.name2codepoint:
                    # We found a known HTML entity.
                    unicodeCodepoint = htmlentitydefs.name2codepoint[name]
            result += text[:match.start()]
            try:
                unicodeCodepoint = convertIllegalHtmlEntities[unicodeCodepoint]
            except KeyError:
                pass
            if unicodeCodepoint and unicodeCodepoint not in ignore:
                # solve narrow Python build exception (UTF-16)
                if unicodeCodepoint > sys.maxunicode:
                    unicode_literal = lambda n: eval("u'\U%08x'" % n)
                    result += unicode_literal(unicodeCodepoint)
                else:
                    result += unichr(unicodeCodepoint)
            else:
                # Leave the entity unchanged
                result += text[match.start():match.end()]
            i = match.end()
        else:
            result += text
            found = False
    return result


def UnicodeToAsciiHtml(s):
    """Convert unicode to a str using HTML entities."""
    html = []
    for c in s:
        cord = ord(c)
        if 31 < cord < 128:
            html.append(c)
        else:
            html.append('&#%d;' % cord)
    return ''.join(html)


def unicode2html(x, encoding):
    """
    Convert unicode string to requested HTML encoding.

    Attempt to encode the
    string into the desired format; if that doesn't work, encode the unicode
    into HTML &#; entities. If it does work, return it unchanged.

    @param x: String to update
    @type x: unicode
    @param encoding: Encoding to use
    @type encoding: str

    @return: str
    """
    try:
        x.encode(encoding)
    except UnicodeError:
        x = UnicodeToAsciiHtml(x)
    return x


def url2unicode(title, site, site2=None):
    """Convert URL-encoded text to unicode using site's encoding.

    If site2 is provided, try its encodings as well.  Uses the first encoding
    that doesn't cause an error.

    """
    # create a list of all possible encodings for both hint sites
    encList = [site.encoding()] + list(site.encodings())
    if site2 and site2 != site:
        encList.append(site2.encoding())
        encList += list(site2.encodings())
    firstException = None
    # try to handle all encodings (will probably retry utf-8)
    for enc in encList:
        try:
            t = title.encode(enc)
            t = unquote_to_bytes(t)
            return unicode(t, enc)
        except UnicodeError as ex:
            if not firstException:
                firstException = ex
            pass
    # Couldn't convert, raise the original exception
    raise firstException
