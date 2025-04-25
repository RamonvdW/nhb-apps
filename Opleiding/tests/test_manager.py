# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import Functie
from Geo.models import Regio
from Instaptoets.models import Vraag, Instaptoets
from Locatie.models import EvenementLocatie
from Opleiding.definities import OPLEIDING_STATUS_INSCHRIJVEN, OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF
from Opleiding.models import Opleiding, OpleidingInschrijving, OpleidingMoment
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestOpleidingManager(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit voor de MO """

    test_after = ('Account', 'Functie')

    url_manager = '/opleiding/manager/'
    url_toevoegen = '/opleiding/manager/toevoegen/'
    url_niet_ingeschreven = '/opleiding/manager/niet-ingeschreven/'
    url_wijzig_opleiding = '/opleiding/manager/wijzig/%s/'                              # opleiding_pk
    url_wijzig_moment = '/opleiding/manager/wijzig/%s/data-en-locaties/wijzig/%s/'      # opleiding_pk, moment_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        self.functie_mo = Functie.objects.get(rol='MO')
        self.functie_mo.accounts.add(self.account_normaal)

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

        now = timezone.now()
        sporter = Sporter(
                    lid_nr=100001,
                    voornaam='Thea',
                    achternaam='de Tester',
                    unaccented_naam='Thea de Tester',
                    email='normaal@test.nhb',
                    geboorte_datum="1970-11-15",
                    geboorteplaats='Pijlstad',
                    geslacht='V',
                    sinds_datum='2000-01-01',
                    telefoon='+123456789',
                    lid_tot_einde_jaar=now.year,
                    account=self.account_normaal)
        sporter.save()
        self.sporter = sporter

        ver = Vereniging(
                    ver_nr=1000,
                    naam='Groot bureau',
                    plaats='Hoofdstad',
                    regio=Regio.objects.get(regio_nr=100))
        ver.save()
        self.ver = ver

    def test_anon(self):
        self.e2e_logout()

        resp = self.client.get(self.url_manager)
        self.assert403(resp, 'Geen toegang')

        resp = self.client.get(self.url_toevoegen)
        self.assert403(resp, 'Geen toegang')

        resp = self.client.get(self.url_wijzig_opleiding % 66666)
        self.assert403(resp, 'Geen toegang')

        resp = self.client.get(self.url_wijzig_moment % (666666, 66666))
        self.assert403(resp, 'Geen toegang')

    def test_lijst(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        # lege lijst
        Opleiding.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/overzicht-manager.dtl', 'plein/site_layout.dtl'))

    def test_niet_ingeschreven(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        # iemand heeft de instaptoets gehaald, maar is niet ingeschreven
        toets = Instaptoets(
                    is_afgerond=True,
                    geslaagd=True,
                    sporter=self.sporter)
        toets.save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_niet_ingeschreven)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/niet-ingeschreven.dtl', 'plein/site_layout.dtl'))

        # nog een keer, maar nu is de sporter wel ingeschreven
        OpleidingInschrijving(
                opleiding=self.opleiding,
                sporter=self.sporter,
                status=OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                nummer=1).save()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_niet_ingeschreven)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/niet-ingeschreven.dtl', 'plein/site_layout.dtl'))

    def test_toevoegen(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        Opleiding.objects.all().delete()

        resp = self.client.post(self.url_toevoegen)
        self.assertEqual(Opleiding.objects.count(), 1)
        opleiding = Opleiding.objects.first()
        self.assertRedirects(resp, self.url_wijzig_opleiding % opleiding.pk)

    def test_wijzig_opleiding(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        bad_url = self.url_wijzig_opleiding % "xxx"
        resp = self.client.get(bad_url)
        self.assert404(resp, 'Opleiding niet gevonden')

        resp = self.client.post(bad_url)
        self.assert404(resp, 'Opleiding niet gevonden')

        url_opleiding = self.url_wijzig_opleiding % self.opleiding.pk

        # zonder moment
        with self.assert_max_queries(20):
            resp = self.client.get(url_opleiding)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/wijzig-opleiding.dtl', 'plein/site_layout.dtl'))

        # zonder parameters
        with self.assert_max_queries(20):
            resp = self.client.post(url_opleiding)
        self.assert_is_redirect(resp, self.url_manager)

        # add moment
        self.assertEqual(OpleidingMoment.objects.count(), 0)
        resp = self.client.post(url_opleiding, {'add-moment': 'y'})
        self.assertEqual(OpleidingMoment.objects.count(), 1)
        moment = OpleidingMoment.objects.first()
        url_moment = self.url_wijzig_moment % (self.opleiding.pk, moment.pk)
        self.assert_is_redirect(resp, url_moment)

        # met momenten
        OpleidingMoment().save()        # ongebruikt moment
        with self.assert_max_queries(20):
            resp = self.client.get(url_opleiding)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/wijzig-opleiding.dtl', 'plein/site_layout.dtl'))

        # wijzig parameters
        self.opleiding.refresh_from_db()
        self.assertEqual(str(self.opleiding.periode_begin), '2024-11-01')       # zie setup
        self.assertEqual(str(self.opleiding.periode_einde), '2024-12-01')       # zie setup
        self.assertEqual(self.opleiding.aantal_dagen, 1)
        self.assertFalse(self.opleiding.eis_instaptoets)
        self.assertEqual(self.opleiding.leeftijd_min, 16)
        self.assertEqual(self.opleiding.leeftijd_max, 0)
        self.assertEqual(self.opleiding.ingangseisen, '')
        self.assertEqual(self.opleiding.beschrijving, '')

        jaar = timezone.now().year
        date1 = '%04d-04-05' % jaar
        date2 = '%04d-06-07' % jaar

        with self.assert_max_queries(20):
            resp = self.client.post(url_opleiding, {'periode_begin': date1,
                                                    'periode_einde': date2,
                                                    'dagen': 3,
                                                    'uren': 20,
                                                    'beschrijving': 'opleiding beschrijving\nmeerdere regels\n',
                                                    'eis_instaptoets': 'on',
                                                    'ingangseisen': 'opleiding eisen\nmeerdere regels\n',
                                                    'leeftijd_min': 20,
                                                    'leeftijd_max': 50,
                                                    'kosten': '12.34'})
        self.assert_is_redirect(resp, self.url_manager)

        self.opleiding.refresh_from_db()
        self.assertEqual(str(self.opleiding.periode_begin), date1)
        self.assertEqual(str(self.opleiding.periode_einde), date2)
        self.assertEqual(self.opleiding.aantal_dagen, 3)
        self.assertTrue(self.opleiding.eis_instaptoets)
        self.assertEqual(self.opleiding.leeftijd_min, 20)
        self.assertEqual(self.opleiding.leeftijd_max, 50)
        self.assertEqual(self.opleiding.ingangseisen, 'opleiding eisen\nmeerdere regels\n')
        self.assertEqual(self.opleiding.beschrijving, 'opleiding beschrijving\nmeerdere regels\n')

        # bad input
        resp = self.client.post(url_opleiding, {'periode_begin': 'test',
                                                'periode_einde': 'test',
                                                'dagen': 'x',
                                                'uren': 'x',
                                                'leeftijd_min': 'x',
                                                'leeftijd_max': 'x',
                                                'kosten': 'x',
                                                'M_xx': 'x'})
        self.assert_is_redirect(resp, self.url_manager)

        # out of range
        resp = self.client.post(url_opleiding, {'periode_begin': '2099-12-31',
                                                'periode_einde': '2000-01-01'})
        self.assert_is_redirect(resp, self.url_manager)

        # moment is nu ontkoppeld
        self.assertEqual(self.opleiding.momenten.count(), 0)

        # koppel een moment
        with self.assert_max_queries(20):
            resp = self.client.post(url_opleiding, {'M_%s' % moment.pk: 'x'})
        self.assert_is_redirect(resp, self.url_manager)
        self.assertEqual(self.opleiding.momenten.count(), 1)

        # al gekoppeld
        resp = self.client.post(url_opleiding, {'M_%s' % moment.pk: 'x'})
        self.assert_is_redirect(resp, self.url_manager)
        self.assertEqual(self.opleiding.momenten.count(), 1)

    def test_wijzig_moment(self):
        self.e2e_login_and_pass_otp(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_mo)

        bad_url = self.url_wijzig_moment % (666666, 666666)
        resp = self.client.get(bad_url)
        self.assert404(resp, 'Opleiding niet gevonden')
        resp = self.client.post(bad_url)
        self.assert404(resp, 'Opleiding niet gevonden')

        bad_url = self.url_wijzig_moment % (self.opleiding.pk, 666666)
        resp = self.client.get(bad_url)
        self.assert404(resp, 'Moment niet gevonden')
        resp = self.client.post(bad_url)
        self.assert404(resp, 'Moment niet gevonden')

        # add moment
        self.assertEqual(OpleidingMoment.objects.count(), 0)
        url_opleiding = self.url_wijzig_opleiding % self.opleiding.pk
        resp = self.client.post(url_opleiding, {'add-moment': 'y'})
        self.assertEqual(OpleidingMoment.objects.count(), 1)
        moment = OpleidingMoment.objects.first()
        url_moment = self.url_wijzig_moment % (self.opleiding.pk, moment.pk)
        self.assert_is_redirect(resp, url_moment)

        locatie = EvenementLocatie(naam='test', vereniging=self.ver)
        locatie.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url_moment)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/wijzig-moment.dtl', 'plein/site_layout.dtl'))

        # wijzig periode_einde.month naar != 12
        self.opleiding.periode_einde = '2024-11-30'
        self.opleiding.save(update_fields=['periode_einde'])

        with self.assert_max_queries(20):
            resp = self.client.get(url_moment)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/wijzig-moment.dtl', 'plein/site_layout.dtl'))

        moment.refresh_from_db()
        self.assertEqual(moment.datum, self.opleiding.periode_begin)
        self.assertEqual(moment.aantal_dagen, 1)
        self.assertEqual(str(moment.begin_tijd), '10:00:00')
        self.assertEqual(moment.duur_minuten, 1)
        self.assertEqual(moment.locatie, None)
        self.assertEqual(moment.opleider_naam, '')
        self.assertEqual(moment.opleider_email, '')
        self.assertEqual(moment.opleider_telefoon, '')

        # zonder parameters
        with self.assert_max_queries(20):
            resp = self.client.post(url_moment)
        self.assert_is_redirect(resp, url_opleiding)

        # wijzigingen
        date_str = str(self.opleiding.periode_begin + datetime.timedelta(days=10))
        with self.assert_max_queries(20):
            resp = self.client.post(url_moment, {'datum': date_str,
                                                 'dagen': 3,
                                                 'begin_tijd': '12:34',
                                                 'minuten': 60,
                                                 'locatie': locatie.pk,
                                                 'naam': 'Dhr. Docent',
                                                 'email': 'docent@khsn.not',
                                                 'tel': '+777888999'})
        self.assert_is_redirect(resp, url_opleiding)

        moment.refresh_from_db()
        self.assertEqual(str(moment.datum), date_str)
        self.assertEqual(moment.aantal_dagen, 3)
        self.assertEqual(str(moment.begin_tijd), '12:34:00')
        self.assertEqual(moment.duur_minuten, 60)
        self.assertEqual(moment.locatie, locatie)
        self.assertEqual(moment.opleider_naam, 'Dhr. Docent')
        self.assertEqual(moment.opleider_email, 'docent@khsn.not')
        self.assertEqual(moment.opleider_telefoon, '+777888999')

        # out of range parameters
        with self.assert_max_queries(20):
            resp = self.client.post(url_moment, {'datum': '2000-01-01',
                                                 'dagen': 99,
                                                 'begin_tijd': '99:66',
                                                 'minuten': 999})
        self.assert_is_redirect(resp, url_opleiding)

        # bad parameters
        with self.assert_max_queries(20):
            resp = self.client.post(url_moment, {'datum': 'xxxxxx',
                                                 'dagen': 'x',
                                                 'begin_tijd': 'xx:yy',
                                                 'minuten': 'x'})
        self.assert_is_redirect(resp, url_opleiding)


# end of file
