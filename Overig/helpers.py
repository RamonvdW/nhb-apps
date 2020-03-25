# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


def get_safe_from_ip(request):
    """ This helper returns the IP address of the request
        and makes sure it is a safe string that just contains an IP address
        any garbage is removed
    """

    # filter out any character that is not part of a valid IPv4 or IPv6 IP address
    # (max length 15) IPv4:                     100.200.100.200
    # (max length 39) IPv6:                     0000:0000:0000:0000:0000:0000:0000:0000
    # (max length 45) IPv6 mapped IPv4 address: 0000:0000:0000:0000:0000:ffff:100.200.100.200

    safe_ip = ""

    if request:
        try:
            from_ip = request.META['REMOTE_ADDR']
        except (KeyError, AttributeError):
            pass
        else:
            for chr in from_ip:
                if chr in '0123456789ABCDEFabcdef:.':
                    safe_ip += chr
            # for

            # also limit it in length
            safe_ip = safe_ip[:46]
    # if

    return safe_ip


# ------------------------------------------------------------------------------------
# Hieronder volgen helpers voor het testen
# ------------------------------------------------------------------------------------


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
        testcase.assertEqual(resp.status_code, 405)  # 405=not allowed

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
