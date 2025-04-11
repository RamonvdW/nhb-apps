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
from Competitie.models import Competitie, CompetitieIndivKlasse, Regiocompetitie, RegiocompetitieSporterBoog
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE, WEDSTRIJD_STATUS_GEACCEPTEERD,
                                    WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING, WEDSTRIJD_KORTING_COMBI)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdKorting, Kwalificatiescore
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

        # maak een test vereniging
        self.ver = Vereniging(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=self.regio112)
        self.ver.save()

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
                    bij_vereniging=self.ver)
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

        # korting niet voor sporter in mandje
        korting_s3 = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_SPORTER,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver,
                            percentage=15,
                            voor_sporter=self.sporter3)
        korting_s3.save()
        self.korting_s2 = korting_s3

        korting_v = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_VERENIGING,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver,
                            percentage=75)
        korting_v.save()
        self.korting_v = korting_v

        korting_c = WedstrijdKorting(
                            soort=WEDSTRIJD_KORTING_COMBI,
                            geldig_tot_en_met='2099-01-01',
                            uitgegeven_door=self.ver,
                            percentage=50)
        korting_c.save()
        self.korting_c = korting_c

    def setUp(self):
        """ initialisatie van de test case """

        # self.account_admin = self.e2e_create_account_admin()
        # self.account_admin.is_BB = True
        # self.account_admin.save()

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.klasse_r = KalenderWedstrijdklasse.objects.get(volgorde=120)

        self._maak_ver_en_sporter()
        self._maak_wedstrijden()
        self._maak_inschrijvingen()
        self._maak_kortingen()

        # self.functie_mwz = Functie.objects.get(rol='MWZ')
        #
        # self.functie_hwl = maak_functie('HWL Ver 1000', 'HWL')
        # self.functie_hwl.vereniging = self.ver1
        # self.functie_hwl.accounts.add(self.account_admin)
        # self.functie_hwl.save()
        #
        # # wordt HWL, stel sporter voorkeuren in en maak een wedstrijd aan
        # self.e2e_login_and_pass_otp(self.account_admin)
        # self.e2e_wissel_naar_functie(self.functie_hwl)
        #
        # self.lid_nr = 123456
        # self.account = self.e2e_create_account(str(self.lid_nr), 'test@test.not', 'Voornaam')
        #
        # self.boog_c = BoogType.objects.get(afkorting='C')




        # sporterboog = SporterBoog.objects.get(sporter=sporter1, boogtype=self.boog_c)
        # sporterboog.voor_wedstrijd = True
        # sporterboog.save(update_fields=['voor_wedstrijd'])
        # self.sporterboog1c = sporterboog
        #
        # sporter2 = Sporter(
        #             lid_nr=self.lid_nr + 1,
        #             geslacht='V',
        #             voornaam='Fa',
        #             achternaam='Millie',
        #             geboorte_datum='1966-06-04',
        #             sinds_datum='2020-02-02',
        #             adres_code='1234AB56',
        #             bij_vereniging=self.ver1)
        # sporter2.save()
        # self.sporter2 = sporter2
        # get_sporter_voorkeuren(sporter2)
        # resp = self.client.post(self.url_sporter_voorkeuren, {'sporter_pk': sporter2.pk})   # maak alle SporterBoog aan
        # self.assert_is_redirect_not_plein(resp)
        #
        # sporterboog = SporterBoog.objects.get(sporter=sporter2, boogtype=self.boog_c)
        # sporterboog.voor_wedstrijd = True
        # sporterboog.save(update_fields=['voor_wedstrijd'])
        # self.sporterboog2c = sporterboog
        #

        # # wordt HWL en maak een wedstrijd aan
        # self.e2e_login_and_pass_otp(self.account_admin)
        # self.e2e_wissel_naar_functie(self.functie_hwl)

        # resp = self.client.post(self.url_wedstrijden_maak_nieuw, {'keuze': 'khsn'})
        # self.assert_is_redirect_not_plein(resp)

        # self.assertEqual(1, Wedstrijd.objects.count())
        # self.wedstrijd = Wedstrijd.objects.first()
        # url = self.url_wedstrijden_wijzig_wedstrijd % self.wedstrijd.pk
        # self.assert_is_redirect(resp, url)



        # # maak een C sessie aan
        # sessie = WedstrijdSessie(
        #                 datum=self.wedstrijd.datum_begin,
        #                 tijd_begin='10:00',
        #                 tijd_einde='15:00',
        #                 max_sporters=50)
        # sessie.save()
        # self.wedstrijd.sessies.add(sessie)
        # wkls_c = self.wedstrijd.wedstrijdklassen.filter(boogtype__afkorting='C')
        # sessie.wedstrijdklassen.set(wkls_c)
        # self.sessie_c = sessie
        #

        # # schrijf de twee sporters in
        # self.e2e_login_and_pass_otp(self.account)
        # # self.e2e_wisselnaarrol_sporter()
        # # url = self.url_inschrijven_groepje % self.wedstrijd.pk
        #
        # # zorg dat de wedstrijd als 'gesloten' gezien wordt
        # begin = self.wedstrijd.datum_begin
        # self.wedstrijd.datum_begin = timezone.now().date()
        # self.wedstrijd.save(update_fields=['datum_begin'])
        # resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
        #                                                                 'wedstrijd': self.wedstrijd.pk,
        #                                                                 'sporterboog': self.sporterboog1r.pk,
        #                                                                 'sessie': self.sessie_r.pk,
        #                                                                 'klasse': wkls_r[0].pk,
        #                                                                 'boog': self.boog_r.pk})
        # self.assert404(resp, 'Inschrijving is gesloten')
        #
        # self.wedstrijd.datum_begin += timedelta(days=self.wedstrijd.inschrijven_tot - 1)
        # self.wedstrijd.save(update_fields=['datum_begin'])
        # resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
        #                                                                 'wedstrijd': self.wedstrijd.pk,
        #                                                                 'sporterboog': self.sporterboog1r.pk,
        #                                                                 'sessie': self.sessie_r.pk,
        #                                                                 'klasse': wkls_r[0].pk,
        #                                                                 'boog': self.boog_r.pk})
        # self.assert404(resp, 'Inschrijving is gesloten')
        #
        # self.wedstrijd.datum_begin = begin
        # self.wedstrijd.save(update_fields=['datum_begin'])
        #
        # resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
        #                                                                 'wedstrijd': self.wedstrijd.pk,
        #                                                                 'sporterboog': self.sporterboog1r.pk,
        #                                                                 'sessie': self.sessie_r.pk,
        #                                                                 'klasse': wkls_r[0].pk,
        #                                                                 'boog': self.boog_r.pk})
        # self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.assert_html_ok(resp)
        # self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl',
        #                                  'plein/site_layout.dtl'))
        #
        # self.assertEqual(1, WedstrijdInschrijving.objects.count())
        # self.inschrijving1r = WedstrijdInschrijving.objects.first()
        #
        # resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
        #                                                                 'wedstrijd': self.wedstrijd.pk,
        #                                                                 'sporterboog': self.sporterboog1c.pk,
        #                                                                 'sessie': self.sessie_c.pk,
        #                                                                 'klasse': wkls_c[0].pk,
        #                                                                 'boog': self.boog_c.pk})
        # self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.assert_html_ok(resp)
        # self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl',
        #                                  'plein/site_layout.dtl'))
        # self.assertEqual(2, WedstrijdInschrijving.objects.count())
        # self.inschrijving1c = WedstrijdInschrijving.objects.exclude(pk=self.inschrijving1r.pk)[0]
        #
        # resp = self.client.post(self.url_inschrijven_toevoegen_mandje, {'snel': 1,
        #                                                                 'wedstrijd': self.wedstrijd.pk,
        #                                                                 'sporterboog': self.sporterboog2c.pk,
        #                                                                 'sessie': self.sessie_c.pk,
        #                                                                 'klasse': wkls_c[1].pk,
        #                                                                 'boog': self.boog_c.pk})
        # self.assertEqual(resp.status_code, 200)     # 200 = OK
        # self.assert_html_ok(resp)
        # self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl',
        #                                  'plein/site_layout.dtl'))
        # self.assertEqual(3, WedstrijdInschrijving.objects.count())
        # self.inschrijving2 = WedstrijdInschrijving.objects.exclude(pk__in=(self.inschrijving1r.pk,
        #                                                                    self.inschrijving1c.pk))[0]
        #
        # korting = WedstrijdKorting(
        #                 geldig_tot_en_met='2099-12-31',
        #                 soort=WEDSTRIJD_KORTING_VERENIGING,
        #                 uitgegeven_door=self.ver1,
        #                 percentage=42)
        # korting.save()
        #
        # self.inschrijving1r.korting = korting
        # self.inschrijving1r.save(update_fields=['korting'])
        #
        # self.inschrijving2.status = WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
        # self.inschrijving2.korting = korting
        # self.inschrijving2.save(update_fields=['status', 'korting'])

    def test_basis(self):
        stdout = OutputWrapper(io.StringIO())
        bepaal = BepaalAutomatischeKorting(stdout)

        regels = [self.regel1.pk, self.regel2.pk]
        res = bepaal.kies_kortingen(regels)
        self.assertEqual(res, [])

        # maak een korting beschikbaar voor een wedstrijd
        self.korting_s.voor_wedstrijden.add(self.wedstrijd1)
        self.korting_s.voor_wedstrijden.add(self.wedstrijd3)        # ligt niet in mandje

        regels = [self.regel1.pk, self.regel2.pk]
        res = bepaal.kies_kortingen(regels)
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 1)

        regel = res[0]
        self.assertTrue(isinstance(regel, BestellingRegel))
        # print(regel)
        self.assertEqual(regel.code, BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
        self.assertEqual(regel.korte_beschrijving, 'Persoonlijke korting: 95%')
        self.assertEqual(regel.korting_redenen, '')     # TODO: klopt dit?
        self.assertEqual(regel.korting_ver_nr, self.ver.ver_nr)
        self.assertEqual(round(regel.bedrag_euro, 2), -23.75)     # 95% van 25 euro
        self.assertFalse('[ERROR]' in stdout.getvalue())
        self.assertFalse('[WARNING]' in stdout.getvalue())

        # wel kortingen, geen inschrijvingen
        WedstrijdInschrijving.objects.all().delete()
        leeg = list()
        res = bepaal.kies_kortingen(leeg)
        self.assertEqual(res, leeg)

        # geen kortingen
        WedstrijdKorting.objects.all().delete()
        leeg = list()
        res = bepaal.kies_kortingen(leeg)
        self.assertEqual(res, leeg)



# end of file
