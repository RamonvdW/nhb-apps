# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType
from Competitie.definities import DEEL_RK, DEEL_BK, DEELNAME_NEE, DEELNAME_JA, KAMP_RANK_BLANCO, KAMP_RANK_NO_SHOW
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse, Regiocompetitie,
                               RegiocompetitieSporterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam, Kampioenschap,
                               KampioenschapSporterBoog, KampioenschapTeam)
from Competitie.test_utils.tijdlijn import (zet_competitie_fases, zet_competitie_fase_regio_inschrijven,
                                            zet_competitie_fase_regio_wedstrijden, zet_competitie_fase_regio_afsluiten)
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from HistComp.models import HistCompSeizoen, HistCompRegioTeam
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompBeheerBko(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module BKO """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_competitie_beheer = '/bondscompetities/beheer/%s/'                                      # comp_pk
    url_klassengrenzen_vaststellen = url_competitie_beheer + 'klassengrenzen-vaststellen/'
    url_doorzetten = url_competitie_beheer + 'doorzetten/'
    url_doorzetten_regio_naar_rk = url_doorzetten + 'regio-naar-rk/'
    url_doorzetten_rk_naar_bk_indiv = url_doorzetten + 'rk-indiv-naar-bk/'
    url_doorzetten_rk_naar_bk_teams = url_doorzetten + 'rk-teams-naar-bk/'
    url_doorzetten_bk_kleine_indiv = url_doorzetten + 'bk-indiv-kleine-klassen-zijn-samengevoegd/'
    url_doorzetten_bk_kleine_teams = url_doorzetten + 'bk-teams-kleine-klassen-zijn-samengevoegd/'
    url_bevestig_eindstand_bk_indiv = url_doorzetten + 'bk-indiv-eindstand-bevestigen/'
    url_bevestig_eindstand_bk_teams = url_doorzetten + 'bk-teams-eindstand-bevestigen/'
    url_teams_klassengrenzen_vaststellen = url_doorzetten + 'rk-bk-teams-klassengrenzen-vaststellen/'

    regio_nr = 101
    ver_nr = 0      # wordt in setUpTestData ingevuld

    testdata = None

    @classmethod
    def setUpTestData(cls):
        s1 = timezone.now()
        print('%s: populating testdata start' % cls.__name__)
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts_admin_en_bb()
        cls.testdata.maak_clubs_en_sporters()
        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][2]
        cls.testdata.maak_bondscompetities()
        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def _prep_beheerder_lid(self, voornaam):
        lid_nr = self._next_lid_nr
        self._next_lid_nr += 1

        sporter = Sporter(
                    lid_nr=lid_nr,
                    geslacht="M",
                    voornaam=voornaam,
                    achternaam="Tester",
                    email=voornaam.lower() + "@test.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=self.ver_101)
        sporter.save()

        return self.e2e_create_account(lid_nr, sporter.email, sporter.voornaam, accepteer_vhpg=True)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._next_lid_nr = 100001

        self.rayon_1 = Rayon.objects.get(rayon_nr=1)
        self.rayon_2 = Rayon.objects.get(rayon_nr=2)
        self.regio_101 = Regio.objects.get(regio_nr=101)
        self.regio_105 = Regio.objects.get(regio_nr=105)
        self.regio_112 = Regio.objects.get(regio_nr=112)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Zuidelijke Club",
                    ver_nr=1111,
                    regio=self.regio_112)
        ver.save()
        self.ver_112 = ver

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=self.regio_101)
        ver.save()
        self.ver_101 = ver

        loc = WedstrijdLocatie(banen_18m=1,
                               banen_25m=1,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(ver)
        self.loc = loc

        # maak HWL functie aan voor deze vereniging
        self.functie_hwl = maak_functie("HWL Vereniging %s" % ver.ver_nr, "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        # maak test leden aan die we kunnen koppelen aan beheerders functies
        self.account_bko_18 = self._prep_beheerder_lid('BKO')
        self.account_bko_25 = self._prep_beheerder_lid('BKO')
        self.account_rko1_25 = self._prep_beheerder_lid('RKO1')

        self.account_sporter1 = self._prep_beheerder_lid('Sporter1')
        self.account_sporter2 = self._prep_beheerder_lid('Sporter2')
        self.account_sporter3 = self._prep_beheerder_lid('Sporter3')

        self.lid_sporter_1 = Sporter.objects.get(lid_nr=self.account_sporter1.username)
        self.lid_sporter_2 = Sporter.objects.get(lid_nr=self.account_sporter2.username)
        self.lid_sporter_3 = Sporter.objects.get(lid_nr=self.account_sporter3.username)

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.boog_c = BoogType.objects.get(afkorting='C')

        self.sporterboog_1r = SporterBoog(sporter=self.lid_sporter_1,
                                          boogtype=self.boog_r,
                                          voor_wedstrijd=True)
        self.sporterboog_1r.save()

        self.sporterboog_1c = SporterBoog(sporter=self.lid_sporter_1,
                                          boogtype=self.boog_c,
                                          voor_wedstrijd=True)
        self.sporterboog_1c.save()

        self.sporterboog_2c = SporterBoog(sporter=self.lid_sporter_2,
                                          boogtype=self.boog_c,
                                          voor_wedstrijd=True)
        self.sporterboog_2c.save()

        # compound, lid 3
        self.sporterboog_3c = SporterBoog(sporter=self.lid_sporter_3,
                                          boogtype=self.boog_c,
                                          voor_wedstrijd=True)
        self.sporterboog_3c.save()

        self.comp_18 = Competitie.objects.get(afstand='18')
        self.comp_25 = Competitie.objects.get(afstand='25')

        self.comp25_klasse_r = CompetitieIndivKlasse.objects.get(competitie=self.comp_25,
                                                                 boogtype__afkorting='R',
                                                                 is_ook_voor_rk_bk=True,
                                                                 volgorde=1100)      # klasse 1, titel: BK

        self.comp25_klasse_c = CompetitieIndivKlasse.objects.get(competitie=self.comp_25,
                                                                 boogtype__afkorting='C',
                                                                 is_ook_voor_rk_bk=True,
                                                                 volgorde=1200)     # klasse 1, titel: NK

        self.comp25_teamklasse_regio_ere_r = CompetitieTeamKlasse.objects.get(
                                                                competitie=self.comp_25,
                                                                is_voor_teams_rk_bk=False,
                                                                volgorde=15)      # klasse 15 = R, ERE

        self.comp25_teamklasse_rk_ere_r = CompetitieTeamKlasse.objects.get(
                                                                competitie=self.comp_25,
                                                                is_voor_teams_rk_bk=True,
                                                                volgorde=115)     # klasse 115 = R, ERE

        self.comp25_teamklasse_regio_ere_c = CompetitieTeamKlasse.objects.get(
                                                                competitie=self.comp_25,
                                                                is_voor_teams_rk_bk=False,
                                                                volgorde=20)      # klasse 20 = C, ERE

        # klassengrenzen vaststellen om de competitie voorbij fase A te krijgen
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        url_klassengrenzen_vaststellen_18 = self.url_klassengrenzen_vaststellen % self.comp_18.pk
        resp = self.client.post(url_klassengrenzen_vaststellen_18)
        self.assert_is_redirect_not_plein(resp)  # check for success

        self.deelkamp_rayon1_25 = Kampioenschap.objects.filter(competitie=self.comp_25,
                                                               deel=DEEL_RK,
                                                               rayon=self.rayon_1).first()
        self.regiocomp25_101 = Regiocompetitie.objects.filter(competitie=self.comp_25,
                                                              regio=self.regio_101).first()
        self.regiocomp25_105 = Regiocompetitie.objects.filter(competitie=self.comp_25,
                                                              regio=self.regio_105).first()

        self.deelkamp_bk_18 = Kampioenschap.objects.filter(competitie=self.comp_18,
                                                           deel=DEEL_BK).first()

        self.functie_bko_18 = self.deelkamp_bk_18.functie
        self.functie_bko_18.accounts.add(self.account_bko_18)

        self.deelkamp_bk_25 = Kampioenschap.objects.filter(competitie=self.comp_25,
                                                           deel=DEEL_BK).first()
        self.functie_bko_25 = self.deelkamp_bk_25.functie
        self.functie_bko_25.accounts.add(self.account_bko_25)

        self.functie_rko1_25 = self.deelkamp_rayon1_25.functie
        self.functie_rko1_25.accounts.add(self.account_rko1_25)

        # maak nog een test vereniging, zonder HWL functie
        ver = Vereniging(
                    naam="Kleine Club",
                    ver_nr=1100,
                    regio=self.regio_101)
        ver.save()

    def _inschrijven_regio_indiv(self):
        # recurve, lid 1
        RegiocompetitieSporterBoog(regiocompetitie=self.regiocomp25_101,
                                   sporterboog=self.sporterboog_1r,
                                   bij_vereniging=self.sporterboog_1r.sporter.bij_vereniging,
                                   indiv_klasse=self.comp25_klasse_r,
                                   aantal_scores=7,
                                   totaal=102).save()

        # compound, lid 1
        RegiocompetitieSporterBoog(regiocompetitie=self.regiocomp25_101,
                                   sporterboog=self.sporterboog_1c,
                                   bij_vereniging=self.sporterboog_1c.sporter.bij_vereniging,
                                   indiv_klasse=self.comp25_klasse_c,
                                   aantal_scores=6,
                                   totaal=101).save()

        # compound, lid 2
        RegiocompetitieSporterBoog(regiocompetitie=self.regiocomp25_101,
                                   sporterboog=self.sporterboog_2c,
                                   bij_vereniging=self.sporterboog_2c.sporter.bij_vereniging,
                                   indiv_klasse=self.comp25_klasse_c,
                                   aantal_scores=6,
                                   totaal=101).save()       # zelfde score als andere sporter in deze klasse

        # compound, lid 3
        RegiocompetitieSporterBoog(regiocompetitie=self.regiocomp25_101,
                                   sporterboog=self.sporterboog_3c,
                                   bij_vereniging=self.sporterboog_3c.sporter.bij_vereniging,
                                   indiv_klasse=self.comp25_klasse_c,
                                   aantal_scores=4,     # te weinig scores
                                   totaal=300).save()

    def _inschrijven_regio_teams(self):
        team = RegiocompetitieTeam(
                    regiocompetitie=self.regiocomp25_101,
                    vereniging=self.sporterboog_1r.sporter.bij_vereniging,
                    volg_nr=1,
                    team_type=self.testdata.afkorting2teamtype_khsn['R2'],
                    team_naam='Test test 1',
                    aanvangsgemiddelde="26.5",
                    team_klasse=self.comp25_teamklasse_regio_ere_r)
        team.save()
        # team.leden = models.ManyToManyField(RegiocompetitieSporterBoog, blank=True)  # mag leeg zijn

        for ronde_nr in range(8):       # begin op 0, dat is goed
            RegiocompetitieRondeTeam(
                    team=team,
                    ronde_nr=ronde_nr,
                    team_score=123,
                    team_punten=2).save()
        # deelnemers_geselecteerd = models.ManyToManyField(RegiocompetitieSporterBoog,
        # deelnemers_feitelijk = models.ManyToManyField(RegiocompetitieSporterBoog,
        # scores_feitelijk = models.ManyToManyField(Score,
        # scorehist_feitelijk = models.ManyToManyField(ScoreHist,

        # team zonder scores (wordt niet opgenomen in HistComp)
        team = RegiocompetitieTeam(
                    regiocompetitie=self.regiocomp25_101,
                    vereniging=self.sporterboog_1r.sporter.bij_vereniging,
                    volg_nr=2,
                    team_type=self.testdata.afkorting2teamtype_khsn['C'],
                    team_naam='Test test 2',
                    aanvangsgemiddelde="29.8",
                    team_klasse=self.comp25_teamklasse_regio_ere_c)
        team.save()
        # team.leden = models.ManyToManyField(RegiocompetitieSporterBoog, blank=True)  # mag leeg zijn

        team = RegiocompetitieTeam(
                    regiocompetitie=self.regiocomp25_101,
                    vereniging=self.sporterboog_1r.sporter.bij_vereniging,
                    volg_nr=3,
                    team_type=self.testdata.afkorting2teamtype_khsn['R2'],
                    team_naam='Test test 2',
                    aanvangsgemiddelde="25.5",
                    team_klasse=self.comp25_teamklasse_regio_ere_r)
        team.save()
        # team.leden = models.ManyToManyField(RegiocompetitieSporterBoog, blank=True)  # mag leeg zijn

        RegiocompetitieRondeTeam(
                team=team,
                ronde_nr=1,
                team_score=90,
                team_punten=0).save()

    def _inschrijven_kamp_indiv(self, kampioenschap):
        # recurve, lid 1
        KampioenschapSporterBoog(kampioenschap=kampioenschap,
                                 sporterboog=self.sporterboog_1r,
                                 bij_vereniging=self.sporterboog_1r.sporter.bij_vereniging,
                                 indiv_klasse=self.comp25_klasse_r,
                                 indiv_klasse_volgende_ronde=self.comp25_klasse_r,
                                 result_rank=1,                 # titel: BK
                                 deelname=DEELNAME_JA).save()

        # recurve, lid 2
        KampioenschapSporterBoog(kampioenschap=kampioenschap,
                                 sporterboog=self.sporterboog_1r,
                                 bij_vereniging=self.sporterboog_1r.sporter.bij_vereniging,
                                 indiv_klasse=self.comp25_klasse_r,
                                 indiv_klasse_volgende_ronde=self.comp25_klasse_r,
                                 deelname=DEELNAME_NEE).save()

        # recurve, lid 2
        KampioenschapSporterBoog(kampioenschap=kampioenschap,
                                 sporterboog=self.sporterboog_1r,
                                 bij_vereniging=self.sporterboog_1r.sporter.bij_vereniging,
                                 indiv_klasse=self.comp25_klasse_r,
                                 indiv_klasse_volgende_ronde=self.comp25_klasse_r,
                                 result_rank=2).save()

        # compound, lid 1
        KampioenschapSporterBoog(kampioenschap=kampioenschap,
                                 sporterboog=self.sporterboog_1c,
                                 bij_vereniging=self.sporterboog_1c.sporter.bij_vereniging,
                                 indiv_klasse=self.comp25_klasse_c,
                                 indiv_klasse_volgende_ronde=self.comp25_klasse_c,
                                 result_rank=1).save()          # titel: NK

        # compound, lid 2
        KampioenschapSporterBoog(kampioenschap=kampioenschap,
                                 sporterboog=self.sporterboog_2c,
                                 bij_vereniging=self.sporterboog_2c.sporter.bij_vereniging,
                                 indiv_klasse=self.comp25_klasse_c,
                                 indiv_klasse_volgende_ronde=self.comp25_klasse_c,
                                 result_rank=KAMP_RANK_BLANCO).save()

        # compound, lid 2
        KampioenschapSporterBoog(kampioenschap=kampioenschap,
                                 sporterboog=self.sporterboog_2c,
                                 bij_vereniging=self.sporterboog_2c.sporter.bij_vereniging,
                                 indiv_klasse=self.comp25_klasse_c,
                                 indiv_klasse_volgende_ronde=self.comp25_klasse_c,
                                 result_rank=KAMP_RANK_NO_SHOW).save()         # komt niet in aanmerking

    def _maak_rk_teams(self, kampioenschap):

        self._inschrijven_kamp_indiv(kampioenschap)

        team = KampioenschapTeam(
                    kampioenschap=kampioenschap,
                    vereniging=self.ver_101,
                    volg_nr=1,
                    team_type=self.testdata.afkorting2teamtype_khsn['R2'],
                    team_naam='test team',
                    deelname=DEELNAME_JA,
                    aanvangsgemiddelde=3*8.0,
                    team_klasse=self.comp25_teamklasse_rk_ere_r,
                    team_klasse_volgende_ronde=self.comp25_teamklasse_rk_ere_r,
                    result_rank=1,          # moet >= 1 zijn
                    result_volgorde=1,
                    result_teamscore=12)
        team.save()

        leden = KampioenschapSporterBoog.objects.filter(bij_vereniging=self.ver_101)
        team.gekoppelde_leden.set(leden)

    def test_bad(self):
        # moet BKO zijn
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        resp = self.client.get(self.url_doorzetten_regio_naar_rk % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_doorzetten_rk_naar_bk_indiv % 999999)
        self.assert403(resp)

        resp = self.client.get(self.url_doorzetten_rk_naar_bk_teams % 999999)
        self.assert403(resp)

        # niet bestaande comp_pk
        self.e2e_wissel_naar_functie(self.functie_bko_18)

        resp = self.client.get(self.url_doorzetten_regio_naar_rk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_doorzetten_regio_naar_rk % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_doorzetten_rk_naar_bk_indiv % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_doorzetten_rk_naar_bk_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_doorzetten_rk_naar_bk_indiv % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_doorzetten_rk_naar_bk_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_bevestig_eindstand_bk_indiv % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_bevestig_eindstand_bk_indiv % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.get(self.url_bevestig_eindstand_bk_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        resp = self.client.post(self.url_bevestig_eindstand_bk_teams % 999999)
        self.assert404(resp, 'Competitie niet gevonden')

        # juiste comp_pk maar verkeerde fase
        zet_competitie_fase_regio_inschrijven(self.comp_18)
        resp = self.client.get(self.url_doorzetten_regio_naar_rk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(self.url_doorzetten_regio_naar_rk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.get(self.url_doorzetten_rk_naar_bk_indiv % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(self.url_doorzetten_rk_naar_bk_indiv % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.get(self.url_doorzetten_rk_naar_bk_teams % self.comp_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertContains(resp, 'De rayonkampioenschappen kunnen op dit moment nog niet doorgezet worden. Wacht tot de tijdlijn fase L bereikt heeft.')

        resp = self.client.post(self.url_doorzetten_rk_naar_bk_teams % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.get(self.url_bevestig_eindstand_bk_indiv % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.post(self.url_bevestig_eindstand_bk_indiv % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        resp = self.client.get(self.url_bevestig_eindstand_bk_teams % self.comp_18.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assertContains(resp, 'De competitie kan op dit moment nog niet doorgezet worden. Wacht tot de tijdlijn fase P bereikt heeft.')

        resp = self.client.post(self.url_bevestig_eindstand_bk_teams % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

    def test_doorzetten_1a(self):
        # regio naar rk
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        url = self.url_doorzetten_regio_naar_rk % self.comp_25.pk

        # wedstrijden fase: geen knop om door te zetten
        zet_competitie_fase_regio_wedstrijden(self.comp_25)

        # status ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-1a-regio-naar-rk.dtl', 'design/site_layout.dtl'))

        # zet een regiocompetitie die geen team competitie organiseert
        self.regiocomp25_101.regio_organiseert_teamcompetitie = False
        self.regiocomp25_101.save(update_fields=['regio_organiseert_teamcompetitie'])

        # zet een regiocompetitie team ronde > 7
        self.regiocomp25_105.huidige_team_ronde = 8
        self.regiocomp25_105.save(update_fields=['huidige_team_ronde'])

        # status ophalen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-1a-regio-naar-rk.dtl', 'design/site_layout.dtl'))

        # sluit alle regiocompetities
        for obj in Regiocompetitie.objects.filter(competitie=self.comp_25,
                                                  is_afgesloten=False):
            obj.is_afgesloten = True
            obj.save()
        # for

        # afsluitende fase, met de knop 'doorzetten'
        zet_competitie_fase_regio_afsluiten(self.comp_25)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-1a-regio-naar-rk.dtl', 'design/site_layout.dtl'))

        # nu echt doorzetten
        self._inschrijven_regio_indiv()
        self._inschrijven_regio_teams()

        self.assertEqual(4, RegiocompetitieSporterBoog.objects.count())
        self.assertEqual(0, KampioenschapSporterBoog.objects.count())
        self.assertEqual(0, HistCompRegioTeam.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        # laat de mutatie verwerken
        self.verwerk_competitie_mutaties()

        self.assertEqual(3, KampioenschapSporterBoog.objects.count())
        self.assertEqual(2, HistCompRegioTeam.objects.count())

        # verkeerde competitie/BKO
        resp = self.client.get(self.url_doorzetten_regio_naar_rk % self.comp_18.pk)
        self.assert404(resp, 'Verkeerde competitie')

    def test_doorzetten_1a_geen_lid(self):
        # variant van doorzetten_rk met een lid dat niet meer bij een vereniging aangesloten is
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        self._inschrijven_regio_indiv()

        self.assertEqual(4, RegiocompetitieSporterBoog.objects.count())
        self.assertEqual(0, KampioenschapSporterBoog.objects.count())

        zet_competitie_fase_regio_afsluiten(self.comp_25)       # fase G

        self.lid_sporter_2.bij_vereniging = None
        self.lid_sporter_2.save()

        url = self.url_doorzetten_regio_naar_rk % self.comp_25.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, '/bondscompetities/')       # redirect = Success

        # laat de mutatie verwerken
        f1, f2 = self.verwerk_competitie_mutaties(show_warnings=False)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(
            "[WARNING] Sporter 100005 - Compound is geen RK deelnemer want heeft geen vereniging" in f2.getvalue())

        # het lid zonder vereniging komt NIET in de RK selectie
        self.assertEqual(2, KampioenschapSporterBoog.objects.count())

        # verdere tests in test_planning_rayon.test_geen_vereniging check

    def test_doorzetten_1b(self):
        # klassengrenzen rk bk teams

        # maak een paar teams aan
        self.testdata.maak_voorinschrijvingen_rk_teamcompetitie(25, self.ver_101.ver_nr, ook_incomplete_teams=False)
        self.testdata.geef_rk_team_tijdelijke_sporters_genoeg_scores(25, self.ver_101.ver_nr)

        # als BKO doorzetten naar RK fase (G --> J) en bepaal de klassengrenzen (fase J --> K)
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        zet_competitie_fases(self.testdata.comp25, 'G', 'G')

        url = self.url_teams_klassengrenzen_vaststellen % 999999
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet gevonden')
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet gevonden')

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Competitie niet in de juiste fase')
        resp = self.client.post(url)
        self.assert404(resp, 'Competitie niet in de juiste fase')

        url = self.url_doorzetten_regio_naar_rk % self.testdata.comp25.pk
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.verwerk_competitie_mutaties()

        comp = Competitie.objects.get(pk=self.testdata.comp25.pk)
        comp.bepaal_fase()
        self.assertEqual(comp.fase_indiv, 'J')

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_template_used(resp,
                                  ('compbeheer/bko-doorzetten-1b-klassengrenzen-rk-bk-teams.dtl',
                                   'design/site_layout.dtl'))
        self.assert_html_ok(resp)

        url = self.url_teams_klassengrenzen_vaststellen % self.testdata.comp25.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)

        resp = self.client.get(url)
        self.assert404(resp, 'De klassengrenzen zijn al vastgesteld')
        resp = self.client.post(url)
        self.assert404(resp, 'De klassengrenzen zijn al vastgesteld')

    def test_doorzetten_2a(self):
        # rk naar bk indiv
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        comp = self.comp_25
        seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)
        HistCompSeizoen(seizoen=seizoen, comp_type=comp.afstand).save()

        self._inschrijven_kamp_indiv(self.deelkamp_rayon1_25)

        url = self.url_doorzetten_rk_naar_bk_indiv % self.comp_25.pk

        # fase L: pagina zonder knop 'doorzetten'
        zet_competitie_fases(self.comp_25, 'L', 'L')
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_indiv, 'L')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-2a-rk-naar-bk-indiv.dtl', 'design/site_layout.dtl'))

        # nu echt doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_competitie_beheer % self.comp_25.pk)       # redirect = Success

        # kietel de achtergrondtaak
        self.verwerk_competitie_mutaties()

        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_indiv, 'N')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, "Verkeerde competitie fase")

        self.assertTrue(str(self.deelkamp_bk_25) != '')

        objs = KampioenschapSporterBoog.objects.filter(kampioenschap=self.deelkamp_bk_25)
        self.assertEqual(objs.count(), 4)

    def test_doorzetten_2b(self):
        # rk naar bk teams
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        # maak RK teams met resultaten aan, voor een betere test
        self._maak_rk_teams(self.deelkamp_rayon1_25)
        url = self.url_doorzetten_rk_naar_bk_teams % self.comp_25.pk

        # fase L: pagina zonder knop 'doorzetten'
        zet_competitie_fases(self.comp_25, 'L', 'L')
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_teams, 'L')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-2b-rk-naar-bk-teams.dtl', 'design/site_layout.dtl'))

        # nu echt doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_competitie_beheer % self.comp_25.pk)       # redirect = Success

        # kietel de achtergrondtaak
        self.verwerk_competitie_mutaties(show_warnings=False)

        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_teams, 'N')

        # controleer dat nog een keer niet mogelijk is
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, "Verkeerde competitie fase")

    def test_doorzetten_3a(self):
        # bk kleine indiv klassen samengevoegd
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        url = self.url_doorzetten_bk_kleine_indiv % self.comp_25.pk

        # samenvoegen van klassen kan in fase N
        zet_competitie_fases(self.comp_25, 'N', 'L')
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_indiv, 'N')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-3a-bk-kleine-klassen-indiv.dtl',
                                         'design/site_layout.dtl'))

        # nu echt doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_competitie_beheer % self.comp_25.pk)       # redirect = Success

        # achtergrond taak wordt hier niet voor gebruikt

        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_indiv, 'O')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, "Verkeerde competitie fase")

    def test_doorzetten_3b(self):
        # bk kleine team klassen samengevoegd
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        url = self.url_doorzetten_bk_kleine_teams % self.comp_25.pk

        # samenvoegen van klassen kan in fase N
        zet_competitie_fases(self.comp_25, 'L', 'N')
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_teams, 'N')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-3b-bk-kleine-klassen-teams.dtl',
                                         'design/site_layout.dtl'))

        # nu echt doorzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_competitie_beheer % self.comp_25.pk)       # redirect = Success

        # achtergrond taak wordt hier niet voor gebruikt

        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_teams, 'O')

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, "Verkeerde competitie fase")

    def test_doorzetten_4a(self):
        # bevestig eindstand bk indiv
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        comp = self.comp_25
        seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)
        HistCompSeizoen(seizoen=seizoen, comp_type=comp.afstand).save()

        self._inschrijven_kamp_indiv(self.deelkamp_bk_25)

        url = self.url_bevestig_eindstand_bk_indiv % self.comp_25.pk

        # pagina ophalen in de verkeerde fase
        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertNotEqual(self.comp_25.fase_indiv, 'P')
        resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie fase')

        zet_competitie_fases(self.comp_25, 'P', 'P')
        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_indiv, 'P')

        # pagina ophalen
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-4a-bevestig-eindstand-bk-indiv.dtl',
                                         'design/site_layout.dtl'))

        # verkeerde BKO
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        # echt doorzetten
        self.e2e_wissel_naar_functie(self.functie_bko_25)
        resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_competitie_beheer % self.comp_25.pk)

        # kietel de achtergrondtaak
        self.verwerk_competitie_mutaties(show_warnings=False)

        # check nieuwe fase
        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertTrue(self.comp_25.fase_indiv, 'Q')

    def test_doorzetten_4b(self):
        # bevestig eindstand bk teams
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_bko_25)

        url = self.url_bevestig_eindstand_bk_teams % self.comp_25.pk

        # pagina ophalen in de verkeerde fase
        self.comp_25.refresh_from_db()
        self.comp_25.bepaal_fase()
        self.assertNotEqual(self.comp_25.fase_teams, 'P')
        resp = self.client.get(url)
        self.assertContains(resp, 'De competitie kan op dit moment nog niet doorgezet worden. Wacht tot de tijdlijn fase P bereikt heeft.')

        zet_competitie_fases(self.comp_25, 'P', 'P')
        self.comp_25.refresh_from_db()
        self.comp_25.bepaal_fase()
        self.assertEqual(self.comp_25.fase_teams, 'P')

        # pagina ophalen
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/bko-doorzetten-4b-bevestig-eindstand-bk-teams.dtl',
                                         'design/site_layout.dtl'))

        # verkeerde BKO
        self.e2e_wissel_naar_functie(self.functie_bko_18)
        resp = self.client.get(url)
        self.assert403(resp)
        resp = self.client.post(url)
        self.assert403(resp)

        # echt doorzetten
        self.e2e_wissel_naar_functie(self.functie_bko_25)
        resp = self.client.post(url)
        self.assert_is_redirect(resp, self.url_competitie_beheer % self.comp_25.pk)

        # kietel de achtergrondtaak
        self.verwerk_competitie_mutaties(show_warnings=False)

        # check nieuwe fase
        self.comp_25 = Competitie.objects.get(pk=self.comp_25.pk)
        self.comp_25.bepaal_fase()
        self.assertTrue(self.comp_25.fase_teams, 'Q')

# end of file
