# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Geo.models import Regio
from Taken.models import Taak
from Taken.operations import eval_open_taken, SESSIONVAR_TAAK_EVAL_AFTER
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging


class TestTakenViews(E2EHelpers, TestCase):

    """ tests voor de applicatie Taken """

    test_after = ('Functie', 'Taken.tests.test_taken')

    url_overzicht = '/taken/'
    url_details = '/taken/details/%s/'  # taak_pk

    emailadres = 'taak@test.not'
    emailadres2 = 'taak2@test.not'

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        """ initialisatie van de test case """

        self.functie_sup = Functie.objects.get(rol='SUP')
        self.functie_sup.bevestigde_email = self.emailadres
        self.functie_sup.laatste_email_over_taken = None
        self.functie_sup.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

        self.functie_mwz = Functie.objects.get(rol='MWZ')
        self.functie_mwz.bevestigde_email = self.emailadres2
        self.functie_mwz.laatste_email_over_taken = None
        self.functie_mwz.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112),
                    contact_email='info@bb.not')
        ver.save()

        self.functie_hwl, _ = Functie.objects.get_or_create(rol='HWL', vereniging=ver)
        self.functie_hwl.bevestigde_email = self.emailadres2
        self.functie_hwl.laatste_email_over_taken = None
        self.functie_hwl.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

        self.functie_wl, _ = Functie.objects.get_or_create(rol='WL', vereniging=ver)
        self.functie_wl.bevestigde_email = self.emailadres2
        self.functie_wl.laatste_email_over_taken = None
        self.functie_wl.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een taak aan
        taak = Taak(toegekend_aan_functie=self.functie_sup,
                    deadline='2020-01-01',
                    onderwerp='Testje taak1',
                    beschrijving='Testje taak1 met meerdere\nregels\ntest')
        taak.save()
        self.taak1 = taak

        # maak nog een taak aan
        taak = Taak(toegekend_aan_functie=self.functie_mwz,
                    deadline='2020-01-01',
                    aangemaakt_door=self.account_normaal,
                    onderwerp='Testje taak2',
                    beschrijving='Testje taak2')
        taak.save()
        self.taak2 = taak

        # maak een afgeronde taak aan
        taak = Taak(is_afgerond=True,
                    toegekend_aan_functie=self.functie_mwz,
                    deadline='2020-01-01',
                    onderwerp='Testje taak3',
                    beschrijving='Afgerond testje taak3')
        taak.save()
        self.taak3 = taak

    def test_anon(self):
        # do een get van het takenoverzicht zonder ingelogd te zijn
        # dit leidt tot een redirect naar het plein
        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details % 0)
        self.assert403(resp)

    def test_allowed(self):
        self.functie_sup.accounts.add(self.testdata.account_admin)
        self.functie_mwz.accounts.add(self.testdata.account_admin)

        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_wissel_naar_functie(self.functie_sup)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/overzicht.dtl', 'design/site_layout.dtl'))

        self.assertContains(resp, 'Testje taak1')
        self.assertContains(resp, 'Testje taak2')
        self.assertContains(resp, 'Testje taak3')

        # al afgesloten taak bekijken
        url = self.url_details % self.taak3.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/details.dtl', 'design/site_layout.dtl'))

        # nog niet afgesloten taak bekijken
        # deze heeft "aangemaakt door"
        url = self.url_details % self.taak2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/details.dtl', 'design/site_layout.dtl'))

        # doe de post om de taak af te ronden
        url = self.url_details % self.taak1.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_overzicht)

        # nogmaals, voor uitbreiding logboek
        self.taak1.refresh_from_db()
        self.taak1.is_afgerond = False
        self.taak1.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_overzicht)

        # nogmaals afronden (is al afgerond)
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_overzicht)

        # details, nu afgerond
        url = self.url_details % self.taak1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/details.dtl', 'design/site_layout.dtl'))

        # overzicht met afgeronde taak
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/overzicht.dtl', 'design/site_layout.dtl'))

        self.assertTrue(str(self.taak1) != '')
        self.assertTrue(str(self.taak3) != '')

        # corner-case
        request = resp.wsgi_request
        eval_open_taken(request, forceer=False)

        session = request.session
        del session[SESSIONVAR_TAAK_EVAL_AFTER]
        session.save()
        eval_open_taken(request, forceer=False)

    def test_bad(self):
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()

        # niet bestaande taak
        url = self.url_details % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Geen valide taak')
        resp = self.client.post(url)
        self.assert404(resp, 'Geen valide taak')

        # taak van een ander
        url = self.url_details % self.taak3.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_hwl(self):
        self.functie_hwl.accounts.add(self.testdata.account_admin)

        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_wissel_naar_functie(self.functie_wl)

        # geen open taken
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/overzicht.dtl', 'design/site_layout.dtl'))

        # huidige functie WL is niet toegekend, maar we laten wel de taken van die functie zien

        # maak een taak aan
        taak = Taak(toegekend_aan_functie=self.functie_wl,
                    deadline='2020-01-01',
                    onderwerp='Testje taak voor WL',
                    beschrijving='Hallo dit is een test')
        taak.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_overzicht)
        self.assertEqual(resp.status_code, 200)
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('taken/overzicht.dtl', 'design/site_layout.dtl'))

        self.assertContains(resp, 'Testje taak voor WL')


# end of file
