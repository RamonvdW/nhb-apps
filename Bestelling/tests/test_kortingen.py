# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.models import BestellingMandje
from Bestelling.operations import (bestel_mutatieverzoek_inschrijven_wedstrijd,
                                   bestel_mutatieverzoek_verwijder_regel_uit_mandje,
                                   bestel_mutatieverzoek_maak_bestellingen)
from Betaal.models import BetaalInstellingenVereniging
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD,
                                    WEDSTRIJD_KORTING_VERENIGING, WEDSTRIJD_KORTING_SPORTER,
                                    WEDSTRIJD_KORTING_COMBI)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting
import datetime


class TestBestellingKortingen(E2EHelpers, TestCase):

    """ tests voor de Bestelling applicatie, kortingen """

    test_after = ('Bestelling.tests.test_mandje',)

    url_mandje_bestellen = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_bestelling_details = '/bestel/details/%s/'          # bestel_nr
    url_bestelling_afrekenen = '/bestel/afrekenen/%s/'      # bestel_nr
    url_check_status = '/bestel/check-status/%s/'           # bestel_nr
    url_na_de_betaling = '/bestel/na-de-betaling/%s/'       # bestel_nr
    url_annuleer_bestelling = '/bestel/annuleer/%s/'        # bestel_nr

    def _maak_sporters(self):
        boog_r = BoogType.objects.get(afkorting='R')

        self.wkls_r = KalenderWedstrijdklasse.objects.filter(boogtype=boog_r, buiten_gebruik=False)

        self.account_sporter1 = self.e2e_create_account('sporter1', 'sporter1@test.com', 'Sporter2')
        self.account_sporter2 = self.e2e_create_account('sporter2', 'sporter2@test.com', 'Sporter1')

        sporter1 = Sporter(
                        lid_nr=100000,
                        voornaam='Sporter1',
                        achternaam='van de Sport',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=self.account_sporter1,
                        bij_vereniging=self.ver)
        sporter1.save()
        self.sporter1 = sporter1

        sporterboog1 = SporterBoog(
                            sporter=sporter1,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog1.save()
        self.sporterboog1 = sporterboog1

        sporter2 = Sporter(
                        lid_nr=100001,
                        voornaam='Sporter2',
                        achternaam='van de Sport',
                        geboorte_datum='1965-06-06',
                        sinds_datum='2021-02-02',
                        account=None,
                        bij_vereniging=self.ver)
        sporter2.save()
        self.sporter2 = sporter2

        sporterboog2 = SporterBoog(
                            sporter=sporter2,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog2.save()
        self.sporterboog2 = sporterboog2

    def _maak_wedstrijden(self):
        now = timezone.now()
        datum = datetime.date(now.year, now.month, now.day) + datetime.timedelta(days=5)

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres='Schietweg 1, Boogdorp',
                        plaats='Boogdrop')
        locatie.save()
        locatie.verenigingen.add(self.ver)

        # maak een kalenderwedstrijd aan, met sessie
        wedstrijd1_sessie1 = WedstrijdSessie(
                                    datum=datum,
                                    tijd_begin='10:00',
                                    tijd_einde='15:00',
                                    max_sporters=50)
        wedstrijd1_sessie1.save()
        self.wedstrijd1_sessie1 = wedstrijd1_sessie1

        wedstrijd1 = Wedstrijd(
                        titel='Wed1',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=self.ver,
                        contact_email='organisatie@ver.not',
                        contact_telefoon='0600000001',
                        contact_naam='Organ is a Tie',
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00)
        wedstrijd1.save()
        wedstrijd1.sessies.add(wedstrijd1_sessie1)
        # wedstrijd.boogtypen.add()
        self.wedstrijd1 = wedstrijd1

        # maak nog een wedstrijd aan, met een sessie
        datum = datetime.date(now.year, now.month, now.day) + datetime.timedelta(days=6)

        wedstrijd2_sessie1 = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='15:00',
                    max_sporters=50)
        wedstrijd2_sessie1.save()
        self.wedstrijd2_sessie1 = wedstrijd2_sessie1

        wedstrijd2 = Wedstrijd(
                        titel='Wed2',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=self.ver,
                        contact_email='organisatie@ver.not',
                        contact_telefoon='0600000001',
                        contact_naam='Organ is a Tie',
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00)
        wedstrijd2.save()
        wedstrijd2.sessies.add(wedstrijd2_sessie1)
        # wedstrijd.boogtypen.add()
        self.wedstrijd2 = wedstrijd2

        # maak nog een wedstrijd aan, met een sessie
        datum = datetime.date(now.year, now.month, now.day) + datetime.timedelta(days=7)

        wedstrijd3_sessie1 = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='15:00',
                    max_sporters=50)
        wedstrijd3_sessie1.save()
        self.wedstrijd3_sessie1 = wedstrijd3_sessie1

        wedstrijd3 = Wedstrijd(
                        titel='Wed3',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=self.ver,
                        contact_email='organisatie@ver.not',
                        contact_telefoon='0600000001',
                        contact_naam='Organ is a Tie',
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00)
        wedstrijd3.save()
        wedstrijd3.sessies.add(wedstrijd3_sessie1)
        # wedstrijd.boogtypen.add()
        self.wedstrijd3 = wedstrijd3

        # maak nog een wedstrijd aan, met een sessie
        wedstrijd4_sessie1 = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='15:00',
                    tijd_einde='20:00',
                    max_sporters=50)
        wedstrijd4_sessie1.save()
        self.wedstrijd4_sessie1 = wedstrijd4_sessie1

        wedstrijd4 = Wedstrijd(
                        titel='Wed4',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=self.ver,
                        contact_email='organisatie@ver.not',
                        contact_telefoon='0600000001',
                        contact_naam='Organ is a Tie',
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00)
        wedstrijd4.save()
        wedstrijd4.sessies.add(wedstrijd4_sessie1)
        # wedstrijd.boogtypen.add()
        self.wedstrijd4 = wedstrijd4

    def _maak_kortingen(self):
        now = timezone.now()
        datum = datetime.date(now.year, now.month, now.day) + datetime.timedelta(days=3)

        ver_korting = WedstrijdKorting(
                            geldig_tot_en_met=datum,
                            soort=WEDSTRIJD_KORTING_VERENIGING,
                            uitgegeven_door=self.ver,
                            percentage=42)
        ver_korting.save()
        ver_korting.voor_wedstrijden.add(self.wedstrijd2)
        ver_korting.voor_wedstrijden.add(self.wedstrijd3)
        self.ver_korting = ver_korting

        lid_korting = WedstrijdKorting(
                            geldig_tot_en_met=datum,
                            soort=WEDSTRIJD_KORTING_SPORTER,
                            uitgegeven_door=self.ver,
                            voor_sporter=self.sporter1,
                            percentage=75)
        lid_korting.save()
        lid_korting.voor_wedstrijden.add(self.wedstrijd1)
        self.lid_korting = lid_korting

        combi_korting1 = WedstrijdKorting(
                            geldig_tot_en_met=datum,
                            soort=WEDSTRIJD_KORTING_COMBI,
                            uitgegeven_door=self.ver,
                            percentage=50)
        combi_korting1.save()
        combi_korting1.voor_wedstrijden.add(self.wedstrijd1)
        combi_korting1.voor_wedstrijden.add(self.wedstrijd2)
        self.combi_korting1 = combi_korting1

        combi_korting2 = WedstrijdKorting(
                            geldig_tot_en_met=datum,
                            soort=WEDSTRIJD_KORTING_COMBI,
                            uitgegeven_door=self.ver,
                            percentage=40)
        combi_korting2.save()
        combi_korting2.voor_wedstrijden.add(self.wedstrijd3)
        combi_korting2.voor_wedstrijden.add(self.wedstrijd4)
        self.combi_korting2 = combi_korting2

        lid_korting2 = WedstrijdKorting(
                            geldig_tot_en_met=datum,
                            soort=WEDSTRIJD_KORTING_SPORTER,
                            uitgegeven_door=self.ver,
                            voor_sporter=self.sporter2,
                            percentage=1)
        lid_korting2.save()
        lid_korting2.voor_wedstrijden.add(self.wedstrijd1)

        ver2_korting = WedstrijdKorting(
                            geldig_tot_en_met=datum,
                            soort=WEDSTRIJD_KORTING_VERENIGING,
                            uitgegeven_door=self.ver2,
                            percentage=42)
        ver2_korting.save()

    def setUp(self):
        """ initialisatie van de test case """

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
        self.ver = ver

        ver2 = Vereniging(
                    ver_nr=1001,
                    naam="Andere Club",
                    regio=Regio.objects.get(regio_nr=113),
                    bank_iban='IBAN123456000',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK4566',
                    website='www.bb2.not',
                    contact_email='info@bb2.not',
                    telefoonnummer='12345600')
        ver2.save()
        self.ver2 = ver2

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_bond=True)
        instellingen.save()
        self.instellingen = instellingen

        self._maak_sporters()
        self._maak_wedstrijden()
        self._maak_kortingen()

        mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account_sporter1)
        self.mandje = mandje

    def NOT_test_mandje(self):
        self.e2e_login(self.account_sporter1)

        now = timezone.now()

        # sporter 1 krijgt korting:
        # persoonlijk: 75% op wedstrijd 1
        # vereniging:  42% op wedstrijd 2
        # combi:       50% op wedstrijd 1 + 2

        # schrijf in op 1e wedstrijd en krijg persoonlijke korting
        inschrijving1_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd1,
                                    sessie=self.wedstrijd1_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving1_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving1_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        self.assertIsNotNone(inschrijving.korting)
        self.assertEqual(inschrijving.korting.pk, self.lid_korting.pk)

        # schrijf in op 2e wedstrijd
        # krijg combi korting i.p.v. persoonlijke korting
        inschrijving2_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd2,
                                    sessie=self.wedstrijd2_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving2_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving2_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving1 = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        inschrijving2 = WedstrijdInschrijving.objects.get(pk=inschrijving2_sporter1.pk)
        kortingen = [korting
                     for korting in (inschrijving1.korting, inschrijving2.korting)
                     if korting is not None]
        self.assertEqual(len(kortingen), 1)
        self.assertEqual(kortingen[0].pk, self.combi_korting1.pk)

        # tweede sporter
        inschrijving_sporter2 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd2,
                                    sessie=self.wedstrijd2_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog2,
                                    koper=self.account_sporter1)
        inschrijving_sporter2.save()
        self.inschrijving_sporter2 = inschrijving_sporter2
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving_sporter2, snel=True)
        self.verwerk_bestel_mutaties()

        # verwijder de inschrijving voor de 1e wedstrijd
        # krijg ver korting i.p.v. combi-korting
        product = inschrijving1.bestellingproduct_set.first()       # TODO: update
        bestel_mutatieverzoek_verwijder_regel_uit_mandje(self.account_sporter1, product, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving1 = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        self.assertEqual(inschrijving1.status, WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
        self.assertIsNone(inschrijving1.korting)

        inschrijving2 = WedstrijdInschrijving.objects.get(pk=inschrijving2_sporter1.pk)
        self.assertEqual(inschrijving2.korting.pk, self.ver_korting.pk)

    def NOT_test_bestelling_plus_mandje(self):
        # test dat de juiste combi-korting in het mandje komt bovenop een bestelling

        self.e2e_login(self.account_sporter1)

        now = timezone.now()

        self.lid_korting.delete()
        self.ver_korting.delete()

        # sporter 1 krijgt korting:
        # combi:       50% op wedstrijd 1 + 2

        # schrijf in op 1e wedstrijd en krijg persoonlijke korting
        inschrijving1_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd1,
                                    sessie=self.wedstrijd1_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving1_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving1_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        bestel_mutatieverzoek_maak_bestellingen(self.account_sporter1, snel=True)

        # schrijf in op 2e wedstrijd
        # krijg combi korting i.p.v. persoonlijke korting
        inschrijving2_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd2,
                                    sessie=self.wedstrijd2_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving2_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving2_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving1 = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        inschrijving2 = WedstrijdInschrijving.objects.get(pk=inschrijving2_sporter1.pk)
        kortingen = [korting for korting in (inschrijving1.korting, inschrijving2.korting) if korting is not None]
        self.assertEqual(len(kortingen), 1)
        self.assertEqual(kortingen[0].pk, self.combi_korting1.pk)

    def NOT_test_niet_stapelen(self):
        # test dat de juiste combi-korting in het mandje komt bovenop een bestelling
        # maar niet als de bestelling al een andere korting gekregen heeft

        self.e2e_login(self.account_sporter1)

        now = timezone.now()

        # sporter 1 krijgt korting:
        # persoonlijk: 75% op wedstrijd 1
        # vereniging:  42% op wedstrijd 2
        # combi:       50% op wedstrijd 1 + 2

        # schrijf in op 1e wedstrijd en krijg persoonlijke korting
        inschrijving1_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd1,
                                    sessie=self.wedstrijd1_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving1_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving1_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        bestel_mutatieverzoek_maak_bestellingen(self.account_sporter1, snel=True)

        # schrijf in op 2e wedstrijd
        # krijg GEEN combi korting i.p.v. persoonlijke korting
        inschrijving2_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd2,
                                    sessie=self.wedstrijd2_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving2_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving2_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving1 = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        self.assertIsNotNone(inschrijving1.korting)
        self.assertEqual(inschrijving1.korting.pk, self.lid_korting.pk)

        inschrijving2 = WedstrijdInschrijving.objects.get(pk=inschrijving2_sporter1.pk)
        self.assertIsNotNone(inschrijving2.korting)
        self.assertEqual(inschrijving2.korting.pk, self.ver_korting.pk)

    def NOT_test_hoogste_1(self):
        self.e2e_login(self.account_sporter1)

        now = timezone.now()

        self.combi_korting1.delete()
        self.combi_korting2.delete()
        self.ver_korting.voor_wedstrijden.set([self.wedstrijd1])

        # sporter 1 krijgt korting:
        # persoonlijk: 75% op wedstrijd 1
        # vereniging:  42% op wedstrijd 1

        # schrijf in op 1e wedstrijd en krijg persoonlijke korting
        inschrijving1_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd1,
                                    sessie=self.wedstrijd1_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving1_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving1_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        self.assertIsNotNone(inschrijving.korting)
        self.assertEqual(inschrijving.korting.pk, self.lid_korting.pk)

    def NOT_test_hoogste_2(self):
        self.e2e_login(self.account_sporter1)

        now = timezone.now()

        self.combi_korting1.delete()
        self.combi_korting2.delete()
        self.lid_korting.percentage = 40
        self.lid_korting.save(update_fields=['percentage'])
        self.ver_korting.voor_wedstrijden.set([self.wedstrijd1])

        # sporter 1 krijgt korting:
        # persoonlijk: 40% op wedstrijd 1
        # vereniging:  42% op wedstrijd 1

        # schrijf in op 1e wedstrijd en krijg persoonlijke korting
        inschrijving1_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd1,
                                    sessie=self.wedstrijd1_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving1_sporter1.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving1_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        self.assertIsNotNone(inschrijving.korting)
        self.assertEqual(inschrijving.korting.pk, self.ver_korting.pk)

    def NOT_test_hoogste_3(self):
        self.e2e_login(self.account_sporter1)

        now = timezone.now()

        # sporter 1 krijgt korting:
        # persoonlijk: 75% op wedstrijd 1
        # vereniging:  42% op wedstrijd 2 + 3
        # combi:       50% op wedstrijd 1 + 2
        # combi:       40% op wedstrijd 3 + 4

        # schrijf in op 1e wedstrijd en krijg persoonlijke korting
        inschrijving1_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd1,
                                    sessie=self.wedstrijd1_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving1_sporter1.save()
        inschrijving2_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd2,
                                    sessie=self.wedstrijd2_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving2_sporter1.save()
        inschrijving3_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd3,
                                    sessie=self.wedstrijd3_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving3_sporter1.save()
        inschrijving4_sporter1 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd4,
                                    sessie=self.wedstrijd4_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog1,
                                    koper=self.account_sporter1)
        inschrijving4_sporter1.save()

        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving1_sporter1, snel=True)
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving2_sporter1, snel=True)
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving3_sporter1, snel=True)
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving4_sporter1, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving1 = WedstrijdInschrijving.objects.get(pk=inschrijving1_sporter1.pk)
        inschrijving2 = WedstrijdInschrijving.objects.get(pk=inschrijving2_sporter1.pk)
        inschrijving3 = WedstrijdInschrijving.objects.get(pk=inschrijving3_sporter1.pk)
        inschrijving4 = WedstrijdInschrijving.objects.get(pk=inschrijving4_sporter1.pk)
        kortingen = [korting for korting in (inschrijving1.korting,
                                             inschrijving2.korting,
                                             inschrijving3.korting,
                                             inschrijving4.korting) if korting is not None]
        # print('kortingen: %s' % kortingen)
        self.assertEqual(len(kortingen), 2)
        self.assertEqual(kortingen[0].pk, self.combi_korting1.pk)
        self.assertEqual(kortingen[1].pk, self.combi_korting2.pk)

    def NOT_test_geen_ver(self):
        self.sporter2.bij_vereniging = None
        self.sporter2.save(update_fields=['bij_vereniging'])

        self.e2e_login(self.account_sporter1)

        now = timezone.now()

        inschrijving_sporter2 = WedstrijdInschrijving(
                                    wanneer=now,
                                    wedstrijd=self.wedstrijd2,
                                    sessie=self.wedstrijd2_sessie1,
                                    wedstrijdklasse=self.wkls_r[0],
                                    sporterboog=self.sporterboog2,
                                    koper=self.account_sporter1)
        inschrijving_sporter2.save()
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_sporter1, inschrijving_sporter2, snel=True)
        self.verwerk_bestel_mutaties()

        inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving_sporter2.pk)
        self.assertIsNone(inschrijving.korting)


# end of file
