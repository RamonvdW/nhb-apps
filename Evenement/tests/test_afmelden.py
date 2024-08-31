# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestel.operations.mutaties import bestel_mutatieverzoek_maak_bestellingen
from Betaal.models import BetaalInstellingenVereniging
from Evenement.definities import (EVENEMENT_STATUS_GEACCEPTEERD, EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE)
from Evenement.models import Evenement, EvenementInschrijving
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import EvenementLocatie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestEvenementAfmelden(E2EHelpers, TestCase):

    """ tests voor de Evenement applicatie, module Afmelden """

    test_after = ('Evenement.tests.test_inschrijven',)

    url_afmelden = '/kalender/evenement/afmelden/%s/'           # inschrijving_pk
    url_aanmeldingen = '/kalender/evenement/aanmeldingen/%s/'   # evenement_pk
    url_toevoegen_mandje = '/kalender/evenement/inschrijven/toevoegen-mandje/'      # POST

    def setUp(self):
        """ initialisatie van de test case """

        # self.account_admin = account = self.e2e_create_account_admin()
        # self.account_admin.is_BB = True
        # self.account_admin.save(update_fields=['is_BB'])

        self.account_100000 = self.e2e_create_account('100000', 'normaal@test.not', 'Tester', accepteer_vhpg=True)
        self.account_100022 = self.e2e_create_account('100022', 'pijl@test.not', 'Pijl')

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

        # nog een sporter met account (voor inschrijven groepje)
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

        # maak een inschrijving op het evenement
        inschrijving = EvenementInschrijving(
                                wanneer=timezone.now(),
                                nummer=1,
                                status=EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                evenement=evenement,
                                sporter=self.sporter_100022,
                                koper=self.account_100022)
        inschrijving.save()
        self.inschrijving = inschrijving

    def test_anon(self):
        resp = self.client.get(self.url_afmelden % 99999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.post(self.url_afmelden % 99999)
        self.assert403(resp, "Geen toegang")

    def test_hwl_definitief(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        resp = self.client.get(self.url_afmelden % 999999)
        self.assertEqual(resp.status_code, 405)     # method not allowed, want GET bestaat niet

        resp = self.client.post(self.url_afmelden % 999999)
        self.assert404(resp, "Inschrijving niet gevonden")

        url = self.url_afmelden % self.inschrijving.pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.evenement.pk)

        # verkeerde vereniging
        ver = Vereniging(
                    ver_nr=1001,
                    naam="Andere Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.ac.not',
                    contact_email='info@ac.not',
                    telefoonnummer='12345678')
        ver.save()
        self.evenement.organiserende_vereniging = ver
        self.evenement.save(update_fields=['organiserende_vereniging'])

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert404(resp, 'Verkeerde vereniging')

    def test_hwl_reservering(self):
        self.e2e_login_and_pass_otp(self.account_100000)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        EvenementInschrijving.objects.all().delete()

        # in het mandje
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_mandje, {'evenement': self.evenement.pk,
                                                                'sporter': self.sporter_100022.pk,
                                                                'goto': 'G',
                                                                'snel': '1'})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('evenement/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))

        self.verwerk_bestel_mutaties()

        self.inschrijving = EvenementInschrijving.objects.first()
        url = self.url_afmelden % self.inschrijving.pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.evenement.pk)

# end of file
