# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Competitie.test_fase import zet_competitie_fase
from Competitie.test_competitie import maak_competities_en_zet_fase_b
from Competitie.models import (Competitie, DeelCompetitie, CompetitieKlasse,
                               LAAG_REGIO, LAAG_RK, LAAG_BK,
                               RegioCompetitieSchutterBoog, DeelcompetitieKlasseLimiet,
                               CompetitieMutatie, MUTATIE_INITIEEL, MUTATIE_CUT, MUTATIE_AFMELDEN,
                               MUTATIE_COMPETITIE_OPSTARTEN, MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M,
                               KampioenschapSchutterBoog, DEELNAME_ONBEKEND, DEELNAME_JA, DEELNAME_NEE)
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime
import io


class TestCompRayonMutatiesRK(E2EHelpers, TestCase):

    """ tests voor de CompRayon applicatie, mutaties van RK/BK deelnemers lijsten """

    url_lijst_rk = '/bondscompetities/rk/lijst-rayonkampioenschappen/%s/'  # deelcomp_rk.pk
    url_wijzig_status = '/bondscompetities/rk/lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/%s/'  # deelnemer_pk
    url_wijzig_cut_rk = '/bondscompetities/rk/planning/%s/limieten/'  # deelcomp_rk.pk

    testdata = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 200000

        self.boogtype = BoogType.objects.get(afkorting='R')

        self._maak_competitie()
        self._maak_verenigingen_schutters()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        ver = NhbVereniging.objects.all()[0]
        self.account_bko = self._prep_beheerder_lid('BKO', ver)
        self.account_rko1 = self._prep_beheerder_lid('RKO1', ver)

        self.functie_bko.accounts.add(self.account_bko)
        self.functie_rko1.accounts.add(self.account_rko1)

        # zet de competitie in fase F
        zet_competitie_fase(self.comp, 'F')

        self.url_lijst = self.url_lijst_rk % self.deelcomp_rk.pk

    def _maak_lid_schutterboog(self, ver, deelcomp, aantal_scores):
        # lid aanmaken
        self._next_lid_nr += 1
        sporter = Sporter(lid_nr=self._next_lid_nr,
                          geslacht='M',
                          voornaam='Voornaam',
                          achternaam='Achternaam',
                          geboorte_datum=datetime.date(1972, 3, 4),
                          sinds_datum=datetime.date(2010, 11, 12),
                          bij_vereniging=ver,
                          email='lid@vereniging.nl')
        sporter.save()

        # schutterboog aanmaken
        sporterboog = SporterBoog(sporter=sporter,
                                  boogtype=self.boogtype,
                                  voor_wedstrijd=True)
        sporterboog.save()

        self.gemiddelde += 0.01

        # inschrijven voor de competitie
        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                 sporterboog=sporterboog,
                                                 bij_vereniging=ver,
                                                 gemiddelde=self.gemiddelde,
                                                 klasse=self.klasse)
        aanmelding.aantal_scores = aantal_scores
        aanmelding.save()

    def _maak_verenigingen_schutters(self):
        for regio in NhbRegio.objects.filter(regio_nr__in=(101, 102, 103, 104)):
            ver = NhbVereniging()
            ver.naam = "Grote Club %s" % regio.regio_nr
            ver.ver_nr = 1000 + regio.regio_nr
            ver.regio = regio
            ver.save()

            self.gemiddelde = 6.0 + (regio.regio_nr - 101) + (regio.regio_nr - 100) / 1000.0

            deelcomp = DeelCompetitie.objects.get(competitie=self.comp,
                                                  laag=LAAG_REGIO,
                                                  nhb_regio=regio)

            # maak 5 schutters aan + 1 die niet mee mag doen
            self._maak_lid_schutterboog(ver, deelcomp, 6)
            self._maak_lid_schutterboog(ver, deelcomp, 6)
            self._maak_lid_schutterboog(ver, deelcomp, 4)       # te weinig scores
            self._maak_lid_schutterboog(ver, deelcomp, 6)
            self._maak_lid_schutterboog(ver, deelcomp, 7)
            self._maak_lid_schutterboog(ver, deelcomp, 6)
        # for

    def _maak_competitie(self):
        # zet de competitie klaar aan het einde van de regiocompetitie
        # zodat de BKO deze door kan zetten
        # er moet dan in 1 rayon en 1 wedstrijdklasse 8 deelnemers komen
        # creëer een competitie met deelcompetities
        self.comp, _ = maak_competities_en_zet_fase_b(startjaar=2019)

        self.client.logout()        # TODO: nodig?

        self.klasse = (CompetitieKlasse
                       .objects
                       .filter(competitie=self.comp,
                               indiv__boogtype=self.boogtype)
                       .order_by('-min_ag'))[0]

        self.deelcomp_rk = DeelCompetitie.objects.get(competitie=self.comp,
                                                      laag=LAAG_RK,
                                                      nhb_rayon__rayon_nr=1)

        # zet de cut op 8
        self.cut = DeelcompetitieKlasseLimiet(deelcompetitie=self.deelcomp_rk,
                                              klasse=self.klasse,
                                              limiet=8)
        self.cut.save()

        self.functie_bko = DeelCompetitie.objects.get(competitie=self.comp, laag=LAAG_BK).functie
        self.functie_rko1 = self.deelcomp_rk.functie

    def _prep_beheerder_lid(self, voornaam, ver):
        sporter = Sporter()
        sporter.lid_nr = self._next_lid_nr = self._next_lid_nr + 1
        sporter.geslacht = "V"
        sporter.voornaam = voornaam
        sporter.achternaam = "Tester"
        sporter.email = voornaam.lower() + "@nhb.test"
        sporter.geboorte_datum = datetime.date(1972, 3, 4)
        sporter.sinds_datum = datetime.date(2010, 11, 12)
        sporter.bij_vereniging = ver
        sporter.save()

        account = self.e2e_create_account(sporter.lid_nr,
                                          sporter.email,
                                          sporter.voornaam,
                                          accepteer_vhpg=True)
        return account

    def _sluit_alle_regiocompetities(self, comp):
        # deze functie sluit alle regiocompetities af zodat de competitie in fase G komt
        comp.bepaal_fase()
        # print(comp.fase)
        self.assertTrue('B' < comp.fase < 'G')
        for deelcomp in DeelCompetitie.objects.filter(competitie=comp, laag=LAAG_REGIO):
            if not deelcomp.is_afgesloten:      # pragma: no branch
                deelcomp.is_afgesloten = True
                deelcomp.save()
        # for

        comp.bepaal_fase()
        self.assertEqual(comp.fase, 'G')

    def _begin_rk(self):
        self._sluit_alle_regiocompetities(self.comp)

        # doorzetten naar RK fase, door BKO
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_bko)
        url = '/bondscompetities/%s/doorzetten/rk/' % self.comp.pk
        self.client.post(url)

        # wacht op het uitvoeren van de achtergrondactiviteit
        self._verwerk_mutaties(135)

        self.comp = Competitie.objects.get(pk=self.comp.pk)
        self.e2e_wissel_naar_functie(self.functie_rko1)

    @staticmethod
    def _dump_deelnemers():                 # pragma: no cover
        print('')
        print('====================================================================')
        print('Deelnemers:')
        for obj in KampioenschapSchutterBoog.objects.order_by('volgorde'):
            print('  rank=%s, volgorde=%s, lid_nr=%s, gem=%s, deelname=%s, label=%s' % (
                obj.rank, obj.volgorde, obj.sporterboog.sporter.lid_nr, obj.gemiddelde,
                obj.deelname, obj.kampioen_label))
        print('====================================================================')

    @staticmethod
    def _get_rank_volg(alleen_kampioenen=False, alle=False):
        if alleen_kampioenen:
            # verwijder iedereen zonder kampioen label
            objs = KampioenschapSchutterBoog.objects.exclude(kampioen_label='')
        elif alle:                          # pragma: no branch
            # all deelnemers
            objs = KampioenschapSchutterBoog.objects.all()
        else:
            # verwijder de kampioenen
            objs = KampioenschapSchutterBoog.objects.filter(kampioen_label='')      # pragma: no cover

        objs = objs.order_by('volgorde')

        rank = list()
        volg = list()
        for obj in objs:
            rank.append(obj.rank)
            volg.append(obj.volgorde)
        # for
        return rank, volg

    def _check_volgorde_en_rank(self):
        rank, volg = self._get_rank_volg(alle=True)

        rank_ok = list()
        volg_ok = list()

        exp_nr = 1
        for nr in rank:
            if nr == 0:
                rank_ok.append(0)
            else:
                rank_ok.append(exp_nr)
                exp_nr += 1
        # for

        exp_nr = 1
        for _ in volg:
            volg_ok.append(exp_nr)
            exp_nr += 1
        # for

        self.assertEqual(volg, volg_ok)
        self.assertEqual(rank, rank_ok)

    def _verwerk_mutaties(self, max_mutaties=20, show=False, check_duration=True):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()

        if max_mutaties > 0:
            with self.assert_max_queries(max_mutaties, check_duration=check_duration):
                management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)
        else:
            management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if show:                    # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

    def test_bko_doorzetten(self):
        # competitie doorzetten en lijst deelnemers controleren

        # 4 regio's met 6 schutters waarvan 1 met te weinig scores
        self.assertEqual(4*6, RegioCompetitieSchutterBoog.objects.count())
        self._begin_rk()        # BB met rol RKO1
        self.assertEqual(4*5, KampioenschapSchutterBoog.objects.count())

        self._check_volgorde_en_rank()

        # controleer dat de regiokampioenen boven de cut staan
        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 6, 7, 8])
        self.assertEqual(rank, volg)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_opnieuw_initieel(self):
        # met de MUTATIE_INITIEEL kunnen we ook een 'reset' uitvoeren
        # daarbij wordt rekening gehouden met schutters die afgemeld zijn
        self._begin_rk()

        # self._dump_deelnemers()

        # meld een paar schutters af: 1 kampioen + 1 schutter boven de cut
        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=1)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=3)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=18)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(92)
        # self._dump_deelnemers()

        CompetitieMutatie(mutatie=MUTATIE_INITIEEL,
                          deelcompetitie=self.deelcomp_rk).save()
        self._verwerk_mutaties(44)
        # self._dump_deelnemers()
        self._check_volgorde_en_rank()

        # nu zonder limiet
        DeelcompetitieKlasseLimiet.objects.all().delete()
        CompetitieMutatie(mutatie=MUTATIE_INITIEEL,
                          deelcompetitie=self.deelcomp_rk).save()
        self._verwerk_mutaties(44)

    def test_rko_bevestigen(self):
        # bevestig deelname door een schutter en een reserve
        self._begin_rk()        # BB met rol RKO1

        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=4)
        self.assertEqual(deelnemer.rank, 4)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(deelnemer.deelname, DEELNAME_JA)
        self.assertEqual(deelnemer.rank, 4)
        self.assertEqual(deelnemer.volgorde, 4)

        self._check_volgorde_en_rank()

    def test_rko_afmelden_onder_cut(self):
        # een reserve-schutter meldt zich af
        # dit heeft geen invloed op de deelnemers-lijst
        self._begin_rk()        # BB met rol RKO1

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=10)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(34)

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(deelnemer.deelname, DEELNAME_NEE)
        self.assertEqual(deelnemer.rank, 0)
        self.assertEqual(deelnemer.volgorde, 10)

        self._check_volgorde_en_rank()

    def test_rko_afmelden_boven_cut(self):
        # kandidaat-schutter (boven de cut) meldt zich af
        # reserve-schutter wordt opgeroepen
        self._begin_rk()        # BB met rol RKO1

        reserve = KampioenschapSchutterBoog.objects.get(volgorde=9)  # cut ligt op 8
        self.assertEqual(reserve.deelname, DEELNAME_ONBEKEND)
        self.assertEqual(reserve.rank, 9)
        self.assertEqual(reserve.volgorde, 9)

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=4)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(37)

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(deelnemer.deelname, DEELNAME_NEE)
        self.assertEqual(deelnemer.rank, 0)
        self.assertEqual(deelnemer.volgorde, 4)

        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_ONBEKEND)
        self.assertEqual(reserve.rank, 6)
        self.assertEqual(reserve.volgorde, 7)

        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_onder_cut(self):
        # een reserve-schutter meldt zich af en weer aan
        # dit heeft geen invloed op de deelnemers-lijst
        self._begin_rk()        # BB met rol RKO1

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(rank=10)    # cut ligt op 8
        self.assertEqual(reserve.volgorde, 10)
        url = self.url_wijzig_status % reserve.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(34)

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_NEE)
        self.assertEqual(reserve.rank, 0)
        self.assertEqual(reserve.volgorde, 10)

        url = self.url_wijzig_status % reserve.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(40)

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_JA)
        self.assertEqual(reserve.rank, 10)
        self.assertEqual(reserve.volgorde, 10)

        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_einde_lijst(self):
        # opnieuw aangemelde schutter komt helemaal aan het einde van de reserve-lijst
        self._begin_rk()        # BB met rol RKO1

        # self._dump_deelnemers()
        pk = KampioenschapSchutterBoog.objects.order_by('-rank')[0].pk
        url = self.url_wijzig_status % pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(66)
        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_boven_cut(self):
        # kandidaat-schutter (boven de cut) meldt zich af
        # reserve-schutter wordt opgeroepen
        # schutter meldt zichzelf daarna weer aan en komt in de lijst met reserve-schutters
        # gesorteerd op gemiddelde
        self._begin_rk()        # BB met rol RKO1
        # self._dump_deelnemers()

        deelnemer = KampioenschapSchutterBoog.objects.get(rank=3)    # cut ligt op 8
        self.assertEqual(deelnemer.volgorde, 3)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties(37)
        # self._dump_deelnemers()

        reserve = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        del deelnemer
        self.assertEqual(reserve.deelname, DEELNAME_NEE)
        self.assertEqual(reserve.rank, 0)
        self.assertEqual(reserve.volgorde, 3)

        # opnieuw aanmelden --> wordt als reserve-schutter op de lijst gezet
        url = self.url_wijzig_status % reserve.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties(40)
        # self._dump_deelnemers()

        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_JA)
        self.assertEqual(reserve.rank, 9)
        self.assertEqual(reserve.volgorde, 9)

        self._check_volgorde_en_rank()

    def test_rko_oproep_reserve_hoog_gemiddelde(self):
        # de eerste reserve heeft een hoger gemiddelde dan de laatste deelnemers
        # na afmelden van een deelnemer wordt de eerste reserve opgeroepen
        # de lijst met deelnemers wordt gesorteerd op gemiddelde
        self._begin_rk()        # BB met rol RKO1

        # bereik dit effect door nr 3 af te melden en daarna weer aan te melden
        deelnemer = KampioenschapSchutterBoog.objects.get(rank=3)    # cut ligt op 8
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(69)

        reserve = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(reserve.volgorde, 9)
        del deelnemer

        # meld nu iemand anders af zodat de eerste reserve opgeroepen wordt
        afmelden = KampioenschapSchutterBoog.objects.get(rank=4)    # cut ligt op 8
        url = self.url_wijzig_status % afmelden.pk
        # self._dump_deelnemers()
        self.client.post(url, {'afmelden': 1, 'snel': 1})
        # self._dump_deelnemers()

        self._verwerk_mutaties(37)

        ex_reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(ex_reserve.volgorde, 3)
        self.assertEqual(ex_reserve.rank, 3)

        # de zojuist afgemelde schutter staat nog steeds waar hij stond
        # maar is 1 omlaag geschoven door de ingeschoven reserve schutter
        afmelden = KampioenschapSchutterBoog.objects.get(pk=afmelden.pk)
        self.assertEqual(afmelden.rank, 0)
        self.assertEqual(afmelden.volgorde, 5)

        self._check_volgorde_en_rank()

    def test_rko_kampioen_opnieuw_aanmelden(self):
        # regiokampioen meldt zich af en daarna weer aan
        # komt in de lijst met reserve-schutters
        self._begin_rk()        # BB met rol RKO1

        # bereik dit effect door nr 8 af te melden en daarna weer aan te melden
        # dit is een regiokampioen met behoorlijk lage gemiddelde
        # self._dump_deelnemers()
        kampioen = KampioenschapSchutterBoog.objects.get(rank=8)    # cut ligt op 8
        url = self.url_wijzig_status % kampioen.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties(70)

        # kijk wat er met de kampioen gebeurd is
        # self._dump_deelnemers()
        kampioen = KampioenschapSchutterBoog.objects.get(pk=kampioen.pk)
        self.assertEqual(kampioen.deelname, DEELNAME_JA)
        self.assertEqual(kampioen.rank, 16)
        self.assertEqual(kampioen.volgorde, 16)

        self._check_volgorde_en_rank()

    def test_rko_drie_kampioenen_opnieuw_aanmelden(self):
        self._begin_rk()        # BB met rol RKO1

        pks = (KampioenschapSchutterBoog
               .objects
               .exclude(kampioen_label='')
               .order_by('volgorde')
               .values_list('pk', flat=True))
        pks = list(pks)
        for pk in pks[:3]:
            url = self.url_wijzig_status % pk
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
            self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        # for

        self._verwerk_mutaties(95)
        # self._dump_deelnemers()

        # de laatste kampioen staat nog steeds onderaan in de lijst
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[3])
        self.assertEqual(kampioen.rank, 8)
        self.assertEqual(kampioen.volgorde, 11)

        # meld de drie kampioenen weer aan
        url = self.url_wijzig_status % pks[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[1]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[2]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(104)
        # self._dump_deelnemers()

        # controleer dat ze in de reserve schutters lijst staan, gesorteerd op gemiddelde
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[0])
        self.assertEqual(kampioen.rank, 9)
        self.assertEqual(kampioen.volgorde, 9)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[1])
        self.assertEqual(kampioen.rank, 10)
        self.assertEqual(kampioen.volgorde, 10)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[2])
        self.assertEqual(kampioen.rank, 12)
        self.assertEqual(kampioen.volgorde, 12)

        self._check_volgorde_en_rank()

    def test_rko_cut24_drie_kampioenen_opnieuw_aanmelden(self):
        self.cut.delete()       # verwijder de cut van 8
        self._begin_rk()        # BB met rol RKO1
        # self._dump_deelnemers()

        pks = (KampioenschapSchutterBoog
               .objects
               .exclude(kampioen_label='')
               .order_by('volgorde')
               .values_list('pk', flat=True))
        pks = list(pks)
        for pk in pks[:3]:
            url = self.url_wijzig_status % pk
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
            self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        # for

        self._verwerk_mutaties(86)
        # self._dump_deelnemers()

        # de laatste kampioen staat nog steeds onderaan in de lijst
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[3])
        self.assertEqual(kampioen.rank, 13)
        self.assertEqual(kampioen.volgorde, 16)

        # meld de drie kampioenen weer aan
        url = self.url_wijzig_status % pks[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[1]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[2]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(100)
        # self._dump_deelnemers()

        # controleer dat ze op hun oude plek terug zijn gekomen
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[0])
        self.assertEqual(kampioen.rank, 1)
        self.assertEqual(kampioen.volgorde, 1)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[1])
        self.assertEqual(kampioen.rank, 6)
        self.assertEqual(kampioen.volgorde, 6)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[2])
        self.assertEqual(kampioen.rank, 11)
        self.assertEqual(kampioen.volgorde, 11)

        self._check_volgorde_en_rank()

    def test_verlaag_cut(self):
        # verplaats de cut en controleer de inhoud na de update
        self._begin_rk()        # BB met rol RKO1

        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 6, 7, 8])
        self.assertEqual(volg, [1, 6, 7, 8])

        # verplaats de cut naar 20
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.klasse.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 20, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)     # check success
        self._verwerk_mutaties(35)

        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 6, 11, 16])
        self.assertEqual(volg, [1, 6, 11, 16])

        # meld ook 3 mensen af: 1 kampioen en 1 niet-kampioen boven de cut + 1 onder cut
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=1).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=2).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=10).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        # verplaats de cut naar 8
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.klasse.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 8, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)     # check success
        self._verwerk_mutaties(114)     # TODO: probeer te verlagen
        # self._dump_deelnemers()

        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [0, 4, 7, 8])
        self.assertEqual(volg, [1, 6, 9, 10])

        self._check_volgorde_en_rank()

    def test_verhoog_cut(self):
        # verplaats de cut en controleer de inhoud na de update
        self._begin_rk()        # BB met rol RKO1

        # default cut is 8
        # verhoog de cut naar 16
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.klasse.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 16, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)     # check success
        # self._verwerk_mutaties()

        # meld iemand af
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=2).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        # verhoog de cut naar 20
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.klasse.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 20, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)     # check success
        self._verwerk_mutaties(85)
        # self._dump_deelnemers()

        rank, volg = self._get_rank_volg(alle=True)
        self.assertEqual(rank[:4], [1, 0, 2, 3])
        self.assertEqual(volg[:4], [1, 2, 3, 4])

        self._check_volgorde_en_rank()

    def test_rko_allemaal_afmelden(self):
        self._begin_rk()        # BB met rol RKO1

        pks = list(KampioenschapSchutterBoog.objects.values_list('pk', flat=True))
        for pk in pks:
            url = self.url_wijzig_status % pk
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
            self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success
        # for

        self._verwerk_mutaties(-1)      # actual = 556 but that just because of many queued-up operations

        self._check_volgorde_en_rank()

    def test_dubbel(self):
        self._begin_rk()        # BB met rol RKO1

        # dubbel afmelden
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=2).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        # dubbel aanmelden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(100)

    def test_bad(self):
        self._begin_rk()        # BB met rol RKO1

        # slechte mutatie code
        mutatie = CompetitieMutatie(mutatie=0,
                                    deelnemer=KampioenschapSchutterBoog.objects.all()[0],
                                    door='Tester')
        mutatie.save()

        self.assertTrue("???" in str(mutatie))  # geen beschrijving beschikbaar
        mutatie.mutatie = MUTATIE_INITIEEL
        self.assertTrue(str(mutatie) != "")     # wel een beschrijving

        mutatie.mutatie = MUTATIE_CUT
        self.assertTrue(str(mutatie) != "")     # wel een beschrijving

        mutatie.mutatie = MUTATIE_AFMELDEN
        self.assertTrue(str(mutatie) != "")     # wel een beschrijving

        mutatie.is_verwerkt = True
        self.assertTrue(str(mutatie) != "")     # wel een beschrijving

        # mutatie die al verwerkt is
        CompetitieMutatie(mutatie=0,
                          is_verwerkt=True,
                          deelnemer=KampioenschapSchutterBoog.objects.all()[0],
                          door='Tester').save()

        # mutatie nieuw record van 24 wordt niet opgeslagen
        CompetitieMutatie(mutatie=MUTATIE_CUT,
                          deelcompetitie=self.deelcomp_rk,
                          klasse=self.klasse,
                          cut_oud=23,
                          cut_nieuw=24,  # verwijder oude record
                          door='Tester').save()

        CompetitieMutatie(mutatie=MUTATIE_CUT,
                          deelcompetitie=self.deelcomp_rk,
                          klasse=self.klasse,
                          cut_oud=23,
                          cut_nieuw=24,
                          door='Tester').save()

        # mutatie die geen wijziging is
        CompetitieMutatie(mutatie=MUTATIE_CUT,
                          deelcompetitie=self.deelcomp_rk,
                          klasse=self.klasse,
                          cut_oud=24,
                          cut_nieuw=24,
                          door='Tester').save()

        self._verwerk_mutaties(69)

    def test_verwerk_all(self):
        # vraag de achtergrond taak om de mutaties te verwerken
        # gebruik --all
        # en laat deze iets langer lopen
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20, check_duration=False):     # 2 seconden is boven de limiet
            management.call_command('regiocomp_mutaties', '2', '--quick', '--all', stderr=f1, stdout=f2)

    def test_competitie(self):
        # competitie opstarten
        CompetitieMutatie(mutatie=MUTATIE_COMPETITIE_OPSTARTEN,
                          door='Tester').save()
        CompetitieMutatie(mutatie=MUTATIE_COMPETITIE_OPSTARTEN,  # triggered "al opgestart" pad
                          door='Tester').save()
        self._verwerk_mutaties(32)

        # AG vaststellen
        CompetitieMutatie(mutatie=MUTATIE_AG_VASTSTELLEN_18M,
                          door='Tester').save()
        CompetitieMutatie(mutatie=MUTATIE_AG_VASTSTELLEN_25M,
                          door='Tester').save()
        self._verwerk_mutaties(20)


# end of file
