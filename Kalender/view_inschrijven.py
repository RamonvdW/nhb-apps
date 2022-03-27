# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from django.views.generic import TemplateView
from BasisTypen.models import BoogType, ORGANISATIE_WA, ORGANISATIE_IFAA
from Functie.rol import Rollen, rol_get_huidige
from Mandje.mandje import eval_mandje_is_leeg
from Plein.menu import menu_dynamics
from Sporter.models import get_sporter_voorkeuren_wedstrijdbogen
from .models import KalenderWedstrijd, KalenderWedstrijdSessie
from Kalender.view_maand import MAAND2URL

TEMPLATE_KALENDER_INSCHRIJVEN_SPORTER = 'kalender/inschrijven-sporter.dtl'
TEMPLATE_KALENDER_INSCHRIJVEN_GROEPJE = 'kalender/inschrijven-groepje.dtl'
TEMPLATE_KALENDER_INSCHRIJVEN_FAMILIE = 'kalender/inschrijven-familie.dtl'


def get_sessies(wedstrijd, sporter, voorkeuren, wedstrijdboog_pks):

    wedstrijdleeftijd = None
    if sporter:
        wedstrijdleeftijd = sporter.bereken_wedstrijdleeftijd(wedstrijd.datum_begin, wedstrijd.organisatie)

    wedstrijd_geslacht = '?'
    if voorkeuren:
        if voorkeuren.wedstrijd_geslacht_gekozen:
            wedstrijd_geslacht = voorkeuren.wedstrijd_geslacht

    sessie_pks = list(wedstrijd.sessies.values_list('pk', flat=True))
    sessies = (KalenderWedstrijdSessie
               .objects
               .filter(pk__in=sessie_pks)
               .prefetch_related('wedstrijdklassen')
               .order_by('datum',
                         'tijd_begin',
                         'pk'))

    wedstrijdklassen = list()
    for sessie in sessies:
        sessie.aantal_beschikbaar = sessie.max_sporters - sessie.aantal_inschrijvingen
        sessie.klassen = sessie.wedstrijdklassen.select_related('leeftijdsklasse').all()

        sessie.kan_aanmelden = False

        compatible_boog = False
        compatible_geslacht = False
        compatible_leeftijd = False

        for klasse in sessie.klassen:
            lkl = klasse.leeftijdsklasse

            if klasse.boogtype.id in wedstrijdboog_pks:
                compatible_boog = True

            # check geslacht is compatible
            if lkl.geslacht_is_compatible(wedstrijd_geslacht):
                compatible_geslacht = True

            # check leeftijd is compatible
            if wedstrijdleeftijd:
                if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                    compatible_leeftijd = True

                    # verzamel een lijstje van compatibele wedstrijdklassen om te tonen
                    if lkl.beschrijving not in wedstrijdklassen:
                        if lkl.geslacht_is_compatible(wedstrijd_geslacht):
                            wedstrijdklassen.append(lkl.beschrijving)
        # for

        if compatible_boog and compatible_leeftijd and compatible_geslacht:
            sessie.kan_aanmelden = True

        sessie.compatible_boog = compatible_boog
        sessie.compatible_leeftijd = compatible_leeftijd
        sessie.compatible_geslacht = compatible_geslacht
    # for

    return sessies, wedstrijdleeftijd, wedstrijdklassen, wedstrijd_geslacht


class WedstrijdInschrijvenSporter(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf inschrijven voor een wedstrijd """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_INSCHRIJVEN_SPORTER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except KalenderWedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        if self.request.user.is_authenticated:
            account = self.request.user
            lid_nr = account.username
        else:
            lid_nr = -1

        sporter, voorkeuren, wedstrijdboog_pks = get_sporter_voorkeuren_wedstrijdbogen(lid_nr)

        context['sporter'] = sporter
        context['bogen'] = BoogType.objects.filter(pk__in=wedstrijdboog_pks).order_by('volgorde')

        tups = get_sessies(wedstrijd, sporter, voorkeuren, wedstrijdboog_pks)
        context['sessies'], context['leeftijd'], context['leeftijdsklassen'], geslacht = tups

        kan_aanmelden = False
        for sessie in context['sessies']:
            if sessie.kan_aanmelden:
                kan_aanmelden = True
                break
        # for
        context['kan_aanmelden'] = kan_aanmelden

        # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
        # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
        if geslacht == '?':
            context['uitleg_geslacht'] = True
            if kan_aanmelden:
                context['uitleg_geslacht'] = False

        context['menu_toon_mandje'] = True

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Kalender:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Inschrijven sporter')
        )

        menu_dynamics(self.request, context, 'kalender')
        return context


class WedstrijdInschrijvenGroepje(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter een groepje inschrijven """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_INSCHRIJVEN_GROEPJE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except KalenderWedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        try:
            lid_nr = self.request.GET['bondsnummer']
            lid_nr = str(lid_nr)[:6]      # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
        except (KeyError, TypeError, ValueError):
            # geen zoekparameter of slechte zoekterm
            lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= lid_nr <= 999999):
                lid_nr = -1

        sporter, voorkeuren, wedstrijdboog_pks = get_sporter_voorkeuren_wedstrijdbogen(lid_nr)

        context['sporter'] = sporter
        context['bogen'] = BoogType.objects.filter(pk__in=wedstrijdboog_pks).order_by('volgorde')

        tups = get_sessies(wedstrijd, sporter, voorkeuren, wedstrijdboog_pks)
        context['sessies'], _, context['leeftijdsklassen'], geslacht = tups

        if context['sporter']:
            kan_aanmelden = False
            for sessie in context['sessies']:
                if sessie.kan_aanmelden:
                    kan_aanmelden = True
                    break
            # for
            context['kan_aanmelden'] = kan_aanmelden

            # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
            # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
            if geslacht == '?':
                context['uitleg_geslacht'] = True
                if kan_aanmelden:
                    context['uitleg_geslacht'] = False

        context['menu_toon_mandje'] = True

        context['url_zoek'] = reverse('Kalender:inschrijven-groepje', kwargs={'wedstrijd_pk': wedstrijd.pk})

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Kalender:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Inschrijven groepje')
        )

        menu_dynamics(self.request, context, 'kalender')
        return context


class WedstrijdInschrijvenFamilie(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf en familie inschrijven """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_INSCHRIJVEN_FAMILIE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except KalenderWedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        context['menu_toon_mandje'] = True

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Kalender:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Wedstrijd details'),
        )

        menu_dynamics(self.request, context, 'kalender')
        return context

# end of file
