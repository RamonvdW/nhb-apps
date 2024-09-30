# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import SCHEIDS_BOND, SCHEIDS_VERENIGING
from Competitie.models import CompetitieMatch, CompetitieIndivKlasse, CompetitieTeamKlasse
from Functie.models import Functie
from Locatie.models import WedstrijdLocatie
from Mailer.models import MailQueue
from Scheidsrechter.definities import BESCHIKBAAR_JA, BESCHIKBAAR_NEE, BESCHIKBAAR_DENK
from Scheidsrechter.models import MatchScheidsrechters, ScheidsBeschikbaarheid, ScheidsMutatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Wedstrijden.models import Wedstrijd
from datetime import timedelta


class TestScheidsrechterCompetitie(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; module Competitie """

    test_after = ('Account',)

    url_overzicht = '/scheidsrechter/'
    url_matches = '/scheidsrechter/bondscompetitie/'
    url_match_details = '/scheidsrechter/bondscompetitie/%s/details/'                            # match_pk
    url_match_cs_koppel_sr = '/scheidsrechter/bondscompetitie/%s/kies-scheidsrechters/'          # match_pk
    url_match_hwl_contact = '/scheidsrechter/bondscompetitie/%s/geselecteerde-scheidsrechters/'  # match_pk
    url_beschikbaarheid_opvragen = '/scheidsrechter/bondscompetitie/beschikbaarheid-opvragen/'   # match_pk

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
        data.maak_bondscompetities()

        cls.ver1 = data.vereniging[data.ver_nrs[0]]
        cls.ver2 = data.vereniging[data.ver_nrs[1]]

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

        self.functie_hwl1, _ = Functie.objects.get_or_create(rol='HWL', vereniging=self.ver1)
        self.functie_hwl2, _ = Functie.objects.get_or_create(rol='HWL', vereniging=self.ver2)

        locatie1 = WedstrijdLocatie(
                        naam='Test locatie 1',
                        discipline_indoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=18,
                        adres='Schietweg 1\n1234 AB Boogdrop',
                        plaats='Boogdrop',
                        adres_lat='loc_lat',
                        adres_lon='loc_lon',
                        adres_uit_crm=True)
        locatie1.save()
        locatie1.verenigingen.add(self.ver1)
        self.locatie1 = locatie1

        locatie2 = WedstrijdLocatie(
                        naam='Test locatie 2',
                        discipline_indoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=25,
                        adres='Schietweg 2\n1234 AB Boogdrop',
                        plaats='Boogdrop',
                        adres_lat='loc_lat',
                        adres_lon='loc_lon',
                        adres_uit_crm=False)
        locatie2.save()
        locatie2.verenigingen.add(self.ver2)
        self.locatie2 = locatie2

        indiv = CompetitieIndivKlasse.objects.filter(competitie=self.testdata.comp18, is_ook_voor_rk_bk=True)[:2]
        teams = CompetitieTeamKlasse.objects.filter(competitie=self.testdata.comp18, is_voor_teams_rk_bk=True)[:2]

        match_bk = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='BK, 2023/2024',
                        datum_wanneer=self.testdata.comp18.begin_fase_P_indiv,
                        tijd_begin_wedstrijd='10:00',
                        vereniging=self.ver1,
                        locatie=self.locatie1,
                        aantal_scheids=2)
        match_bk.save()
        match_bk.indiv_klassen.set(indiv)
        self.match_bk = match_bk

        # nog een BK wedstrijd
        match_bk = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='BK, 2023/2024',
                        datum_wanneer=self.testdata.comp18.begin_fase_P_indiv,
                        tijd_begin_wedstrijd='10:00',
                        vereniging=self.ver2,
                        locatie=None,
                        aantal_scheids=1)
        match_bk.save()
        self.match_bk2 = match_bk

        match_rk = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='RK Rayon 1, 2023/2024',
                        datum_wanneer=self.testdata.comp18.begin_fase_L_indiv,
                        tijd_begin_wedstrijd='10:00',
                        vereniging=self.ver2,
                        locatie=self.locatie2,
                        aantal_scheids=1)
        match_rk.save()
        match_rk.team_klassen.set(teams)
        self.match_rk = match_rk

        # nog een RK match op dezelfde datum
        match_rk = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='RK Rayon 1, 2023/2024',
                        datum_wanneer=self.testdata.comp18.begin_fase_L_indiv,
                        tijd_begin_wedstrijd='10:00',
                        vereniging=self.ver2,
                        locatie=None,
                        aantal_scheids=1)
        match_rk.save()

    def test_anon(self):
        resp = self.client.get(self.url_matches)
        self.assert_is_redirect_login(resp, self.url_matches)

        url = self.url_match_details % self.match_rk.pk
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, url)

        url = self.url_match_cs_koppel_sr % self.match_rk.pk
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, url)

        url = self.url_match_hwl_contact % self.match_rk.pk
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, url)

    def test_sr(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid opvragen
        ScheidsMutatie.objects.all().delete()       # voorkom blokkade door recent verzoek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        f1, f2 = self.verwerk_scheids_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        match_sr = MatchScheidsrechters.objects.get(match=self.match_bk)
        self.assertIsNone(match_sr.gekozen_hoofd_sr)
        self.assertIsNone(match_sr.gekozen_sr1)
        self.assertIsNone(match_sr.gekozen_sr2)

        self.e2e_login(self.sr3_met_account.account)

        # bondscompetitie wedstrijden (matches)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # haal de details op van een match op (locatie met adres uit CRM)
        url = self.url_match_details % self.match_rk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-details.dtl', 'plein/site_layout.dtl'))

        # koppel een HWL
        self.functie_hwl1.accounts.add(self.lijst_hsr[0].account)

        # koppel een SR
        match_sr.gekozen_hoofd_sr = self.sr3_met_account
        match_sr.save(update_fields=['gekozen_hoofd_sr'])

        # haal de details op van een match op (locatie dat niet uit CRM komt)
        url = self.url_match_details % self.match_bk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-details.dtl', 'plein/site_layout.dtl'))

        # corner-case: geen HWL
        self.functie_hwl1.delete()
        url = self.url_match_details % self.match_bk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-details.dtl', 'plein/site_layout.dtl'))

        # corner-cases
        resp = self.client.get(self.url_match_details % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_cs_opvragen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # bondscompetitie wedstrijden (matches)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # controleer dat notificaties nog niet gestuurd kunnen worden
        self.assertFalse('Stuur notificatie e-mails' in resp.content.decode('utf-8'))

        # beschikbaarheid opvragen
        self.assertEqual(0, MatchScheidsrechters.objects.count())
        self.assertEqual(0, MailQueue.objects.count())
        self.assertEqual(0, Wedstrijd.objects.count())
        ScheidsMutatie.objects.all().delete()       # voorkom blokkade door recent verzoek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        f1, f2 = self.verwerk_scheids_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        # zijn nu 2 wedstrijden aangemaakt: RK en BK
        self.assertEqual(2, Wedstrijd.objects.count())
        self.assertEqual(4, MatchScheidsrechters.objects.count())

        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_scheidsrechter/beschikbaarheid-opgeven.dtl')
        self.assert_consistent_email_html_text(mail)

        # competitiematches; beschikbaarheid is al opgevraagd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # wijzig de datum-reeks voor het RK
        self.match_rk.datum_wanneer += timedelta(days=1)
        self.match_rk.save(update_fields=['datum_wanneer'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # verwerk wijziging
        ScheidsMutatie.objects.all().delete()       # voorkom blokkade door recent verzoek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        f1, f2 = self.verwerk_scheids_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # wijzig de datum-reeks voor het BK
        self.match_bk.datum_wanneer += timedelta(days=1)
        self.match_bk.save(update_fields=['datum_wanneer'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # verwerk wijziging
        ScheidsMutatie.objects.all().delete()       # voorkom blokkade door recent verzoek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        f1, f2 = self.verwerk_scheids_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # corner case: RK wedstrijden zijn verwijderd
        Wedstrijd.objects.filter(titel__startswith='RK').delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # verwerk wijziging
        ScheidsMutatie.objects.all().delete()       # voorkom blokkade door recent verzoek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        f1, f2 = self.verwerk_scheids_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # corner case: BK wedstrijden zijn verwijderd
        Wedstrijd.objects.filter(titel__startswith='BK').delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # corner-case: geen BK matches
        CompetitieMatch.objects.filter(beschrijving__startswith='BK').delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # corner-case: geen RK matches
        CompetitieMatch.objects.filter(beschrijving__startswith='RK').update(beschrijving='BK test')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

        # corner-case: geen matches (meer)
        CompetitieMatch.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_matches)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/matches.dtl', 'plein/site_layout.dtl'))

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

            elif opgaaf == BESCHIKBAAR_NEE:
                self.sr_niet_beschikbaar_pk = beschikbaar.pk
        # for

    def test_cs_kies_sr(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # match BK details zonder wedstrijd
        url = self.url_match_cs_koppel_sr % self.match_bk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # post zonder MatchScheidsrechters
        resp = self.client.post(url, {'aantal_scheids': '#'})   # ValueError
        self.assert_is_redirect(resp, self.url_matches)

        resp = self.client.post(url, {'aantal_scheids': 1})     # 1 = geen wijziging
        self.assert_is_redirect(resp, self.url_matches)

        resp = self.client.post(url, {'aantal_scheids': 0})     # 0 = out of range
        self.assert_is_redirect(resp, self.url_matches)

        # match RK details zonder wedstrijd, adres niet uit CRM
        url = self.url_match_cs_koppel_sr % self.match_rk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid opvragen
        ScheidsMutatie.objects.all().delete()       # voorkom blokkade door recent verzoek
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        f1, f2 = self.verwerk_scheids_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        # zijn nu 2 wedstrijden aangemaakt: RK en BK
        self.assertEqual(2, Wedstrijd.objects.count())
        self.assertEqual(4, MatchScheidsrechters.objects.count())

        match_sr = MatchScheidsrechters.objects.get(match=self.match_bk)
        self.assertIsNone(match_sr.gekozen_hoofd_sr)
        self.assertIsNone(match_sr.gekozen_sr1)
        self.assertIsNone(match_sr.gekozen_sr2)

        # match details met wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # koppel een HWL
        self.functie_hwl2.accounts.add(self.lijst_hsr[0].account)

        # match details met wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # geeft SR beschikbaarheid op
        wedstrijd = Wedstrijd.objects.get(titel__startswith='BK')
        self._zet_beschikbaarheid(wedstrijd, 0)

        url = self.url_match_cs_koppel_sr % self.match_bk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        obj_ja = ScheidsBeschikbaarheid.objects.filter(wedstrijd=wedstrijd, opgaaf=BESCHIKBAAR_JA).first()
        obj_denk = ScheidsBeschikbaarheid.objects.filter(wedstrijd=wedstrijd, opgaaf=BESCHIKBAAR_DENK).first()

        # maak keuzes
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 1,
                                          'hsr': '',
                                          'sr_%s' % obj_ja.pk: 'Ja'})
        self.assert_is_redirect(resp, self.url_matches)

        match_sr.refresh_from_db()
        self.assertIsNone(match_sr.gekozen_hoofd_sr)
        self.assertIsNotNone(match_sr.gekozen_sr1)
        self.assertEqual(match_sr.gekozen_sr1.pk, obj_ja.scheids.pk)
        self.assertIsNone(match_sr.gekozen_sr2)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # bekijk de andere BK wedstrijd op dezelfde dag - de gekozen hoofd-SR is nu "bezet"
        url2 = self.url_match_cs_koppel_sr % self.match_bk2.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url2)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        # kies een andere hoofd-sr die niet meer beschikbaar is
        match_sr.refresh_from_db()
        match_sr.gekozen_hoofd_sr = obj_denk.scheids
        match_sr.gekozen_sr1 = obj_denk.scheids
        match_sr.save(update_fields=['gekozen_hoofd_sr', 'gekozen_sr1'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        resp = self.client.post(url, {'aantal_scheids': 2,
                                      'hsr': '#',
                                      'sr_%s' % obj_ja.pk: 'Ja'})
        self.assert404(resp, 'Slechte parameter (1)')

        # maak keuzes
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 2,
                                          'hsr': obj_ja.pk,
                                          'sr_%s' % obj_ja.pk: 'Ja'})
        self.assert_is_redirect(resp, self.url_matches)

        match_sr.refresh_from_db()
        self.assertIsNotNone(match_sr.gekozen_hoofd_sr)
        self.assertEqual(match_sr.gekozen_hoofd_sr.pk, obj_ja.scheids.pk)
        self.assertIsNone(match_sr.gekozen_sr1)
        self.assertIsNone(match_sr.gekozen_sr2)

        # maak keuzes
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 1,
                                          'hsr': 'geen',
                                          'sr_%s' % obj_ja.pk: 'Ja'})
        self.assert_is_redirect(resp, self.url_matches)

        # corner-case: geen HWL
        self.functie_hwl2.delete()

        # datum match buiten range wedstrijd
        self.match_rk.datum_wanneer -= timedelta(days=14)
        self.match_rk.save(update_fields=['datum_wanneer'])
        url = self.url_match_cs_koppel_sr % self.match_rk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-cs-kies-sr.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 1})
        self.assert_is_redirect(resp, self.url_matches)

        # corner cases
        resp = self.client.get(self.url_match_cs_koppel_sr % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(self.url_match_cs_koppel_sr % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_hwl_ziet_gekozen_srs(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_hwl1)
        self.e2e_check_rol('HWL')

        resp = self.client.get(self.url_match_hwl_contact % self.match_rk.pk)
        self.assert404(resp, 'Verkeerde beheerder')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_match_hwl_contact % self.match_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-hwl-contact.dtl', 'plein/site_layout.dtl'))

        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid opvragen
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)

        self.verwerk_scheids_mutaties()
        self.assertEqual(4, MatchScheidsrechters.objects.count())       # 1 per match

        wedstrijd = Wedstrijd.objects.get(titel__startswith='BK')
        self._zet_beschikbaarheid(wedstrijd, 0)

        obj_ja = ScheidsBeschikbaarheid.objects.filter(wedstrijd=wedstrijd, opgaaf=BESCHIKBAAR_JA).first()
        match_sr = MatchScheidsrechters.objects.get(match=self.match_bk)
        match_sr.gekozen_hoofd_sr = obj_ja.scheids
        match_sr.save(update_fields=['gekozen_hoofd_sr'])

        # maak keuzes
        url = self.url_match_cs_koppel_sr % self.match_bk.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.match_bk.aantal_scheids,
                                          'hsr':  self.hsr_beschikbaar_pk,
                                          'sr_%s' % self.lijst_sr_beschikbaar_pk[0]: 'ja',
                                          'sr_%s' % self.lijst_sr_beschikbaar_pk[1]: 'ja',
                                          'sr_%s' % self.hsr_beschikbaar_pk: 'ja'})        # dubbele keuze: hsr + sr
        self.assert_is_redirect(resp, self.url_matches)

        # stuur notificaties
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'notify': 'J', 'snel': 1})
        self.assert_is_redirect(resp, self.url_matches)

        self.verwerk_scheids_mutaties()

        # toon contact pagina: MatchScheidsrechters zijn er nu wel
        self.e2e_wissel_naar_functie(self.functie_hwl1)
        self.e2e_check_rol('HWL')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_match_hwl_contact % self.match_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-hwl-contact.dtl', 'plein/site_layout.dtl'))

        # corner cases
        self.match_bk.aantal_scheids = 0
        self.match_bk.save(update_fields=['aantal_scheids'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_match_hwl_contact % self.match_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/match-hwl-contact.dtl', 'plein/site_layout.dtl'))

        resp = self.client.get(self.url_match_hwl_contact % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')


# end of file
