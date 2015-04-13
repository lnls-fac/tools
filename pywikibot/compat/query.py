import pywikibot
from pywikibot.data import api
from pywikibot import deprecated
from pywikibot import deprecate_arg


@deprecated("pywikibot.data.api.Request")
@deprecate_arg("useAPI", None)
@deprecate_arg("retryCount", None)
@deprecate_arg("encodeTitle", None)
def GetData(request, site=None, back_response=False):
    if site:
        request['site'] = site

    req = api.Request(**request)
    result = req.submit()

    if back_response:
        pywikibot.warning(u"back_response is no longer supported; an empty "
                          u"response object will be returned")
        import StringIO
        res_dummy = StringIO.StringIO()
        res_dummy.__dict__.update({u'code': 0, u'msg': u''})
        return res_dummy, result
    return result
