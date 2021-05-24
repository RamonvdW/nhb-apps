# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.templatetags.static import static
from Competitie.models import (Competitie, DeelCompetitie, DeelcompetitieRonde,
                               LAAG_REGIO, LAAG_RK, INSCHRIJF_METHODE_1)
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Taken.taken import eval_open_taken
from Wedstrijden.models import CompetitieWedstrijd, BAAN_TYPE_EXTERN


TEMPLATE_OVERZICHT = 'vereniging/overzicht.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = ver = functie_nu.nhb_ver

        context['clusters'] = ver.clusters.all()

        context['toon_aanmelden'] = (rol_nu != Rollen.ROL_WL)

        if functie_nu.nhb_ver.wedstrijdlocatie_set.exclude(baan_type=BAAN_TYPE_EXTERN).count() > 0:
            context['accommodatie_details_url'] = reverse('Vereniging:vereniging-accommodatie-details',
                                                          kwargs={'vereniging_pk': ver.pk})

        context['url_externe_locaties'] = reverse('Vereniging:externe-locaties',
                                                  kwargs={'vereniging_pk': ver.pk})

        if rol_nu == Rollen.ROL_SEC or ver.regio.is_administratief:
            context['competities'] = list()
            context['deelcomps'] = list()
            context['deelcomps_rk'] = list()
        else:
            context['toon_competities'] = True

            if rol_nu == Rollen.ROL_HWL:
                context['toon_wedstrijdkalender'] = True

            context['competities'] = (Competitie
                                      .objects
                                      .filter(is_afgesloten=False)
                                      .order_by('afstand'))

            context['deelcomps'] = (DeelCompetitie
                                    .objects
                                    .filter(laag=LAAG_REGIO,
                                            competitie__is_afgesloten=False,
                                            nhb_regio=ver.regio)
                                    .select_related('competitie')
                                    .order_by('competitie__afstand', 'competitie__begin_jaar'))

            context['deelcomps_rk'] = (DeelCompetitie
                                       .objects
                                       .filter(laag=LAAG_RK,
                                               competitie__is_afgesloten=False,
                                               nhb_rayon=ver.regio.rayon)
                                       .select_related('competitie')
                                       .order_by('competitie__afstand'))

            pks = (DeelcompetitieRonde
                   .objects
                   .filter(deelcompetitie__is_afgesloten=False,
                           plan__wedstrijden__vereniging=ver)
                   .values_list('plan__wedstrijden', flat=True))
            if CompetitieWedstrijd.objects.filter(pk__in=pks).count() > 0:
                context['heeft_wedstrijden'] = True

        # comp is nodig voor inschrijven
        for comp in context['competities']:
            comp.bepaal_fase()
            if comp.afstand == '18':
                comp.icon = static('plein/badge_nhb_indoor.png')
            else:
                comp.icon = static('plein/badge_nhb_25m1p.png')
        # for

        # deelcomp is nodig voor afmelden
        for deelcomp in context['deelcomps']:
            deelcomp.competitie.bepaal_fase()
            if deelcomp.competitie.afstand == '18':
                deelcomp.icon = static('plein/badge_nhb_indoor.png')
            else:
                deelcomp.icon = static('plein/badge_nhb_25m1p.png')

            deelcomp.toon_wie_schiet_waar = deelcomp.inschrijf_methode == INSCHRIJF_METHODE_1
        # for

        for deelcomp_rk in context['deelcomps_rk']:
            if deelcomp_rk.heeft_deelnemerslijst:
                comp = deelcomp_rk.competitie
                comp.bepaal_fase()
                if comp.fase == 'K':
                    # RK voorbereidende fase
                    deelcomp_rk.text_str = "Schutters van de vereniging aan-/afmelden voor het RK van de %s" % comp.beschrijving
                    deelcomp_rk.url_lijst_rk = reverse('Vereniging:lijst-rk',
                                                       kwargs={'deelcomp_pk': deelcomp_rk.pk})
        # for

        eval_open_taken(self.request)

        menu_dynamics(self.request, context, actief='vereniging')
        return context


# end of file
