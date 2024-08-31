# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEANNULEERD
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
import datetime


class TestWedstrijdenWijzigSessies(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module sessie wijzigen """

    url_wedstrijden_vereniging = '/wedstrijden/vereniging/'
    url_wedstrijden_sessies = '/wedstrijden/%s/sessies/'                  # wedstrijd_pk
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijden_wijzig_sessie = '/wedstrijden/%s/sessies/%s/wijzig/'  # wedstrijd_pk, sessie_pk
    url_wedstrijden_wijzig_wedstrijd = '/wedstrijden/%s/wijzig/'          # wedstrijd_pk
    url_sporter_voorkeuren = '/sporter/voorkeuren/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        self.lid_nr = 123456
        self.account = self.e2e_create_account(str(self.lid_nr), 'test@test.not', 'Voornaam')

        self.boog_r = BoogType.objects.get(afkorting='R')

        sporter = Sporter(
                    lid_nr=self.lid_nr,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    account=self.account)
        sporter.save()

        # maak een test vereniging
        self.ver1 = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver1.save()

        self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        self.functie_hwl.vereniging = self.ver1
        self.functie_hwl.accounts.add(self.account_admin)
        self.functie_hwl.save()

        # wordt HWL, stel sporter voorkeuren in en maak een wedstrijd aan
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        sporter1 = Sporter(
                        lid_nr=self.lid_nr,
                        geslacht='M',
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        adres_code='1234AB56',
                        account=self.account,
                        bij_vereniging=self.ver1)
        sporter1.save()
        self.sporter1 = sporter1
        self.sporter_voorkeuren = get_sporter_voorkeuren(sporter1)

        # maak alle SporterBoog aan
        resp = self.client.post(self.url_sporter_voorkeuren, {'sporter_pk': sporter1.pk})
        self.assert_is_redirect_not_plein(resp)

        sporterboog = SporterBoog.objects.get(sporter=sporter1, boogtype=self.boog_r)
        sporterboog.voor_wedstrijd = True
        sporterboog.save(update_fields=['voor_wedstrijd'])
        self.sporterboog1r = sporterboog

        self.ver2 = Vereniging(
                            ver_nr=1001,
                            naam="Kleine Club",
                            regio=Regio.objects.get(regio_nr=112))
        self.ver2.save()

    @staticmethod
    def _maak_externe_locatie(ver):
        # voeg een locatie toe
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(ver)

        return locatie

    def test_sessies(self):
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

        url = self.url_wedstrijden_sessies % wedstrijd.pk

        # haal de sessie op
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-sessies.dtl', 'plein/site_layout.dtl'))

        # post zonder actie
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, url)

        # nieuwe sessie
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)

        # schakel naar BB rol
        self.e2e_wisselnaarrol_bb()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-sessies.dtl', 'plein/site_layout.dtl'))

        # annuleer de wedstrijd
        wedstrijd.status = 'X'
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_sessies_bad(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # niet bestaande sessie
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden_sessies % 99999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wedstrijden_sessies % 99999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # maak een wedstrijd aan en wissel die naar een andere vereniging
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)
        wedstrijd.organiserende_vereniging = self.ver2
        wedstrijd.save()

        # verkeerde vereniging
        url = self.url_wedstrijden_sessies % wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert403(resp)

    def test_wijzig_sessie(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'wa'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)
        wedstrijd.datum_einde = wedstrijd.datum_begin + datetime.timedelta(days=2)
        wedstrijd.save()

        url = self.url_wedstrijden_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, WedstrijdSessie.objects.count())
        sessie = WedstrijdSessie.objects.first()

        # haal de wijzig pagina op
        url = self.url_wedstrijden_wijzig_sessie % (wedstrijd.pk, sessie.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-sessie.dtl', 'plein/site_layout.dtl'))

        # lege post
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_wedstrijden_sessies % wedstrijd.pk)

        # zet de datum op de 3 mogelijkheden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum': 'datum_2'})
        self.assert_is_redirect(resp, self.url_wedstrijden_sessies % wedstrijd.pk)
        sessie = WedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(sessie.datum, wedstrijd.datum_einde)

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum': 'datum_0'})
        self.assert_is_redirect(resp, self.url_wedstrijden_sessies % wedstrijd.pk)
        sessie = WedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(sessie.datum, wedstrijd.datum_begin)

        wkl = wedstrijd.wedstrijdklassen.first()

        # wijzig een aantal parameters en koppel een wedstrijdklasse
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'datum': 'datum_0',
                                          'tijd_begin': '12:34',
                                          'duur': 'duur_60',
                                          'max_sporters': '42',
                                          'klasse_%s' % wkl.pk: 'jo!'})
        self.assert_is_redirect(resp, self.url_wedstrijden_sessies % wedstrijd.pk)
        sessie = WedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(sessie.datum, wedstrijd.datum_begin)
        self.assertEqual(sessie.tijd_begin.hour, 12)
        self.assertEqual(sessie.tijd_begin.minute, 34)
        self.assertEqual(str(sessie.tijd_einde), '13:34:00')
        self.assertEqual(sessie.max_sporters, 42)

        # test de tijdstippen voor een nachtverschieting
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'tijd_begin': '23:30',
                                          'duur': 'duur_90'})
        self.assert_is_redirect(resp, self.url_wedstrijden_sessies % wedstrijd.pk)
        sessie = WedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(str(sessie.tijd_begin), '23:30:00')
        self.assertEqual(str(sessie.tijd_einde), '01:00:00')

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'tijd_begin': '22:00',
                                          'duur': 'duur_120'})
        self.assert_is_redirect(resp, self.url_wedstrijden_sessies % wedstrijd.pk)
        sessie = WedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(str(sessie.tijd_begin), '22:00:00')
        self.assertEqual(str(sessie.tijd_einde), '00:00:00')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-sessie.dtl', 'plein/site_layout.dtl'))

        # annuleer de wedstrijd
        old_status = wedstrijd.status
        wedstrijd.status = WEDSTRIJD_STATUS_GEANNULEERD
        wedstrijd.save()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/wijzig-sessie.dtl', 'plein/site_layout.dtl'))

        # verwijder de sessie
        self.assertEqual(1, WedstrijdSessie.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_sessie': 'graag'})
        self.assert404(resp, 'Wedstrijd is geannuleerd')
        self.assertEqual(1, WedstrijdSessie.objects.count())

        # herstel de wedstrijd
        wedstrijd.status = old_status
        wedstrijd.save()

        # koppel een inschrijving
        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=self.sporterboog1r,
                            wedstrijdklasse=wkl,
                            koper=self.account,
                            log='test')
        inschrijving.save()

        # verwijderen kan niet omdat er een inschrijving aan gekoppeld is
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_sessie': 'graag'})
        self.assert404(resp, 'Sessie heeft aanmeldingen')
        self.assertEqual(1, WedstrijdSessie.objects.count())

        inschrijving.delete()

        # verwijder de sessie
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'verwijder_sessie': 'graag'})
        self.assert_is_redirect(resp, self.url_wedstrijden_sessies % wedstrijd.pk)
        self.assertEqual(0, WedstrijdSessie.objects.count())

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

    def test_wijzig_sessie_bad(self):
        # wordt HWL
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # maak een wedstrijd en sessie aan
        self._maak_externe_locatie(self.ver1)
        resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        self.assert_is_redirect_not_plein(resp)

        self.assertEqual(1, Wedstrijd.objects.count())
        wedstrijd = Wedstrijd.objects.first()
        url = self.url_wedstrijden_wijzig_wedstrijd % wedstrijd.pk
        self.assert_is_redirect(resp, url)

        url = self.url_wedstrijden_sessies % wedstrijd.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(1, WedstrijdSessie.objects.count())
        sessie = WedstrijdSessie.objects.first()

        # niet bestaande wedstrijd
        url = self.url_wedstrijden_wijzig_sessie % (999999, 0)
        resp = self.client.get(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')
        resp = self.client.post(url)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # niet bestaande sessie
        url = self.url_wedstrijden_wijzig_sessie % (wedstrijd.pk, 999999)
        resp = self.client.get(url)
        self.assert404(resp, 'Sessie niet gevonden')
        resp = self.client.post(url)
        self.assert404(resp, 'Sessie niet gevonden')

        url = self.url_wedstrijden_wijzig_sessie % (wedstrijd.pk, sessie.pk)

        # slechte datum en tijd
        oude_datum = sessie.datum
        self.client.post(url, {'datum': 'datum_999'})
        sessie = WedstrijdSessie.objects.get(pk=sessie.pk)
        self.assertEqual(oude_datum, sessie.datum)

        # slechte tijd
        resp = self.client.post(url, {'tijd_begin': 'hoi'})
        self.assert404(resp, 'Geen valide tijd')
        resp = self.client.post(url, {'tijd_begin': '24:60'})
        self.assert404(resp, 'Geen valide tijd')

        # goede tijd, slechte duur
        resp = self.client.post(url, {'tijd_begin': '10:30',
                                      'duur': 'hoi'})
        self.assert_is_redirect_not_plein(resp)
        resp = self.client.post(url, {'tijd_begin': '10:30',
                                      'duur': 'duur_99999'})
        self.assert_is_redirect_not_plein(resp)

        # slecht aantal sporters
        resp = self.client.post(url, {'max_sporters': 'hoi'})
        self.assert404(resp, 'Geen toegestaan aantal sporters')
        resp = self.client.post(url, {'max_sporters': '-1'})
        self.assert404(resp, 'Geen toegestaan aantal sporters')
        resp = self.client.post(url, {'max_sporters': 0.141})
        self.assert404(resp, 'Geen toegestaan aantal sporters')
        resp = self.client.post(url, {'max_sporters': '0'})
        self.assert404(resp, 'Geen toegestaan aantal sporters')
        resp = self.client.post(url, {'max_sporters': '1000'})
        self.assert404(resp, 'Geen toegestaan aantal sporters')

        # niet van deze vereniging
        wedstrijd.organiserende_vereniging = self.ver2
        wedstrijd.save()
        url = self.url_wedstrijden_wijzig_sessie % (wedstrijd.pk, sessie.pk)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        # maak nog een wedstrijd en sessie aan
        self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'wa'})
        self.assertEqual(2, Wedstrijd.objects.count())
        wedstrijd2 = Wedstrijd.objects.exclude(pk=wedstrijd.pk)[0]
        url = self.url_wedstrijden_sessies % wedstrijd2.pk
        resp = self.client.post(url, {'nieuwe_sessie': 'graag'})
        self.assert_is_redirect(resp, url)
        self.assertEqual(2, WedstrijdSessie.objects.count())
        sessie2 = WedstrijdSessie.objects.exclude(pk=sessie.pk)[0]

        # mix de twee: sessie hoort niet bij wedstrijd
        url = self.url_wedstrijden_wijzig_sessie % (wedstrijd2.pk, sessie.pk)
        resp = self.client.get(url)
        self.assert404(resp, 'Sessie hoort niet bij wedstrijd')
        resp = self.client.post(url)
        self.assert404(resp, 'Sessie hoort niet bij wedstrijd')

# end of file
