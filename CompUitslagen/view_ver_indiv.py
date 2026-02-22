# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from Account.models import get_account
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieSporterBoog
from Competitie.seizoenen import get_comp_pk
from Functie.rol import rol_get_huidige_functie
from Sporter.models import get_sporter
from Vereniging.models import Vereniging


TEMPLATE_COMPUITSLAGEN_VERENIGING_INDIV = 'compuitslagen/vereniging-indiv.dtl'


def get_sporter_ver_nr(request):

    """ Geeft het vereniging bondsnummer van de ingelogde sporter terug,
        of 101 als er geen regio vastgesteld kan worden
    """
    ver_nr = -1

    if request.user.is_authenticated:
        rol_nu, functie_nu = rol_get_huidige_functie(request)

        if functie_nu and functie_nu.vereniging:
            # HWL, WL, SEC
            ver_nr = functie_nu.vereniging.ver_nr

        if ver_nr < 0:
            # pak de vereniging van de ingelogde gebruiker
            account = get_account(request)
            sporter = get_sporter(account)
            if sporter.is_actief_lid and sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr

    ver_nrs = list(Vereniging.objects.order_by('ver_nr').values_list('ver_nr', flat=True))
    if ver_nr not in ver_nrs:
        ver_nr = ver_nrs[0]

    return ver_nr


class UitslagenVerenigingIndivView(TemplateView):

    """ Django class-based view voor de de uitslagen van de competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPUITSLAGEN_VERENIGING_INDIV

    @staticmethod
    def _maak_filter_knoppen(context, comp, ver_nr, comp_boog):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        # boogtype filters
        boogtypen = comp.boogtypen.order_by('volgorde')

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            boogtype.sel = 'boog_' + boogtype.afkorting
            if boogtype.afkorting.upper() == comp_boog.upper():
                boogtype.selected = True
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled

            boogtype.zoom_url = reverse('CompUitslagen:uitslagen-vereniging-indiv-n',
                                        kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                                'comp_boog': boogtype.afkorting.lower(),
                                                'ver_nr': ver_nr})
        # for

    @staticmethod
    def _get_deelcomp(comp, regio_nr):
        if regio_nr == 100:
            regio_nr = 101

        try:
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie', 'regio')
                        .get(competitie=comp,
                             competitie__is_afgesloten=False,
                             regio__regio_nr=regio_nr))
        except Regiocompetitie.DoesNotExist:     # pragma: no cover
            raise Http404('Competitie niet gevonden')

        return deelcomp

    @staticmethod
    def _get_deelnemers(deelcomp, boogtype, ver_nr):
        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'indiv_klasse',
                                      'indiv_klasse__boogtype')
                      .filter(regiocompetitie=deelcomp,
                              bij_vereniging__ver_nr=ver_nr,
                              indiv_klasse__boogtype=boogtype)
                      .order_by('-gemiddelde'))

        rank = 1
        for deelnemer in deelnemers:
            sporter = deelnemer.sporterboog.sporter
            deelnemer.rank = rank
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
            deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving
            rank += 1
        # for

        return deelnemers

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = get_comp_pk(kwargs['comp_pk_of_seizoen'])
            comp = (Competitie
                    .objects
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        comp.bepaal_fase()
        context['comp'] = comp

        comp_boog = kwargs['comp_boog'][:2]     # afkappen voor de veiligheid

        # ver_nr is optioneel en resulteert in het nummer van de sporter
        try:
            ver_nr = kwargs['ver_nr'][:4]     # afkappen voor de veiligheid
            ver_nr = int(ver_nr)
        except KeyError:
            # zoek de vereniging die bij de huidige gebruiker past
            ver_nr = get_sporter_ver_nr(self.request)
        except ValueError:
            raise Http404('Verkeerd verenigingsnummer')

        try:
            ver = Vereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        except Vereniging.DoesNotExist:
            raise Http404('Vereniging niet gevonden')

        context['ver'] = ver

        self._maak_filter_knoppen(context, comp, ver_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Http404('Boogtype niet bekend')

        regio_nr = ver.regio.regio_nr
        context['url_terug'] = reverse('CompUitslagen:uitslagen-regio-indiv-n',
                                       kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                               'comp_boog': comp_boog,
                                               'regio_nr': regio_nr})

        context['deelcomp'] = deelcomp = self._get_deelcomp(comp, regio_nr)

        context['deelnemers'] = deelnemers = self._get_deelnemers(deelcomp, boogtype, ver_nr)
        context['aantal_deelnemers'] = len(deelnemers)
        context['aantal_regels'] = len(deelnemers) + 2

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}),
                comp.beschrijving.replace(' competitie', '')),
            (context['url_terug'], 'Uitslag regio individueel'),
            (None, 'Vereniging')
        )

        return context


# end of file
