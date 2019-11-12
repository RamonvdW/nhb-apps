# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth import get_user_model
from django.test import TestCase
from .menu import menu_dynamics

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
    testcase.assertEqual(lst, list())


def assert_other_http_commands_not_supported(testcase, url, post=True, delete=True, put=True, patch=True):
    """ Test een aantal 'common' http methoden
        en controleer dat deze niet ondersteund zijn (status code 405 = not allowed)
        POST, DELETE, PATCH
    """
    if post:
        resp = testcase.client.post(url)
        testcase.assertEqual(resp.status_code, 405)  # 405=not allowd

    if delete:
        resp = testcase.client.delete(url)
        testcase.assertEqual(resp.status_code, 405)

    if put:
        resp = testcase.client.put(url)
        testcase.assertEqual(resp.status_code, 405)

    if patch:
        resp = testcase.client.patch(url)
        testcase.assertEqual(resp.status_code, 405)


class PleinTest(TestCase):

    def setUp(self):
        """ initializatie van de test case """
        usermodel = get_user_model()
        usermodel.objects.create_user('normaal', 'normaal@test.com', 'wachtwoord')
        usermodel.objects.create_superuser('admin', 'admin@test.com', 'wachtwoord')

    def test_root_redirect(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)     # 302 = redirect
        self.assertEqual(resp.url, '/plein/')

    def test_plein_annon(self):
        self.client.logout()
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/plein.dtl', 'plein/site_layout.dtl'))

    def test_plein_normaal(self):
        self.client.login(username='normaal', password='wachtwoord')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertNotContains(resp, '/admin/')
        assert_template_used(self, resp, ('plein/plein.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_plein_admin(self):
        self.client.login(username='admin', password='wachtwoord')
        resp = self.client.get('/plein/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '/admin/')
        assert_template_used(self, resp, ('plein/plein.dtl', 'plein/site_layout.dtl'))
        self.client.logout()

    def test_privacy(self):
        resp = self.client.get('/plein/privacy/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/privacy.dtl', 'plein/site_layout.dtl'))
        assert_other_http_commands_not_supported(self, '/plein/privacy/')

    def test_wisselvanrol(self):
        self.client.login(username='admin', password='wachtwoord')
        resp = self.client.get('/plein/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        assert_html_ok(self, resp)
        assert_template_used(self, resp, ('plein/wissel-van-rol.dtl', 'plein/site_layout.dtl'))
        assert_other_http_commands_not_supported(self, '/plein/privacy/')
        self.client.logout()

    def test_wisselvanrol_menu(self):
        self.client.login(username='admin', password='wachtwoord')
        session = self.client.session
        session['gebruiker_heeft_rol'] = True
        session.save()
        resp = self.client.get('/plein/')
        self.assertContains(resp, "Wissel van rol")
        self.client.logout()

    def test_dynamic_menu_asssert(self):
        # test the assert in menu_dynamics
        context = dict()
        request = lambda: None      # create an empty object
        request.user = lambda: None
        request.user.is_authenticated = False
        with self.assertRaises(AssertionError):
            menu_dynamics(request, context, actief='test-bestaat-niet')

# end of file
