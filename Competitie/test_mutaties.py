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
from .models import (Competitie, DeelCompetitie, CompetitieKlasse, DeelcompetitieKlasseLimiet,
                     RegioCompetitieSchutterBoog, KampioenschapSchutterBoog, KampioenschapMutatie,
                     LAAG_REGIO, LAAG_RK, LAAG_BK, AG_NUL, competitie_aanmaken, MUTATIE_INITIEEL)
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

        self.url_lijst_rk = '/competitie/lijst-rayonkampioenschappen/%s/'              # deelcomp_rk.pk
        self.url_wijzig_status = '/competitie/lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/%s/'  # deelnemer_pk
        self.url_wijzig_cut_rk = '/competitie/planning/rayoncompetitie/%s/limieten/'   # deelcomp_rk.pk

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
        resp = self.client.post(self.url_klassegrenzen_vaststellen_18)
        self.assertEqual(resp.status_code, 302)     # 302 = Redirect = success
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
            print('  rank=%s, volgorde=%s, nhb_nr=%s, gem=%s, afgemeld=%s, deelnemer=%s, label=%s' % (
                obj.rank, obj.volgorde, obj.schutterboog.nhblid.nhb_nr, obj.gemiddelde,
                obj.is_afgemeld, obj.deelname_bevestigd, obj.kampioen_label))
        print('====================================================================')

    def _get_rank_volg(self, alleen_kampioenen=False, alle=False):
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

    @staticmethod
    def _verwerk_mutaties(show=False):
        # vraag de achtergrond taak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('kampioenschap_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if show:                    # pragma: no coverage
            print(f1.getvalue())
            print(f2.getvalue())

    def test_deelnemers(self):
        # competitie doorzetten en lijst deelnemers controleren

        # 4 regio's met 6 schutters waarvan 1 met te weinig scores
        self.assertEqual(4*6, RegioCompetitieSchutterBoog.objects.count())
        self._begin_rk()        # BB met rol RKO1
        self.assertEqual(4*5, KampioenschapSchutterBoog.objects.count())

        self._verwerk_mutaties()
        self._check_volgorde_en_rank()

        # controleer dat de regiokampioenen boven de cut staan
        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 6, 7, 8])
        self.assertEqual(rank, volg)

        resp = self.client.get(self.url_lijst)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)

    def test_rko_bevestigen(self):
        # bevestig deelname door een schutter en een reserve
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=4)
        self.assertEqual(deelnemer.rank, 4)
        url = self.url_wijzig_status % deelnemer.pk
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertTrue(deelnemer.deelname_bevestigd)
        self.assertFalse(deelnemer.is_afgemeld)
        self.assertEqual(deelnemer.rank, 4)
        self.assertEqual(deelnemer.volgorde, 4)

        self._check_volgorde_en_rank()

    def test_rko_afmelden_onder_cut(self):
        # een reserve-schutter meldt zich af
        # dit heeft geen invloed op de deelnemers-lijst
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=10)
        url = self.url_wijzig_status % deelnemer.pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertTrue(deelnemer.is_afgemeld)
        self.assertFalse(deelnemer.deelname_bevestigd)
        self.assertEqual(deelnemer.rank, 0)
        self.assertEqual(deelnemer.volgorde, 10)

        self._check_volgorde_en_rank()

    def test_rko_afmelden_boven_cut(self):
        # kandidaat-schutter (boven de cut) meldt zich af
        # reserve-schutter wordt opgeroepen
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        reserve = KampioenschapSchutterBoog.objects.get(volgorde=9)  # cut ligt op 8
        self.assertFalse(reserve.is_afgemeld)
        self.assertFalse(reserve.deelname_bevestigd)
        self.assertEqual(reserve.rank, 9)
        self.assertEqual(reserve.volgorde, 9)

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(volgorde=4)
        url = self.url_wijzig_status % deelnemer.pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertTrue(deelnemer.is_afgemeld)
        self.assertFalse(deelnemer.deelname_bevestigd)
        self.assertEqual(deelnemer.rank, 0)
        self.assertEqual(deelnemer.volgorde, 4)

        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertFalse(reserve.is_afgemeld)
        self.assertFalse(reserve.deelname_bevestigd)
        self.assertEqual(reserve.rank, 6)
        self.assertEqual(reserve.volgorde, 7)

        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_onder_cut(self):
        # een reserve-schutter meldt zich af en weer aan
        # dit heeft geen invloed op de deelnemers-lijst
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(rank=10)    # cut ligt op 8
        self.assertEqual(reserve.volgorde, 10)
        url = self.url_wijzig_status % reserve.pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertTrue(reserve.is_afgemeld)
        self.assertFalse(reserve.deelname_bevestigd)
        self.assertEqual(reserve.rank, 0)
        self.assertEqual(reserve.volgorde, 10)

        url = self.url_wijzig_status % reserve.pk
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertFalse(reserve.is_afgemeld)
        self.assertTrue(reserve.deelname_bevestigd)
        self.assertEqual(reserve.rank, 10)
        self.assertEqual(reserve.volgorde, 10)

        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_boven_cut(self):
        # kandidaat-schutter (boven de cut) meldt zich af
        # reserve-schutter wordt opgeroepen
        # schutter meldt zichzelf daarna weer aan en komt in de lijst met reserve-schutters
        # gesorteerd op gemiddelde
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()
        # self._dump_deelnemers()

        deelnemer = KampioenschapSchutterBoog.objects.get(rank=3)    # cut ligt op 8
        self.assertEqual(deelnemer.volgorde, 3)
        url = self.url_wijzig_status % deelnemer.pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties()
        # self._dump_deelnemers()

        reserve = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        del deelnemer
        self.assertTrue(reserve.is_afgemeld)
        self.assertFalse(reserve.deelname_bevestigd)
        self.assertEqual(reserve.rank, 0)
        self.assertEqual(reserve.volgorde, 3)

        # opnieuw aanmelden --> wordt als reserve-schutter op de lijst gezet
        url = self.url_wijzig_status % reserve.pk
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties()
        # self._dump_deelnemers()

        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertFalse(reserve.is_afgemeld)
        self.assertTrue(reserve.deelname_bevestigd)
        self.assertEqual(reserve.rank, 9)
        self.assertEqual(reserve.volgorde, 9)

        self._check_volgorde_en_rank()

    def test_rko_oproep_reserve_hoog_gemiddelde(self):
        # de eerste reserve heeft een hoger gemiddelde dan de laatste deelnemers
        # na afmelden van een deelnemer wordt de eerste reserve opgeroepen
        # de lijst met deelnemers wordt gesorteerd op gemiddelde
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        # bereik dit effect door nr 3 af te melden en daarna weer aan te melden
        deelnemer = KampioenschapSchutterBoog.objects.get(rank=3)    # cut ligt op 8
        url = self.url_wijzig_status % deelnemer.pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

        reserve = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(reserve.volgorde, 9)
        del deelnemer

        # meld nu iemand anders af zodat de eerste reserve opgeroepen wordt
        afmelden = KampioenschapSchutterBoog.objects.get(rank=4)    # cut ligt op 8
        url = self.url_wijzig_status % afmelden.pk
        # self._dump_deelnemers()
        resp = self.client.post(url, {'afmelden': 1})
        # self._dump_deelnemers()

        self._verwerk_mutaties()

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
        # komt bovenaan in de lijst met reserve-schutters
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        # bereik dit effect door nr 8 af te melden en daarna weer aan te melden
        # dit is een regiokampioen met behoorlijk lage gemiddelde
        # self._dump_deelnemers()
        kampioen = KampioenschapSchutterBoog.objects.get(rank=8)    # cut ligt op 8
        url = self.url_wijzig_status % kampioen.pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties()

        # kijk wat er met de kampioen gebeurd is
        # self._dump_deelnemers()
        kampioen = KampioenschapSchutterBoog.objects.get(pk=kampioen.pk)
        self.assertFalse(kampioen.is_afgemeld)
        self.assertTrue(kampioen.deelname_bevestigd)
        self.assertEqual(kampioen.rank, 9)
        self.assertEqual(kampioen.volgorde, 9)

        # meld nu iemand anders af zodat de eerste reserve opgeroepen wordt
        # self._dump_deelnemers()
        afmelden = KampioenschapSchutterBoog.objects.get(rank=4)    # cut ligt op 8
        url = self.url_wijzig_status % afmelden.pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        self._verwerk_mutaties()

        # kampioen heeft nu zijn oude plekje weer terug
        # self._dump_deelnemers()
        kampioen = KampioenschapSchutterBoog.objects.get(pk=kampioen.pk)
        self.assertFalse(kampioen.is_afgemeld)
        self.assertTrue(kampioen.deelname_bevestigd)
        self.assertEqual(kampioen.rank, 8)
        self.assertEqual(kampioen.volgorde, 9)      # volgorde=4 is de de afgemelde schutter

        self._check_volgorde_en_rank()

    def test_rko_drie_kampioenen_opnieuw_aanmelden(self):
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        pks = (KampioenschapSchutterBoog
               .objects
               .exclude(kampioen_label='')
               .order_by('volgorde')
               .values_list('pk', flat=True))
        pks = list(pks)
        for pk in pks[:3]:
            url = self.url_wijzig_status % pk
            resp = self.client.post(url, {'afmelden': 1})
            self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        # for

        self._verwerk_mutaties()
        # self._dump_deelnemers()

        # de laatste kampioen staat nog steeds onderaan in de lijst
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[3])
        self.assertEqual(kampioen.rank, 8)
        self.assertEqual(kampioen.volgorde, 11)

        # meld de drie kampioenen weer aan
        url = self.url_wijzig_status % pks[0]
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[1]
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[2]
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()
        # self._dump_deelnemers()

        # controleer dat ze in de reserve schutters lijst staan, gesorteerd op gemiddelde
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[0])
        self.assertEqual(kampioen.rank, 9)
        self.assertEqual(kampioen.volgorde, 9)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[1])
        self.assertEqual(kampioen.rank, 10)
        self.assertEqual(kampioen.volgorde, 10)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[2])
        self.assertEqual(kampioen.rank, 11)
        self.assertEqual(kampioen.volgorde, 11)

        self._check_volgorde_en_rank()

    def test_rko_cut24_drie_kampioenen_opnieuw_aanmelden(self):
        self.cut.delete()       # verwijder de cut van 8
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()
        # self._dump_deelnemers()

        pks = (KampioenschapSchutterBoog
               .objects
               .exclude(kampioen_label='')
               .order_by('volgorde')
               .values_list('pk', flat=True))
        pks = list(pks)
        for pk in pks[:3]:
            url = self.url_wijzig_status % pk
            resp = self.client.post(url, {'afmelden': 1})
            self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success
        # for

        self._verwerk_mutaties()
        # self._dump_deelnemers()

        # de laatste kampioen staat nog steeds onderaan in de lijst
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[3])
        self.assertEqual(kampioen.rank, 13)
        self.assertEqual(kampioen.volgorde, 16)

        # meld de drie kampioenen weer aan
        url = self.url_wijzig_status % pks[0]
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[1]
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[2]
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()
        # self._dump_deelnemers()

        # controleer dat ze in de reserve schutters lijst staan, gesorteerd op gemiddelde
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[0])
        self.assertEqual(kampioen.rank, 18)
        self.assertEqual(kampioen.volgorde, 18)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[1])
        self.assertEqual(kampioen.rank, 19)
        self.assertEqual(kampioen.volgorde, 19)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[2])
        self.assertEqual(kampioen.rank, 20)
        self.assertEqual(kampioen.volgorde, 20)

        self._check_volgorde_en_rank()

    def test_move_cut(self):
        # verplaats de cut en controleer de inhoud na de update
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 6, 7, 8])
        self.assertEqual(volg, [1, 6, 7, 8])

        # verplaats de cut naar 20
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.klasse.pk
        resp = self.client.post(url, {sel: 20})
        self.assertEqual(resp.status_code, 302)     # 302 = redirect = success
        self._verwerk_mutaties()

        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 6, 11, 16])
        self.assertEqual(volg, [1, 6, 11, 16])

        # meld ook 3 mensen af: 1 kampioen en 1 niet-kampioen boven de cut + 1 onder cut
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=1).pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=2).pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=10).pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        # verplaats de cut naar 8
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.klasse.pk
        resp = self.client.post(url, {sel: 8})
        self.assertEqual(resp.status_code, 302)     # 302 = redirect = success
        self._verwerk_mutaties()
        # self._dump_deelnemers()

        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [0, 4, 7, 8])
        self.assertEqual(volg, [1, 6, 9, 10])

        self._check_volgorde_en_rank()

    def test_rko_allemaal_afmelden(self):
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        pks = list(KampioenschapSchutterBoog.objects.values_list('pk', flat=True))
        for pk in pks:
            url = self.url_wijzig_status % pk
            resp = self.client.post(url, {'afmelden': 1})
            self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success
        # for

        self._verwerk_mutaties()

        self._check_volgorde_en_rank()

    def test_dubbel(self):
        self._begin_rk()        # BB met rol RKO1
        self._verwerk_mutaties()

        # dubbel afmelden
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.get(rank=2).pk
        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        resp = self.client.post(url, {'afmelden': 1})
        self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success

        # dubbel aanmelden
        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        resp = self.client.post(url, {'bevestig': 1})
        self.assert_is_redirect(resp, self.url_lijst)        # 302 = redirect = success

        self._verwerk_mutaties()

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

        # mutatie die al verwerkt is
        KampioenschapMutatie(mutatie=0,
                             is_verwerkt=True,
                             deelnemer=KampioenschapSchutterBoog.objects.all()[0],
                             door='Tester').save()

        self._verwerk_mutaties()

# end of file
