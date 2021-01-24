# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.templatetags.static import static
from Competitie.models import Competitie, DeelCompetitie, LAAG_REGIO, LAAG_RK
from Functie.rol import Rollen, rol_get_huidige_functie
from NhbStructuur.models import NhbCluster
from Plein.menu import menu_dynamics
from Taken.taken import eval_open_taken


TEMPLATE_OVERZICHT = 'vereniging/overzicht.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        context['clusters'] = functie_nu.nhb_ver.clusters.all()

        context['toon_aanmelden'] = (rol_nu != Rollen.ROL_WL)

        if functie_nu.nhb_ver.wedstrijdlocatie_set.count() > 0:
            locatie = functie_nu.nhb_ver.wedstrijdlocatie_set.all()[0]
            context['accommodatie_details_url'] = reverse('Vereniging:vereniging-accommodatie-details',
                                                          kwargs={'locatie_pk': locatie.pk,
                                                                  'vereniging_pk': functie_nu.nhb_ver.pk})

        if rol_nu == Rollen.ROL_SEC or functie_nu.nhb_ver.regio.is_administratief:
            context['competities'] = list()
            context['deelcomps'] = list()
            context['deelcomps_rk'] = list()
        else:
            context['competities'] = (Competitie
                                      .objects
                                      .filter(is_afgesloten=False)
                                      .order_by('afstand'))

            context['deelcomps'] = (DeelCompetitie
                                    .objects
                                    .filter(laag=LAAG_REGIO,
                                            competitie__is_afgesloten=False,
                                            nhb_regio=functie_nu.nhb_ver.regio)
                                    .select_related('competitie')
                                    .order_by('competitie__afstand'))

            context['deelcomps_rk'] = (DeelCompetitie
                                       .objects
                                       .filter(laag=LAAG_RK,
                                               competitie__is_afgesloten=False,
                                               nhb_rayon=functie_nu.nhb_ver.regio.rayon)
                                       .select_related('competitie')
                                       .order_by('competitie__afstand'))

        # comp is nodig voor inschrijven
        for comp in context['competities']:
            comp.zet_fase()
            if comp.afstand == '18':
                comp.icon = static('plein/badge_nhb_indoor.png')
            else:
                comp.icon = static('plein/badge_nhb_25m1p.png')
        # for

        # deelcomp is nodig voor afmelden
        for deelcomp in context['deelcomps']:
            deelcomp.competitie.zet_fase()
            if deelcomp.competitie.afstand == '18':
                deelcomp.icon = static('plein/badge_nhb_indoor.png')
            else:
                deelcomp.icon = static('plein/badge_nhb_25m1p.png')
        # for

        for deelcomp_rk in context['deelcomps_rk']:
            if deelcomp_rk.heeft_deelnemerslijst:
                comp = deelcomp_rk.competitie
                comp.zet_fase()
                if comp.fase == 'K':
                    # RK voorbereidende fase
                    deelcomp_rk.text_str = "Schutters van de vereniging aan-/afmeldenvoor het RK van de %s" % comp.beschrijving
                    deelcomp_rk.url_lijst_rk = reverse('Vereniging:lijst-rk',
                                                       kwargs={'deelcomp_pk': deelcomp_rk.pk})
        # for

        eval_open_taken(self.request)

        menu_dynamics(self.request, context, actief='vereniging')
        return context


# end of file
