# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import TemplateView
from django.urls import reverse, Resolver404
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbRayon, NhbRegio
from Competitie.models import (AG_NUL, LAAG_REGIO, LAAG_RK, LAAG_BK,
                               DeelCompetitie, RegioCompetitieSchutterBoog)
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_huidige
from Plein.menu import menu_dynamics
from .models import Competitie


TEMPLATE_COMPETITIE_TUSSENSTAND = 'competitie/tussenstand.dtl'
TEMPLATE_COMPETITIE_TUSSENSTAND_REGIO = 'competitie/tussenstand-regio.dtl'
TEMPLATE_COMPETITIE_TUSSENSTAND_RAYON = 'competitie/tussenstand-rayon.dtl'
TEMPLATE_COMPETITIE_TUSSENSTAND_BOND = 'competitie/tussenstand-bond.dtl'

TEMPLATE_COMPETITIE_TUSSENSTAND_REGIO_ALT = 'competitie/tussenstand-regio-alt.dtl'


class TussenstandView(TemplateView):

    """ Django class-based view voor de de tussenstand van de competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_TUSSENSTAND

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # TODO: besluit wanneer uitslag vorig seizoen niet meer tonen
        context['toon_histcomp'] = True

        # kijk of de tussenstand klaar is om te tonen
        context['toon_comps'] = False

        for comp in Competitie.objects.filter(is_afgesloten=False).all():
            comp.zet_fase()
            if comp.fase >= 'B':        # inschrijving is open
                context['toon_comps'] = True
        # for

        context['url_18_regio'] = reverse('Competitie:tussenstand-regio',
                                          kwargs={'afstand': 18, 'comp_boog': 'r'})
        context['url_18_rayon'] = reverse('Competitie:tussenstand-rayon',
                                          kwargs={'afstand': 18, 'comp_boog': 'r'})
        context['url_18_bond'] = reverse('Competitie:tussenstand-bond',
                                         kwargs={'afstand': 18, 'comp_boog': 'r'})

        context['url_25_regio'] = reverse('Competitie:tussenstand-regio',
                                          kwargs={'afstand': 25, 'comp_boog': 'r'})
        context['url_25_rayon'] = reverse('Competitie:tussenstand-rayon',
                                          kwargs={'afstand': 25, 'comp_boog': 'r'})
        context['url_25_bond'] = reverse('Competitie:tussenstand-bond',
                                         kwargs={'afstand': 25, 'comp_boog': 'r'})

        menu_dynamics(self.request, context, actief='histcomp')
        return context


class TussenstandRegioView(TemplateView):

    """ Django class-based view voor de de tussenstand van de competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_TUSSENSTAND_REGIO
    url_name = 'Competitie:tussenstand-regio-n'
    url_switch = 'Competitie:tussenstand-regio-n-alt'
    order_gemiddelde = '-gemiddelde'

    def _get_schutter_regio_nr(self):
        """ Geeft het regio nummer van de ingelogde schutter terug,
            of 101 als er geen regio vastgesteld kan worden
        """
        regio_nr = 101

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if functie_nu:
            if functie_nu.nhb_ver:
                # HWL, WL
                regio_nr = functie_nu.nhb_ver.regio.regio_nr
            elif functie_nu.nhb_regio:
                # RCL
                regio_nr = functie_nu.nhb_regio.regio_nr
            elif functie_nu.nhb_rayon:
                # RKO
                regio = (NhbRegio
                         .objects
                         .filter(rayon=functie_nu.nhb_rayon,
                                 is_administratief=False)
                         .order_by('regio_nr'))[0]
                regio_nr = regio.regio_nr
        elif rol_nu == Rollen.ROL_SCHUTTER:
            # schutter
            account = self.request.user
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                if nhblid.is_actief_lid and nhblid.bij_vereniging:
                    nhb_ver = nhblid.bij_vereniging
                    regio_nr = nhb_ver.regio.regio_nr

        return regio_nr

    def _maak_filter_knoppen(self, context, afstand, gekozen_regio_nr, comp_boog):
        """ filter knoppen per regio, gegroepeerd per rayon en per competitie boog type """

        # boogtype files
        boogtypen = BoogType.objects.order_by('volgorde').all()

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled
            else:
                boogtype.zoom_url = reverse(self.url_name,
                                            kwargs={'afstand': afstand,
                                                    'comp_boog': boogtype.afkorting.lower(),
                                                    'regio_nr': gekozen_regio_nr})
        # for

        if context['comp_boog']:
            # regio filters
            regios = (NhbRegio
                      .objects
                      .select_related('rayon')
                      .filter(is_administratief=False)
                      .order_by('rayon__rayon_nr'))

            context['regio_filters'] = regios

            prev_rayon = 1
            for regio in regios:
                regio.break_before = (prev_rayon != regio.rayon.rayon_nr)
                prev_rayon = regio.rayon.rayon_nr

                regio.title_str = 'Regio %s' % regio.regio_nr
                if regio.regio_nr != gekozen_regio_nr:
                    regio.zoom_url = reverse(self.url_name,
                                             kwargs={'afstand': afstand,
                                                     'comp_boog': comp_boog,
                                                     'regio_nr': regio.regio_nr})
                else:
                    # geen zoom_url --> knop disabled
                    context['regio'] = regio
            # for

        context['url_switch'] = reverse(self.url_switch,
                                        kwargs={'afstand': afstand,
                                                'comp_boog': comp_boog,
                                                'regio_nr': gekozen_regio_nr})

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        afstand = kwargs['afstand'][:2]         # afkappen voor veiligheid
        comp_boog = kwargs['comp_boog'][:2]     # afkappen voor veiligheid

        # regio_nr is optioneel (eerste binnenkomst zonder regio nummer)
        try:
            regio_nr = kwargs['regio_nr'][:3]   # afkappen voor veiligheid
            regio_nr = int(regio_nr)
        except KeyError:
            # keep welke (initiële) regio bij de huidige gebruiker past
            regio_nr = self._get_schutter_regio_nr()
        except ValueError:
            raise Resolver404()

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(laag=LAAG_REGIO,
                             competitie__afstand=afstand,
                             competitie__is_afgesloten=False,
                             nhb_regio__regio_nr=regio_nr))
        except DeelCompetitie.DoesNotExist:
            # niet mogelijk: return HttpResponseRedirect(reverse('Competitie:tussenstand'))
            raise Resolver404()

        context['deelcomp'] = deelcomp

        self._maak_filter_knoppen(context, afstand, regio_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Resolver404()

        deelnemers = (RegioCompetitieSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp)
                      .select_related('schutterboog', 'schutterboog__nhblid',
                                      'bij_vereniging', 'klasse', 'klasse__indiv', 'klasse__indiv__boogtype')
                      .filter(klasse__indiv__boogtype=boogtype)
                      .order_by('klasse__indiv__volgorde', self.order_gemiddelde))

        klasse = -1
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
            klasse = deelnemer.klasse.indiv.volgorde

            lid = deelnemer.schutterboog.nhblid
            deelnemer.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
            deelnemer.ver_str = str(deelnemer.bij_vereniging)
        # for

        context['deelnemers'] = deelnemers

        rol_nu = rol_get_huidige(self.request)
        is_beheerder = rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)
        context['is_beheerder'] = is_beheerder

        menu_dynamics(self.request, context, actief='histcomp')
        return context


