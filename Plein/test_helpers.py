# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


def extract_all_href_urls(resp):
    content = str(resp.content)
    pos = content.find('<body')
    if pos > 0:                             # pragma: no branch
        content = content[pos:]             # strip head
    urls = list()
    while len(content):
        pos = content.find('href="')
        if pos > 0:
            content = content[pos+6:]       # strip all before href
            pos = content.find('"')
            urls.append(content[:pos])
            content = content[pos:]
        else:
            content = ""
    # while
    return urls

def assert_html_ok(testcase, response):
    """ Doe een aantal basic checks op een html response """
    html = str(response.content)
    testcase.assertContains(response, "<html")
    testcase.assertIn("lang=", html)
    testcase.assertIn("</html>", html)
    testcase.assertIn("<head>", html)
    testcase.assertIn("</head>", html)
    testcase.assertIn("<body ", html)
    testcase.assertIn("</body>", html)
    testcase.assertIn("<!DOCTYPE html>", html)


def assert_template_used(testcase, response, template_names):
    """ Controleer dat de gevraagde templates gebruikt zijn """
    lst = list(template_names)
    for templ in response.templates:
        # print("template name: %s" % templ.name)
        if templ.name in lst:
            lst.remove(templ.name)
    # for
    if len(lst):    # pragma: no coverage
        msg = "Following templates should have been used: %s\n(actually used: %s)" % (repr(lst), repr([t.name for t in response.templates]))
        testcase.assertTrue(False, msg=msg)


def assert_other_http_commands_not_supported(testcase, url, post=True, delete=True, put=True, patch=True):
    """ Test een aantal 'common' http methoden
        en controleer dat deze niet ondersteund zijn (status code 405 = not allowed)
        POST, DELETE, PATCH
    """
    if post:
        resp = testcase.client.post(url)
        testcase.assertEqual(resp.status_code, 405)  # 405=not allowd

    if delete:                                  # pragma: no branch
        resp = testcase.client.delete(url)
        testcase.assertEqual(resp.status_code, 405)

    if put:                                     # pragma: no branch
        resp = testcase.client.put(url)
        testcase.assertEqual(resp.status_code, 405)

    if patch:                                   # pragma: no branch
        resp = testcase.client.patch(url)
        testcase.assertEqual(resp.status_code, 405)


# end of file
