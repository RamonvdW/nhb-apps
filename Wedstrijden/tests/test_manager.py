# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Mailer.models import MailQueue
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.models import Wedstrijd


class TestWedstrijdenManager(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Manager """

    url_wedstrijden_manager = '/wedstrijden/manager/'
    url_wedstrijden_manager_geannuleerd = '/wedstrijden/manager/geannuleerd/'
    url_wedstrijden_vereniging = '/wedstrijden/vereniging/lijst/'
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijden_wijzig_wedstrijd = '/wedstrijden/%s/wijzig/'  # wedstrijd_pk
    url_wedstrijden_zet_status = '/wedstrijden/%s/zet-status/'    # wedstrijd_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        # geef de vereniging een locatie
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.ver1)

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        self.ver2 = Vereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver2.save()

        self.functie_cs = maak_functie('Commissie Scheidsrechters', 'CS')
        self.functie_cs.bevestigde_email = 'cs@khsn.not'
        self.functie_cs.save(update_fields=['bevestigde_email'])

    @staticmethod
    def _maak_externe_locatie(ver):
        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(ver)

        return locatie

    def test_manager(self):
        # anon mag niet
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_manager)
        self.assert_is_redirect_not_plein(resp)

        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_manager_geannuleerd)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)

        # wissel terug naar BB
        self.e2e_wisselnaarrol_bb()

        # haal het overzicht op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        wedstrijd = Wedstrijd.objects.first()
        wedstrijd.eis_kwalificatie_scores = True
        wedstrijd.save(update_fields=['eis_kwalificatie_scores'])

        # haal het overzicht op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_manager)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/overzicht-manager.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden_manager, post=False)

    def test_zet_status(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)

        url = self.url_wedstrijden_zet_status % wedstrijd.pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)

        # doorzetten naar 'Wacht op goedkeuring'
        # mag alleen als de verkoopvoorwaarden geaccepteerd zijn
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert404(resp, 'Verkoopvoorwaarden')

        wedstrijd.verkoopvoorwaarden_status_acceptatie = True
        wedstrijd.save(update_fields=['verkoopvoorwaarden_status_acceptatie'])

        # doorzetten naar 'Wacht op goedkeuring'
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'W')

        # verkeerde vereniging
        wedstrijd.organiserende_vereniging = self.ver2
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert403(resp)

        wedstrijd.organiserende_vereniging = self.ver1
        wedstrijd.save()

        # nu als BB
        self.e2e_wisselnaarrol_bb()

        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)

        # van Wacht-op-goedkeuring terug naar Ontwerp
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'terug': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'O')

        # vanuit ontwerp blijf je in Ontwerp
        with self.assert_max_queries(20):
            resp = self.client.post(url, {})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)

        # van Ontwerp weer naar Wacht-op-goedkeuring
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'W')

        Taak.objects.all().delete()

        # van Wacht-op-goedkeuring door naar Geaccepteerd
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        self.assertEqual(1, Taak.objects.count())       # 1 voor de HWL, 0 voor CS

        # van Geaccepteerd kan je niet verder of terug
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'terug': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        # Annuleer
        for status in "OWAX":   # noqa
            wedstrijd.status = status
            wedstrijd.save()
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'annuleer': 'ja'})
            self.assert_is_redirect(resp, self.url_wedstrijden_manager)
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
            self.assertEqual(wedstrijd.status, 'X')
        # for

        # slechte wedstrijd_pk
        resp = self.client.post(self.url_wedstrijden_zet_status % 999999, {})
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_goedkeuren_met_scheids(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        # wissel naar HWL en maak een wedstrijd aan
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)

        wedstrijd.verkoopvoorwaarden_status_acceptatie = True
        wedstrijd.save(update_fields=['verkoopvoorwaarden_status_acceptatie'])

        url = self.url_wedstrijden_zet_status % wedstrijd.pk

        # doorzetten naar 'Wacht op goedkeuring'
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_vereniging)
        wedstrijd.refresh_from_db()
        self.assertEqual(wedstrijd.status, 'W')

        # wissel naar BB/MWZ
        self.e2e_wisselnaarrol_bb()

        wedstrijd.aantal_scheids = 2
        wedstrijd.save(update_fields=['aantal_scheids'])

        Taak.objects.all().delete()

        # van Wacht-op-goedkeuring door naar Geaccepteerd
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verder': 'ja'})
        self.assert_is_redirect(resp, self.url_wedstrijden_manager)
        wedstrijd = Wedstrijd.objects.get(pk=wedstrijd.pk)
        self.assertEqual(wedstrijd.status, 'A')

        self.assertEqual(2, Taak.objects.count())       # 1 voor de HWL, 1 voor CS

        mail = MailQueue.objects.filter(mail_to=self.functie_cs.bevestigde_email).first()
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

# end of file
