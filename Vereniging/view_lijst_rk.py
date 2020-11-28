# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Competitie.models import (LAAG_REGIO, LAAG_RK, DeelCompetitie,
                               DeelcompetitieKlasseLimiet, KampioenschapSchutterBoog)


TEMPLATE_VERENIGING_LIJST_RK = 'vereniging/lijst-rk.dtl'


class VerenigingLijstRkSchuttersView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de kandidaat-schutters van en RK zien van de vereniging van de HWL,
        met mogelijkheid voor de HWL om deze te bevestigen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_VERENIGING_LIJST_RK
    toon_alles = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # er zijn 2 situaties:
        # 1) regiocompetities zijn nog niet afgesloten --> verwijst naar pagina tussenstand rayon
        # 2) deelnemers voor RK zijn vastgesteld --> toon lijst

        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:6])  # afkappen geeft beveiliging
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Resolver404()

        if not deelcomp_rk.heeft_deelnemerslijst:
            raise Resolver404()

        context['deelcomp_rk'] = deelcomp_rk

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        deelnemers = (KampioenschapSchutterBoog
                      .objects
                      .select_related('deelcompetitie',
                                      'klasse__indiv',
                                      'schutterboog__nhblid',
                                      'bij_vereniging')
                      .filter(deelcompetitie=deelcomp_rk,
                              volgorde__lte=48)             # max 48 schutters per klasse tonen
                      .order_by('klasse__indiv__volgorde',  # groepeer per klasse
                                'volgorde',                 # oplopend op volgorde (dubbelen mogelijk)
                                '-gemiddelde'))             # aflopend op gemiddelde

        if not self.toon_alles:
            deelnemers = deelnemers.filter(bij_vereniging=functie_nu.nhb_ver)

        wkl2limiet = dict()    # [pk] = aantal
        for limiet in (DeelcompetitieKlasseLimiet
                       .objects
                       .select_related('klasse')
                       .filter(deelcompetitie=deelcomp_rk)):
            wkl2limiet[limiet.klasse.pk] = limiet.limiet
        # for

        context['kan_wijzigen'] = kan_wijzigen = (rol_nu == Rollen.ROL_HWL)

        aantal_klassen = 0
        keep = list()

        groepje = list()
        behoud_groepje = False
        klasse = -1
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                if len(groepje) and behoud_groepje:
                    aantal_klassen += 1
                    keep.extend(groepje)
                groepje = list()
                behoud_groepje = False
                deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
                klasse = deelnemer.klasse.indiv.volgorde
                try:
                    limiet = wkl2limiet[deelnemer.klasse.pk]
                except KeyError:
                    limiet = 24

            lid = deelnemer.schutterboog.nhblid
            deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())

            if deelnemer.bij_vereniging == functie_nu.nhb_ver:
                behoud_groepje = True
                deelnemer.mijn_vereniging = True
                if kan_wijzigen:
                    deelnemer.url_wijzig = reverse('Competitie:wijzig-status-rk-deelnemer',
                                                   kwargs={'deelnemer_pk': deelnemer.pk})

            if deelnemer.rank > limiet:
                deelnemer.is_reserve = True

            groepje.append(deelnemer)
        # for

        if len(groepje) and behoud_groepje:
            aantal_klassen += 1
            keep.extend(groepje)

        context['deelnemers'] = keep
        context['aantal_klassen'] = aantal_klassen

        if self.toon_alles:
            context['url_filtered'] = reverse('Vereniging:lijst-rk',
                                              kwargs={'deelcomp_pk': deelcomp_rk.pk})
        else:
            context['url_alles'] = reverse('Vereniging:lijst-rk-alles',
                                           kwargs={'deelcomp_pk': deelcomp_rk.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class VerenigingLijstRkSchuttersAllesView(VerenigingLijstRkSchuttersView):

    """ Deze view laat alle kandidaat-schutters van en RK zien,
        met mogelijkheid voor de HWL om deze te bevestigen.
    """

    toon_alles = True


# end of file
