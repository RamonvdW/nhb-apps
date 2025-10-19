# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestelling.definities import BESTELLING_REGEL_CODE_EVENEMENT
from Bestelling.models import Bestelling, BestellingRegel
from Betaal.models import BetaalInstellingenVereniging
from Evenement.definities import (EVENEMENT_STATUS_GEACCEPTEERD,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  EVENEMENT_INSCHRIJVING_STATUS_BESTELD,
                                  EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                  EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                                  EVENEMENT_AFMELDING_STATUS_GEANNULEERD)
from Evenement.models import Evenement, EvenementInschrijving, EvenementAfgemeld
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestEvenementAanmeldingen(E2EHelpers, TestCase):

    """ tests voor de Evenement applicatie, module Aanmeldingen """

    test_after = ('Evenement.tests.test_inschrijven',)

    url_download = '/kalender/evenement/aanmeldingen/%s/download/csv/'      # evenement_pk
    url_aanmeldingen = '/kalender/evenement/aanmeldingen/%s/'               # evenement_pk
    url_workshop_keuzes = '/kalender/evenement/workshop-keuzes/%s/'         # evenement_pk
    url_details_aanmelding = '/kalender/evenement/details-aanmelding/%s/'   # inschrijving_pk
    url_details_afmelding = '/kalender/evenement/details-afmelding/%s/'     # afmelding_pk

    url_afmelden = '/kalender/evenement/afmelden/%s/'                       # inschrijving_pk
    url_toevoegen_mandje = '/kalender/evenement/inschrijven/toevoegen-mandje/'  # POST

    volgende_bestel_nr = 1234567

    def setUp(self):
        """ initialisatie van de test case """

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Tester', accepteer_vhpg=True)
        self.account_100022 = self.e2e_create_account('100022', 'pijl@test.not', 'Pijl')
        self.account_100023 = self.e2e_create_account('100023', 'veer@test.not', 'Veer')

        ver_bond = Vereniging(
                    ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                    naam='Bondsbureau',
                    plaats='Schietstad',
                    regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_bond,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_bond = instellingen

        self.assertEqual(settings.BETAAL_VIA_BOND_VER_NR, settings.WEBWINKEL_VERKOPER_VER_NR)

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver.save()

        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_100000)

        self.functie_sec = maak_functie("SEC test", "SEC")
        self.functie_sec.vereniging = ver
        self.functie_sec.save()
        self.functie_sec.accounts.add(self.account_100000)

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_bond=True)
        instellingen.save()
        self.instellingen = instellingen

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.account_100000,
                        bij_vereniging=ver,
                        adres_code='1234XX')
        sporter.save()
        self.sporter_100000 = sporter

        locatie = EvenementLocatie(
                    naam='Arnhemhal',
                    vereniging=ver,
                    adres='Papendallaan 9\n6816VD Arnhem',
                    plaats='Arnhem')
        locatie.save()

        now_date = timezone.now().date()
        soon_date = now_date + datetime.timedelta(days=60)

        evenement = Evenement(
                        titel='Test evenement',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver,
                        datum=soon_date,
                        aanvang='09:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        contact_naam='Dhr. Organisator',
                        contact_email='info@test.not',
                        contact_website='www.test.not',
                        contact_telefoon='023-1234567',
                        beschrijving='Test beschrijving',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement.save()
        self.evenement = evenement

        # nog een sporter met account
        sporter = Sporter(
                        lid_nr=100022,
                        voornaam='Pijl',
                        achternaam='de Boog',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.account_100022,
                        bij_vereniging=ver,
                        adres_code='5678YY')
        sporter.save()
        self.sporter_100022 = sporter

        # een sporter zonder vereniging
        sporter = Sporter(
                        lid_nr=100022,
                        voornaam='Veer',
                        achternaam='van de Pijl}',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=None,
                        bij_vereniging=ver,
                        adres_code='5678YY')
        sporter.save()
        self.sporter_100023 = sporter

        # nog een sporter, zonder account
        sporter = Sporter(
                        lid_nr=100023,
                        voornaam='Pees',
                        achternaam='de Boog',
                        geboorte_datum='1966-05-05',
                        sinds_datum='2020-02-02',
                        bij_vereniging=ver)
        sporter.save()
        self.sporter_100023 = sporter

        regel = BestellingRegel(
                        korte_beschrijving='evenement',
                        bedrag_euro=10.0,
                        code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()

        # maak een inschrijving op het evenement
        inschrijving = EvenementInschrijving(
                                wanneer=timezone.now(),
                                nummer=1,
                                status=EVENEMENT_INSCHRIJVING_STATUS_BESTELD,
                                evenement=evenement,
                                sporter=self.sporter_100022,
                                koper=self.account_100022,
                                bestelling=regel)
        inschrijving.save()
        self.inschrijving = inschrijving

        bestelling = Bestelling(
                        bestel_nr=self.volgende_bestel_nr,
                        account=self.account_100022,
                        log='Test')
        bestelling.save()
        bestelling.regels.add(regel)
        self.bestelling = bestelling

        # handmatige inschrijving
        inschrijving = EvenementInschrijving(
                                wanneer=timezone.now(),
                                nummer=3,
                                status=EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                evenement=evenement,
                                sporter=self.sporter_100023,
                                koper=self.account_100022)
        inschrijving.save()
        self.inschrijving2 = inschrijving

        regel = BestellingRegel(
                    korte_beschrijving='evenement_afgemeld',
                    bedrag_euro=10.0,
                    code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel.save()
        self.bestelling.regels.add(regel)

        # afmelding gekoppeld aan een bestelling
        afgemeld = EvenementAfgemeld(
                            wanneer_inschrijving=timezone.now() - datetime.timedelta(hours=4),
                            nummer=2,
                            wanneer_afgemeld=timezone.now() - datetime.timedelta(hours=3),
                            status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                            evenement=self.evenement,
                            sporter=self.sporter_100022,
                            koper=self.account_100022,
                            bedrag_ontvangen=10.0,
                            bedrag_retour=9.0,
                            bestelling=regel,
                            log='test')
        afgemeld.save()
        self.afgemeld = afgemeld

        # handmatig inschrijving die afgemeld is
        afgemeld = EvenementAfgemeld(
                            wanneer_inschrijving=timezone.now() - datetime.timedelta(hours=4),
                            nummer=2,
                            wanneer_afgemeld=timezone.now() - datetime.timedelta(hours=3),
                            status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                            evenement=self.evenement,
                            sporter=self.sporter_100022,
                            koper=self.account_100000,
                            bedrag_ontvangen=0.0,
                            bedrag_retour=0.0,
                            # geen bestelling=
                            log='test handmatig')
        afgemeld.save()

    def test_anon(self):
        resp = self.client.get(self.url_aanmeldingen % 99999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_download % 99999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_details_aanmelding % 99999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_details_afmelding % 99999)
        self.assert403(resp, "Geen toegang")

    def test_aanmeldingen(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_aanmeldingen % 999999)
        self.assert404(resp, 'Evenement niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmeldingen % self.evenement.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/aanmeldingen.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # geen aanmeldingen
        EvenementInschrijving.objects.all().delete()
        EvenementAfgemeld.objects.all().delete()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_aanmeldingen % self.evenement.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/aanmeldingen.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_aanmeldingen % self.evenement.pk)

    def test_download(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_download % 999999)
        self.assert404(resp, 'Evenement niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_download % self.evenement.pk)
        self.assert200_is_bestand_csv(resp)

        # uitzondering: sporter zonder vereniging
        self.sporter_100023.bij_vereniging = None
        self.sporter_100023.save(update_fields=['bij_vereniging'])

        self.sporter_100022.bij_vereniging = None
        self.sporter_100022.save(update_fields=['bij_vereniging'])

        # haal het product uit de bestelling
        self.bestelling.regels.clear()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_download % self.evenement.pk)
        self.assert200_is_bestand_csv(resp)

        self.e2e_assert_other_http_commands_not_supported(self.url_download % self.evenement.pk)

    def test_details_aanmelding(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_details_aanmelding % 'xxx')
        self.assert404(resp, 'Geen valide parameter')

        resp = self.client.get(self.url_details_aanmelding % 999999)
        self.assert404(resp, 'Aanmelding niet gevonden')

        # inschrijving via bestelling
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % self.inschrijving.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/aanmelding-details.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # handmatige inschrijving
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % self.inschrijving2.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/aanmelding-details.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # in mandje
        self.inschrijving.status = EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE
        self.inschrijving.save(update_fields=['status'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % self.inschrijving.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/aanmelding-details.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_details_afmelding(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_details_afmelding % 'xxx')
        self.assert404(resp, 'Geen valide parameter')

        resp = self.client.get(self.url_details_afmelding % 999999)
        self.assert404(resp, 'Afmelding niet gevonden')

        self.assertTrue(str(self.afgemeld) != '')

        self.assertEqual(self.afgemeld.korte_beschrijving(), 'Test evenement, voor 100022')
        self.afgemeld.evenement.titel = 'Dit is een hele lange titel die afgekapt gaat worden'
        self.assertTrue('.., voor 100022' in self.afgemeld.korte_beschrijving())

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_afmelding % self.afgemeld.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/afmelding-details.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # geannuleerd
        self.afgemeld.status = EVENEMENT_AFMELDING_STATUS_GEANNULEERD
        self.afgemeld.save(update_fields=['status'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_afmelding % self.afgemeld.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/afmelding-details.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

    def test_workshop_keuzes(self):
        # 1 regel met keuze
        # format: "n.m titel" met n = workshop ronde, m = volgorde (1, 2, etc.)
        self.evenement.workshop_keuze = "1.1 test A\r\n1.2 test B\nskip\nno-dot x\nerr.or error\n2.1 test C\n3.1 test D"
        self.evenement.save(update_fields=['workshop_keuze'])

        self.inschrijving.gekozen_workshops = '1.1 2.1'
        self.inschrijving.save(update_fields=['gekozen_workshops'])

        # anon werk gewoon
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_workshop_keuzes % self.evenement.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/workshop-keuzes.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # corner cases
        resp = self.client.get(self.url_workshop_keuzes % 999999)
        self.assert404(resp, 'Evenement niet gevonden')

        # inloggen
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # download aanmeldingen, met workshop keuzes
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_download % self.evenement.pk)
        self.assert200_is_bestand_csv(resp)

        # details aanmelding, met workshop keuzes
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % self.inschrijving.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/aanmelding-details.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        # details aanmelding, evenement heeft workshops maar inschrijving heeft geen keuzes gemaakt
        self.inschrijving.gekozen_workshops = ''
        self.inschrijving.save(update_fields=['gekozen_workshops'])

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_details_aanmelding % self.inschrijving.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('evenement/aanmelding-details.dtl', 'design/site_layout.dtl'))
        self.assert_html_ok(resp)


# end of file
