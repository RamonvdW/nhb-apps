# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from .kruimels import make_context_broodkruimels, KRUIMEL2LABEL


def assert_html_ok(testcase, response):
    """ Doe een aantal basic checks op een html response """
    html = str(response.content)
    testcase.assertContains(response, "<html")
    testcase.assertIn("lang=", html)
    testcase.assertIn("</html>", html)
    testcase.assertIn("<head>", html)
    testcase.assertIn("</head>", html)
    testcase.assertIn("<body>", html)
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
    testcase.assertEqual(lst, list())


def assert_other_http_commands_not_supported(testcase, url, post=True, delete=True, put=True, patch=True):
    """ Test een aantal 'common' http methoden
        en controleer dat deze niet ondersteund zijn (status code 405 = not allowed)
        POST, DELETE, PATCH
    """
    if post:
        rsp = testcase.client.post(url)
        testcase.assertEqual(rsp.status_code, 405)  # 405=not allowd

    if delete:
        rsp = testcase.client.delete(url)
        testcase.assertEqual(rsp.status_code, 405)

    if put:
        rsp = testcase.client.put(url)
        testcase.assertEqual(rsp.status_code, 405)

    if patch:
        rsp = testcase.client.patch(url)
        testcase.assertEqual(rsp.status_code, 405)


class PleinTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')

    def test_broodkruimels(self):
        unknown_label = 'Account:logout'       # niet in KRUIMEL2LABEL
        self.assertNotIn(unknown_label, KRUIMEL2LABEL)

        context = dict()
        kruimels = list()
        make_context_broodkruimels(context, 'Plein:plein', ('abc', 'def'), unknown_label)
        self.assertIn('broodkruimels', context)
        self.assertEqual(len(context['broodkruimels']), 3)
        # print("context['broodkruimels'] = %s" % repr(context['broodkruimels']))

        tup = context['broodkruimels'][0]
        self.assertEqual(tup[0], 'Home')

        tup = context['broodkruimels'][1]
        self.assertEqual(tup[1], 'def')

        tup = context['broodkruimels'][2]
        self.assertEqual(tup[0], '?label?')

    def test_root_redirect(self):
        rsp = self.client.get('/')
        self.assertEqual(rsp.status_code, 302)
        self.assertEqual(rsp.url, '/plein/')

    def test_plein_annon(self):
        self.client.logout()
        rsp = self.client.get('/plein/')
        self.assertEqual(rsp.status_code, 200)
        assert_html_ok(self, rsp)
        assert_template_used(self, rsp, ('plein/plein.dtl', 'plein/site_layout.dtl'))

    def test_plein_normaal(self):
        self.client.login(username='normaal', password='wachtwoord')
        rsp = self.client.get('/plein/')
        self.assertEqual(rsp.status_code, 200)
        self.assertNotContains(rsp, '/admin/')
        assert_template_used(self, rsp, ('plein/plein.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_plein_admin(self):
        self.client.login(username='admin', password='wachtwoord')
        rsp = self.client.get('/plein/')
        self.assertEqual(rsp.status_code, 200)
        self.assertContains(rsp, '/admin/')
        assert_template_used(self, rsp, ('plein/plein.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_privacy(self):
        rsp = self.client.get('/plein/privacy/')
        self.assertEqual(rsp.status_code, 200)
        assert_html_ok(self, rsp)
        assert_other_http_commands_not_supported(self, '/plein/privacy/')
        assert_template_used(self, rsp, ('plein/privacy.dtl', 'plein/site_layout.dtl'))

# end of file
