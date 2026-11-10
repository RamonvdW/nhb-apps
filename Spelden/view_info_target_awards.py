# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from Spelden.definities import SPELD_CATEGORIE_WA_TARGET_AWARD, SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER
from Spelden.models import SpeldVoorwaarden

TEMPLATE_PRESTATIESPELDEN_TARGET_AWARDS = 'spelden/wa-target-awards.dtl'


class TargetAwardsView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_TARGET_AWARDS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        done = list()
        toon = list()
        for voorwaarde in (SpeldVoorwaarden
                           .objects
                           .filter(speld__categorie__in=(SPELD_CATEGORIE_WA_TARGET_AWARD,
                                                         SPELD_CATEGORIE_WA_TARGET_AWARD_ZILVER))
                           .order_by('wedstrijd_soort',
                                     'benodigde_score')):     # laagste eerst
            tup = (voorwaarde.wedstrijd_soort, voorwaarde.benodigde_score)
            if tup not in done:
                done.append(tup)
                toon.append(voorwaarde)
        # for

        # ophakken in blokjes van 6, voor presentatie in een tabel
        context['voorwaarden'] = voorwaarden = list()
        while len(toon):
            benodigde_scores = [voorwaarde.benodigde_score
                                for voorwaarde in toon[:6]]
            voorwaarde = toon[0]
            tup = (voorwaarde.wedstrijd_soort, voorwaarde.aantal_pijlen, benodigde_scores)
            voorwaarden.append(tup)
            toon = toon[6:]
        # while

        context['kruimels'] = (
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Target awards')
        )

        return context


# end of file
