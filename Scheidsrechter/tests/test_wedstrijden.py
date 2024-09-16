# -*- coding: utf-8 -*-
import datetime

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import SCHEIDS_BOND, SCHEIDS_VERENIGING
from BasisTypen.models import KalenderWedstrijdklasse
from Functie.models import Functie
from Locatie.models import WedstrijdLocatie, Reistijd
from Mailer.models import MailQueue
from Scheidsrechter.definities import BESCHIKBAAR_JA, BESCHIKBAAR_NEE, BESCHIKBAAR_DENK
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsBeschikbaarheid, ScheidsMutatie
from Sporter.models import Sporter
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, ORGANISATIE_IFAA
from Wedstrijden.models import WedstrijdSessie, Wedstrijd
from datetime import timedelta


class TestScheidsrechterWedstrijden(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; module Overzicht """

    test_after = ('Account',)

    url_overzicht = '/scheidsrechter/'
    url_wedstrijden = '/scheidsrechter/wedstrijden/'
    url_wedstrijd_details = '/scheidsrechter/wedstrijden/%s/details/'                            # wedstrijd_pk
    url_wedstrijd_cs_koppel_sr = '/scheidsrechter/wedstrijden/%s/kies-scheidsrechters/'          # wedstrijd_pk
    url_wedstrijd_hwl_contact = '/scheidsrechter/wedstrijden/%s/geselecteerde-scheidsrechters/'  # wedstrijd_pk
    url_beschikbaarheid_opvragen = '/scheidsrechter/beschikbaarheid-opvragen/'

    testdata = None
    ver = None

    sr3_met_account = None

    lijst_hsr = list()
    lijst_sr = list()

    hsr_beschikbaar_pk = 0
    hsr_scheids_pk = 0
    hsr_niet_beschikbaar_pk = 0
    sr_niet_beschikbaar_pk = 0

    lijst_sr_beschikbaar_pk = list()
    lijst_sr_scheids_pk = list()

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()

        cls.ver = data.vereniging[data.ver_nrs[0]]

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:             # pragma: no branch
            if sporter.account is not None:
                cls.sr3_met_account = sporter
                sporter.adres_lat = 'sr3_lat'
                sporter.adres_lon = 'sr3_lon'
                sporter.save(update_fields=['adres_lat', 'adres_lon'])
                break
        # for

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:             # pragma: no branch
            if sporter.account is not None:
                cls.lijst_hsr.append(sporter)
                if len(cls.lijst_hsr) == 5:
                    break
        # for

        for sporter in data.sporters_scheids[SCHEIDS_VERENIGING]:       # pragma: no branch
            if sporter.account is not None:
                cls.lijst_sr.append(sporter)
        # for

    def setUp(self):
        """ initialisatie van de test case """
        self.assertIsNotNone(self.sr3_met_account)
        self.functie_cs = Functie.objects.get(rol='CS')
        self.functie_cs.bevestigde_email = 'cs@khsn.not'
        self.functie_cs.save(update_fields=['bevestigde_email'])

        now = timezone.now()
        datum = now.date()      # pas op met testen ronde 23:59

        self.functie_hwl, _ = Functie.objects.get_or_create(rol='HWL', vereniging=self.ver)

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres='Schietweg 1\n1234 AB Boogdrop',
                        plaats='Boogdrop',
                        adres_lat='loc_lat',
                        adres_lon='loc_lon')
        locatie.save()
        locatie.verenigingen.add(self.ver)
        self.locatie = locatie

        sessie = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    max_sporters=50)
        sessie.save()
        # sessie.wedstrijdklassen.add()

        # maak een kalenderwedstrijd aan, met sessie
        wedstrijd = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum, # + timedelta(days=1),
                        locatie=locatie,
                        organiserende_vereniging=self.ver,
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00,
                        aantal_scheids=2,
                        contact_email='org@ver.not',
                        contact_telefoon='+31234567890',
                        contact_naam='De Organisator')
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        # wedstrijd.boogtypen.add()

        klasse = KalenderWedstrijdklasse.objects.first()
        sessie.wedstrijdklassen.add(klasse)

        self.wedstrijd = wedstrijd

    def test_anon(self):
        resp = self.client.get(self.url_wedstrijden)
        self.assert_is_redirect_login(resp, self.url_wedstrijden)

        url = self.url_wedstrijd_details % self.wedstrijd.pk
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, url)

        url = self.url_wedstrijd_cs_koppel_sr % self.wedstrijd.pk
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, url)

        url = self.url_wedstrijd_hwl_contact % self.wedstrijd.pk
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, url)

    def test_sr3(self):
        self.e2e_login(self.sr3_met_account.account)

        # zet de reistijd
        Reistijd(vanaf_lat='sr3_lat',
                 vanaf_lon='sr3_lon',
                 naar_lat=self.locatie.adres_lat,
                 naar_lon=self.locatie.adres_lon,
                 reistijd_min=42).save()

        # wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijden.dtl', 'plein/site_layout.dtl'))

        # wedstrijd details
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        self.locatie.adres_uit_crm = True
        self.locatie.save(update_fields=['adres_uit_crm'])

        # maak een meerdaagse wedstrijd
        self.wedstrijd.datum_einde += datetime.timedelta(days=1)
        self.wedstrijd.organisatie = ORGANISATIE_IFAA
        self.wedstrijd.aantal_scheids = 1
        self.wedstrijd.save(update_fields=['datum_einde', 'organisatie', 'aantal_scheids'])

        # wedstrijd details
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # verwijder de knop om de kaart te tonen
        self.locatie.plaats = '(diverse)'
        self.locatie.save(update_fields=['plaats'])

        # wedstrijd details
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # corner case
        resp = self.client.get(self.url_wedstrijd_details % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)
        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijd_details % 999999)

    def test_cs_opvragen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijden.dtl', 'plein/site_layout.dtl'))

        # wedstrijd details
        url = self.url_wedstrijd_cs_koppel_sr % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # controleer dat notificaties nog niet gestuurd kunnen worden
        self.assertFalse('Stuur notificatie e-mails' in resp.content.decode('utf-8'))

        # beschikbaarheid opvragen
        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk, 'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.verwerk_scheids_mutaties()
        self.assertEqual(1, WedstrijdDagScheidsrechters.objects.count())

        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_scheidsrechter/beschikbaarheid-opgeven.dtl')
        self.assert_consistent_email_html_text(mail)

        # wedstrijd details (beschikbaarheid opgevraagd)
        url = self.url_wedstrijd_cs_koppel_sr % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # wijzig het aantal benodigde scheidsrechters
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 5})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd.pk)
        self.assertEqual(5, wedstrijd.aantal_scheids)

        # corner cases
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 99})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd.pk)
        self.assertEqual(5, wedstrijd.aantal_scheids)       # no change

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 'X'})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd.pk)
        self.assertEqual(1, wedstrijd.aantal_scheids)       # default

        resp = self.client.get(self.url_wedstrijd_cs_koppel_sr % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(self.url_wedstrijd_cs_koppel_sr % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        self.wedstrijd.locatie.adres_uit_crm = True
        self.wedstrijd.locatie.save(update_fields=['adres_uit_crm'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        self.wedstrijd.locatie.plaats = '(diverse)'
        self.wedstrijd.locatie.save(update_fields=['plaats'])
        self.wedstrijd.organisatie = ORGANISATIE_IFAA
        self.wedstrijd.save(update_fields=['organisatie'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijd_cs_koppel_sr % 999999, post=False)

    def _zet_beschikbaarheid(self, wedstrijd, dag_offset):
        datum = wedstrijd.datum_begin + timedelta(days=dag_offset)
        keuzes = [BESCHIKBAAR_JA, BESCHIKBAAR_NEE, BESCHIKBAAR_DENK]
        keuze_nr = 0

        for sr in self.lijst_hsr:
            opgaaf = keuzes[keuze_nr]
            keuze_nr = (keuze_nr + 1) % len(keuzes)

            beschikbaar = ScheidsBeschikbaarheid(
                                    scheids=sr,
                                    wedstrijd=wedstrijd,
                                    datum=datum,
                                    opgaaf=opgaaf)
            beschikbaar.save()

            if opgaaf == BESCHIKBAAR_JA:
                self.hsr_beschikbaar_pk = beschikbaar.pk
                self.hsr_scheids_pk = sr.pk

            if opgaaf == BESCHIKBAAR_NEE:
                self.hsr_niet_beschikbaar_pk = beschikbaar.pk
        # for

        self.lijst_sr_beschikbaar_pk = list()
        for sr in self.lijst_sr:
            opgaaf = keuzes[keuze_nr]
            keuze_nr = (keuze_nr + 1) % len(keuzes)

            beschikbaar = ScheidsBeschikbaarheid(
                                    scheids=sr,
                                    wedstrijd=wedstrijd,
                                    datum=datum,
                                    opgaaf=opgaaf)
            beschikbaar.save()

            if opgaaf == BESCHIKBAAR_JA:
                self.lijst_sr_beschikbaar_pk.append(beschikbaar.pk)
                self.lijst_sr_scheids_pk.append(sr.pk)
            if opgaaf == BESCHIKBAAR_NEE:
                self.sr_niet_beschikbaar_pk = beschikbaar.pk
        # for

    def test_cs_kies_sr(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid opvragen
        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk, 'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)

        self.verwerk_scheids_mutaties()
        self.assertEqual(1, WedstrijdDagScheidsrechters.objects.count())
        dag = WedstrijdDagScheidsrechters.objects.first()

        MailQueue.objects.all().delete()

        # geeft SR beschikbaarheid in
        self._zet_beschikbaarheid(self.wedstrijd, 0)

        # corner case: scheidsrechter zonder account
        sr = Sporter.objects.get(pk=self.lijst_sr_scheids_pk[1])
        sr.account = None
        sr.save(update_fields=['account'])

        url = self.url_wedstrijd_cs_koppel_sr % self.wedstrijd.pk

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # maak keuzes
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                          'hsr_0':  self.hsr_beschikbaar_pk,
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[0]: 'ja',
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[1]: 'ja',
                                          'sr_0_%s' % self.hsr_beschikbaar_pk: 'ja'})        # dubbele keuze: hsr + sr
        self.assert_is_redirect(resp, self.url_wedstrijden)
        dag = WedstrijdDagScheidsrechters.objects.get(pk=dag.pk)
        self.assertEqual(dag.gekozen_hoofd_sr.pk, self.hsr_scheids_pk)
        self.assertEqual(dag.gekozen_sr1.pk, self.lijst_sr_scheids_pk[0])
        self.assertEqual(dag.gekozen_sr2.pk, self.lijst_sr_scheids_pk[1])
        self.assertIsNone(dag.gekozen_sr3)

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # controleer dat notificaties verstuurd kunnen worden
        self.assertTrue('Stuur notificatie e-mails' in resp.content.decode('utf-8'))

        self.assertEqual(0, MailQueue.objects.count())
        Taak.objects.all().delete()
        self.assertEqual(0, dag.notified_srs.count())

        # stuur notificaties
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'notify': 'J', 'snel': 1})
        self.assert_is_redirect(resp, self.url_wedstrijden)

        f1, f2 = self.verwerk_scheids_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # controleer dat 3 scheidsrechters gekozen zijn en maar 2 een mailtje krijgen
        dag.refresh_from_db()
        self.assertEqual(2, dag.notified_srs.count())

        self.assertEqual(2, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_scheidsrechter/voor-wedstrijddag-gekozen.dtl')
        self.assert_consistent_email_html_text(mail)

        self.assertEqual(1, Taak.objects.count())
        taak = Taak.objects.first()
        self.assertEqual(taak.toegekend_aan_functie.rol, "HWL")
        self.assertEqual(taak.toegekend_aan_functie.vereniging, self.ver)

        # niet meer beschikbaar maken
        beschikbaar = ScheidsBeschikbaarheid(pk=self.hsr_beschikbaar_pk)
        beschikbaar.opgaaf = BESCHIKBAAR_NEE
        beschikbaar.save(update_fields=['opgaaf'])

        beschikbaar = ScheidsBeschikbaarheid(pk=self.lijst_sr_beschikbaar_pk[1])
        beschikbaar.opgaaf = BESCHIKBAAR_DENK
        beschikbaar.save(update_fields=['opgaaf'])

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        beschikbaar = ScheidsBeschikbaarheid(pk=self.lijst_sr_beschikbaar_pk[1])
        beschikbaar.opgaaf = BESCHIKBAAR_NEE
        beschikbaar.save(update_fields=['opgaaf'])

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # keuze uitzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                          'hsr_0':  'geen'})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        dag.refresh_from_db()
        self.assertIsNone(dag.gekozen_hoofd_sr)
        self.assertIsNone(dag.gekozen_sr1)
        self.assertIsNone(dag.gekozen_sr2)
        self.assertEqual(2, dag.notified_srs.count())

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # controleer dat notificaties verstuurd kunnen worden
        self.assertTrue('Stuur notificatie e-mails' in resp.content.decode('utf-8'))

        # stuur notificaties
        ScheidsMutatie.objects.all().delete()       # verwijder oude, ivm speed limiter
        MailQueue.objects.all().delete()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'notify': 'J', 'snel': 1})
        self.assert_is_redirect(resp, self.url_wedstrijden)

        self.verwerk_scheids_mutaties()

        # controleer dat 2 scheidsrechters een mailtje krijgen
        dag.refresh_from_db()
        self.assertEqual(0, dag.notified_srs.count())

        self.assertEqual(2, MailQueue.objects.count())
        # TODO: niet gesorteerd, dus risico verkeerde mail
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_scheidsrechter/voor-wedstrijddag-niet-meer-nodig.dtl')
        self.assert_consistent_email_html_text(mail)

        # corner cases
        resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                      'hsr_0': 999999})
        self.assert404(resp, 'Slechte parameter (1)')

    def test_hwl_ziet_gekozen_srs(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijd_hwl_contact % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-hwl-contact.dtl', 'plein/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid opvragen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk, 'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)

        self.verwerk_scheids_mutaties()
        self.assertEqual(1, WedstrijdDagScheidsrechters.objects.count())
        dag = WedstrijdDagScheidsrechters.objects.first()

        # geeft SR beschikbaarheid in
        self._zet_beschikbaarheid(self.wedstrijd, 0)

        # maak keuzes
        url = self.url_wedstrijd_cs_koppel_sr % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                          'hsr_0':  self.hsr_beschikbaar_pk,
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[0]: 'ja',
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[1]: 'ja',
                                          'sr_0_%s' % self.hsr_beschikbaar_pk: 'ja'})        # dubbele keuze: hsr + sr
        self.assert_is_redirect(resp, self.url_wedstrijden)

        # stuur notificaties
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'notify': 'J', 'snel': 1})
        self.assert_is_redirect(resp, self.url_wedstrijden)

        self.verwerk_scheids_mutaties()

        # toon contact pagina: WedstrijdDagScheidsrechters zijn er nu wel
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijd_hwl_contact % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-hwl-contact.dtl', 'plein/site_layout.dtl'))

        dag.refresh_from_db()
        dag.gekozen_hoofd_sr = None
        dag.save(update_fields=['gekozen_hoofd_sr'])

        self.wedstrijd.aantal_scheids = 1
        self.wedstrijd.save(update_fields=['aantal_scheids'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijd_hwl_contact % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-hwl-contact.dtl', 'plein/site_layout.dtl'))

        # corner cases
        self.wedstrijd.aantal_scheids = 0
        self.wedstrijd.save(update_fields=['aantal_scheids'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijd_hwl_contact % self.wedstrijd.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-hwl-contact.dtl', 'plein/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_wedstrijd_hwl_contact % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        ver2 = self.testdata.vereniging[self.testdata.ver_nrs[1]]
        self.wedstrijd.organiserende_vereniging = ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        resp = self.client.get(self.url_wedstrijd_hwl_contact % self.wedstrijd.pk)
        self.assert404(resp, 'Verkeerde beheerder')

    def test_sr_ziet_gekozen_sr(self):
        # kijk als sporter naar de wedstrijd pagina: gekozen scheidsrechters worden getoond
        self.e2e_login(self.sr3_met_account.account)

        # geen sr gekozen; geen beschikbaarheid opgevraagd
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid opvragen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')
        resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk, 'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)

        self.verwerk_scheids_mutaties()

        # geeft SR beschikbaarheid in
        self._zet_beschikbaarheid(self.wedstrijd, 0)

        # kijk als sporter naar de wedstrijd pagina: gekozen scheidsrechters worden getoond
        self.e2e_login(self.sr3_met_account.account)

        # geen sr gekozen; beschikbaarheid opgevraagd
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # maak keuzes
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        url = self.url_wedstrijd_cs_koppel_sr % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                          'hsr_0':  self.hsr_beschikbaar_pk,
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[0]: 'ja',
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[1]: 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden)

        # kijk als sporter naar de wedstrijd pagina: gekozen scheidsrechters worden getoond
        self.e2e_login(self.sr3_met_account.account)

        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))


# end of file
