# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestel.models import BestelMandje
from Bestel.operations.mutaties import (bestel_mutatieverzoek_inschrijven_wedstrijd,
                                        bestel_mutatieverzoek_webwinkel_keuze)
from Betaal.models import BetaalInstellingenVereniging
from Functie.models import Functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Mailer.models import MailQueue
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_KORTING_VERENIGING
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting
from decimal import Decimal


class TestBestelHerinnering(E2EHelpers, TestCase):

    """ tests voor de Bestel-applicatie, module herinnering """

    test_after = ('Bestel.tests.test_mandje',)

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

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
        self.ver1 = ver

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
                        account=account,
                        bij_vereniging=ver)
        sporter.save()
        self.sporter = sporter

        boog_r = BoogType.objects.get(afkorting='R')

        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog.save()

        now = timezone.now()
        datum = now.date()      # pas op met testen ronde 23:59

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres='Schietweg 1, Boogdorp',
                        plaats='Boogdorp')
        locatie.save()
        locatie.verenigingen.add(ver)

        # maak een kalenderwedstrijd aan, met sessie
        sessie = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    max_sporters=50)
        sessie.save()
        self.sessie = sessie

        wedstrijd = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        minuten_voor_begin_sessie_aanwezig_zijn=42,
                        organiserende_vereniging=ver,
                        contact_email='organisatie@ver.not',
                        contact_telefoon='0600000001',
                        contact_naam='Organ is a Tie',
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=42.00)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        # wedstrijd.boogtypen.add()
        self.wedstrijd = wedstrijd

        wkls_r = KalenderWedstrijdklasse.objects.filter(boogtype=boog_r, buiten_gebruik=False)

        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_r[0],
                            sporterboog=sporterboog,
                            koper=account)
        inschrijving.save()
        self.inschrijving = inschrijving

        korting = WedstrijdKorting(
                    geldig_tot_en_met=datum,
                    soort=WEDSTRIJD_KORTING_VERENIGING,
                    uitgegeven_door=ver,
                    percentage=42)
        korting.save()
        korting.voor_wedstrijden.add(wedstrijd)
        self.korting = korting

        mandje, is_created = BestelMandje.objects.get_or_create(account=account)
        self.mandje = mandje

        self.functie_mww = Functie.objects.filter(rol='MWW').first()
        self.functie_mww.bevestigde_email = 'mww@bond.tst'
        self.functie_mww.save(update_fields=['bevestigde_email'])

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='meervoud',
                        bestel_begrenzing='1-5',
                        prijs_euro="1.23")
        product.save()
        self.product = product

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        koper=self.account_admin,
                        product=product,
                        aantal=1,
                        totaal_euro=Decimal('1.23'),
                        log='test')
        keuze.save()
        self.keuze = keuze

    def test_bestelling(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # leg 1e product in mandje
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        self.assertEqual(MailQueue.objects.count(), 0)

        f1, f2 = self.run_management_command('stuur_mandje_herinneringen')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('[INFO] Mandje met producten: 424242' in f2.getvalue())

        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)
        self.assertTrue('1 product ' in mail.mail_text)
        mail.delete()

        # leg 2e product in mandje
        bestel_mutatieverzoek_webwinkel_keuze(self.account_admin, self.keuze, snel=True)
        self.verwerk_bestel_mutaties()

        f1, f2 = self.run_management_command('stuur_mandje_herinneringen')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('[INFO] Mandje met producten: 424242' in f2.getvalue())

        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)
        self.assertTrue('2 producten ' in mail.mail_text)
        mail.delete()


# end of file
