# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               DeelcompetitieIndivKlasseLimiet, DeelcompetitieTeamKlasseLimiet,
                               CompetitieMutatie, MUTATIE_INITIEEL, MUTATIE_CUT, MUTATIE_AFMELDEN,
                               MUTATIE_COMPETITIE_OPSTARTEN, MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M,
                               KampioenschapSchutterBoog, DEELNAME_ONBEKEND, DEELNAME_JA, DEELNAME_NEE)
from Competitie.tests.test_fase import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import io


class TestCompLaagRayonMutatiesRK(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, mutaties van RK/BK deelnemers lijsten """

    url_lijst_rk_rko = '/bondscompetities/rk/lijst-rayonkampioenschappen/%s/'                              # deelcomp_rk.pk
    url_lijst_rk_hwl = '/bondscompetities/rk/lijst-rayonkampioenschappen/%s/vereniging/'                   # deelcomp_rk.pk
    url_wijzig_status = '/bondscompetities/rk/lijst-rayonkampioenschappen/wijzig-status-rk-deelnemer/%s/'  # deelnemer_pk
    url_wijzig_cut_rk = '/bondscompetities/rk/planning/%s/limieten/'                                       # deelcomp_rk.pk

    testdata = None
    rayon_nr = 1
    regio_nr_begin = 101 + (rayon_nr - 1) * 4
    regio_nr_einde = regio_nr_begin + 3
    ver_nrs = list()

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_bondscompetities()

        for regio_nr in range(cls.regio_nr_begin, cls.regio_nr_einde + 1):
            ver_nr = cls.testdata.regio_ver_nrs[regio_nr][0]
            cls.testdata.maak_rk_deelnemers(18, ver_nr, regio_nr)
            cls.ver_nrs.append(ver_nr)
        # for

        cls.testdata.maak_label_regiokampioenen(18, cls.regio_nr_begin, cls.regio_nr_einde)

        # zet de competitie in fase J
        zet_competitie_fase(cls.testdata.comp18, 'J')

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 200000

        self.boogtype = BoogType.objects.get(afkorting='R')

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko = self.testdata.comp18_account_bko
        self.account_rko = self.testdata.comp18_account_rko[self.rayon_nr]

        self.functie_bko = self.testdata.comp18_functie_bko
        self.functie_rko = self.testdata.comp18_functie_rko[self.rayon_nr]

        self.hwl_ver_nr = self.ver_nrs[1]
        self.functie_hwl = self.testdata.functie_hwl[self.hwl_ver_nr]

        self.comp = self.testdata.comp18
        self.deelcomp_rk = self.testdata.deelcomp18_rk[self.rayon_nr]
        self.url_lijst_rko = self.url_lijst_rk_rko % self.deelcomp_rk.pk
        self.url_lijst_hwl = self.url_lijst_rk_hwl % self.deelcomp_rk.pk

        self.klasse = (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=self.comp,
                               boogtype=self.boogtype,
                               beschrijving__contains="Recurve klasse 6"))[0]

        # zet de cut op 16 voor de gekozen klasse
        self.cut = DeelcompetitieIndivKlasseLimiet(deelcompetitie=self.deelcomp_rk,
                                                   indiv_klasse=self.klasse,
                                                   limiet=16)
        self.cut.save()

    @staticmethod
    def _dump_klasse_deelnemers(klasse):                                            # pragma: no cover
        print('')
        print('====================================================================')
        print('Klasse: %s' % klasse)
        print('Deelnemers:')
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .filter(indiv_klasse=klasse)
                    .select_related('sporterboog__sporter')
                    .order_by('volgorde')):
            print('  rank=%s, volgorde=%s, sporterboog_pk=%s, boog=%s, lid_nr=%s, gem=%s, deelname=%s, kampioen_label=%s' % (
                    obj.rank, obj.volgorde, obj.sporterboog.pk, obj.sporterboog.boogtype.afkorting,
                    obj.sporterboog.sporter.lid_nr, obj.gemiddelde, obj.deelname, obj.kampioen_label))
        print('====================================================================')

    def _dump_deelnemers(self, alle_klassen=False):                 # pragma: no cover
        if alle_klassen:
            for temp in KampioenschapSchutterBoog.objects.distinct('klasse'):
                self._dump_klasse_deelnemers(temp.klasse)
            # for
        else:
            self._dump_klasse_deelnemers(self.klasse)

    def _get_rank_volg(self, alleen_kampioenen=False, alle=False):
        if alleen_kampioenen:
            # verwijder iedereen zonder kampioen label
            objs = KampioenschapSchutterBoog.objects.exclude(kampioen_label='')
        elif alle:                          # pragma: no branch
            # all deelnemers
            objs = KampioenschapSchutterBoog.objects.all()
        else:
            # verwijder de kampioenen
            objs = KampioenschapSchutterBoog.objects.filter(kampioen_label='')  # pragma: no cover

        objs = objs.filter(indiv_klasse=self.klasse).order_by('volgorde')

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

    def test_begin_rk(self):
        # competitie is doorgezet - controleer de lijst deelnemers

        # 4 regio's met 6 schutters waarvan 1 met te weinig scores
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)

        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)
        # self._dump_deelnemers()

        self.assertEqual(60, KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).count())

        self._check_volgorde_en_rank()

        # controleer dat de regiokampioenen boven de cut staan
        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 11, 12, 13])
        self.assertEqual(rank, volg)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_rko)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/rko-rk-selectie.dtl', 'plein/site_layout.dtl'))

    def test_opnieuw_initieel(self):
        # met de MUTATIE_INITIEEL kunnen we ook een 'reset' uitvoeren
        # daarbij wordt rekening gehouden met schutters die afgemeld zijn

        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)
        # self._dump_deelnemers()

        # meld een paar schutters af: 1 kampioen + 1 schutter boven de cut
        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(volgorde=1)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-status-rk-deelnemer.dtl', 'plein/site_layout.dtl'))

        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(volgorde=3)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(volgorde=18)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        CompetitieMutatie(mutatie=MUTATIE_INITIEEL,
                          deelcompetitie=self.deelcomp_rk).save()
        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()
        self._check_volgorde_en_rank()

        # nu zonder limiet
        DeelcompetitieIndivKlasseLimiet.objects.all().delete()
        DeelcompetitieTeamKlasseLimiet.objects.all().delete()
        CompetitieMutatie(mutatie=MUTATIE_INITIEEL,
                          deelcompetitie=self.deelcomp_rk).save()
        self.verwerk_regiocomp_mutaties()

    def test_rko_bevestigen(self):
        # bevestig deelname door een schutter en een reserve
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(volgorde=4)
        self.assertEqual(deelnemer.rank, 4)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(pk=deelnemer.pk)
        self.assertEqual(deelnemer.deelname, DEELNAME_JA)
        self.assertEqual(deelnemer.rank, 4)
        self.assertEqual(deelnemer.volgorde, 4)

        self._check_volgorde_en_rank()

    def test_rko_afmelden_onder_cut(self):
        # een reserve-schutter meldt zich af
        # dit heeft geen invloed op de deelnemers-lijst
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(volgorde=10)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(deelnemer.deelname, DEELNAME_NEE)
        self.assertEqual(deelnemer.rank, 0)
        self.assertEqual(deelnemer.volgorde, 10)

        self._check_volgorde_en_rank()

    def test_rko_afmelden_boven_cut(self):
        # sporter boven de cut meldt zich af
        # reserve-schutter wordt opgeroepen
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)
        # self._dump_deelnemers()

        nr = 16 + 1   # cut ligt op 16
        reserve = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(volgorde=nr)
        self.assertEqual(reserve.deelname, DEELNAME_ONBEKEND)
        self.assertEqual(reserve.rank, nr)
        self.assertEqual(reserve.volgorde, nr)

        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(volgorde=4)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

        # self._dump_deelnemers()
        deelnemer = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(deelnemer.deelname, DEELNAME_NEE)
        self.assertEqual(deelnemer.rank, 0)
        self.assertEqual(deelnemer.volgorde, 4)

        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_ONBEKEND)
        self.assertEqual(reserve.rank, nr - 1)
        self.assertEqual(reserve.volgorde, nr)

        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_onder_cut(self):
        # een reserve-schutter meldt zich af en weer aan
        # dit heeft geen invloed op de deelnemers-lijst
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # self._dump_deelnemers()
        nr = 18     # cut ligt op 16
        reserve = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=nr)
        self.assertEqual(reserve.volgorde, nr)
        url = self.url_wijzig_status % reserve.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_NEE)
        self.assertEqual(reserve.rank, 0)
        self.assertEqual(reserve.volgorde, nr)

        url = self.url_wijzig_status % reserve.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

        # self._dump_deelnemers()
        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_JA)
        self.assertEqual(reserve.rank, nr)
        self.assertEqual(reserve.volgorde, nr)

        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_einde_lijst(self):
        # opnieuw aangemelde schutter komt helemaal aan het einde van de reserve-lijst
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # self._dump_deelnemers()
        pk = KampioenschapSchutterBoog.objects.order_by('-rank')[0].pk
        url = self.url_wijzig_status % pk

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()
        self._check_volgorde_en_rank()

    def test_rko_opnieuw_aanmelden_boven_cut(self):
        # sporter boven de cut meldt zich af
        # reserve-schutter wordt opgeroepen
        # sporter meldt zichzelf daarna weer aan en komt in de lijst met reserve-schutters
        # gesorteerd op gemiddelde
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)
        # self._dump_deelnemers()

        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=3)    # cut ligt op 16
        self.assertEqual(deelnemer.volgorde, 3)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()
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
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        reserve = KampioenschapSchutterBoog.objects.get(pk=reserve.pk)
        self.assertEqual(reserve.deelname, DEELNAME_JA)
        self.assertEqual(reserve.rank, 16+1)
        self.assertEqual(reserve.volgorde, 16+1)

        self._check_volgorde_en_rank()

    def test_rko_oproep_reserve_hoog_gemiddelde(self):
        # de eerste reserve heeft een hoger gemiddelde dan de laatste deelnemers
        # na afmelden van een deelnemer wordt de eerste reserve opgeroepen
        # de lijst met deelnemers wordt gesorteerd op gemiddelde
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # bereik dit effect door nr 3 af te melden en daarna weer aan te melden
        deelnemer = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=3)
        url = self.url_wijzig_status % deelnemer.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

        reserve = KampioenschapSchutterBoog.objects.get(pk=deelnemer.pk)
        self.assertEqual(reserve.volgorde, 17)
        del deelnemer

        # meld nu iemand anders af zodat de eerste reserve opgeroepen wordt
        afmelden = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=4)    # cut ligt op 16
        url = self.url_wijzig_status % afmelden.pk
        # self._dump_deelnemers()
        self.client.post(url, {'afmelden': 1, 'snel': 1})
        # self._dump_deelnemers()

        self.verwerk_regiocomp_mutaties()

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
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # bereik dit effect door nr 14 af te melden en daarna weer aan te melden
        # dit is een regiokampioen met het laagste gemiddelde
        # self._dump_deelnemers()
        kampioen = KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=14)
        url = self.url_wijzig_status % kampioen.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        # kijk wat er met de kampioen gebeurd is
        kampioen = KampioenschapSchutterBoog.objects.get(pk=kampioen.pk)
        self.assertEqual(kampioen.deelname, DEELNAME_JA)
        self.assertEqual(kampioen.rank, 17)
        self.assertEqual(kampioen.volgorde, 17)

        self._check_volgorde_en_rank()

    def test_rko_drie_regiokampioenen_opnieuw_aanmelden(self):
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # zoek de sporters met regiokampioen label op
        pks = (KampioenschapSchutterBoog
               .objects
               .exclude(kampioen_label='')
               .filter(indiv_klasse=self.klasse)
               .order_by('volgorde')
               .values_list('pk', flat=True))
        pks = list(pks)
        self.assertEqual(4, len(pks))
        for pk in pks[:3]:
            url = self.url_wijzig_status % pk
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
            self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success
        # for

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        # de laatste regiokampioen staat nog steeds onderaan in de lijst
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[3])
        self.assertEqual(kampioen.rank, 10)
        self.assertEqual(kampioen.volgorde, 13)

        # meld de drie kampioenen weer aan
        url = self.url_wijzig_status % pks[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[1]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[2]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        # controleer dat ze in de reserve schutters lijst staan, gesorteerd op gemiddelde
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[0])
        self.assertEqual(kampioen.rank, 17)
        self.assertEqual(kampioen.volgorde, 17)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[1])
        self.assertEqual(kampioen.rank, 18)
        self.assertEqual(kampioen.volgorde, 18)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[2])
        self.assertEqual(kampioen.rank, 19)
        self.assertEqual(kampioen.volgorde, 19)

        self._check_volgorde_en_rank()

    def test_rko_cut24_drie_kampioenen_opnieuw_aanmelden(self):
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)
        # self._dump_deelnemers()

        self.cut.delete()       # verwijder de cut van 16

        # zoek de sporters met regiokampioen label op
        pks = (KampioenschapSchutterBoog
               .objects
               .exclude(kampioen_label='')
               .filter(indiv_klasse=self.klasse)
               .order_by('volgorde')
               .values_list('pk', flat=True))
        pks = list(pks)
        for pk in pks[:3]:
            url = self.url_wijzig_status % pk
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
            self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success
        # for

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        # de laatste kampioen staat nog steeds in de lijst en boven de cut
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[3])
        self.assertEqual(kampioen.rank, 10)
        self.assertEqual(kampioen.volgorde, 13)

        # meld de drie kampioenen weer aan
        url = self.url_wijzig_status % pks[0]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[1]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        url = self.url_wijzig_status % pks[2]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        # controleer dat de kampioenen nu als reserve in de lijst staan
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[0])
        self.assertEqual(kampioen.rank, 25)
        self.assertEqual(kampioen.volgorde, 25)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[1])
        self.assertEqual(kampioen.rank, 26)
        self.assertEqual(kampioen.volgorde, 26)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[2])
        self.assertEqual(kampioen.rank, 27)
        self.assertEqual(kampioen.volgorde, 27)

        self._check_volgorde_en_rank()

        # meld nu 3 sporters af, boven de cut
        # en controleer dat de regiokampioenen weer deelnemer zijn, op de juiste plek
        temp_pks = (KampioenschapSchutterBoog
                    .objects
                    .filter(indiv_klasse=self.klasse,
                            rank__gte=10)
                    .order_by('rank')
                    .values_list('pk', flat=True))
        for pk in list(temp_pks)[:3]:
            url = self.url_wijzig_status % pk
            with self.assert_max_queries(20):
                resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
            self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success
        # for

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        # controleer dat de kampioenen nu als deelnemer in de lijst staan
        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[0])
        self.assertEqual(kampioen.rank, 1)
        self.assertEqual(kampioen.volgorde, 1)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[1])
        self.assertEqual(kampioen.rank, 11)
        self.assertEqual(kampioen.volgorde, 11)

        kampioen = KampioenschapSchutterBoog.objects.get(pk=pks[2])
        self.assertEqual(kampioen.rank, 12)
        self.assertEqual(kampioen.volgorde, 12)

    def test_verlaag_cut(self):
        # verplaats de cut en controleer de inhoud na de update
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # self._dump_deelnemers()
        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [1, 11, 12, 13])
        self.assertEqual(volg, [1, 11, 12, 13])

        # meld 3 sporters af: 1 kampioen en 1 niet-kampioen boven de cut + 1 onder cut

        # onder de cut
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=17).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)  # 302 = redirect = success

        # normale deelnemer
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=2).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)  # 302 = redirect = success

        # kampioen
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=1).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)  # 302 = redirect = success

        self.assertTrue(str(self.cut) != '')

        temp = DeelcompetitieTeamKlasseLimiet(deelcompetitie=self.deelcomp_rk)
        self.assertTrue(str(temp) != '')
        temp.team_klasse = CompetitieTeamKlasse.objects.all()[0]
        self.assertTrue(str(temp) != '')

        # verplaats de cut naar 8
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.indiv_klasse.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 8, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)     # check success

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        rank, volg = self._get_rank_volg(alleen_kampioenen=True)
        self.assertEqual(rank, [0, 9, 10, 11])          # kampioenen boven de cut
        self.assertEqual(volg, [1, 11, 12, 13])

        self._check_volgorde_en_rank()

    def test_verhoog_cut(self):
        # verplaats de cut en controleer de inhoud na de update
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # default cut is 16
        # verhoog de cut naar 24
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.indiv_klasse.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 24, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)     # check success

        self.verwerk_regiocomp_mutaties()

        # meld iemand af
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=2).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)  # 302 = redirect = success

        # verlaag de cut naar 20
        url = self.url_wijzig_cut_rk % self.deelcomp_rk.pk
        sel = 'sel_%s' % self.cut.indiv_klasse.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {sel: 20, 'snel': 1})
        self.assert_is_redirect_not_plein(resp)     # check success

        self.verwerk_regiocomp_mutaties()
        # self._dump_deelnemers()

        rank, volg = self._get_rank_volg(alle=True)
        self.assertEqual(rank[:4], [1, 0, 2, 3])
        self.assertEqual(volg[:4], [1, 2, 3, 4])

        self._check_volgorde_en_rank()

    # def test_rko_allemaal_afmelden(self):
    #     self.e2e_login_and_pass_otp(self.account_bko)
    #     self.e2e_wissel_naar_functie(self.functie_rko)
    #     self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)
    #
    #     pks = list(KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).values_list('pk', flat=True))
    #     for pk in pks:
    #         url = self.url_wijzig_status % pk
    #         with self.assert_max_queries(20):
    #             resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
    #         self.assert_is_redirect(resp, self.url_lijst)  # 302 = redirect = success
    #     # for
    #
    #     self.verwerk_regiocomp_mutaties()
    #
    #     self._check_volgorde_en_rank()

    def test_dubbel(self):
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

        # dubbel afmelden
        url = self.url_wijzig_status % KampioenschapSchutterBoog.objects.filter(indiv_klasse=self.klasse).get(rank=2).pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)  # 302 = redirect = success

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)  # 302 = redirect = success

        # dubbel aanmelden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_rko)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

    def test_bad(self):
        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_rko)
        self.assertTrue(KampioenschapSchutterBoog.objects.count() > 0)

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
                          indiv_klasse=self.klasse,
                          cut_oud=23,
                          cut_nieuw=24,  # verwijder oude record
                          door='Tester').save()

        CompetitieMutatie(mutatie=MUTATIE_CUT,
                          deelcompetitie=self.deelcomp_rk,
                          indiv_klasse=self.klasse,
                          cut_oud=23,
                          cut_nieuw=24,
                          door='Tester').save()

        # mutatie die geen wijziging is
        CompetitieMutatie(mutatie=MUTATIE_CUT,
                          deelcompetitie=self.deelcomp_rk,
                          indiv_klasse=self.klasse,
                          cut_oud=24,
                          cut_nieuw=24,
                          door='Tester').save()

        self.verwerk_regiocomp_mutaties()

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
        self.verwerk_regiocomp_mutaties()

        # AG vaststellen
        CompetitieMutatie(mutatie=MUTATIE_AG_VASTSTELLEN_18M,
                          door='Tester').save()
        CompetitieMutatie(mutatie=MUTATIE_AG_VASTSTELLEN_25M,
                          door='Tester').save()
        self.verwerk_regiocomp_mutaties()

    def test_hwl_mutaties(self):
        # de HWL meldt leden van zijn eigen vereniging aan/af

        deelnemer_pks = (KampioenschapSchutterBoog
                         .objects
                         .filter(bij_vereniging__ver_nr=self.hwl_ver_nr,
                                 deelname=DEELNAME_ONBEKEND)
                         .values_list('pk', flat=True))

        self.e2e_login_and_pass_otp(self.account_bko)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_hwl)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-selectie.dtl', 'plein/site_layout.dtl'))

        # bad situaties
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_rk_hwl % 99999)
        self.assert404(resp, 'Competitie niet gevonden')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_status % 999999)
        self.assert404(resp, 'Deelnemer niet gevonden')

        # fase E
        comp = Competitie.objects.get(pk=self.testdata.comp18.pk)
        zet_competitie_fase(comp, 'E')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_hwl)
        self.assert404(resp, 'Pagina kan nog niet gebruikt worden')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_status % deelnemer_pks[1])
        self.assert404(resp, 'Mag nog niet wijzigen')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_status % deelnemer_pks[1])
        self.assert404(resp, 'Mag nog niet wijzigen')

        # fase P
        zet_competitie_fase(comp, 'P')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_hwl)
        self.assert404(resp, 'Pagina kan niet meer gebruikt worden')

        # tijdens fase K en L mag de pagina gebruikt worden
        zet_competitie_fase(comp, 'K')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_hwl)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-selectie.dtl', 'plein/site_layout.dtl'))

        url = self.url_wijzig_status % deelnemer_pks[1]
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/wijzig-status-rk-deelnemer.dtl', 'plein/site_layout.dtl'))

        # 1 sporter afmelden
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'afmelden': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_hwl)        # 302 = redirect = success

        # 1 sporter bevestigen
        url = self.url_wijzig_status % deelnemer_pks[2]
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'bevestig': 1, 'snel': 1})
        self.assert_is_redirect(resp, self.url_lijst_hwl)        # 302 = redirect = success

        self.verwerk_regiocomp_mutaties()

        zet_competitie_fase(comp, 'L')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_hwl)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/hwl-rk-selectie.dtl', 'plein/site_layout.dtl'))

        zet_competitie_fase(comp, 'M')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_lijst_hwl)
        self.assert404(resp, 'Pagina kan niet meer gebruikt worden')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_status % deelnemer_pks[1])
        self.assert404(resp, 'Mag niet meer wijzigen')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_wijzig_status % deelnemer_pks[1])
        self.assert404(resp, 'Mag niet meer wijzigen')

        # sporter van andere vereniging
        andere_ver = self.ver_nrs[0]
        andere_deelnemer_pk = (KampioenschapSchutterBoog
                               .objects
                               .filter(bij_vereniging__ver_nr=andere_ver,
                                       deelname=DEELNAME_ONBEKEND))[0].pk

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wijzig_status % andere_deelnemer_pk)
        self.assert403(resp, 'Geen sporter van jouw vereniging')


# end of file
