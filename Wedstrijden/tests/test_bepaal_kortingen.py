# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management.base import OutputWrapper
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import BESTELLING_REGEL_CODE_WEDSTRIJD, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING
from Bestelling.models import BestellingRegel
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_STATUS_GEACCEPTEERD,
                                    WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING, WEDSTRIJD_KORTING_COMBI)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting
from Wedstrijden.operations.bepaal_kortingen import BepaalAutomatischeKorting
from datetime import timedelta
from decimal import Decimal
import io


class TestWedstrijdenBepaalKortingen(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module Bepaal Kortingen """

    test_after = ('Wedstrijden.tests.test_wedstrijd_details',)

    url_aanmeldingen_wedstrijd = '/wedstrijden/%s/aanmeldingen/'                    # wedstrijd_pk
    url_details_aanmelding = '/wedstrijden/details-aanmelding/%s/'                  # inschrijving_pk
    url_aanmeldingen_afmelden = '/wedstrijden/afmelden/%s/'                         # inschrijving_pk
    url_aanmeldingen_download_tsv = '/wedstrijden/%s/aanmeldingen/download/tsv/'    # wedstrijd_pk
    url_aanmeldingen_download_csv = '/wedstrijden/%s/aanmeldingen/download/csv/'    # wedstrijd_pk

    url_wedstrijd_details = '/wedstrijden/%s/details/'                              # wedstrijd_pk
    url_wedstrijden_wijzig_wedstrijd = '/wedstrijden/%s/wijzig/'                    # wedstrijd_pk
    url_wedstrijden_maak_nieuw = '/wedstrijden/vereniging/kies-type/'
    url_wedstrijden_vereniging = '/wedstrijden/vereniging/'
    url_inschrijven_groepje = '/wedstrijden/inschrijven/%s/groep/'                  # wedstrijd_pk
    url_inschrijven_toevoegen_mandje = '/wedstrijden/inschrijven/toevoegen-mandje/'
    url_sporter_voorkeuren = '/sporter/voorkeuren/'

    def _maak_ver_en_sporter(self):
        self.regio112 = Regio.objects.get(regio_nr=112)

        self.ver = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=self.regio112)
        self.ver.save()

        self.ver2 = Vereniging(
                            ver_nr=1001,
                            naam="Andere Club",
                            regio=self.regio112)
        self.ver2.save()

        lid_nr = 102030
        self.account_102030 = self.e2e_create_account(str(lid_nr), 'sporter102030@khsn.not', 'Piet')

        sporter1 = Sporter(
                        lid_nr=lid_nr,
                        geslacht='M',
                        voornaam='Piet',
                        achternaam='Veer',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        adres_code='1234AB56',
                        account=self.account_102030,
                        bij_vereniging=self.ver)
        sporter1.save()
        self.sporter1 = sporter1

        sporterboog1 = SporterBoog(sporter=sporter1, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog1.save()
        self.sporterboog1_r = sporterboog1

        lid_nr += 1
        sporter2 = Sporter(
                    lid_nr=lid_nr,
                    geslacht='V',
                    voornaam='Fa',
                    achternaam='Millie',
                    geboorte_datum='1966-06-04',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    bij_vereniging=self.ver2)
        sporter2.save()
        self.sporter2 = sporter2

        sporterboog2 = SporterBoog(sporter=sporter2, boogtype=self.boog_r, voor_wedstrijd=True)
        sporterboog2.save()
        self.sporterboog2_r = sporterboog2

        lid_nr += 1
        sporter3 = Sporter(
                    lid_nr=lid_nr,
                    geslacht='M',
                    voornaam='Fa',
                    achternaam='Millie',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    adres_code='1234AB56',
                    bij_vereniging=self.ver)
        sporter3.save()
        self.sporter3 = sporter3

    def _maak_wedstrijden(self):
        # maak een wedstrijdlocatie aan
        locatie = WedstrijdLocatie(
                        baan_type='E',      # externe locatie
                        naam='Test locatie')
        locatie.save()
        locatie.verenigingen.add(self.ver)

        over_twee_weken = timezone.now() + timedelta(days=14)
        over_twee_weken = over_twee_weken.date()

        # maak een wedstrijd aan
        wedstrijd = Wedstrijd(
                        titel='Test wedstrijd 1',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=over_twee_weken,
                        datum_einde=over_twee_weken,
                        organiserende_vereniging=self.ver,
                        locatie=locatie,
                        prijs_euro_normaal=Decimal(25.0),
                        prijs_euro_onder18=Decimal(15.0))
        wedstrijd.save()
        self.wedstrijd1 = wedstrijd

        over_drie_weken = timezone.now() + timedelta(days=21)
        over_drie_weken = over_drie_weken.date()

        # maak een wedstrijd aan
        wedstrijd = Wedstrijd(
                        titel='Test wedstrijd 2',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=over_drie_weken,
                        datum_einde=over_drie_weken,
                        organiserende_vereniging=self.ver,
                        locatie=locatie,
                        prijs_euro_normaal=Decimal(25.0),
                        prijs_euro_onder18=Decimal(15.0))
        wedstrijd.save()
        self.wedstrijd2 = wedstrijd

        self.wedstrijd1.boogtypen.add(self.boog_r)
        self.wedstrijd2.boogtypen.add(self.boog_r)

        # maak een R sessie aan
        sessie = WedstrijdSessie(
                        datum=self.wedstrijd1.datum_begin,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        max_sporters=50)
        sessie.save()
        sessie.wedstrijdklassen.add(self.klasse_r)
        self.sessie1 = sessie

        self.wedstrijd1.sessies.add(sessie)

        # maak een R sessie aan
        sessie = WedstrijdSessie(
                        datum=self.wedstrijd2.datum_begin,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        max_sporters=50)
        sessie.save()
        sessie.wedstrijdklassen.add(self.klasse_r)
        self.sessie2 = sessie

        self.wedstrijd2.sessies.add(sessie)

        # maak een wedstrijd aan die we niet in het mandje gaan leggen
        morgen = timezone.now() + timedelta(days=1)
        wedstrijd = Wedstrijd(
                        titel='Test wedstrijd 3',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=morgen,
                        datum_einde=morgen,
                        organiserende_vereniging=self.ver,
                        locatie=locatie,
                        prijs_euro_normaal=Decimal(25.0),
                        prijs_euro_onder18=Decimal(15.0))
        wedstrijd.save()
        self.wedstrijd3 = wedstrijd

    def _maak_inschrijvingen(self):
        regel = BestellingRegel(
                    korte_beschrijving='Wedstrijd %s' % repr(self.wedstrijd1.titel),
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD,
                    bedrag_euro=self.wedstrijd1.prijs_euro_normaal)
        regel.save()
        self.regel1 = regel

        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            wedstrijd=self.wedstrijd1,
                            sessie=self.sessie1,
                            sporterboog=self.sporterboog1_r,
                            wedstrijdklasse=self.klasse_r,
                            bestelling=regel,
                            koper=self.account_102030,
                            korting=None)
        inschrijving.save()
        self.inschrijving1 = inschrijving

        regel = BestellingRegel(
                        korte_beschrijving='Wedstrijd %s' % repr(self.wedstrijd2.titel),
                        code=BESTELLING_REGEL_CODE_WEDSTRIJD,
                        bedrag_euro=self.wedstrijd2.prijs_euro_normaal)
        regel.save()
        self.regel2 = regel

        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            wedstrijd=self.wedstrijd2,
                            sessie=self.sessie2,
                            sporterboog=self.sporterboog1_r,
                            wedstrijdklasse=self.klasse_r,
                            bestelling=regel,
                            koper=self.account_102030,
                            korting=None)
        inschrijving.save()
        self.inschrijving2 = inschrijving

        regel = BestellingRegel(
                        korte_beschrijving='Wedstrijd %s' % repr(self.wedstrijd1.titel),
                        code=BESTELLING_REGEL_CODE_WEDSTRIJD,
                        bedrag_euro=self.wedstrijd1.prijs_euro_normaal)
        regel.save()
        self.regel3 = regel

        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            wedstrijd=self.wedstrijd1,
                            sessie=self.sessie1,
                            sporterboog=self.sporterboog2_r,
                            wedstrijdklasse=self.klasse_r,
                            bestelling=regel,
                            koper=self.account_102030,
                            korting=None)
        inschrijving.save()
        self.inschrijving3 = inschrijving

    def _maak_kortingen(self):
        korting_s = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_SPORTER,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver,
                            percentage=95,
                            voor_sporter=self.sporter1)
        korting_s.save()
        self.korting_s = korting_s
        # print('korting_s: %s' % korting_s)

        # korting niet voor sporter in mandje
        korting_s2 = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_SPORTER,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver,
                            percentage=15,
                            voor_sporter=self.sporter3)
        korting_s2.save()
        self.korting_s2 = korting_s2
        # print('korting_s2: %s' % korting_s2)

        korting_v = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_VERENIGING,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver,
                            percentage=50)
        korting_v.save()
        self.korting_v = korting_v
        # print('korting_v: %s' % korting_v)

        korting_v2 = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_VERENIGING,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver2,
                            percentage=50)
        korting_v2.save()
        self.korting_v2 = korting_v2
        # print('korting_v2: %s' % korting_v2)

        korting_c = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_COMBI,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver,
                            percentage=50)
        korting_c.save()
        self.korting_c = korting_c
        # print('korting_c: %s' % korting_c)

    def setUp(self):
        """ initialisatie van de test case """

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.klasse_r = KalenderWedstrijdklasse.objects.get(volgorde=120)

        self._maak_ver_en_sporter()
        self._maak_wedstrijden()
        self._maak_inschrijvingen()
        self._maak_kortingen()

    def test_korting_persoonlijk(self):
        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        # regel1 en regel2 zijn wedstrijden

        # geen kortingen
        regels = [self.regel1.pk, self.regel2.pk, self.regel3.pk]
        res = bepaal.kies_kortingen(regels)
        self.assertEqual(res, [])

        # maak een korting beschikbaar voor een wedstrijd
        self.korting_s.voor_wedstrijden.add(self.wedstrijd1)
        self.korting_s.voor_wedstrijden.add(self.wedstrijd3)        # ligt niet in mandje

        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        regels = [self.regel1.pk, self.regel2.pk, self.regel3.pk]
        res = bepaal.kies_kortingen(regels)
        # print(stdout.getvalue())
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)
        regel = res[0]
        self.assertTrue(isinstance(regel, BestellingRegel))
        # print(regel)
        self.assertEqual(regel.code, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
        self.assertEqual(regel.korte_beschrijving, 'Persoonlijke korting: 95%')
        self.assertEqual(regel.korting_redenen, '')     # TODO: zou alle redenen voor deze korting moeten bevatten
        self.assertEqual(regel.korting_ver_nr, self.ver.ver_nr)
        self.assertEqual(round(regel.bedrag_euro, 2), -23.75)     # 95% van 25 euro
        self.assertFalse('[ERROR]' in stdout.getvalue())
        self.assertFalse('[WARNING]' in stdout.getvalue())

        # wel kortingen, geen inschrijvingen
        WedstrijdInschrijving.objects.all().delete()
        leeg = list()
        res = bepaal.kies_kortingen(leeg)
        # print(stdout.getvalue())
        self.assertEqual(res, leeg)

        # geen kortingen
        WedstrijdKorting.objects.all().delete()
        leeg = list()
        res = bepaal.kies_kortingen(leeg)
        self.assertEqual(res, leeg)

    def test_korting_vereniging(self):
        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        # regel1 en regel2 zijn wedstrijden

        # geen kortingen
        regels = [self.regel1.pk, self.regel2.pk]
        res = bepaal.kies_kortingen(regels)
        self.assertEqual(res, [])

        # maak een korting beschikbaar voor een wedstrijd
        self.korting_v.voor_wedstrijden.add(self.wedstrijd1)
        self.korting_v2.voor_wedstrijden.add(self.wedstrijd3)        # ligt niet in mandje

        regels = [self.regel1.pk, self.regel2.pk]
        res = bepaal.kies_kortingen(regels)
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)
        regel = res[0]
        self.assertTrue(isinstance(regel, BestellingRegel))
        self.assertEqual(regel.code, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
        self.assertEqual(regel.korte_beschrijving, 'Verenigingskorting: 50%')
        self.assertEqual(regel.korting_redenen, '')     # TODO: zou alle redenen voor deze korting moeten bevatten
        self.assertEqual(regel.korting_ver_nr, self.ver.ver_nr)
        self.assertEqual(round(regel.bedrag_euro, 2), -12.50)     # 50% van 25 euro
        self.assertFalse('[ERROR]' in stdout.getvalue())
        self.assertFalse('[WARNING]' in stdout.getvalue())

    def test_korting_combi(self):
        # combi-korting
        self.korting_c.voor_wedstrijden.add(self.wedstrijd1)
        self.korting_c.voor_wedstrijden.add(self.wedstrijd2)

        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        regels = [self.regel1.pk, self.regel2.pk, self.regel3.pk]
        res = bepaal.kies_kortingen(regels)
        # print(stdout.getvalue())
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)
        regel = res[0]
        self.assertTrue(isinstance(regel, BestellingRegel))
        self.assertEqual(regel.korte_beschrijving, 'Combinatiekorting: 50%')
        self.assertEqual(regel.korting_redenen, 'Test wedstrijd 1||Test wedstrijd 2')
        self.assertEqual(round(regel.bedrag_euro, 2), -25.00)

        # maar 1 van de wedstrijden van de combinatiekorting
        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        regels = [self.regel1.pk]
        res = bepaal.kies_kortingen(regels)
        # print(stdout.getvalue())
        leeg = list()
        self.assertEqual(res, leeg)

        # zowel persoonlijke als combi kortingen
        self.korting_s.voor_wedstrijden.add(self.wedstrijd1)
        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        regels = [self.regel1.pk, self.regel2.pk, self.regel3.pk]
        res = bepaal.kies_kortingen(regels)
        # print(stdout.getvalue())
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)
        regel = res[0]
        # print(regel)
        self.assertEqual(regel.code, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
        self.assertEqual(regel.korte_beschrijving, 'Combinatiekorting: 50%')
        self.assertEqual(round(regel.bedrag_euro, 2), -25.0)
        self.assertEqual(regel.korting_redenen, 'Test wedstrijd 1||Test wedstrijd 2')

        # persoonlijke korting wordt belangrijker
        self.regel1.bedrag_euro = Decimal(250.0)
        self.regel1.save(update_fields=['bedrag_euro'])
        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        regels = [self.regel1.pk, self.regel2.pk, self.regel3.pk]
        res = bepaal.kies_kortingen(regels)
        # print(stdout.getvalue())
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)
        regel = res[0]
        self.assertEqual(regel.code, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
        self.assertEqual(regel.korte_beschrijving, 'Persoonlijke korting: 95%')
        self.assertEqual(round(regel.bedrag_euro, 2), -237.50)
        self.assertEqual(regel.korting_redenen, '')

        # nog een keer, zonder verbose
        self.regel1.bedrag_euro = Decimal(250.0)
        self.regel1.save(update_fields=['bedrag_euro'])
        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=False)
        regels = [self.regel1.pk, self.regel2.pk, self.regel3.pk]
        res = bepaal.kies_kortingen(regels)
        # print(stdout.getvalue())
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)

    def test_eerdere(self):
        # combi-korting voor situatie: 1x al ingeschreven + 1x in mandje
        self.korting_c.voor_wedstrijden.add(self.wedstrijd1)
        self.korting_c.voor_wedstrijden.add(self.wedstrijd2)

        # schrijf in op wedstrijd 1
        self.inschrijving1.status = WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF
        self.inschrijving1.save(update_fields=['status'])

        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout, verbose=True)
        regels = [self.regel2.pk]
        res = bepaal.kies_kortingen(regels)
        # print(stdout.getvalue())
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)
        regel = res[0]
        self.assertTrue(isinstance(regel, BestellingRegel))
        self.assertEqual(regel.korte_beschrijving, 'Combinatiekorting: 50%')
        self.assertEqual(regel.korting_redenen, 'Test wedstrijd 1||Test wedstrijd 2')
        self.assertEqual(round(regel.bedrag_euro, 2), -12.50)


# end of file
