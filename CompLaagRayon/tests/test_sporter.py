# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import KampioenschapSporterBoog, CompetitieMutatie
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_rk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonBko(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, Sporter geeft status deelname RK door """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_wijzig_status_sporter = '/bondscompetities/rk/wijzig-status-rk-deelname/'

    testdata = None
    rayon_nr = 1
    regio_nr = 102
    ver_nr = None
    deelnemer_geen_ver = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()       # maakt account_beheerders, die nodig is voor BKO
        cls.ver_nr = data.regio_ver_nrs[cls.regio_nr][0]
        data.maak_bondscompetities()
        data.maak_inschrijvingen_regiocompetitie(18, cls.ver_nr)
        data.geef_regio_deelnemers_genoeg_scores_voor_rk(18)
        zet_competitie_fase_rk_prep(data.comp18)

        # plaats 2 sporterboog in een RK, in dezelfde klasse
        klasse = data.comp18_klassen_indiv['R'][0]
        # nr = 0
        # for deelnemer in data.comp18_deelnemers:
        #     print('[%s] deelnemer: %s' % (nr, deelnemer))
        #     nr += 1
        # # for
        deelnemer1 = data.comp18_deelnemers[13]
        # print('deelnemer1: %s' % repr(deelnemer1))

        kampioen = KampioenschapSporterBoog(
                            kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                            sporterboog=deelnemer1.sporterboog,
                            indiv_klasse=klasse,
                            bij_vereniging=deelnemer1.bij_vereniging)
        kampioen.save()
        cls.account_sporter = deelnemer1.sporterboog.sporter.account
        cls.kampioen = kampioen

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_wijzig_status(self):
        # anon
        self.client.logout()
        resp = self.client.get(self.url_wijzig_status_sporter)
        self.assert403(resp, "Geen toegang")

        # log in als sporter
        self.e2e_login(self.account_sporter)

        resp = self.client.get(self.url_wijzig_status_sporter)
        self.assert404(resp, 'Niet mogelijk')

        resp = self.client.post(self.url_wijzig_status_sporter)
        self.assert404(resp, 'Deelnemer niet gevonden')

        resp = self.client.post(self.url_wijzig_status_sporter, data={'deelnemer': self.kampioen.pk})
        self.assert_is_redirect(resp, '/sporter/')
        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        resp = self.client.post(self.url_wijzig_status_sporter, data={'deelnemer': self.kampioen.pk,
                                                                      'snel': 1,
                                                                      'keuze': 'J'})
        self.assert_is_redirect(resp, '/sporter/')
        self.assertEqual(CompetitieMutatie.objects.count(), 1)

        resp = self.client.post(self.url_wijzig_status_sporter, data={'deelnemer': self.kampioen.pk,
                                                                      'snel': 1,
                                                                      'keuze': 'N'})
        self.assert_is_redirect(resp, '/sporter/')
        self.assertEqual(CompetitieMutatie.objects.count(), 2)

        # maak de sporter niet meer lid bij een vereniging
        self.kampioen.refresh_from_db()
        self.kampioen.bij_vereniging = None
        self.kampioen.save(update_fields=['bij_vereniging'])

        resp = self.client.post(self.url_wijzig_status_sporter, data={'deelnemer': self.kampioen.pk,
                                                                      'snel': 1,
                                                                      'keuze': 'J'})
        self.assert404(resp, 'Je moet lid zijn bij een vereniging')
        self.assertEqual(CompetitieMutatie.objects.count(), 2)

        # zet de competitie door, zodat aanmelden/afmelden niet meer mag
        comp = self.kampioen.kampioenschap.competitie
        zet_competitie_fase_rk_wedstrijden(comp)

        resp = self.client.post(self.url_wijzig_status_sporter, data={'deelnemer': self.kampioen.pk})
        self.assert404(resp, 'Mag niet wijzigen')


# end of file
