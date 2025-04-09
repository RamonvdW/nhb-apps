# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from Functie.models import Functie
from Geo.models import Regio
from Instaptoets.models import Vraag
from Opleiding.definities import (OPLEIDING_STATUS_INSCHRIJVEN, OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                                  OPLEIDING_INSCHRIJVING_STATUS_INSCHRIJVEN,         # 'I'  nog niet in mandje
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,  # 'R'  in mandje
                                  OPLEIDING_INSCHRIJVING_STATUS_BESTELD,             # 'B'  besteld
                                  OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,          # 'D'  betaald
                                  OPLEIDING_INSCHRIJVING_STATUS_AFGEMELD)            # 'A'  geannuleerd
from Opleiding.models import Opleiding, OpleidingInschrijving, OpleidingAfgemeld
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging


class TestOpleidingVereniging(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit voor de HWL """

    test_after = ('Account', 'Functie')

    url_overzicht = '/opleiding/'
    url_ver_lijst = '/opleiding/vereniging/lijst/'
    url_aanmeldingen = '/opleiding/aanmeldingen/%s/'                # opleiding_pk
    url_download = '/opleiding/aanmeldingen/%s/download/csv/'       # opleiding_pk
    url_details_aanmelding = '/opleiding/details-aanmelding/%s/'    # inschrijving_pk
    url_details_afmelding = '/opleiding/details-afmelding/%s/'      # afmelding_pk
    url_details = '/opleiding/details/%s/'                          # opleiding_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

        # maak een test vereniging
        self.ver = Vereniging(
                        ver_nr=settings.OPLEIDINGEN_VERKOPER_VER_NRS[0],
                        naam="Bondsbureau",
                        regio=Regio.objects.get(regio_nr=100))
        self.ver.save()

        self.functie_hwl = Functie(
                                beschrijving='HWL ver BB',
                                rol='HWL',
                                bevestigde_email='hwl@khsn.not',
                                vereniging=self.ver)
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_normaal)

        self.functie_sec = Functie(
                                beschrijving='SEC ver BB',
                                rol='SEC',
                                bevestigde_email='sec@khsn.not',
                                vereniging=self.ver)
        self.functie_sec.save()
        self.functie_sec.accounts.add(self.account_normaal)

        now = timezone.now()
        sporter = Sporter(
                    lid_nr=100001,
                    voornaam='Thea',
                    achternaam='de Tester',
                    unaccented_naam='Thea de Tester',
                    email='normaal@test.nhb',
                    geboorte_datum="1970-11-15",
                    geslacht='V',
                    sinds_datum='2000-01-01',
                    lid_tot_einde_jaar=now.year,
                    bij_vereniging=self.ver,
                    account=self.account_normaal)
        sporter.save()

        # maak een basiscursus aan zodat het kaartje Basiscursus getoond wordt op het overzicht
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_begin="2024-11-01",
                        periode_einde="2024-12-01",
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True)
        opleiding.save()
        self.opleiding = opleiding
        self.opleiding.refresh_from_db()

        # maak de instaptoets beschikbaar
        Vraag().save()

        inschrijving = OpleidingInschrijving(
                            opleiding=opleiding,
                            sporter=sporter,
                            status=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            koper=self.account_normaal)
        inschrijving.save()
        self.inschrijving1 = inschrijving

        inschrijving = OpleidingInschrijving(
                            opleiding=opleiding,
                            sporter=sporter,
                            status=OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                            koper=self.account_normaal)
        inschrijving.save()
        self.inschrijving2 = inschrijving

        inschrijving = OpleidingInschrijving(
                            opleiding=opleiding,
                            sporter=sporter,
                            status=OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                            koper=self.account_normaal)
        inschrijving.save()
        self.inschrijving3 = inschrijving

        inschrijving = OpleidingInschrijving(
                            opleiding=opleiding,
                            sporter=sporter,
                            status=OPLEIDING_INSCHRIJVING_STATUS_AFGEMELD,
                            koper=self.account_normaal)
        inschrijving.save()
        self.inschrijving4 = inschrijving

        afgemeld = OpleidingAfgemeld(
                        wanneer_afgemeld=now,
                        status=OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                        opleiding=self.opleiding,
                        sporter=sporter,
                        wanneer_aangemeld=now,
                        koper=self.account_normaal,
                        bedrag_ontvangen='1.00')
        afgemeld.save()

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ver_lijst)
        self.assert403(resp, 'Geen toegang')

    def test_geen_verkoper(self):
        # maak een test vereniging die geen opleidingen mag verkopen
        ver_nr = 1000
        self.assertNotIn(ver_nr, settings.OPLEIDINGEN_VERKOPER_VER_NRS)

        self.ver = Vereniging(
                        ver_nr=1000,
                        naam="Grote Club",
                        regio=Regio.objects.get(regio_nr=101))
        self.ver.save()

        functie_hwl = Functie(
                            beschrijving='HWL ver 1000',
                            rol='HWL',
                            bevestigde_email='hwl@khsn.not',
                            vereniging=self.ver)
        functie_hwl.save()
        functie_hwl.accounts.add(self.account_normaal)

        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmeldingen % self.opleiding.pk)
        self.assert403(resp, 'Geen toegang')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_download % self.opleiding.pk)
        self.assert403(resp, 'Geen toegang')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % self.inschrijving1.pk)
        self.assert403(resp, 'Geen toegang')

    def test_lijst(self):
        self.e2e_login_and_pass_otp(self.account_normaal)

        # SEC
        self.e2e_wissel_naar_functie(self.functie_sec)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ver_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        # HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ver_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

        # lege lijst
        OpleidingInschrijving.objects.all().delete()
        OpleidingAfgemeld.objects.all().delete()
        Opleiding.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_ver_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht-vereniging.dtl', 'plein/site_layout.dtl'))

    def test_aanmeldingen(self):
        self.e2e_login_and_pass_otp(self.account_normaal)

        url = self.url_aanmeldingen % self.opleiding.pk

        # HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanmeldingen.dtl', 'plein/site_layout.dtl'))

        # SEC (heeft geen download knop)
        self.e2e_wissel_naar_functie(self.functie_sec)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanmeldingen.dtl', 'plein/site_layout.dtl'))

        # MO
        self.e2e_wissel_naar_functie(self.functie_mo)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanmeldingen.dtl', 'plein/site_layout.dtl'))

        # lege lijst
        OpleidingInschrijving.objects.all().delete()
        OpleidingAfgemeld.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanmeldingen.dtl', 'plein/site_layout.dtl'))

        # corner case
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmeldingen % 999999)
        self.assert404(resp, 'Opleiding niet gevonden')

        # BB
        self.account_normaal.is_BB = True
        self.account_normaal.save(update_fields=['is_BB'])
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

    def test_details_aanmelding(self):
        self.e2e_login_and_pass_otp(self.account_normaal)

        # HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % '%%%')
        self.assert404(resp, 'Geen valide parameter')

        self.e2e_wissel_naar_functie(self.functie_mo)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % 999999)
        self.assert404(resp, 'Aanmelding niet gevonden')

        # SEC
        url = self.url_details_aanmelding % self.inschrijving1.pk

        self.e2e_wissel_naar_functie(self.functie_sec)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/aanmelding-details.dtl', 'plein/site_layout.dtl'))

        # MO
        for url in (self.url_details_aanmelding % self.inschrijving2.pk,
                    self.url_details_aanmelding % self.inschrijving3.pk,
                    self.url_details_aanmelding % self.inschrijving4.pk):

            self.e2e_wissel_naar_functie(self.functie_mo)
            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('opleiding/aanmelding-details.dtl', 'plein/site_layout.dtl'))
        # for

        # BB
        self.account_normaal.is_BB = True
        self.account_normaal.save(update_fields=['is_BB'])
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

    def test_download(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        url = self.url_download % self.opleiding.pk

        # HWL
        self.e2e_wissel_naar_functie(self.functie_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert200_is_bestand_csv(resp)

        # SEC
        self.e2e_wissel_naar_functie(self.functie_sec)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Geen toegang')

        # MO
        self.e2e_wissel_naar_functie(self.functie_mo)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert200_is_bestand_csv(resp)

        # corner case
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_download % 999999)
        self.assert404(resp, 'Opleiding niet gevonden')

    def test_afmelden(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url_details_afmelding = '/opleiding/details-afmelding/%s/'  # afmelding_pk
        # url = self.url_details_afmelding % self.afmelding.pk

# end of file
