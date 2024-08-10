# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_RK, DEELNAME_JA, DEELNAME_NEE
from Competitie.models import Kampioenschap, KampioenschapSporterBoog
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie


TEMPLATE_COMPRAYON_LIJST_RK = 'complaagrayon/hwl-rk-selectie.dtl'


class LijstRkSelectieView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de (kandidaat) schutters van en RK zien,
        met mogelijkheid voor de RKO om deze te bevestigen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_LIJST_RK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        ver = self.functie_nu.vereniging
        rayon = ver.regio.rayon

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'rayon')
                        .get(pk=deelkamp_pk,
                             rayon=rayon,
                             deel=DEEL_RK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['deelcomp_rk'] = deelkamp

        comp = deelkamp.competitie
        comp.bepaal_fase()

        if comp.fase_indiv not in ('J', 'K', 'L'):
            raise Http404('Pagina kan niet gebruikt worden')

        mag_wijzigen = ('J' <= comp.fase_indiv <= 'K')

        deelnemers = (KampioenschapSporterBoog
                      .objects
                      .select_related('kampioenschap',
                                      'indiv_klasse',
                                      'sporterboog__sporter',
                                      'bij_vereniging')
                      .filter(kampioenschap=deelkamp,
                              bij_vereniging=ver)
                      .order_by('indiv_klasse__volgorde',   # groepeer per klasse
                                'volgorde',                 # oplopend op volgorde
                                '-gemiddelde'))             # aflopend op gemiddelde

        aantal_afgemeld = 0
        aantal_bevestigd = 0
        aantal_onbekend = 0
        aantal_klassen = 0

        klasse = -1
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
            if deelnemer.break_klasse:
                aantal_klassen += 1
                deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving
                klasse = deelnemer.indiv_klasse.volgorde

            sporter = deelnemer.sporterboog.sporter
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

            if mag_wijzigen:
                deelnemer.url_wijzig = reverse('CompLaagRayon:wijzig-status-rk-deelnemer',
                                               kwargs={'deelnemer_pk': deelnemer.pk})

            # tel de status van de deelnemers en eerste 8 reserveschutters
            if deelnemer.deelname == DEELNAME_NEE:
                aantal_afgemeld += 1
            elif deelnemer.deelname == DEELNAME_JA:
                aantal_bevestigd += 1
            else:
                aantal_onbekend += 1
        # for

        context['deelnemers'] = deelnemers

        context['aantal_afgemeld'] = aantal_afgemeld
        context['aantal_onbekend'] = aantal_onbekend
        context['aantal_bevestigd'] = aantal_bevestigd

        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer Vereniging'),
            (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
            (None, 'Deelnemers RK'),
        )

        return context


# end of file
