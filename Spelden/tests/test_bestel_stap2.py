# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Spelden.models import SpeldAanvraagPrep
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
import datetime


class TestSpeldenBestelStap2(E2EHelpers, TestCase):

    """ tests voor de Spelden applicatie, bestelprocess stap 2 """

    url_begin = '/spelden/'
    url_bestel_stap2 = '/spelden/bestel/stap2/'
    url_bestel_stap3 = '/spelden/bestel/stap3/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()

        # maak een vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        # maak de sporter aan
        self.account_sporter = self.e2e_create_account('100001', 'normaal@test.com', 'Normaal')
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_sporter,
                    email=self.account_sporter.email)
        sporter.save()
        self.sporter_100001 = sporter

        # zet een wedstrijd op de kalender, 2 maanden terug
        now = timezone.now()
        wed_datum = (now - datetime.timedelta(days=60)).date()

        self.locatie = WedstrijdLocatie.objects.create(
                                naam='test',
                                adres='',
                                notities='')

        self.wedstrijd = Wedstrijd.objects.create(
                                status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                datum_begin=wed_datum,
                                datum_einde=wed_datum,
                                organiserende_vereniging=ver,
                                locatie=self.locatie)

        self.prep = SpeldAanvraagPrep.objects.create(
                                voor_sporter=sporter,
                                wedstrijd_geslacht='M',
                                heeft_data_stap1=True,
                                discipline='OD',
                                boog='R',
                                score='500',
                                datum_wedstrijd=wed_datum.strftime('%Y-%m-%d'))


    def test_stap2_foutjes(self):
        self.e2e_login(self.account_sporter)

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            # GET zonder data van stap2
            self.prep.heeft_data_stap1 = False
            self.prep.save()

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap2)
            self.assert404(resp, 'Onvolledige verzoek (2)')

            # GET zonder SpeldenAanvraagPrep
            self.prep.delete()
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap2)
            self.assert404(resp, 'Onvolledige verzoek (1)')

    def test_stap2(self):
        self.e2e_login(self.account_sporter)

        with override_settings(TOON_SPELDEN_BESTELLEN=False):
            resp = self.client.get(self.url_bestel_stap2)
        self.assert404(resp, 'Bestellen is niet mogelijk')

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            # GET, discipline outdoor
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap2)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap2.dtl', 'design/site_layout.dtl'))

            # GET, discipline veld + wedstrijd gekozen
            self.prep.discipline = 'VE'
            self.prep.wedstrijd = self.wedstrijd
            self.prep.informatie_wedstrijd = 'Plaats|Land'
            self.prep.save()
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap2)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap2.dtl', 'design/site_layout.dtl'))

            # post met geen wedstrijd + land en plaats
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap2, {'plaats': 'Test1', 'land': 'Test2'})
            self.assert_is_redirect(resp, self.url_bestel_stap3)
            self.prep.refresh_from_db()
            self.assertEqual(self.prep.informatie_wedstrijd, 'Test1|Test2')

            # post met wedstrijd
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap2, {'wedstrijd': 'wed_%s' % self.wedstrijd.pk})
            self.assert404(resp, 'Wedstrijd niet gevonden')

            self.prep.discipline = self.wedstrijd.discipline  # werkt omdat WEDSTRIJD_DISCIPLINE* == SPELD_DISCIPLINE*
            self.prep.save()
            self.locatie.plaats = 'Boogstad'
            self.locatie.save()
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap2, {'wedstrijd': 'wed_%s' % self.wedstrijd.pk})
            self.assert_is_redirect(resp, self.url_bestel_stap3)
            self.prep.refresh_from_db()
            self.assertEqual(self.prep.wedstrijd_id, self.wedstrijd.pk)
            self.assertEqual(self.prep.informatie_wedstrijd, 'Boogstad|Nederland')


# end of file
