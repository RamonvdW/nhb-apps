# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Competitie.models import Competitie
from SiteMap.definities import CHECK_LOW, CHECK_MED, CHECK_HIGH


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    yield CHECK_LOW, reverse('Competitie:info-competitie')
    yield CHECK_LOW, reverse('Competitie:info-teamcompetitie')
    yield CHECK_LOW, reverse('HistComp:top')
    yield CHECK_LOW, reverse('Competitie:kies')
    yield CHECK_LOW, reverse('Sporter:leeftijdsgroepen')

    # seizoenen
    for comp in Competitie.objects.order_by('pk'):
        comp.bepaal_fase()
        if comp.is_openbaar_voor_publiek():
            seizoen_url = comp.maak_seizoen_url()
            boog_urls = [boogtype.afkorting.lower()
                         for boogtype in comp.boogtypen.order_by('volgorde')]
            team_urls = [teamtype.afkorting.lower()
                         for teamtype in comp.teamtypen.order_by('volgorde')]

            yield CHECK_MED, reverse('Competitie:overzicht',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url})

            yield CHECK_MED, reverse('Competitie:klassengrenzen-tonen',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url})

            # TODO: overweeg vereniging-specifieke pagina's toe te voegen
            # name = 'uitslagen-vereniging-indiv-n'
            # name = 'uitslagen-vereniging-teams-n'
            # name = 'uitslagen-vereniging-indiv'

            # -- regio uitslag --

            check = CHECK_HIGH if comp.fase_indiv in "FG" else CHECK_MED
            for boog_url in boog_urls:
                yield check, reverse('CompUitslagen:uitslagen-regio-indiv',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url,
                                             'comp_boog': boog_url})

                for regio_nr in (101, 116+1):
                    yield check, reverse('CompUitslagen:uitslagen-regio-indiv-n',
                                         kwargs={'comp_pk_of_seizoen': seizoen_url,
                                                 'regio_nr': regio_nr,
                                                 'comp_boog': boog_url})
                # for
            # for

            for team_url in team_urls:
                yield check, reverse('CompUitslagen:uitslagen-regio-teams',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url,
                                             'team_type': team_url})

                # TODO: weglaten voor teams die geen regiocompetitie doen
                for regio_nr in (101, 116+1):
                    yield check, reverse('CompUitslagen:uitslagen-regio-teams-n',
                                         kwargs={'comp_pk_of_seizoen': seizoen_url,
                                                 'regio_nr': regio_nr,
                                                 'team_type': team_url})
                # for
            # for

            # -- RK uitslag --

            check = CHECK_HIGH if comp.fase_indiv in "JKL" else CHECK_MED
            for boog_url in boog_urls:
                yield check, reverse('CompUitslagen:uitslagen-rk-indiv',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url,
                                             'comp_boog': boog_url})

                for rayon_nr in (1, 2, 3, 4):
                    yield check, reverse('CompUitslagen:uitslagen-rk-indiv-n',
                                         kwargs={'comp_pk_of_seizoen': seizoen_url,
                                                 'rayon_nr': rayon_nr,
                                                 'comp_boog': boog_url})
                # for
            # for

            check = CHECK_HIGH if comp.fase_teams in "JKL" else CHECK_MED
            for team_url in team_urls:
                yield check, reverse('CompUitslagen:uitslagen-rk-teams',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url,
                                             'team_type': team_url})

                for rayon_nr in (1, 2, 3, 4):
                    yield check, reverse('CompUitslagen:uitslagen-rk-teams-n',
                                         kwargs={'comp_pk_of_seizoen': seizoen_url,
                                                 'rayon_nr': rayon_nr,
                                                 'team_type': team_url})
                # for
            # for

            # -- BK uitslag --

            check = CHECK_HIGH if comp.fase_indiv in "NOP" else CHECK_MED
            for boog_url in boog_urls:
                yield check, reverse('CompUitslagen:uitslagen-bk-indiv',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url,
                                             'comp_boog': boog_url})
            # for

            check = CHECK_HIGH if comp.fase_teams in "NOP" else CHECK_MED
            for team_url in team_urls:
                yield check, reverse('CompUitslagen:uitslagen-bk-teams',
                                     kwargs={'comp_pk_of_seizoen': seizoen_url,
                                             'team_type': team_url})
            # for
    # for

# end of file