class TussenstandRegioAltView(UserPassesTestMixin, TussenstandRegioView):

    """ Django class-based view voor de de alternative tussenstand van de competitie """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_TUSSENSTAND_REGIO_ALT
    url_name = 'Competitie:tussenstand-regio-n-alt'
    url_switch = 'Competitie:tussenstand-regio-n'
    order_gemiddelde = '-alt_gemiddelde'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle beheerders mogen deze lijst zien
        rol_nu = rol_get_huidige(self.request)
        is_beheerder = rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)
        return is_beheerder

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        path = self.request.path.replace('/regio-alt/', '/regio/')
        return HttpResponseRedirect(path)


class TussenstandRayonView(TemplateView):

    """ Django class-based view voor de de tussenstand van de rayonkampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_TUSSENSTAND_RAYON

    def _maak_filter_knoppen(self, context, afstand, gekozen_rayon_nr, comp_boog):
        """ filter knoppen per rayon en per competitie boog type """

        # boogtype files
        boogtypen = BoogType.objects.order_by('volgorde').all()

        context['comp_boog'] = None
        context['boog_filters'] = boogtypen

        for boogtype in boogtypen:
            if boogtype.afkorting.upper() == comp_boog.upper():
                context['comp_boog'] = boogtype
                comp_boog = boogtype.afkorting.lower()
                # geen url --> knop disabled
            else:
                boogtype.zoom_url = reverse('Competitie:tussenstand-rayon-n',
                                            kwargs={'afstand': afstand,
                                                    'comp_boog': boogtype.afkorting.lower(),
                                                    'rayon_nr': gekozen_rayon_nr})
        # for

        if context['comp_boog']:
            # rayon filters
            rayons = (NhbRayon
                      .objects
                      .order_by('rayon_nr')
                      .all())

            context['rayon_filters'] = rayons

            for rayon in rayons:
                rayon.title_str = 'Rayon %s' % rayon.rayon_nr
                if rayon.rayon_nr != gekozen_rayon_nr:
                    rayon.zoom_url = reverse('Competitie:tussenstand-rayon-n',
                                             kwargs={'afstand': afstand,
                                                     'comp_boog': comp_boog,
                                                     'rayon_nr': rayon.rayon_nr})
                else:
                    # geen zoom_url --> knop disabled
                    context['rayon'] = rayon
            # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            afstand = int(kwargs['afstand'][:2])     # afkappen voor veiligheid
        except ValueError:
            raise Resolver404()

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor veiligheid

        # rayon_nr is optioneel (eerste binnenkomst zonder rayon nummer)
        try:
            rayon_nr = kwargs['rayon_nr'][:2]        # afkappen voor veiligheid
            rayon_nr = int(rayon_nr)
        except KeyError:
            rayon_nr = 1
        except ValueError:
            raise Resolver404()

        self._maak_filter_knoppen(context, afstand, rayon_nr, comp_boog)

        boogtype = context['comp_boog']
        if not boogtype:
            raise Resolver404()

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_rayon')
                        .get(laag=LAAG_RK,
                             competitie__is_afgesloten=False,
                             competitie__afstand=afstand,
                             nhb_rayon__rayon_nr=rayon_nr))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        context['deelcomp'] = deelcomp

        menu_dynamics(self.request, context, actief='histcomp')
        return context


class TussenstandBondView(TemplateView):

    """ Django class-based view voor de de tussenstand van de bondskampioenschappen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_TUSSENSTAND_BOND

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            afstand = int(kwargs['afstand'][:2])     # afkappen voor veiligheid
        except ValueError:
            raise Resolver404()

        comp_boog = kwargs['comp_boog'][:2]          # afkappen voor veiligheid

        try:
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(laag=LAAG_BK,
                             competitie__is_afgesloten=False,
                             competitie__afstand=afstand))
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()

        menu_dynamics(self.request, context, actief='histcomp')
        return context


# end of file
