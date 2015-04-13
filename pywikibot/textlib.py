# -*- coding: utf-8  -*-
"""
Functions for manipulating wiki-text.

Unless otherwise noted, all functions take a unicode string as the argument
and return a unicode string.

"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: 92d62d555d6904daff58d07def09406cf2882fcb $'
#

try:
    import mwparserfromhell
except ImportError:
    mwparserfromhell = False
import pywikibot
import datetime
import re
import sys
if sys.version_info[0] == 2:
    from HTMLParser import HTMLParser
else:
    from html.parser import HTMLParser

from . import config2 as config

TEMP_REGEX = re.compile(
    '{{(?:msg:)?(?P<name>[^{\|]+?)(?:\|(?P<params>[^{]+?(?:{[^{]+?}[^{]*?)?))?}}')


def unescape(s):
    """Replace escaped HTML-special characters by their originals"""
    if '&' not in s:
        return s
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&")  # Must be last
    return s


def replaceExcept(text, old, new, exceptions, caseInsensitive=False,
                  allowoverlap=False, marker='', site=None):
    """
    Return text with 'old' replaced by 'new', ignoring specified types of text.

    Skips occurrences of 'old' within exceptions; e.g., within nowiki tags or
    HTML comments. If caseInsensitive is true, then use case insensitive
    regex matching. If allowoverlap is true, overlapping occurrences are all
    replaced (watch out when using this, it might lead to infinite loops!).

    Parameters:
        text            - a unicode string
        old             - a compiled or uncompiled regular expression
        new             - a unicode string (which can contain regular
                          expression references), or a function which takes
                          a match object as parameter. See parameter repl of
                          re.sub().
        exceptions      - a list of strings which signal what to leave out,
                          e.g. ['math', 'table', 'template']
        caseInsensitive - a boolean
        marker          - a string that will be added to the last replacement;
                          if nothing is changed, it is added at the end

    """
    if site is None:
        site = pywikibot.Site()

    exceptionRegexes = {
        'comment':      re.compile(r'(?s)<!--.*?-->'),
        # section headers
        'header':       re.compile(r'\r?\n=+.+=+ *\r?\n'),
        # preformatted text
        'pre':          re.compile(r'(?ism)<pre>.*?</pre>'),
        'source':       re.compile(r'(?is)<source .*?</source>'),
        # inline references
        'ref':          re.compile(r'(?ism)<ref[ >].*?</ref>'),
        # lines that start with a space are shown in a monospace font and
        # have whitespace preserved.
        'startspace':   re.compile(r'(?m)^ (.*?)$'),
        # tables often have whitespace that is used to improve wiki
        # source code readability.
        # TODO: handle nested tables.
        'table':        re.compile(r'(?ims)^{\|.*?^\|}|<table>.*?</table>'),
        'hyperlink':    compileLinkR(),
        'gallery':      re.compile(r'(?is)<gallery.*?>.*?</gallery>'),
        # this matches internal wikilinks, but also interwiki, categories, and
        # images.
        'link':         re.compile(r'\[\[[^\]\|]*(\|[^\]]*)?\]\]'),
        # also finds links to foreign sites with preleading ":"
        'interwiki':    re.compile(r'(?i)\[\[:?(%s)\s?:[^\]]*\]\][\s]*'
                                   % '|'.join(site.validLanguageLinks() +
                                              list(site.family.obsolete.keys()))),
        # Wikibase property inclusions
        'property':     re.compile(r'(?i)\{\{\s*#property:\s*p\d+\s*\}\}'),
        # Module invocations (currently only Lua)
        'invoke':       re.compile(r'(?i)\{\{\s*#invoke:.*?}\}'),
        # categories
        'category':     re.compile(u'\[\[ *(?:%s)\s*:.*?\]\]' % u'|'.join(site.namespace(14, all=True))),
        # files
        'file':         re.compile(u'\[\[ *(?:%s)\s*:.*?\]\]' % u'|'.join(site.namespace(6, all=True))),

    }

    # if we got a string, compile it as a regular expression
    if isinstance(old, basestring):
        if caseInsensitive:
            old = re.compile(old, re.IGNORECASE | re.UNICODE)
        else:
            old = re.compile(old)

    dontTouchRegexes = []
    except_templates = False
    for exc in exceptions:
        if isinstance(exc, basestring):
            # assume it's a reference to the exceptionRegexes dictionary
            # defined above.
            if exc in exceptionRegexes:
                dontTouchRegexes.append(exceptionRegexes[exc])
            elif exc == 'template':
                except_templates = True
            else:
                # nowiki, noinclude, includeonly, timeline, math ond other
                # extensions
                dontTouchRegexes.append(re.compile(r'(?is)<%s>.*?</%s>'
                                                   % (exc, exc)))
            # handle alias
            if exc == 'source':
                dontTouchRegexes.append(re.compile(
                    r'(?is)<syntaxhighlight .*?</syntaxhighlight>'))
        else:
            # assume it's a regular expression
            dontTouchRegexes.append(exc)

    # mark templates
    # don't care about mw variables and parser functions
    if except_templates:
        marker1 = findmarker(text)
        marker2 = findmarker(text, u'##', u'#')
        Rvalue = re.compile('{{{.+?}}}')
        Rmarker1 = re.compile('%(mark)s(\d+)%(mark)s' % {'mark': marker1})
        Rmarker2 = re.compile('%(mark)s(\d+)%(mark)s' % {'mark': marker2})
        # hide the flat template marker
        dontTouchRegexes.append(Rmarker1)
        origin = text
        values = {}
        count = 0
        for m in Rvalue.finditer(text):
            count += 1
            # If we have digits between brackets, restoring from dict may fail.
            # So we need to change the index. We have to search in the origin.
            while u'}}}%d{{{' % count in origin:
                count += 1
            item = m.group()
            text = text.replace(item, '%s%d%s' % (marker2, count, marker2))
            values[count] = item
        inside = {}
        seen = set()
        count = 0
        while TEMP_REGEX.search(text) is not None:
            for m in TEMP_REGEX.finditer(text):
                item = m.group()
                if item in seen:
                    continue  # speed up
                seen.add(item)
                count += 1
                while u'}}%d{{' % count in origin:
                    count += 1
                text = text.replace(item, '%s%d%s' % (marker1, count, marker1))

                # Make sure stored templates don't contain markers
                for m2 in Rmarker1.finditer(item):
                    item = item.replace(m2.group(), inside[int(m2.group(1))])
                for m2 in Rmarker2.finditer(item):
                    item = item.replace(m2.group(), values[int(m2.group(1))])
                inside[count] = item
    index = 0
    markerpos = len(text)
    while True:
        match = old.search(text, index)
        if not match:
            # nothing left to replace
            break

        # check which exception will occur next.
        nextExceptionMatch = None
        for dontTouchR in dontTouchRegexes:
            excMatch = dontTouchR.search(text, index)
            if excMatch and (
                    nextExceptionMatch is None or
                    excMatch.start() < nextExceptionMatch.start()):
                nextExceptionMatch = excMatch

        if nextExceptionMatch is not None \
                and nextExceptionMatch.start() <= match.start():
            # an HTML comment or text in nowiki tags stands before the next
            # valid match. Skip.
            index = nextExceptionMatch.end()
        else:
            # We found a valid match. Replace it.
            if callable(new):
                # the parameter new can be a function which takes the match
                # as a parameter.
                replacement = new(match)
            else:
                # it is not a function, but a string.

                # it is a little hack to make \n work. It would be better
                # to fix it previously, but better than nothing.
                new = new.replace('\\n', '\n')

                # We cannot just insert the new string, as it may contain regex
                # group references such as \2 or \g<name>.
                # On the other hand, this approach does not work because it
                # can't handle lookahead or lookbehind (see bug #1731008):
                #
                #  replacement = old.sub(new, text[match.start():match.end()])
                #  text = text[:match.start()] + replacement + text[match.end():]

                # So we have to process the group references manually.
                replacement = new

                groupR = re.compile(r'\\(?P<number>\d+)|\\g<(?P<name>.+?)>')
                while True:
                    groupMatch = groupR.search(replacement)
                    if not groupMatch:
                        break
                    groupID = (groupMatch.group('name') or
                               int(groupMatch.group('number')))
                    try:
                        replacement = (replacement[:groupMatch.start()] +
                                       ('' if match.group(groupID) is None else match.group(groupID)) + \
                                       replacement[groupMatch.end():])
                    except IndexError:
                        pywikibot.output('\nInvalid group reference: %s' % groupID)
                        pywikibot.output('Groups found:\n%s' % match.groups())
                        raise IndexError
            text = text[:match.start()] + replacement + text[match.end():]

            # continue the search on the remaining text
            if allowoverlap:
                index = match.start() + 1
            else:
                index = match.start() + len(replacement)
            markerpos = match.start() + len(replacement)
    text = text[:markerpos] + marker + text[markerpos:]

    if except_templates:  # restore templates from dict
        for m2 in Rmarker1.finditer(text):
            text = text.replace(m2.group(), inside[int(m2.group(1))])
        for m2 in Rmarker2.finditer(text):
            text = text.replace(m2.group(), values[int(m2.group(1))])
    return text


def removeDisabledParts(text, tags=['*']):
    """
    Return text without portions where wiki markup is disabled

    Parts that can/will be removed are --
    * HTML comments
    * nowiki tags
    * pre tags
    * includeonly tags

    The exact set of parts which should be removed can be passed as the
    'parts' parameter, which defaults to all.

    """
    regexes = {
        'comments':        r'<!--.*?-->',
        'includeonly':     r'<includeonly>.*?</includeonly>',
        'nowiki':          r'<nowiki>.*?</nowiki>',
        'pre':             r'<pre>.*?</pre>',
        'source':          r'<source .*?</source>',
        'syntaxhighlight': r'<syntaxhighlight .*?</syntaxhighlight>',
    }
    if '*' in tags:
        tags = list(regexes.keys())
    # add alias
    tags = set(tags)
    if 'source' in tags:
        tags.add('syntaxhighlight')
    toRemoveR = re.compile('|'.join([regexes[tag] for tag in tags]),
                           re.IGNORECASE | re.DOTALL)
    return toRemoveR.sub('', text)


def removeHTMLParts(text, keeptags=['tt', 'nowiki', 'small', 'sup']):
    """
    Return text without portions where HTML markup is disabled

    Parts that can/will be removed are --
    * HTML and all wiki tags

    The exact set of parts which should NOT be removed can be passed as the
    'keeptags' parameter, which defaults to ['tt', 'nowiki', 'small', 'sup'].

    """
    # try to merge with 'removeDisabledParts()' above into one generic function
    # thanks to https://www.hellboundhackers.org/articles/read-article.php?article_id=841
    parser = _GetDataHTML()
    parser.keeptags = keeptags
    parser.feed(text)
    parser.close()
    return parser.textdata


# thanks to https://docs.python.org/2/library/htmlparser.html
class _GetDataHTML(HTMLParser):
    textdata = u''
    keeptags = []

    def handle_data(self, data):
        self.textdata += data

    def handle_starttag(self, tag, attrs):
        if tag in self.keeptags:
            self.textdata += u"<%s>" % tag

    def handle_endtag(self, tag):
        if tag in self.keeptags:
            self.textdata += u"</%s>" % tag


def isDisabled(text, index, tags=['*']):
    """
    Return True if text[index] is disabled, e.g. by a comment or by nowiki tags.
    For the tags parameter, see removeDisabledParts() above.

    """
    # Find a marker that is not already in the text.
    marker = findmarker(text)
    text = text[:index] + marker + text[index:]
    text = removeDisabledParts(text, tags)
    return (marker not in text)


def findmarker(text, startwith=u'@@', append=None):
    # find a string which is not part of text
    if not append:
        append = u'@'
    mymarker = startwith
    while mymarker in text:
        mymarker += append
    return mymarker


def expandmarker(text, marker='', separator=''):
    # set to remove any number of separator occurrences plus arbitrary
    # whitespace before, after, and between them,
    # by allowing to include them into marker.
    if separator:
        firstinmarker = text.find(marker)
        firstinseparator = firstinmarker
        lenseparator = len(separator)
        striploopcontinue = True
        while firstinseparator > 0 and striploopcontinue:
            striploopcontinue = False
            if (firstinseparator >= lenseparator) and \
               (separator == text[firstinseparator -
                                  lenseparator:firstinseparator]):
                firstinseparator -= lenseparator
                striploopcontinue = True
            elif text[firstinseparator - 1] < ' ':
                firstinseparator -= 1
                striploopcontinue = True
        marker = text[firstinseparator:firstinmarker] + marker
    return marker


# -----------------------------------------------
# Functions dealing with interwiki language links
# -----------------------------------------------
# Note - MediaWiki supports several kinds of interwiki links; two kinds are
#        inter-language links. We deal here with those kinds only.
#        A family has by definition only one kind of inter-language links:
#        1 - inter-language links inside the own family.
#            They go to a corresponding page in another language in the same
#            family, such as from 'en.wikipedia' to 'pt.wikipedia', or from
#            'es.wiktionary' to 'arz.wiktionary'.
#            Families with this kind have several language-specific sites.
#            They have their interwiki_forward attribute set to None
#        2 - language links forwarding to another family.
#            They go to a corresponding page in another family, such as from
#            'commons' to 'zh.wikipedia, or from 'incubator' to 'en.wikipedia'.
#            Families having those have one member only, and do not have
#            language-specific sites. The name of the target family of their
#            inter-language links is kept in their interwiki_forward attribute.
#        These functions only deal with links of these two kinds only.  They
#        do not find or change links of other kinds, nor any that are formatted
#        as in-line interwiki links (e.g., "[[:es:Articulo]]".

def getLanguageLinks(text, insite=None, pageLink="[[]]",
                     template_subpage=False):
    """
    Return a dict of inter-language links found in text.

    The returned dict uses language codes as keys and Page objects as values.

    Do not call this routine directly, use Page.interwiki() method
    instead.

    """
    if insite is None:
        insite = pywikibot.Site()
    fam = insite.family
    # when interwiki links forward to another family, retrieve pages & other
    # infos there
    if fam.interwiki_forward:
        fam = pywikibot.site.Family(fam.interwiki_forward)
    result = {}
    # Ignore interwiki links within nowiki tags, includeonly tags, pre tags,
    # and HTML comments
    tags = ['comments', 'nowiki', 'pre', 'source']
    if not template_subpage:
        tags += ['includeonly']
    text = removeDisabledParts(text, tags)

    # This regular expression will find every link that is possibly an
    # interwiki link.
    # NOTE: language codes are case-insensitive and only consist of basic latin
    # letters and hyphens.
    # TODO: currently, we do not have any, but BCP 47 allows digits, and
    #       underscores.
    # TODO: There is no semantic difference between hyphens and
    #       underscores -> fold them.
    interwikiR = re.compile(r'\[\[([a-zA-Z\-]+)\s?:([^\[\]\n]*)\]\]')
    for lang, pagetitle in interwikiR.findall(text):
        lang = lang.lower()
        # Check if it really is in fact an interwiki link to a known
        # language, or if it's e.g. a category tag or an internal link
        if lang in fam.obsolete:
            lang = fam.obsolete[lang]
        if lang in list(fam.langs.keys()):
            if '|' in pagetitle:
                # ignore text after the pipe
                pagetitle = pagetitle[:pagetitle.index('|')]
            # we want the actual page objects rather than the titles
            site = pywikibot.Site(code=lang, fam=fam)
            try:
                result[site] = pywikibot.Page(site, pagetitle, insite=insite)
            except pywikibot.InvalidTitle:
                pywikibot.output(u'[getLanguageLinks] Text contains invalid '
                                 u'interwiki link [[%s:%s]].'
                                 % (lang, pagetitle))
                continue
    return result


def removeLanguageLinks(text, site=None, marker=''):
    """Return text with all inter-language links removed.

    If a link to an unknown language is encountered, a warning is printed.
    If a marker is defined, that string is placed at the location of the
    last occurrence of an interwiki link (at the end if there are no
    interwiki links).

    """
    if site is None:
        site = pywikibot.Site()
    if not site.validLanguageLinks():
        return text
    # This regular expression will find every interwiki link, plus trailing
    # whitespace.
    languages = '|'.join(site.validLanguageLinks() +
                         list(site.family.obsolete.keys()))
    interwikiR = re.compile(r'\[\[(%s)\s?:[^\[\]\n]*\]\][\s]*'
                            % languages, re.IGNORECASE)
    text = replaceExcept(text, interwikiR, '',
                         ['nowiki', 'comment', 'math', 'pre', 'source'],
                         marker=marker)
    return text.strip()


def removeLanguageLinksAndSeparator(text, site=None, marker='', separator=''):
    """
    Return text with all inter-language links, plus any preceding whitespace
    and separator occurrences removed.

    If a link to an unknown language is encountered, a warning is printed.
    If a marker is defined, that string is placed at the location of the
    last occurrence of an interwiki link (at the end if there are no
    interwiki links).

    """
    if separator:
        mymarker = findmarker(text, u'@L@')
        newtext = removeLanguageLinks(text, site, mymarker)
        mymarker = expandmarker(newtext, mymarker, separator)
        return newtext.replace(mymarker, marker)
    else:
        return removeLanguageLinks(text, site, marker)


def replaceLanguageLinks(oldtext, new, site=None, addOnly=False,
                         template=False, template_subpage=False):
    """Replace inter-language links in the text with a new set of links.

    'new' should be a dict with the Site objects as keys, and Page or Link
    objects as values (i.e., just like the dict returned by getLanguageLinks
    function).

    """
    # Find a marker that is not already in the text.
    marker = findmarker(oldtext)
    if site is None:
        site = pywikibot.Site()
    separator = site.family.interwiki_text_separator
    cseparator = site.family.category_text_separator
    separatorstripped = separator.strip()
    cseparatorstripped = cseparator.strip()
    if addOnly:
        s2 = oldtext
    else:
        s2 = removeLanguageLinksAndSeparator(oldtext, site=site, marker=marker,
                                             separator=separatorstripped)
    s = interwikiFormat(new, insite=site)
    if s:
        if site.language() in site.family.interwiki_attop or \
           u'<!-- interwiki at top -->' in oldtext:
            # do not add separator if interwiki links are on one line
            newtext = s + (u'' if site.language()
                           in site.family.interwiki_on_one_line
                           else separator) + s2.replace(marker, '').strip()
        else:
            # calculate what was after the language links on the page
            firstafter = s2.find(marker)
            if firstafter < 0:
                firstafter = len(s2)
            else:
                firstafter += len(marker)
            # Any text in 'after' part that means we should keep it after?
            if "</noinclude>" in s2[firstafter:]:
                if separatorstripped:
                    s = separator + s
                newtext = (s2[:firstafter].replace(marker, '') +
                           s +
                           s2[firstafter:])
            elif site.language() in site.family.categories_last:
                cats = getCategoryLinks(s2, site=site)
                s2 = removeCategoryLinksAndSeparator(
                    s2.replace(marker, cseparatorstripped).strip(), site) + \
                    separator + s
                newtext = replaceCategoryLinks(s2, cats, site=site,
                                               addOnly=True)
            # for Wikitravel's language links position.
            # (not supported by rewrite - no API)
            elif site.family.name == 'wikitravel':
                s = separator + s + separator
                newtext = (s2[:firstafter].replace(marker, '') +
                           s +
                           s2[firstafter:])
            else:
                if template or template_subpage:
                    if template_subpage:
                        includeOn = '<includeonly>'
                        includeOff = '</includeonly>'
                    else:
                        includeOn = '<noinclude>'
                        includeOff = '</noinclude>'
                        separator = ''
                    # Do we have a noinclude at the end of the template?
                    parts = s2.split(includeOff)
                    lastpart = parts[-1]
                    if re.match('\s*%s' % marker, lastpart):
                        # Put the langlinks back into the noinclude's
                        regexp = re.compile('%s\s*%s' % (includeOff, marker))
                        newtext = regexp.sub(s + includeOff, s2)
                    else:
                        # Put the langlinks at the end, inside noinclude's
                        newtext = (s2.replace(marker, '').strip() +
                                   separator +
                                   u'%s\n%s%s\n' % (includeOn, s, includeOff)
                                   )
                else:
                    newtext = s2.replace(marker, '').strip() + separator + s
    else:
        newtext = s2.replace(marker, '')
    return newtext


def interwikiFormat(links, insite=None):
    """Convert interwiki link dict into a wikitext string.

    'links' should be a dict with the Site objects as keys, and Page
    or Link objects as values.

    Return a unicode string that is formatted for inclusion in insite
    (defaulting to the current site).

    """
    if insite is None:
        insite = pywikibot.Site()
    if not links:
        return ''

    ar = interwikiSort(list(links.keys()), insite)
    s = []
    for site in ar:
        try:
            title = links[site].title(asLink=True, forceInterwiki=True,
                                      insite=insite)
            link = title.replace('[[:', '[[')
            s.append(link)
        except AttributeError:
            s.append(pywikibot.Site(code=site).linkto(links[site], othersite=insite))
    if insite.lang in insite.family.interwiki_on_one_line:
        sep = u' '
    else:
        sep = config.line_separator
    s = sep.join(s) + config.line_separator
    return s


# Sort sites according to local interwiki sort logic
def interwikiSort(sites, insite=None):
    if not sites:
        return []
    if insite is None:
        insite = pywikibot.Site()

    sites.sort()
    putfirst = insite.interwiki_putfirst()
    if putfirst:
        # In this case I might have to change the order
        firstsites = []
        for code in putfirst:
            if code in insite.validLanguageLinks():
                site = insite.getSite(code=code)
                if site in sites:
                    del sites[sites.index(site)]
                    firstsites = firstsites + [site]
        sites = firstsites + sites
    if insite.interwiki_putfirst_doubled(sites):
        # some (all?) implementations return False
        sites = insite.interwiki_putfirst_doubled(sites) + sites
    return sites


# -------------------------------------
# Functions dealing with category links
# -------------------------------------

def getCategoryLinks(text, site=None):
    """Return a list of category links found in text.

    @return: all category links found
    @returntype: list of Category objects

    """
    result = []
    if site is None:
        site = pywikibot.Site()
    # Ignore category links within nowiki tags, pre tags, includeonly tags,
    # and HTML comments
    text = removeDisabledParts(text)
    catNamespace = '|'.join(site.category_namespaces())
    R = re.compile(r'\[\[\s*(?P<namespace>%s)\s*:\s*(?P<catName>.+?)'
                   r'(?:\|(?P<sortKey>.*?))?\]\]'
                   % catNamespace, re.I)
    for match in R.finditer(text):
        cat = pywikibot.Category(pywikibot.Link(
                                 '%s:%s' % (match.group('namespace'),
                                            match.group('catName')),
                                 site),
                                 sortKey=match.group('sortKey'))
        result.append(cat)
    return result


def removeCategoryLinks(text, site=None, marker=''):
    """Return text with all category links removed.

    Put the string marker after the last replacement (at the end of the text
    if there is no replacement).

    """
    # This regular expression will find every link that is possibly an
    # interwiki link, plus trailing whitespace. The language code is grouped.
    # NOTE: This assumes that language codes only consist of non-capital
    # ASCII letters and hyphens.
    if site is None:
        site = pywikibot.Site()
    catNamespace = '|'.join(site.category_namespaces())
    categoryR = re.compile(r'\[\[\s*(%s)\s*:.*?\]\]\s*' % catNamespace, re.I)
    text = replaceExcept(text, categoryR, '',
                         ['nowiki', 'comment', 'math', 'pre', 'source'],
                         marker=marker)
    if marker:
        # avoid having multiple linefeeds at the end of the text
        text = re.sub('\s*%s' % re.escape(marker), config.LS + marker,
                      text.strip())
    return text.strip()


def removeCategoryLinksAndSeparator(text, site=None, marker='', separator=''):
    """
    Return text with all category links, plus any preceding whitespace
    and separator occurrences removed.

    Put the string marker after the last replacement (at the end of the text
    if there is no replacement).

    """
    if site is None:
        site = pywikibot.Site()
    if separator:
        mymarker = findmarker(text, u'@C@')
        newtext = removeCategoryLinks(text, site, mymarker)
        mymarker = expandmarker(newtext, mymarker, separator)
        return newtext.replace(mymarker, marker)
    else:
        return removeCategoryLinks(text, site, marker)


def replaceCategoryInPlace(oldtext, oldcat, newcat, site=None):
    """Replace the category oldcat with the category newcat and return
       the modified text.

    """
    if site is None:
        site = pywikibot.Site()

    catNamespace = '|'.join(site.category_namespaces())
    title = oldcat.title(withNamespace=False)
    if not title:
        return
    # title might contain regex special characters
    title = re.escape(title)
    # title might not be capitalized correctly on the wiki
    if title[0].isalpha() and not site.nocapitalize:
        title = "[%s%s]" % (title[0].upper(), title[0].lower()) + title[1:]
    # spaces and underscores in page titles are interchangeable and collapsible
    title = title.replace(r"\ ", "[ _]+").replace(r"\_", "[ _]+")
    categoryR = re.compile(r'\[\[\s*(%s)\s*:\s*%s\s*((?:\|[^]]+)?\]\])'
                           % (catNamespace, title), re.I)
    categoryRN = re.compile(
        r'^[^\S\n]*\[\[\s*(%s)\s*:\s*%s\s*((?:\|[^]]+)?\]\])[^\S\n]*\n'
        % (catNamespace, title), re.I | re.M)
    if newcat is None:
        """ First go through and try the more restrictive regex that removes
        an entire line, if the category is the only thing on that line (this
        prevents blank lines left over in category lists following a removal.)
        """

        text = replaceExcept(oldtext, categoryRN, '',
                             ['nowiki', 'comment', 'math', 'pre', 'source'])
        text = replaceExcept(text, categoryR, '',
                             ['nowiki', 'comment', 'math', 'pre', 'source'])
    else:
        text = replaceExcept(oldtext, categoryR,
                             '[[%s:%s\\2' % (site.namespace(14),
                                             newcat.title(withNamespace=False)),
                             ['nowiki', 'comment', 'math', 'pre', 'source'])
    return text


def replaceCategoryLinks(oldtext, new, site=None, addOnly=False):
    """
    Replace the category links given in the wikitext given
    in oldtext by the new links given in new.

    'new' should be a list of Category objects or strings
          which can be either the raw name or [[Category:..]].

    If addOnly is True, the old category won't be deleted and the
    category(s) given will be added (and so they won't replace anything).

    """
    # Find a marker that is not already in the text.
    marker = findmarker(oldtext)
    if site is None:
        site = pywikibot.Site()
    if site.sitename() == 'wikipedia:de' and "{{Personendaten" in oldtext:
        raise pywikibot.Error("""\
The Pywikibot is no longer allowed to touch categories on the German
Wikipedia on pages that contain the Personendaten template because of the
non-standard placement of that template.
See https://de.wikipedia.org/wiki/Hilfe_Diskussion:Personendaten/Archiv/1#Position_der_Personendaten_am_.22Artikelende.22
""")
    separator = site.family.category_text_separator
    iseparator = site.family.interwiki_text_separator
    separatorstripped = separator.strip()
    iseparatorstripped = iseparator.strip()
    if addOnly:
        s2 = oldtext
    else:
        s2 = removeCategoryLinksAndSeparator(oldtext, site=site, marker=marker,
                                             separator=separatorstripped)
    s = categoryFormat(new, insite=site)
    if s:
        if site.language() in site.family.category_attop:
            newtext = s + separator + s2
        else:
            # calculate what was after the categories links on the page
            firstafter = s2.find(marker)
            if firstafter < 0:
                firstafter = len(s2)
            else:
                firstafter += len(marker)
            # Is there text in the 'after' part that means we should keep it
            # after?
            if "</noinclude>" in s2[firstafter:]:
                if separatorstripped:
                    s = separator + s
                newtext = (s2[:firstafter].replace(marker, '') +
                           s +
                           s2[firstafter:])
            elif site.language() in site.family.categories_last:
                newtext = s2.replace(marker, '').strip() + separator + s
            else:
                interwiki = getLanguageLinks(s2)
                s2 = removeLanguageLinksAndSeparator(s2.replace(marker, ''),
                                                     site, '',
                                                     iseparatorstripped
                                                     ) + separator + s
                newtext = replaceLanguageLinks(s2, interwiki, site=site,
                                               addOnly=True)
    else:
        newtext = s2.replace(marker, '')
    return newtext.strip()


def categoryFormat(categories, insite=None):
    """Return a string containing links to all categories in a list.

    'categories' should be a list of Category objects or strings
        which can be either the raw name or [[Category:..]].

    The string is formatted for inclusion in insite.

    """
    if not categories:
        return ''
    if insite is None:
        insite = pywikibot.Site()

    if isinstance(categories[0], basestring):
        if categories[0][0] == '[':
            catLinks = categories
        else:
            catLinks = ['[[Category:%s]]' % category for category in categories]
    else:
        catLinks = [pywikibot.Category(category).aslink()
                    for category in categories]

    if insite.category_on_one_line():
        sep = ' '
    else:
        sep = config.line_separator
    # Some people don't like the categories sorted
    #catLinks.sort()
    return sep.join(catLinks) + config.line_separator


# -------------------------------------
# Functions dealing with external links
# -------------------------------------

def compileLinkR(withoutBracketed=False, onlyBracketed=False):
    """Return a regex that matches external links."""
    # RFC 2396 says that URLs may only contain certain characters.
    # For this regex we also accept non-allowed characters, so that the bot
    # will later show these links as broken ('Non-ASCII Characters in URL').
    # Note: While allowing dots inside URLs, MediaWiki will regard
    # dots at the end of the URL as not part of that URL.
    # The same applies to comma, colon and some other characters.
    notAtEnd = '\]\s\.:;,<>"\|\)'
    # So characters inside the URL can be anything except whitespace,
    # closing squared brackets, quotation marks, greater than and less
    # than, and the last character also can't be parenthesis or another
    # character disallowed by MediaWiki.
    notInside = '\]\s<>"'
    # The first half of this regular expression is required because '' is
    # not allowed inside links. For example, in this wiki text:
    #       ''Please see https://www.example.org.''
    # .'' shouldn't be considered as part of the link.
    regex = r'(?P<url>http[s]?://[^%(notInside)s]*?[^%(notAtEnd)s]' \
            r'(?=[%(notAtEnd)s]*\'\')|http[s]?://[^%(notInside)s]*' \
            r'[^%(notAtEnd)s])' % {'notInside': notInside, 'notAtEnd': notAtEnd}

    if withoutBracketed:
        regex = r'(?<!\[)' + regex
    elif onlyBracketed:
        regex = r'\[' + regex
    linkR = re.compile(regex)
    return linkR


# --------------------------------
# Functions dealing with templates
# --------------------------------

def extract_templates_and_params(text):
    """Return a list of templates found in text.

    Return value is a list of tuples. There is one tuple for each use of a
    template in the page, with the template title as the first entry and a
    dict of parameters as the second entry.  Parameters are indexed by
    strings; as in MediaWiki, an unnamed parameter is given a parameter name
    with an integer value corresponding to its position among the unnamed
    parameters, and if this results multiple parameters with the same name
    only the last value provided will be returned.

    This uses a third party library (mwparserfromhell) if it is installed
    and enabled in the user-config.py. Otherwise it falls back on a
    regex based function defined below.

    @param text: The wikitext from which templates are extracted
    @type text: unicode or string

    """

    if not (config.use_mwparserfromhell and mwparserfromhell):
        return extract_templates_and_params_regex(text)
    code = mwparserfromhell.parse(text)
    result = []
    for template in code.filter_templates(recursive=True):
        params = {}
        for param in template.params:
            params[unicode(param.name)] = unicode(param.value)
        result.append((unicode(template.name.strip()), params))
    return result


def extract_templates_and_params_regex(text):
    """
    See the documentation for extract_templates_and_params
    This does basically the same thing, but uses regex.
    @param text:
    @return:
    """

    # remove commented-out stuff etc.
    thistxt = removeDisabledParts(text)

    # marker for inside templates or parameters
    marker1 = findmarker(thistxt)

    # marker for links
    marker2 = findmarker(thistxt, u'##', u'#')

    # marker for math
    marker3 = findmarker(thistxt, u'%%', u'%')

    # marker for value parameter
    marker4 = findmarker(thistxt, u'§§', u'§')

    result = []
    Rmath = re.compile(r'<math>[^<]+</math>')
    Rvalue = re.compile(r'{{{.+?}}}')
    Rmarker1 = re.compile(r'%s(\d+)%s' % (marker1, marker1))
    Rmarker2 = re.compile(r'%s(\d+)%s' % (marker2, marker2))
    Rmarker3 = re.compile(r'%s(\d+)%s' % (marker3, marker3))
    Rmarker4 = re.compile(r'%s(\d+)%s' % (marker4, marker4))

    # Replace math with markers
    maths = {}
    count = 0
    for m in Rmath.finditer(thistxt):
        count += 1
        item = m.group()
        thistxt = thistxt.replace(item, '%s%d%s' % (marker3, count, marker3))
        maths[count] = item

    values = {}
    count = 0
    for m in Rvalue.finditer(thistxt):
        count += 1
        # If we have digits between brackets, restoring from dict may fail.
        # So we need to change the index. We have to search in the origin text.
        while u'}}}%d{{{' % count in text:
            count += 1
        item = m.group()
        thistxt = thistxt.replace(item, '%s%d%s' % (marker4, count, marker4))
        values[count] = item

    inside = {}
    seen = set()
    count = 0
    while TEMP_REGEX.search(thistxt) is not None:
        for m in TEMP_REGEX.finditer(thistxt):
            # Make sure it is not detected again
            item = m.group()
            if item in seen:
                continue  # speed up
            seen.add(item)
            count += 1
            while u'}}%d{{' % count in text:
                count += 1
            thistxt = thistxt.replace(item,
                                      '%s%d%s' % (marker1, count, marker1))

            # Make sure stored templates don't contain markers
            for m2 in Rmarker1.finditer(item):
                item = item.replace(m2.group(), inside[int(m2.group(1))])
            for m2 in Rmarker3.finditer(item):
                item = item.replace(m2.group(), maths[int(m2.group(1))])
            for m2 in Rmarker4.finditer(item):
                item = item.replace(m2.group(), values[int(m2.group(1))])
            inside[count] = item

            # Name
            name = m.group('name').strip()
            m2 = Rmarker1.search(name) or Rmath.search(name)
            if m2 is not None:
                # Doesn't detect templates whose name changes,
                # or templates whose name contains math tags
                continue

            # {{#if: }}
            if not name or name.startswith('#'):
                continue

# TODO: merged from wikipedia.py - implement the following
#            if self.site().isInterwikiLink(name):
#                continue
#            # {{DEFAULTSORT:...}}
#            from distutils.version import LooseVersion as LV
#            defaultKeys = LV(self.site.version()) > LV("1.13") and \
#                          self.site().getmagicwords('defaultsort')
#            # It seems some wikis does not have this magic key
#            if defaultKeys:
#                found = False
#                for key in defaultKeys:
#                    if name.startswith(key):
#                        found = True
#                        break
#                if found: continue
#
#            try:
#                name = Page(self.site(), name).title()
#            except InvalidTitle:
#                if name:
#                    output(
#                        u"Page %s contains invalid template name {{%s}}."
#                       % (self.title(), name.strip()))
#                continue

            # Parameters
            paramString = m.group('params')
            params = {}
            numbered_param = 1
            if paramString:
                # Replace wikilinks with markers
                links = {}
                count2 = 0
                for m2 in pywikibot.link_regex.finditer(paramString):
                    count2 += 1
                    item = m2.group(0)
                    paramString = paramString.replace(
                        item, '%s%d%s' % (marker2, count2, marker2))
                    links[count2] = item
                # Parse string
                markedParams = paramString.split('|')
                # Replace markers
                for param in markedParams:
                    if "=" in param:
                        param_name, param_val = param.split("=", 1)
                    else:
                        param_name = unicode(numbered_param)
                        param_val = param
                        numbered_param += 1
                    count = len(inside)
                    for m2 in Rmarker1.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      inside[int(m2.group(1))])
                    for m2 in Rmarker2.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      links[int(m2.group(1))])
                    for m2 in Rmarker3.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      maths[int(m2.group(1))])
                    for m2 in Rmarker4.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      values[int(m2.group(1))])
                    params[param_name.strip()] = param_val.strip()

            # Add it to the result
            result.append((name, params))
    return result


def glue_template_and_params(template_and_params):
    """Return wiki text of template glued from params.

    You can use items from extract_templates_and_params here to get
    an equivalent template wiki text (it may happen that the order
    of the params changes).

    """
    (template, params) = template_and_params
    text = u''
    for item in params:
        text += u'|%s=%s\n' % (item, params[item])

    return u'{{%s\n%s}}' % (template, text)


# --------------------------
# Page parsing functionality
# --------------------------

def does_text_contain_section(pagetext, section):
    """
    Determines whether the page text contains the given section title.

    @param pagetext: The wikitext of a page
    @type text: unicode or string
    @param section: a section of a page including wikitext markups
    @type section: unicode or string

    Note: It does not care whether a section string may contain spaces or
          underlines. Both will match.
          If a section parameter contains a internal link, it will match the
          section with or without a preceding colon which is required for a
          text link e.g. for categories and files.

    """
    # match preceding colon for text links
    section = re.sub(r'\\\[\\\[(\\\:)?', '\[\[\:?', re.escape(section))
    # match underscores and white spaces
    section = re.sub(r'\\[ _]', '[ _]', section)
    m = re.search("=+[ ']*%s[ ']*=+" % section, pagetext)
    return bool(m)


# ---------------------------------------
# Time parsing functionality (Archivebot)
# ---------------------------------------

class tzoneFixedOffset(datetime.tzinfo):

    """
    Class building tzinfo objects for fixed-offset time zones

    @offset: a number indicating fixed offset in minutes east from UTC
    @name: a string with name of the timezone"""

    def __init__(self, offset, name):
        self.__offset = datetime.timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta(0)

    def __repr__(self):
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            self.__offset.days * 86400 + self.__offset.seconds,
            self.__name
        )


class TimeStripper(object):

    """
    Find timestamp in page text and returns it as timezone aware datetime object
    """

    def __init__(self, site=None):
        if site is None:
            self.site = pywikibot.Site()
        else:
            self.site = site

        self.origNames2monthNum = {}
        for n, (_long, _short) in enumerate(self.site.months_names, start=1):
            self.origNames2monthNum[_long] = n
            self.origNames2monthNum[_short] = n
            if _short.endswith('.'):
                self.origNames2monthNum[_short[:-1]] = n

        self.groups = [u'year', u'month',  u'hour',  u'time', u'day', u'minute', u'tzinfo']

        timeR = r'(?P<time>(?P<hour>[0-2]\d)[:\.h](?P<minute>[0-5]\d))'
        timeznR = r'\((?P<tzinfo>[A-Z]+)\)'
        yearR = r'(?P<year>(19|20)\d\d)'
        monthR = r'(?P<month>(%s))' % (u'|'.join(self.origNames2monthNum))
        dayR = r'(?P<day>(3[01]|[12]\d|0?[1-9]))'

        self.ptimeR = re.compile(timeR)
        self.timeznR = re.compile(timeznR)
        self.yearR = re.compile(yearR)
        self.pmonthR = re.compile(monthR, re.U)
        self.pdayR = re.compile(dayR)

        # order is important to avoid mismatch when searching
        self.patterns = [
            self.ptimeR,
            self.timeznR,
            self.yearR,
            self.pmonthR,
            self.pdayR,
        ]

    def findmarker(self, text, base=u'@@', delta='@'):
        # find a string which is not part of text
        while base in text:
            base += delta
        return base

    def last_match_and_replace(self, txt, pat):
        """
        Take the rightmost match, to prevent spurious earlier matches, and replace with marker
        """
        m = None
        for m in pat.finditer(txt):
            pass

        if m:
            marker = self.findmarker(txt)
            txt = pat.sub(marker, txt)
            return (txt, m.groupdict())
        else:
            return (txt, None)

    def timestripper(self, line):
        """
        Find timestamp in line and convert it to time zone aware datetime.
        All the following items must be matched, otherwise None is returned:
        -. year, month, hour, time, day, minute, tzinfo

        """
        # match date fields
        dateDict = dict()
        for pat in self.patterns:
            line, matchDict = self.last_match_and_replace(line, pat)
            if matchDict:
                dateDict.update(matchDict)

        # all fields matched -> date valid
        if all(g in dateDict for g in self.groups):
            # remove 'time' key, now splitted in hour/minute and not needed by datetime
            del dateDict['time']

            # replace month name in original language with month number
            try:
                dateDict['month'] = self.origNames2monthNum[dateDict['month']]
            except KeyError:
                pywikibot.output(u'incorrect month name in page')

            # convert to integers
            for k, v in dateDict.items():
                try:
                    dateDict[k] = int(v)
                except ValueError:
                    pass

            # find timezone
            dateDict['tzinfo'] = tzoneFixedOffset(self.site.siteinfo['timeoffset'],
                                                  self.site.siteinfo['timezone'])

            timestamp = datetime.datetime(**dateDict)

        else:
            timestamp = None

        return timestamp
