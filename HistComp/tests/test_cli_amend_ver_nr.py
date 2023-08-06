# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from HistComp.definities import HISTCOMP_TYPE_18, HIST_BOGEN_DEFAULT, HIST_TEAM_TYPEN_DEFAULT
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from NhbStructuur.models import NhbVereniging, NhbRegio
from TestHelpers.e2ehelpers import E2EHelpers


class TestCompLaagRayonCliImportUitslagRkIndiv(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, import van de RK/BK uitslag """

    def setUp(self):
        hist_seizoen = HistCompSeizoen(
                            seizoen='2017/2018',
                            comp_type=HISTCOMP_TYPE_18,
                            indiv_bogen=",".join(HIST_BOGEN_DEFAULT),
                            team_typen=",".join(HIST_TEAM_TYPEN_DEFAULT))
        hist_seizoen.save()
        self.hist_seizoen = hist_seizoen
        self.seizoen4url = '2018-2019'

        HistCompRegioIndiv(
                seizoen=hist_seizoen,
                rank=1,
                indiv_klasse='Recurve klasse 1',
                sporter_lid_nr=100001,
                sporter_naam='Heeft naam',
                boogtype='R',
                vereniging_nr=1001,
                vereniging_naam='Test Club',
                vereniging_plaats="Pijlstad",
                regio_nr=102,
                score1=10,
                score2=20,
                score3=30,
                score4=40,
                score5=50,
                score6=60,
                score7=70,
                laagste_score_nr=1,
                totaal=80,
                gemiddelde=5.321).save()

        HistCompRegioIndiv(
                seizoen=hist_seizoen,
                rank=1,
                indiv_klasse='Recurve klasse 1',
                sporter_lid_nr=100002,
                sporter_naam='',
                boogtype='R',
                vereniging_nr=1234,
                vereniging_naam='Test Club',
                vereniging_plaats="Pijlstad",
                regio_nr=102,
                score1=10,
                score2=20,
                score3=30,
                score4=40,
                score5=50,
                score6=60,
                score7=70,
                laagste_score_nr=1,
                totaal=80,
                gemiddelde=5.321).save()

        HistCompRegioIndiv(
                seizoen=hist_seizoen,
                rank=1,
                indiv_klasse='Recurve klasse 1',
                sporter_lid_nr=100003,
                sporter_naam='',
                boogtype='R',
                vereniging_nr=1234,
                vereniging_naam='Test Club',
                vereniging_plaats="Pijlstad",
                regio_nr=102,
                score1=10,
                score2=20,
                score3=30,
                score4=40,
                score5=50,
                score6=60,
                score7=70,
                laagste_score_nr=1,
                totaal=80,
                gemiddelde=5.321).save()

        HistCompRegioIndiv(
                seizoen=hist_seizoen,
                rank=1,
                indiv_klasse='Recurve klasse 1',
                sporter_lid_nr=100004,
                sporter_naam='',
                boogtype='R',
                vereniging_nr=1234,
                vereniging_naam='Test Club',
                vereniging_plaats="Pijlstad",
                regio_nr=102,
                score1=10,
                score2=20,
                score3=30,
                score4=40,
                score5=50,
                score6=60,
                score7=70,
                laagste_score_nr=1,
                totaal=80,
                gemiddelde=5.321).save()

    def test_cli(self):
        some_file = 'HistComp/management/testfiles/2017-2018.xlsx'

        # seizoen NOK
        f1, _ = self.run_management_command('histcomp_amend_ver_nr', '2000/2001', '18', 'bestand', 'blad', 'A', 'B', 'C', report_exit_code=False)
        self.assertTrue('[ERROR] Historisch seizoen' in f1.getvalue())

        # bestand NOK
        f1, _ = self.run_management_command('histcomp_amend_ver_nr', '2017/2018', '18', 'bestand', 'blad', 'A', 'B', 'C', report_exit_code=False)
        self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())

        # tabblad NOK
        f1, _ = self.run_management_command('histcomp_amend_ver_nr', '--dryrun', '--verbose', '2017/2018', '18', some_file, 'blad', 'A', 'B', 'C')
        self.assertTrue('[ERROR] Kan tabblad' in f1.getvalue())

        # vereniging NOK
        f1, f2 = self.run_management_command('histcomp_amend_ver_nr', '--dryrun', '--verbose', '2017/2018', '18', some_file, 'Data', 'A', 'C', 'B')
        self.assertTrue('[ERROR] Kan vereniging 1001 niet vinden' in f1.getvalue())
        self.assertTrue('[ERROR] Sporter 100005 van vereniging 1377 mag niet in de uitslag' in f1.getvalue())

        NhbVereniging(
                ver_nr=1001,
                naam='Ver',
                plaats='Pijlstad',
                regio=NhbRegio.objects.get(regio_nr=102),
                contact_email='').save()

        f1, f2 = self.run_management_command('histcomp_amend_ver_nr', '--dryrun', '--verbose', '2017/2018', '18', some_file, 'Data', 'A', 'C', 'B')
        self.assertTrue("[ERROR] Rejected: 'Bad4'" in f1.getvalue())
        # print('\nf1: %s' % f1.getvalue())
        # print('\nf2: %s' % f2.getvalue())

        self.run_management_command('histcomp_amend_ver_nr', '2017/2018', '18', some_file, 'Data', 'A', 'C', 'B')

# end of file
