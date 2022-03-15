# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import DeelCompetitie, RegioCompetitieSchutterBoog
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics


TEMPLATE_COMPREGIO_MEDAILLES = 'compregio/medailles.dtl'


class ToonMedailles(UserPassesTestMixin, TemplateView):

    """ Met deze view kan een lijst van teams getoond worden, zowel landelijk, rayon als regio """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_MEDAILLES
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL

    @staticmethod
    def _split_aspiranten(asps, objs):
        klasse_str = asps[0].klasse_str
        rank_m = 0
        rank_v = 0
        asps_v = list()
        for deelnemer in asps:
            if deelnemer.sporterboog.sporter.geslacht == 'V':
                if rank_v == 0:
                    deelnemer.klasse_str = klasse_str + ', meisjes'
                    deelnemer.break_klasse = True
                rank_v += 1
                deelnemer.rank = rank_v
                asps_v.append(deelnemer)
            else:
                if rank_m == 0:
                    deelnemer.klasse_str = klasse_str + ', jongens'
                    deelnemer.break_klasse = True
                rank_m += 1
                deelnemer.rank = rank_m
                objs.append(deelnemer)

            # aspiranten klassen krijgen altijd medaille, onafhankelijk van aantal deelnemers
            if deelnemer.rank <= 3:
                if deelnemer.rank == 1:
                    deelnemer.toon_goud = True
                elif deelnemer.rank == 2:
                    deelnemer.toon_zilver = True
                elif deelnemer.rank == 3:
                    deelnemer.toon_brons = True
        # for

        if len(asps_v):
            objs.extend(asps_v)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            regio_nr = int(str(kwargs['regio'][:3]))       # afkappen voor de veiligheid
            # TODO: filter op is_afgesloten=True zodat deze lijst niet te vroeg komt?
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(competitie__afstand=self.functie_nu.comp_type,
                             nhb_regio__regio_nr=regio_nr))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # elke RCL mag de medailles lijst van elke andere regio inzien, dus geen check hier
        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        comp.bepaal_fase()
        # TODO: check fase

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp,
                              aantal_scores__gte=6)
                      .exclude(indiv_klasse__is_onbekend=True)
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'indiv_klasse__boogtype')
                      .order_by('indiv_klasse__volgorde',
                                '-gemiddelde'))

        context['deelnemers'] = uitslag = list()

        klasse = -1
        rank = 0
        asps = list()
        is_asp = False
        deelnemer_een = deelnemer_twee = deelnemer_drie = None
        for deelnemer in deelnemers:

            deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
            if deelnemer.break_klasse:
                if len(asps):
                    self._split_aspiranten(asps, uitslag)      # TODO: niet meer nodig in seizoen 2022/2023
                    asps = list()
                else:
                    if rank >= 9:
                        # vanaf 9 deelnemers: 3 medailles
                        deelnemer_drie.toon_brons = True

                    if rank >= 5:
                        # tot 8 deelnemers: 2 medailles
                        deelnemer_twee.toon_zilver = True

                    if rank > 0:
                        # tot 4 deelnemers: 1 medaille
                        deelnemer_een.toon_goud = True

                deelnemer.is_eerste_groep = (klasse == -1)
                deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving

                is_asp = False
                if not deelnemer.indiv_klasse.is_voor_rk_bk:
                    # dit is een aspiranten klassen of een klasse onbekend
                    for lkl in deelnemer.indiv_klasse.leeftijdsklassen.all():       # pragma: no branch
                        if lkl.is_aspirant_klasse():                                # pragma: no branch
                            is_asp = True
                            break
                    # for

                rank = 0
                deelnemer_een = deelnemer_twee = deelnemer_drie = None

            klasse = deelnemer.indiv_klasse.volgorde

            if rank < 9:
                rank += 1
                sporter = deelnemer.sporterboog.sporter
                deelnemer.rank = rank
                deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                deelnemer.ver_str = str(deelnemer.bij_vereniging)

                if is_asp:
                    asps.append(deelnemer)
                else:
                    uitslag.append(deelnemer)

                if rank == 1:
                    deelnemer_een = deelnemer
                elif rank == 2:
                    deelnemer_twee = deelnemer
                elif rank == 3:
                    deelnemer_drie = deelnemer
        # for

        if len(asps):
            # aspiranten opsplitsen in jongens en meisjes klasse
            self._split_aspiranten(asps, uitslag)
        else:
            if rank >= 9:
                # vanaf 9 deelnemers: 3 medailles
                deelnemer_drie.toon_brons = True

            if rank >= 5:
                # tot 8 deelnemers: 2 medailles
                deelnemer_twee.toon_zilver = True

            if rank > 0:
                # tot 4 deelnemers: 1 medaille
                deelnemer_een.toon_goud = True

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Medailles')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
