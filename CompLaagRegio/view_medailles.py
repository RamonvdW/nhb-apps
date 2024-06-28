# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Regiocompetitie, RegiocompetitieSporterBoog
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie


TEMPLATE_COMPREGIO_MEDAILLES = 'complaagregio/medailles.dtl'


def bepaal_medailles(sub_uitslag, is_asp_klasse):

    aantal_medailles = 0
    aantal = len(sub_uitslag)
    # print('aantal: %s, sub_uitslag: %s' % (aantal, [deelnemer.rank for deelnemer in sub_uitslag]))

    if aantal > 0 and is_asp_klasse:
        # aspirant klasse: altijd 3 medailles
        for deelnemer in sub_uitslag:
            if deelnemer.rank == 1:
                deelnemer.toon_goud = True
            elif deelnemer.rank == 2:
                deelnemer.toon_zilver = True
            elif deelnemer.rank == 3:
                deelnemer.toon_brons = True
        # for
    else:
        # tot 4 deelnemers: 1 medaille
        # tot 8 deelnemers: 2 medailles
        # vanaf 9 deelnemers: 3 medailles

        # TODO: we tellen nu dubbele medaille kleuren mee in bovenstaande aantallen. Correct??

        if aantal > 0:
            for deelnemer in sub_uitslag:
                if deelnemer.rank == 1:
                    deelnemer.toon_goud = True
                    aantal_medailles += 1
            # for

        if aantal >= 5 and aantal_medailles < 2:
            for deelnemer in sub_uitslag:
                if deelnemer.rank == 2:
                    deelnemer.toon_zilver = True
                    aantal_medailles += 1
            # for

        if aantal >= 9 and aantal_medailles < 3:
            for deelnemer in sub_uitslag:
                if deelnemer.rank == 3:
                    deelnemer.toon_brons = True
                    # aantal_medailles += 1
            # for


class ToonMedailles(UserPassesTestMixin, TemplateView):

    """ Met deze view kan een lijst van teams getoond worden, zowel landelijk, rayon als regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_MEDAILLES
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL

    @staticmethod
    def bepaal_uitslag(deelcomp, min_aantal_scores):

        uitslag = list()

        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .filter(regiocompetitie=deelcomp,
                              aantal_scores__gte=min_aantal_scores)
                      .exclude(indiv_klasse__is_onbekend=True)
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'indiv_klasse__boogtype')
                      .order_by('indiv_klasse__volgorde',
                                '-gemiddelde'))

        klasse = -1
        prev_gemiddelde = -1
        prev_rank = 0
        rank = 0
        sub_uitslag = list()
        is_asp_klasse = False
        deelnemer_een = deelnemer_twee = deelnemer_drie = None
        for deelnemer in deelnemers:

            deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
            if deelnemer.break_klasse:
                bepaal_medailles(sub_uitslag, is_asp_klasse)

                deelnemer.is_eerste_groep = (klasse == -1)
                deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving

                is_asp_klasse = False
                if not deelnemer.indiv_klasse.is_ook_voor_rk_bk:
                    # dit is een aspiranten klassen of een klasse onbekend
                    for lkl in deelnemer.indiv_klasse.leeftijdsklassen.all():       # pragma: no branch
                        if lkl.is_aspirant_klasse():                                # pragma: no branch
                            is_asp_klasse = True
                            break
                    # for

                rank = 0
                prev_gemiddelde = -1
                sub_uitslag = list()

            klasse = deelnemer.indiv_klasse.volgorde

            if len(sub_uitslag) < 9:

                sporter = deelnemer.sporterboog.sporter
                deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                deelnemer.ver_str = str(deelnemer.bij_vereniging)

                rank += 1
                if deelnemer.gemiddelde == prev_gemiddelde:
                    deelnemer.rank = prev_rank
                else:
                    deelnemer.rank = rank
                    prev_rank = rank
                    prev_gemiddelde = deelnemer.gemiddelde

                sub_uitslag.append(deelnemer)
                uitslag.append(deelnemer)
        # for

        bepaal_medailles(sub_uitslag, is_asp_klasse)

        return uitslag

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            regio_nr = int(str(kwargs['regio'][:3]))       # afkappen voor de veiligheid
            # niet nodig om te filteren op is_afgesloten=True
            # want het kaartje wordt toch pas getoond bij is_afgesloten=True
            deelcomps = (Regiocompetitie
                         .objects
                         .select_related('competitie')
                         .filter(competitie__afstand=self.functie_nu.comp_type,
                                 regio__regio_nr=regio_nr)
                         .order_by('competitie__begin_jaar'))       # oudste eerst

            if deelcomps.count() < 1:
                raise Http404('Competitie niet gevonden')

            deelcomp = deelcomps[0]  # neem de oudste
        except ValueError:
            raise Http404('Competitie niet gevonden')

        # elke RCL mag de medailles lijst van elke andere regio inzien, dus geen check hier
        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        comp.bepaal_fase()
        # TODO: check fase

        context['min_aantal_scores'] = min_aantal_scores = comp.aantal_scores_voor_rk_deelname

        context['deelnemers'] = self.bepaal_uitslag(deelcomp, min_aantal_scores)

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Medailles')
        )

        return context


# end of file
