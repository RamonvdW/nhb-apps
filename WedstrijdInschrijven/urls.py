# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import path
from WedstrijdInschrijven import view_inschrijven, view_kwalificatie_scores

app_name = 'WedstrijdInschrijven'

# basis = /wedstrijden/inschrijven/

urlpatterns = [

    # inschrijven
    path('<wedstrijd_pk>/sporter/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenSporter.as_view(),
         name='inschrijven-sporter-boog'),

    path('<wedstrijd_pk>/sporter/',
         view_inschrijven.WedstrijdInschrijvenSporter.as_view(),
         name='inschrijven-sporter'),

    path('<wedstrijd_pk>/groep/<lid_nr>/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenGroepje.as_view(),
         name='inschrijven-groepje-lid-boog'),

    path('<wedstrijd_pk>/groep/',
         view_inschrijven.WedstrijdInschrijvenGroepje.as_view(),
         name='inschrijven-groepje'),

    path('<wedstrijd_pk>/familie/<lid_nr>/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenFamilie.as_view(),
         name='inschrijven-familie-lid-boog'),

    path('<wedstrijd_pk>/familie/',
         view_inschrijven.WedstrijdInschrijvenFamilie.as_view(),
         name='inschrijven-familie'),

    path('<wedstrijd_pk>/handmatig/<lid_nr>/<boog_afk>/',
         view_inschrijven.WedstrijdInschrijvenHandmatig.as_view(),
         name='inschrijven-handmatig-lid-boog'),

    path('<wedstrijd_pk>/handmatig/',
         view_inschrijven.WedstrijdInschrijvenHandmatig.as_view(),
         name='inschrijven-handmatig'),

    # toevoegen aan winkelwagentje
    path('toevoegen-mandje/',
         view_inschrijven.ToevoegenAanMandjeView.as_view(),
         name='inschrijven-toevoegen-aan-mandje'),

    path('kwalificatie-scores-doorgeven/<inschrijving_pk>/',
         view_kwalificatie_scores.KwalificatieScoresOpgevenView.as_view(),
         name='inschrijven-kwalificatie-scores'),
]

# end of file
