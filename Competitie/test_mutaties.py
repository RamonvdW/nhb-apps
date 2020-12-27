# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRegio, NhbVereniging, NhbLid
from Competitie.test_fase import zet_competitie_fase
from Schutter.models import SchutterBoog
from Overig.e2ehelpers import E2EHelpers
from .models import (Competitie, DeelCompetitie, CompetitieKlasse, competitie_aanmaken,
                     LAAG_REGIO, LAAG_RK, LAAG_BK, AG_NUL,
                     RegioCompetitieSchutterBoog,  DeelcompetitieKlasseLimiet,
                     KampioenschapMutatie, MUTATIE_INITIEEL, MUTATIE_CUT, MUTATIE_AFMELDEN,
                     KampioenschapSchutterBoog, DEELNAME_ONBEKEND, DEELNAME_JA, DEELNAME_NEE)
import datetime
import io


class TestCompetitieMutaties(E2EHelpers, TestCase):

    """ unit tests voor de Competitie applicatie, mutaties van RK/BK deelnemers lijsten """

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_nhb_nr = 200000

        self.boogtype = BoogType.objects.get(afkorting='R')

        # maak een BB aan (geen NHB lid)
        self.account_bb = self.e2e_create_account('bb', 'bko@nhb.test', 'BB', accepteer_vhpg=True)
        self.account_bb.is_BB = True
        self.account_bb.save()

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

        self.url_lijst_rk = '/competitie/lijst-rayonkampioenschappen/%s/'    # deelcomp_rk.pk
        self.url_wijzig_status = '/competitie/lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/%s/'  # deelnemer_pk
        self.url_wijzig_cut_rk = '/competitie/planning/rk/%s/limieten/'      # deelcomp_rk.pk

        self.url_lijst = self.url_lijst_rk % self.deelcomp_rk.pk

    def _maak_lid_schutterboog(self, ver, deelcomp, aantal_scores):
        # lid aanmaken
        self._next_nhb_nr += 1
        lid = NhbLid(nhb_nr=self._next_nhb_nr,
                     geslacht='M',
                     voornaam='Voornaam',
                     achternaam='Achternaam',
                     geboorte_datum=datetime.date(1972, 3, 4),
                     sinds_datum=datetime.date(2010, 11, 12),
                     bij_vereniging=ver,
                     email='lid@vereniging.nl')
        lid.save()

        # schutterboog aanmaken
        schutterboog = SchutterBoog(nhblid=lid,
                                    boogtype=self.boogtype,
                                    voor_wedstrijd=True)
        schutterboog.save()

        self.gemiddelde += 0.01

        # inschrijven voor de competitie
        aanmelding = RegioCompetitieSchutterBoog(deelcompetitie=deelcomp,
                                                 schutterboog=schutterboog,
                                                 bij_vereniging=ver,
                                                 aanvangsgemiddelde=AG_NUL,
                                                 gemiddelde=self.gemiddelde,
                                                 klasse=self.klasse)
        aanmelding.aantal_scores = aantal_scores
        aanmelding.save()

    def _maak_verenigingen_schutters(self):
        for regio in NhbRegio.objects.filter(regio_nr__in=(101, 102, 103, 104)):
            ver = NhbVereniging()
            ver.naam = "Grote Club %s" % regio.regio_nr
            ver.nhb_nr = 1000 + regio.regio_nr
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
        self.e2e_login_and_pass_otp(self.account_bb)
        self.e2e_wisselnaarrol_bb()

        # zet de competitie klaar aan het einde van de regiocompetitie
        # zodat de BKO deze door kan zetten
        # er moet dan in 1 rayon en 1 wedstrijdklasse 8 deelnemers komen
        # creëer een competitie met deelcompetities
        competitie_aanmaken(jaar=2019)

        # klassengrenzen vaststellen om de competitie voorbij fase A1 te krijgen
        self.url_klassegrenzen_vaststellen_18 = '/competitie/klassegrenzen/vaststellen/18/'
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)     # check success
        self.client.logout()

        self.comp = Competitie.objects.get(afstand='18')
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
        lid = NhbLid()
        lid.nhb_nr = self._next_nhb_nr = self._next_nhb_nr + 1
        lid.geslacht = "V"
        lid.voornaam = voornaam
        lid.achternaam = "Tester"
        lid.email = voornaam.lower() + "@nhb.test"
        lid.geboorte_datum = datetime.date(1972, 3, 4)
        lid.sinds_datum = datetime.date(2010, 11, 12)
        lid.bij_vereniging = ver
        lid.save()

        account = self.e2e_create_account(lid.nhb_nr,
                                          lid.email,
                                          lid.voornaam,
                                          accepteer_vhpg=True)
        return account

    def _sluit_alle_regiocompetities(self, comp):
        # deze functie sluit alle regiocompetities af zodat de competitie in fase G komt
        comp.zet_fase()
        # print(comp.fase)
        self.assertTrue('B' < comp.fase < 'G')
        for deelcomp in DeelCompetitie.objects.filter(competitie=comp, laag=LAAG_REGIO):
            if not deelcomp.is_afgesloten:      # pragma: no branch
                deelcomp.is_afgesloten = True
                deelcomp.save()
        # for

        comp.zet_fase()
        self.assertEqual(comp.fase, 'G')

    def _begin_rk(self):
        self._sluit_alle_regiocompetities(self.comp)

        # doorzetten naar RK fase, door BKO
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_bko)
        url = '/competitie/planning/doorzetten/%s/rk/' % self.comp.pk
        self.client.post(url)

        self.comp = Competitie.objects.get(pk=self.comp.pk)
        self.e2e_wissel_naar_functie(self.functie_rko1)

    @staticmethod
    def _dump_deelnemers():                 # pragma: no coverage
        print('')
        print('====================================================================')
        print('Deelnemers:')
        for obj in KampioenschapSchutterBoog.objects.order_by('volgorde'):
            print('  rank=%s, volgorde=%s, nhb_nr=%s, gem=%s, deelname=%s, label=%s' % (
                obj.rank, obj.volgorde, obj.schutterboog.nhblid.nhb_nr, obj.gemiddelde,
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
            objs = KampioenschapSchutterBoog.objects.filter(kampioen_label='')      # pragma: no coverage

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

    def _verwerk_mutaties(self, max_mutaties=20, show=False):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(max_mutaties):
            management.call_command('kampioenschap_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if show:                    # pragma: no coverage
            print(f1.getvalue())
            print(f2.getvalue())

    def test_bko_doorzetten(self):
        # competitie doorzetten en lijst deelnemers controleren

        # 4 regio's met 6 schutters waarvan 1 met te weinig scores
        self.assertEqual(4*6, RegioCompetitieSchutterBoog.objects.count())
        self._begin_rk()        # BB met rol RKO1
        self.assertEqual(4*5, KampioenschapSchutterBoog.objects.count())

        self._verwerk_mutaties(150)
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
        self._verwerk_mutaties(150)

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

        self._verwerk_mutaties(90)
        # self._dump_deelnemers()

        KampioenschapMutatie(mutatie=MUTATIE_INITIEEL,
                             deelcompetitie=self.deelcomp_rk).save()
        self._verwerk_mutaties(42)
        # self._dump_deelnemers()
        self._check_volgorde_en_rank()

        # nu zonder limiet
        DeelcompetitieKlasseLimiet.objects.all().delete()
        KampioenschapMutatie(mutatie=MUTATIE_INITIEEL,
                             deelcompetitie=self.deelcomp_rk).save()
        self._verwerk_mutaties(42)

    def test_rko_bevestigen(self):
        # bevestig deelname door een schutter en een reserve
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties(150)

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
        self._verwerk_mutaties(150)

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=10)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(32)

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
        self._verwerk_mutaties(150)

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

        self._verwerk_mutaties(35)

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
        self._verwerk_mutaties(150)

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(rank=10)    # cut ligt op 8
        self.assertEqual(reserve.volgorde, 10)
        url = self.url_wijzig_status % reserve.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(32)

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
        self._verwerk_mutaties(150)

        # self._dump_deelnemers()
        pk = KampioenschapSchutterBoog.objects.order_by('-rank')[0].pk
        url = self.url_wijzig_status % pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(65)
        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_boven_cut(self):
        # kandidaat-schutter (boven de cut) meldt zich af
        # reserve-schutter wordt opgeroepen
        # schutter meldt zichzelf daarna weer aan en komt in de lijst met reserve-schutters
        # gesorteerd op gemiddelde
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties(150)
        # self._dump_deelnemers()

        deelnemer = KampioenschapSchutterBoog.objects.get(rank=3)    # cut ligt op 8
        self.assertEqual(deelnemer.volgorde, 3)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties(35)
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
        self._verwerk_mutaties(150)

        # bereik dit effect door nr 3 af te melden en daarna weer aan te melden
        deelnemer = KampioenschapSchutterBoog.objects.get(rank=3)    # cut ligt op 8
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties(67)

        reserve = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(reserve.volgorde, 9)
        del deelnemer

        # meld nu iemand anders af zodat de eerste reserve opgeroepen wordt
        afmelden = KampioenschapSchutterBoog.objects.get(rank=4)    # cut ligt op 8
        url = self.url_wijzig_status % afmelden.pk
        # self._dump_deelnemers()
        self.client.post(url, {'afmelden': 1, 'snel': 1})
        # self._dump_deelnemers()

        self._verwerk_mutaties(35)

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
        self._verwerk_mutaties(150)

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
        self._verwerk_mutaties(150)

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

        self._verwerk_mutaties(102)
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
        self._verwerk_mutaties(150)
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

        self._verwerk_mutaties(85)
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
        self._verwerk_mutaties(150)

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
        self._verwerk_mutaties(33)

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
        self._verwerk_mutaties(112)     # TODO: probeer te verlagen
        # self._dump_deelnemers()

        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [0, 4, 7, 8])
        self.assertEqual(volg, [1, 6, 9, 10])

        self._check_volgorde_en_rank()

    def test_verhoog_cut(self):
        # verplaats de cut en controleer de inhoud na de update
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties(150)

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
        self._verwerk_mutaties(150)

        pks = list(KampioenschapSchutterBoog.objects.values_list('pk', flat=True))
        for pk in pks:
            url = self.url_wijzig_status % pk
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
            self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success
        # for

        self._verwerk_mutaties(554)     # TODO: reduce

        self._check_volgorde_en_rank()

    def test_dubbel(self):
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties(150)

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
        mutatie = KampioenschapMutatie(mutatie=0,
                                       deelnemer=KampioenschapSchutterBoog.objects.all()[0],
                                       door='Tester')
        mutatie.save()

        self.assertTrue("???" in str(mutatie))  # geen beschrijving beschikbaar
        mutatie.code = MUTATIE_INITIEEL
        self.assertTrue(str(mutatie) != "")     # wel een beschrijving

        mutatie.code = MUTATIE_CUT
        self.assertTrue(str(mutatie) != "")     # wel een beschrijving

        mutatie.code = MUTATIE_AFMELDEN
        self.assertTrue(str(mutatie) != "")     # wel een beschrijving

        # mutatie die al verwerkt is
        KampioenschapMutatie(mutatie=0,
                             is_verwerkt=True,
                             deelnemer=KampioenschapSchutterBoog.objects.all()[0],
                             door='Tester').save()

        # mutatie nieuw record van 24 wordt niet opgeslagen
        KampioenschapMutatie(mutatie=MUTATIE_CUT,
                             deelcompetitie=self.deelcomp_rk,
                             klasse=self.klasse,
                             cut_oud=23,
                             cut_nieuw=24,              # verwijder oude record
                             door='Tester').save()

        KampioenschapMutatie(mutatie=MUTATIE_CUT,
                             deelcompetitie=self.deelcomp_rk,
                             klasse=self.klasse,
                             cut_oud=23,
                             cut_nieuw=24,
                             door='Tester').save()

        # mutatie die geen wijziging is
        KampioenschapMutatie(mutatie=MUTATIE_CUT,
                             deelcompetitie=self.deelcomp_rk,
                             klasse=self.klasse,
                             cut_oud=24,
                             cut_nieuw=24,
                             door='Tester').save()

        self._verwerk_mutaties(210)

    def test_verwerk_all(self):
        # vraag de achtergrond taak om de mutaties te verwerken
        # gebruik --all
        # en laat deze iets langer lopen
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('kampioenschap_mutaties', '2', '--quick', '--all', stderr=f1, stdout=f2)

# end of file
