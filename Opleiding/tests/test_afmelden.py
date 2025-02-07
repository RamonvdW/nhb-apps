# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from Bestelling.models import Bestelling
from Bestelling.operations.mutaties import bestel_mutatieverzoek_maak_bestellingen
from Functie.models import Functie
from Geo.models import Regio
from Instaptoets.models import Vraag, Instaptoets
from Mailer.models import MailQueue
from Opleiding.definities import (OPLEIDING_STATUS_INSCHRIJVEN,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_BESTELD)
from Opleiding.models import Opleiding, OpleidingInschrijving, OpleidingAfgemeld
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestOpleidingAfmelden(E2EHelpers, TestCase):

    """ tests voor de Opleiding applicatie, functionaliteit Afmelden """

    test_after = ('Opleiding.tests.test_inschrijven',)

    url_inschrijven_basiscursus = '/opleiding/inschrijven/basiscursus/'
    url_toevoegen_aan_mandje = '/opleiding/inschrijven/toevoegen-mandje/'
    url_mandje_verwijder = '/bestel/mandje/verwijderen/%s/'     # product_pk

    url_afmelden = '/opleiding/afmelden/%s/'            # inschrijving_pk
    url_aanmeldingen = '/opleiding/aanmeldingen/%s/'    # opleiding_pk

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.nhb', 'Normaal')
        self.e2e_account_accepteert_vhpg(self.account_normaal)

        ver_bond = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam='Bondsbureau',
                        plaats='Schietstad',
                        regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

        self.functie_hwl = Functie(rol='HWL', vereniging=ver_bond)
        self.functie_hwl.save()
        self.functie_hwl.accounts.add(self.account_normaal)

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

        # maak een basiscursus aan zodat het kaartje Basiscursus getoond wordt op het overzicht
        opleiding = Opleiding(
                        titel="Test",
                        is_basiscursus=True,
                        periode_begin="2024-11-01",
                        periode_einde="2024-12-01",
                        beschrijving="Test",
                        status=OPLEIDING_STATUS_INSCHRIJVEN,
                        eis_instaptoets=True,
                        kosten_euro=10.00)
        opleiding.save()
        self.opleiding = opleiding

        # maak de instaptoets beschikbaar
        Vraag().save()

        # instaptoets is gehaald
        now = timezone.now() - datetime.timedelta(days=10)
        toets = Instaptoets(
                    afgerond=now,
                    sporter=sporter,
                    aantal_vragen=10,
                    aantal_antwoorden=10,
                    is_afgerond=True,
                    aantal_goed=9,
                    geslaagd=True)
        toets.save()
        self.toets = toets

    def test_anon(self):
        self.e2e_logout()

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_afmelden % 999999)
        self.assert_is_redirect_login(resp)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % 999999)
        self.assert_is_redirect_login(resp)

    def test_verwijder_nog_in_mandje(self):
        # als HWL, verwijder een bestelling die nog in het mandje van een sporter ligt

        # maak een bestelling
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self.assertEqual(OpleidingInschrijving.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)
        inschrijving = OpleidingInschrijving.objects.first()

        # laat de achtergrond taak het toevoegen aan het mandje verwerken
        self.verwerk_bestel_mutaties()

        self.assertEqual(Bestelling.objects.count(), 0)

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE)

        # verwijder de mail over de bestelling
        MailQueue.objects.all().delete()

        # wissel naar de HWL van het bondsbureau
        self.e2e_login(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # annuleer de bestelling
        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.opleiding.pk)

        # laat de achtergrond taak het annuleren verwerken
        self.verwerk_bestel_mutaties()

        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)

    def test_annuleer_bestelling(self):
        # maak een bestelling
        self.e2e_login(self.account_normaal)
        self.e2e_check_rol('sporter')

        self.assertEqual(OpleidingInschrijving.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_toevoegen_aan_mandje, {'opleiding': self.opleiding.pk,
                                                                    'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('opleiding/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(OpleidingInschrijving.objects.count(), 1)
        inschrijving = OpleidingInschrijving.objects.first()

        # laat de achtergrond taak het toevoegen aan het mandje verwerken
        self.verwerk_bestel_mutaties()

        # omzetten in een bestelling
        self.assertEqual(Bestelling.objects.count(), 0)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        # print('\nf1: %s\nf2: %s\n' % (f1.getvalue(), f2.getvalue()))

        self.assertEqual(Bestelling.objects.count(), 1)
        # bestelling = Bestelling.objects.first()

        inschrijving.refresh_from_db()
        self.assertEqual(inschrijving.status, OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_BESTELD)

        # verwijder de mail over de bestelling
        MailQueue.objects.all().delete()

        # wissel naar de HWL van het bondsbureau
        self.e2e_login(self.account_normaal)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        # corner case
        resp = self.client.post(self.url_afmelden % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')

        # annuleer de bestelling (die nog in het mandje ligt)
        self.assertEqual(OpleidingAfgemeld.objects.count(), 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afmelden % inschrijving.pk, {'snel': 1})
        self.assert_is_redirect(resp, self.url_aanmeldingen % self.opleiding.pk)

        # laat de achtergrond taak het annuleren verwerken
        self.verwerk_bestel_mutaties()

        self.assertEqual(OpleidingAfgemeld.objects.count(), 1)

# end of file
