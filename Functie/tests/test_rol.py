# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Account.models import get_account
from Functie.definities import Rol
from Functie.operations import maak_account_vereniging_secretaris
from Functie.tests.helpers import maak_functie
from Functie.rol import (rol_mag_wisselen, rol_get_beschrijving, rol_zet_beschrijving, rol_activeer_functie,
                         rol_activeer_rol, rol_get_huidige, rol_get_huidige_functie)
from Functie.rol.bepaal import RolBepaler
from Functie.rol.beschrijving import SESSIONVAR_ROL_BESCHRIJVING
from Functie.rol.huidige import SESSIONVAR_ROL_HUIDIGE, SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK
from Functie.rol.mag_wisselen import SESSIONVAR_ROL_MAG_WISSELEN_BOOL
from Functie.rol.scheids import gebruiker_is_scheids, SESSIONVAR_SCHEIDS
from Geo.models import Regio
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestFunctieRol(E2EHelpers, TestCase):

    """ tests voor de Functie applicatie, diverse corner-cases """

    url_wissel_naar_sec = '/functie/wissel-van-rol/secretaris/'
    url_email_sec_hwl = '/functie/beheerders/email/sec-hwl/'
    url_activeer_rol = '/functie/activeer-rol/%s/'
    url_vereniging = '/vereniging/'
    url_login = '/account/login/'
    url_plein = '/plein/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.not', 'Normaal')

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

        # e-mail moet bevestigd zijn (anders kunnen we de mail niet sturen)
        self.account_normaal.email_is_bevestigd = False
        self.account_normaal.save(update_fields=['email_is_bevestigd'])
        added = maak_account_vereniging_secretaris(self.ver1, self.account_normaal)
        self.assertFalse(added)
        self.assertEqual(self.functie_sec.accounts.count(), 0)

        # normale situatie
        self.account_normaal.email_is_bevestigd = True
        self.account_normaal.save(update_fields=['email_is_bevestigd'])
        added = maak_account_vereniging_secretaris(self.ver1, self.account_normaal)
        self.assertTrue(added)
        self.assertEqual(self.functie_sec.accounts.count(), 1)

        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_functie/rollen-gewijzigd.dtl')
        self.assert_consistent_email_html_text(mail)

        # dubbel koppelen wordt voorkomen
        added = maak_account_vereniging_secretaris(self.ver1, self.account_normaal)
        self.assertFalse(added)
        self.assertEqual(self.functie_sec.accounts.count(), 1)

    def test_huidige(self):
        self.e2e_login_no_check(self.account_normaal)
        resp = self.client.get(self.url_plein)
        request = resp.wsgi_request
        self.assertTrue(request.user.is_authenticated)

        # if SESSIONVAR_ROL_HUIDIGE in request.session:
        del request.session[SESSIONVAR_ROL_HUIDIGE]
        rol = rol_get_huidige(request)
        self.assertEqual(rol, Rol.ROL_NONE)

        session = request.session
        session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = 'Test1!'
        session.save()

        rol, functie = rol_get_huidige_functie(request)
        self.assertIsNone(functie)

        del request.session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK]
        rol, functie = rol_get_huidige_functie(request)
        self.assertEqual(rol, Rol.ROL_NONE)
        self.assertIsNone(functie)

        self.assertTrue(SESSIONVAR_SCHEIDS in request.session.keys())
        self.assertFalse(gebruiker_is_scheids(request))

        del request.session[SESSIONVAR_SCHEIDS]
        self.assertFalse(gebruiker_is_scheids(request))

    def test_geen_sessie(self):
        # probeer beveiliging tegen afwezigheid sessie variabelen
        # typisch tweedelijns, want views checken user.is_authenticated

        resp = self.client.get('/plein/')
        request = resp.wsgi_request
        account = request.user

        self.assertTrue(SESSIONVAR_ROL_BESCHRIJVING not in request.session.keys())
        self.assertEqual(rol_get_beschrijving(request), "?")

        self.assertTrue(SESSIONVAR_SCHEIDS not in request.session.keys())
        self.assertFalse(gebruiker_is_scheids(request))

        self.assertTrue(SESSIONVAR_ROL_MAG_WISSELEN_BOOL not in request.session.keys())
        res = rol_mag_wisselen(request)
        self.assertFalse(res)

        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session.keys())
        rol_activeer_rol(request, account, 'bestaat niet')
        self.assertTrue(SESSIONVAR_ROL_HUIDIGE not in request.session.keys())

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
        self.assert_is_redirect(resp, self.url_login)

        # roep een view aan die rol_get_huidige_functie aanroept
        # (als onderdeel van de test_func van UserPassesTestMixin)
        resp = self.client.get(self.url_email_sec_hwl)
        self.assert_is_redirect(resp, self.url_login)

        # geen PK maar iets wat niet eens een getal is
        session = self.client.session
        session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = 'Test2!'
        session.save()

        # roep een view aan die rol_get_huidige_functie aanroept
        # (als onderdeel van de test_func van UserPassesTestMixin)
        resp = self.client.get(self.url_email_sec_hwl)
        self.assert_is_redirect(resp, self.url_login)

        # niet bestaande PK
        session = self.client.session
        session[SESSIONVAR_ROL_HUIDIGE_FUNCTIE_PK] = 999999
        session.save()

        # roep een view aan die rol_get_huidige_functie aanroept
        # (als onderdeel van de test_func van UserPassesTestMixin)
        resp = self.client.get(self.url_email_sec_hwl)
        self.assert_is_redirect(resp, self.url_login)

        # corner case (niet mogelijk via de view)
        request = resp.wsgi_request
        account = get_account(request)      # geen AnonymousUser terug
        rol = rol_get_huidige(request)
        self.assertEqual(rol, Rol.ROL_NONE)
        rol_activeer_functie(request, account, self.functie_sec)
        rol = rol_get_huidige(request)
        self.assertEqual(rol, Rol.ROL_NONE)

    def test_activeer(self):
        self.assertFalse(self.account_normaal.is_BB)
        self.assertFalse(self.account_normaal.is_staff)
        self.functie_sec.accounts.add(self.account_normaal)     # zorgt voor rol_mag_wisselen = True

        self.e2e_login_and_pass_otp(self.account_normaal)

        resp = self.client.get(self.url_plein)
        request = resp.wsgi_request
        self.assertTrue(request.user.is_authenticated)

        rol = rol_get_huidige(request)
        self.assertEqual(rol, Rol.ROL_SPORTER)

        resp = self.client.post(self.url_activeer_rol % 'BB')
        self.assert_is_redirect(resp, self.url_plein)

        rol = rol_get_huidige(request)
        self.assertEqual(rol, Rol.ROL_SPORTER)

        # speciale situatie
        rol_zet_beschrijving(request, Rol.ROL_SEC, self.functie_sec.pk, functie=None)

    def test_bepaler(self):
        # direct checks van een paar corner cases die via de views lastig te raken zijn
        resp = self.client.get(self.url_plein)
        request = resp.wsgi_request

        bepaler = RolBepaler(self.account_admin)

        # niet bestaande functie_pk
        mag, rol = bepaler.mag_functie(request, 999999)
        self.assertFalse(mag)
        self.assertEqual(rol, Rol.ROL_NONE)


# end of file
