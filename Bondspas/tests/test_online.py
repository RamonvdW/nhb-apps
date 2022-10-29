# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Sporter.models import Sporter, SporterVoorkeuren, GESLACHT_ANDERS
from NhbStructuur.models import NhbVereniging, NhbRegio
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestBondspas(E2EHelpers, TestCase):

    """ tests voor de Bondspas applicatie """

    url_toon = '/sporter/bondspas/toon/'

    def setUp(self):

        self.lid_nr = 123456

        now = datetime.datetime.now()

        # maak een test vereniging
        self.nhbver1 = NhbVereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=NhbRegio.objects.get(regio_nr=112))
        self.nhbver1.save()

        self.sporter = sporter = Sporter(
                                    lid_nr=self.lid_nr,
                                    voornaam='Tester',
                                    achternaam='De tester',
                                    unaccented_naam='test',
                                    email='tester@mail.not',
                                    geboorte_datum=datetime.date(year=now.year - 55, month=3, day=4),
                                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                                    geslacht='M',
                                    bij_vereniging=self.nhbver1,
                                    lid_tot_einde_jaar=now.year)
        self.account = self.e2e_create_account(self.lid_nr, sporter.email, sporter.voornaam)
        sporter.account = self.account
        sporter.save()

    def test_toon(self):
        # anon
        resp = self.client.get(self.url_toon)
        self.assert403(resp)

        # sporter
        self.e2e_login(self.account)

        now = datetime.datetime.now()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-tonen.dtl', 'plein/site_layout.dtl'))

        # speciaal geval: jarig op 1 januari
        # speciaal geval: geslacht X
        # speciaal geval: geen vereniging
        # speciaal: NHB leeftijdsklassen die anders is dan WA: 60
        self.sporter.geboorte_datum = '%4d-01-01' % (now.year - 60)
        self.sporter.geslacht = GESLACHT_ANDERS
        self.sporter.bij_vereniging = None
        self.sporter.save(update_fields=['geboorte_datum', 'geslacht', 'bij_vereniging'])

        voorkeuren = SporterVoorkeuren.objects.get(sporter=self.sporter)
        voorkeuren.wedstrijd_geslacht_gekozen = False
        voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-tonen.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_toon)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bondspas/bondspas-tonen.dtl', 'plein/site_layout.dtl'))


        self.e2e_assert_other_http_commands_not_supported(self.url_toon)


# end of file
