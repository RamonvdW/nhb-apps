# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (LAAG_REGIO, AG_NUL,
                               TEAM_PUNTEN_MODEL_FORMULE1, TEAM_PUNTEN_MODEL_TWEE, TEAM_PUNTEN_F1,
                               Competitie, CompetitieTeamKlasse, DeelCompetitie, RegioCompetitieSchutterBoog,
                               RegiocompetitieTeam, RegiocompetitieTeamPoule, RegiocompetitieRondeTeam,
                               CompetitieMutatie, MUTATIE_TEAM_RONDE)
from Competitie.operations.poules import maak_poule_schema
from Functie.rol import Rollen, rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek
from NhbStructuur.models import NhbRayon
from Plein.menu import menu_dynamics
from types import SimpleNamespace
import time


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
                      .filter(deelcompetitie=deelcomp)
                      .select_related('sporterboog__sporter',
                                      'bij_vereniging',
                                      'indiv_klasse__boogtype')
                      .order_by('indiv_klasse__volgorde',
                                '-gemiddelde'))

        context['deelnemers'] = uitslag = list()

        klasse = -1
        rank = 0
        deelnemer_count = deelnemer_een = deelnemer_twee = deelnemer_drie = None
        for deelnemer in deelnemers:

            deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
            if deelnemer.break_klasse:
                if rank >= 9:
                    # vanaf 9 deelnemers: 3 medailles
                    deelnemer_drie.toon_brons = True

                if rank >= 5:
                    # tot 8 deelnemers: 2 medailles
                    deelnemer_twee.toon_zilver = True

                if rank > 0:
                    # tot 4 deelnemers: 1 medaille
                    deelnemer_een.toon_goud = True

                deelnemer_count = deelnemer
                deelnemer_count.aantal_in_groep = 2   # 1 extra zodat balk doorloopt tot horizontale afsluiter

                deelnemer.is_eerste_groep = (klasse == -1)
                deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving
                rank = 0

                deelnemer_een = deelnemer_twee = deelnemer_drie = None

            klasse = deelnemer.indiv_klasse.volgorde

            if rank < 9:
                rank += 1
                sporter = deelnemer.sporterboog.sporter
                deelnemer.rank = rank
                deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                deelnemer.ver_str = str(deelnemer.bij_vereniging)

                deelnemer_count.aantal_in_groep += 1
                uitslag.append(deelnemer)

                if rank == 1:
                    deelnemer_een = deelnemer
                elif rank == 2:
                    deelnemer_twee = deelnemer
                elif rank == 3:
                    deelnemer_drie = deelnemer
        # for

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
