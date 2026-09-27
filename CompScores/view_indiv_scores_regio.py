# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import CompetitieMatch
from CompLaagRegio.models import RegioComp, RegioRonde
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_huidige_functie

TEMPLATE_COMPSCORES_REGIO = 'compscores/rcl-scores-regio.dtl'


class ScoresRegioView(UserPassesTestMixin, TemplateView):

    """ Deze view geeft de RCL een lijst met wedstrijden en toegang tot scores/accorderen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPSCORES_REGIO
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:7])            # afkappen voor de veiligheid
            deelcomp = (RegioComp
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if deelcomp.functie != functie_nu:
            # niet de beheerder
            raise PermissionDenied('Niet de beheerder')

        context['deelcomp'] = deelcomp

        comp = deelcomp.competitie
        # TODO: check competitie fase

        # regiocompetitie bestaat uit rondes
        # elke ronde heeft een plan met wedstrijden

        match_pks = list()
        match2beschrijving = dict()

        for ronde in (RegioRonde
                      .objects
                      .prefetch_related('matches')
                      .filter(regiocomp=deelcomp)):

            for match in ronde.matches.all():
                match_pks.append(match.pk)
                beschrijving = ronde.beschrijving
                if not beschrijving and ronde.cluster:
                    beschrijving = ronde.cluster.naam
                if not beschrijving:
                    beschrijving = "?? (ronde)"
                match2beschrijving[match.pk] = beschrijving
            # for
        # for

        matches = (CompetitieMatch
                   .objects
                   .select_related('uitslag',
                                   'vereniging')
                   .filter(pk__in=match_pks)
                   .annotate(scores_count=Count('uitslag__scores'))
                   .order_by('datum_wanneer', 'tijd_begin_wedstrijd',
                             'pk'))     # vaste sortering bij gelijke datum/tijd

        for match in matches:
            heeft_uitslag = (match.uitslag and match.scores_count > 0)

            beschrijving = match2beschrijving[match.pk]
            if match.beschrijving != beschrijving:
                match.beschrijving = beschrijving

            # geef RCL de mogelijkheid om de scores aan te passen
            # de HWL/WL krijgen deze link vanuit Vereniging.Wedstrijden
            if heeft_uitslag and not match.uitslag.is_bevroren:
                match.url_uitslag_controleren = reverse('CompScores:uitslag-controleren',
                                                        kwargs={'match_pk': match.pk})
            else:
                # TODO: knop pas beschikbaar maken op wedstrijddatum tot datum+N
                match.url_uitslag_invoeren = reverse('CompScores:uitslag-invoeren',
                                                     kwargs={'match_pk': match.pk})
        # for

        context['wedstrijden'] = matches

        context['aantal_regels'] = matches.count() + 2

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Scores')
        )

        return context


# end of file
