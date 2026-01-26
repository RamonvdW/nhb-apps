# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import MUTATIE_KAMP_REINIT_TEST
from Competitie.models import (Competitie, Kampioenschap,
                               CompetitieIndivKlasse, CompetitieTeamKlasse,
                               CompetitieMutatie, CompetitieMatch,
                               KampioenschapIndivKlasseLimiet, KampioenschapSporterBoog, KampioenschapTeam)
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep
from Functie.models import Functie
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonCliOverig(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, overige management commando's """

    cli_check_rk_inschrijvingen = 'check_rk_inschrijvingen'
    cli_check_rk_uitslagen = 'check_rk_uitslagen'
    cli_email_rk_indiv_deelnemers = 'email_rk_indiv_deelnemers'

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4
    cut = 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        ver_nr = data.regio_ver_nrs[cls.regio_nr][0]
        data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr)

        # zet de competities in fase J
        zet_competitie_fase_rk_prep(data.comp18)

        klasse = (CompetitieIndivKlasse
                  .objects
                  .filter(competitie=data.comp18,
                          boogtype=data.afkorting2boogtype_khsn['R'],
                          beschrijving__contains="Recurve klasse 6")
                  .first())
        cls.indiv_klasse = klasse

        # zet de cut op 16 voor de gekozen klasse
        KampioenschapIndivKlasseLimiet(
                kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                indiv_klasse=klasse,
                limiet=cls.cut).save()

        klasse = (CompetitieTeamKlasse
                  .objects
                  .filter(competitie=data.comp18,
                          team_type=data.afkorting2teamtype_khsn['TR'])
                  .first())
        cls.team_klasse = klasse

        team = KampioenschapTeam(
                    kampioenschap=data.deelkamp18_rk[cls.rayon_nr])
        team.save()
        team.gekoppelde_leden.set(data.comp18_rk_deelnemers[:3])

        team = KampioenschapTeam(
                    kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                    volg_nr=2)
        team.save()

    def setUp(self):
        pass

    def test_check_rk(self):
        CompetitieMutatie(mutatie=MUTATIE_KAMP_REINIT_TEST,
                          kampioenschap=self.testdata.deelkamp18_rk[self.rayon_nr]).save()
        self.verwerk_competitie_mutaties()

        # verpruts een ranking/volgorde
        deelnemer = (KampioenschapSporterBoog
                     .objects
                     .filter(sporterboog__boogtype__afkorting='R',
                             volgorde=self.cut)
                     .order_by('indiv_klasse__volgorde')
                     .first())
        deelnemer.volgorde = 2
        deelnemer.save(update_fields=['volgorde'])

        deelnemer = (KampioenschapSporterBoog
                     .objects
                     .filter(sporterboog__boogtype__afkorting='R',
                             volgorde=1)
                     .order_by('indiv_klasse__volgorde')
                     .first())
        deelnemer.rank = 0
        deelnemer.save(update_fields=['rank'])

        # maak een dubbele inschrijving
        deelnemer.pk = 0
        deelnemer.volgorde = 100
        deelnemer.save()

        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(self.cli_check_rk_inschrijvingen,
                                                 '18', self.rayon_nr)
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        self.assertTrue('Dubbele sporterboog' in f1.getvalue())
        self.assertTrue('klassen hebben geen afwijkingen' in f2.getvalue())

        # alle klassen hebben fouten
        KampioenschapSporterBoog.objects.exclude(indiv_klasse=deelnemer.indiv_klasse).delete()
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(self.cli_check_rk_inschrijvingen,
                                                 '18', self.rayon_nr, '--verbose')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertFalse('klassen hebben geen afwijkingen' in f2.getvalue())

        # niets gevonden
        with self.assert_max_queries(20):
            f1, f2 = self.run_management_command(self.cli_check_rk_inschrijvingen,
                                                 '25', self.rayon_nr)
        self.assertTrue('Geen deelnemers gevonden' in f2.getvalue())

    def test_recalc(self):
        f1, f2 = self.run_management_command('recalc_rkteam_sterkte')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

    def test_check_rk_uitslagen(self):
        f1, f2 = self.run_management_command(self.cli_check_rk_uitslagen,
                                             '18')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        f1, f2 = self.run_management_command(self.cli_check_rk_uitslagen,
                                             '25', '--verbose')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

    def test_email_rk_indiv_deelnemers(self):
        # 18m
        _, f2 = self.run_management_command(self.cli_email_rk_indiv_deelnemers,
                                             '18', '1')
        self.assertTrue('[INFO] Kampioenschap: Indoor competitie' in f2.getvalue())
        self.assertTrue(' - RK Rayon 1' in f2.getvalue())
        self.assertTrue('[INFO] 0 RK wedstrijden gevonden' in f2.getvalue())

        # 25m, zonder deelkamp
        self.testdata.comp25.regiocompetitie_is_afgesloten = True
        self.testdata.comp25.save()
        Kampioenschap.objects.filter(competitie=self.testdata.comp25).delete()
        _, f2 = self.run_management_command(self.cli_email_rk_indiv_deelnemers,
                                             '25', '1', '--stuur')
        self.assertTrue('[ERROR] Competitie niet gevonden' in f2.getvalue())

        ver = self.testdata.vereniging[self.testdata.regio_ver_nrs[self.regio_nr][0]]
        loc = self.testdata.maak_wedstrijd_locatie(ver.ver_nr)

        deelkamp = self.testdata.deelkamp18_rk[self.rayon_nr]
        deelnemer = self.testdata.comp18_rk_deelnemers[0]

        # maak een wedstrijd aan
        match = CompetitieMatch(
                    competitie=self.testdata.comp18,
                    beschrijving='RK Rayon 1',
                    datum_wanneer='2021-02-03',
                    tijd_begin_wedstrijd='12:34',
                    vereniging=ver,
                    locatie=loc)
        match.save()
        match.indiv_klassen.add(deelnemer.indiv_klasse)
        deelkamp.rk_bk_matches.add(match)

        # zet functie e-mail
        Functie.objects.filter(rol='HWL', vereniging=ver).update(bevestigde_email='hwl@org_ver.nl')

        _, f2 = self.run_management_command(self.cli_email_rk_indiv_deelnemers,
                                             '18', str(self.rayon_nr))
        self.assertTrue('[INFO] 1 RK wedstrijden gevonden' in f2.getvalue())
        self.assertTrue('[ERROR] 9 fouten gevonden' in f2.getvalue())

        # zet alle klassen in een tweede match, zonder locatie
        match = CompetitieMatch(
                    competitie=self.testdata.comp18,
                    beschrijving='RK Rayon 1',
                    datum_wanneer='2021-02-03',
                    tijd_begin_wedstrijd='12:34',
                    vereniging=ver)
        match.save()
        deelkamp.rk_bk_matches.add(match)

        pks = [deelnemer.indiv_klasse.pk]
        for deelnemer in self.testdata.comp18_rk_deelnemers:
            pk = deelnemer.indiv_klasse.pk
            if pk not in pks:
                match.indiv_klassen.add(deelnemer.indiv_klasse)
                pks.append(pk)
        # for

        self.assertEqual(MailQueue.objects.count(), 0)
        _, f2 = self.run_management_command(self.cli_email_rk_indiv_deelnemers,
                                             '18', str(self.rayon_nr), '--stuur')
        # print('f2:', f2.getvalue())
        self.assertTrue('[INFO] 10 RK wedstrijden gevonden' in f2.getvalue())
        self.assertFalse('fouten gevonden' in f2.getvalue())
        self.assertTrue('[INFO] 8 e-mails verstuurd' in f2.getvalue())
        self.assertEqual(MailQueue.objects.count(), 8)

        mail = MailQueue.objects.first()
        # self.e2e_show_email_in_browser(mail)
        self.assert_email_html_ok(mail, 'email_complaagrayon/bevestig-deelname.dtl')
        self.assert_consistent_email_html_text(mail)

        # verwijder de functie
        Functie.objects.filter(rol='HWL', vereniging=ver).delete()
        _, f2 = self.run_management_command(self.cli_email_rk_indiv_deelnemers,
                                             '18', str(self.rayon_nr))

        # competitie is verkeerde fase
        Competitie.objects.update(regiocompetitie_is_afgesloten=False)
        _, f2 = self.run_management_command(self.cli_email_rk_indiv_deelnemers,
                                             '18', '4')
        self.assertTrue('[ERROR] Competitie niet gevonden' in f2.getvalue())


# end of file
