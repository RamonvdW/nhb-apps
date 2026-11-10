# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from Spelden.definities import SPELD_CATEGORIE_WA_ARROWHEAD_2024
from Spelden.models import SpeldVoorwaarden

TEMPLATE_PRESTATIESPELDEN_ARROWHEAD = 'spelden/wa-arrowhead-spelden.dtl'


class ArrowheadView(TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_PRESTATIESPELDEN_ARROWHEAD

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        qset = (SpeldVoorwaarden
                .objects
                .filter(speld__categorie=SPELD_CATEGORIE_WA_ARROWHEAD_2024)
                .select_related('leeftijdsklasse',
                                'boog_type',
                                'speld')
                .order_by('speld__volgorde',
                          'boog_type__volgorde',
                          'leeftijdsklasse__wedstrijd_geslacht'))

        context['ah_24'] = spelden = list()
        speld = None
        for obj in qset.filter(aantal_doelen=24):
            kleur = obj.speld.beschrijving.split()[-1]
            if speld is None or speld['kleur'] != kleur:
                speld = {
                    'kleur': kleur,
                    'R': dict(),
                    'C': dict(),
                    'BB': dict()
                }
                spelden.append(speld)

            scores = speld[obj.boog_type.afkorting]
            scores[obj.leeftijdsklasse.wedstrijd_geslacht] = obj.benodigde_score
        # for

        context['ah_48'] = spelden = list()
        speld = None
        for obj in qset.filter(aantal_doelen=48):
            kleur = obj.speld.beschrijving.split()[-1]
            if speld is None or speld['kleur'] != kleur:
                speld = {
                    'kleur': kleur,
                    'R': dict(),
                    'C': dict(),
                    'BB': dict()
                }
                spelden.append(speld)

            scores = speld[obj.boog_type.afkorting]
            scores[obj.leeftijdsklasse.wedstrijd_geslacht] = obj.benodigde_score
        # for

        context['kruimels'] = (
            (reverse('Spelden:begin'), 'Prestatiespelden'),
            (None, 'Arrowhead spelden')
        )

        return context


# end of file
