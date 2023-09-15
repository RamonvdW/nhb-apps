# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.definities import Rollen
from Functie.operations import maak_functie, maak_account_vereniging_secretaris
from Functie.rol import (SESSIONVAR_ROL_HUIDIGE, SESSIONVAR_ROL_MAG_WISSELEN,
                         SESSIONVAR_ROL_PALLET_FUNCTIES, SESSIONVAR_ROL_PALLET_VAST,
                         SESSIONVAR_ROL_BESCHRIJVING, SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK,
                         rol_mag_wisselen, rol_enum_pallet, rol_get_beschrijving,
                         rol_activeer_rol, rol_activeer_functie,
                         rol_get_huidige, rol_get_huidige_functie)
from Geo.models import Regio
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestFunctieRol(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, diverse corner-cases """

    url_wissel_naar_sec = '/functie/wissel-van-rol/secretaris/'
    url_overzicht_sec_hwl = '/functie/overzicht/beheerders/sec-hwl/'
    url_activeer_functie = '/functie/activeer-functie/%s/'          # functie_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_tst = maak_functie("Test test", "x")

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver1 = ver

        self.functie_sec.vereniging = ver
        self.functie_sec.save()

    def test_maak_sec(self):
        self.assertEqual(self.functie_sec.accounts.count(), 0)
        added = maak_account_vereniging_secretaris(self.ver1, self.account_normaal)
        self.assertTrue(added)
        self.assertEqual(self.functie_sec.accounts.count(), 1)

        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

        # opnieuw toevoegen heeft geen effect
        added = maak_account_vereniging_secretaris(self.ver1, self.account_normaal)
        self.assertFalse(added)
        self.assertEqual(self.functie_sec.accounts.count(), 1)

    def test_huidige(self):
        self.e2e_login_no_check(self.account_normaal)
        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        self.assertTrue(request.user.is_authenticated)

        del request.session[SESSIONVAR_ROL_HUIDIGE]
        rol = rol_get_huidige(request)
        self.assertEqual(rol, Rollen.ROL_NONE)

        session = request.session
        session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = 'Test1!'
        session.save()

        rol, functie = rol_get_huidige_functie(request)
        self.assertIsNone(functie)

        del request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK]
        rol, functie = rol_get_huidige_functie(request)
        self.assertEqual(rol, Rollen.ROL_NONE)
        self.assertIsNone(functie)

    def test_geen_sessie(self):
        # probeer beveiliging tegen afwezigheid sessie variabelen
        # typisch tweedelijns, want views checken user.is_authenticated

        request = self.client

        self.assertTrue(SESSIONVAR_ROL_MAG_WISSELEN not in request.session.keys())
        res = rol_mag_wisselen(request)
        self.assertFalse(res)

        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session.keys())
        rol_activeer_rol(request, 'bestaat niet')
        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session.keys())

        rol_activeer_functie(request, 'geen getal')
        self.assertTrue(SESSIONVAR_ROL_PALLET_FUNCTIES not in request.session.keys())
        rol_activeer_functie(request, 0)

        self.assertTrue(SESSIONVAR_ROL_PALLET_VAST not in request.session.keys())
        pallet = [tup for tup in rol_enum_pallet(request)]
        self.assertEqual(len(pallet), 0)
        rol_activeer_rol(request, 'geen')

        self.assertTrue(SESSIONVAR_ROL_BESCHRIJVING not in request.session.keys())
        self.assertEqual(rol_get_beschrijving(request), "?")

    def test_anon(self):
        # zorg dan request.user.is_authenticated op False staat
        self.client.logout()

        # reproduceer probleem uit de praktijk: AnonymousUser had toch opgeslagen sessie data
        # geef deze anonymous user toch sessie data
        session = self.client.session
        session[SESSIONVAR_ROL_HUIDIGE] = 'Test1!'
        session.save()

        # roep een view aan die rol_get_huidige aanroept
        # (als onderdeel van de test_func van UserPassesTestMixin)
        resp = self.client.get(self.url_wissel_naar_sec)
        self.assert_is_redirect(resp, '/account/login/')

        # roep een view aan die rol_get_huidige_functie aanroept
        # (als onderdeel van de test_func van UserPassesTestMixin)
        resp = self.client.get(self.url_overzicht_sec_hwl)
        self.assert_is_redirect(resp, '/account/login/')

        # geen PK maar iets wat niet eens een getal is
        session = self.client.session
        session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = 'Test2!'
        session.save()

        # roep een view aan die rol_get_huidige_functie aanroept
        # (als onderdeel van de test_func van UserPassesTestMixin)
        resp = self.client.get(self.url_overzicht_sec_hwl)
        self.assert_is_redirect(resp, '/account/login/')

        # niet bestaande PK
        session = self.client.session
        session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = 999999
        session.save()

        # roep een view aan die rol_get_huidige_functie aanroept
        # (als onderdeel van de test_func van UserPassesTestMixin)
        resp = self.client.get(self.url_overzicht_sec_hwl)
        self.assert_is_redirect(resp, '/account/login/')


# end of file
