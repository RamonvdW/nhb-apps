# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import ObjectDoesNotExist
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import BoogType
from Functie.rol import Rollen, rol_get_huidige
from Mandje.mandje import mandje_is_gewijzigd
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
from Sporter.models import Sporter, SporterBoog, get_sporter_voorkeuren_wedstrijdbogen
from .models import (KalenderWedstrijd, KalenderWedstrijdSessie, KalenderInschrijving,
                     KalenderMutatie, KALENDER_MUTATIE_INSCHRIJVEN)
from Kalender.view_maand import MAAND2URL
import time


TEMPLATE_KALENDER_INSCHRIJVEN_SPORTER = 'kalender/inschrijven-sporter.dtl'
TEMPLATE_KALENDER_INSCHRIJVEN_GROEPJE = 'kalender/inschrijven-groepje.dtl'
TEMPLATE_KALENDER_INSCHRIJVEN_FAMILIE = 'kalender/inschrijven-familie.dtl'

kalender_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__KALENDER_MUTATIES)


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

    # kijk of de sporter al ingeschreven is
    sessie_pk2inschrijving = dict()       # [sessie.pk] = inschrijving
    if sporter:
        for inschrijving in (KalenderInschrijving
                             .objects
                             .select_related('sessie',
                                             'sporterboog',
                                             'sporterboog__sporter')
                             .filter(sessie__pk__in=sessie_pks,
                                     sporterboog__sporter=sporter)):

            sessie_pk = inschrijving.sessie.pk
            sessie_pk2inschrijving[sessie_pk] = inschrijving
        # for

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
                sessie.boogtype_pk = klasse.boogtype.id

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
            try:
                sessie.inschrijving = sessie_pk2inschrijving[sessie.pk]
            except KeyError:
                # nog niet in geschreven
                sessie.kan_aanmelden = True
            else:
                # al ingeschreven
                sessie.al_ingeschreven = True

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

        context['url_toevoegen'] = reverse('Kalender:inschrijven-toevoegen')

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

            # kijk of deze sporter al ingeschreven is
            sessie_pk2inschrijving = dict()
            for inschrijving in (KalenderInschrijving
                                 .objects.filter(wedstrijd=wedstrijd,
                                                 sporterboog__sporter=sporter)
                                 .select_related('sessie',
                                                 'sporterboog',
                                                 'sporterboog__sporter')):
                sessie_pk2inschrijving[inschrijving.sessie.pk] = inschrijving
            # for

            kan_aanmelden = False
            al_ingeschreven = False
            for sessie in context['sessies']:
                try:
                    inschrijving = sessie_pk2inschrijving[sessie.pk]
                except KeyError:
                    # sporter is nog niet ingeschreven
                    if sessie.kan_aanmelden:
                        kan_aanmelden = True
                else:
                    # sporter is ingeschreven
                    al_ingeschreven = True
                    context['inschrijving'] = inschrijving
            # for
            context['kan_aanmelden'] = kan_aanmelden
            context['al_ingeschreven'] = al_ingeschreven

            # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
            # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
            if geslacht == '?':
                context['uitleg_geslacht'] = True
                if kan_aanmelden:
                    context['uitleg_geslacht'] = False

        context['menu_toon_mandje'] = True

        context['url_toevoegen'] = reverse('Kalender:inschrijven-toevoegen')

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

        account = self.request.user
        sporter = Sporter.objects.get(account=account)
        adres_code = sporter.adres_code

        try:
            lid_nr = str(kwargs['lid_nr'])[:6]                  # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
        except (KeyError, TypeError, ValueError):
            # val terug op de ingelogde gebruiker
            lid_nr = sporter.lid_nr
        else:
            # controleer de range
            if not (100000 <= lid_nr <= 999999):
                # val terug op de ingelogde gebruiker
                lid_nr = sporter.lid_nr

        context['familie'] = (SporterBoog
                              .objects
                              .filter(sporter__adres_code=adres_code,
                                      voor_wedstrijd=True)
                              .select_related('sporter',
                                              'boogtype')
                              .order_by('sporter__sinds_datum'))

        sporter, voorkeuren, wedstrijdboog_pks = None, None, list()
        for sporterboog in context['familie']:
            if sporterboog.sporter.lid_nr == lid_nr:
                sporterboog.is_geselecteerd = True
                sporter, voorkeuren, wedstrijdboog_pks = get_sporter_voorkeuren_wedstrijdbogen(lid_nr)
            else:
                sporterboog.is_geselecteerd = False
                sporterboog.url_selecteer = reverse('Kalender:inschrijven-familie-lid-nr',
                                                    kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                            'lid_nr': sporterboog.sporter.lid_nr})
        # for

        if sporter:
            context['sporter'] = sporter

            context['bogen'] = BoogType.objects.filter(pk__in=wedstrijdboog_pks).order_by('volgorde')

            tups = get_sessies(wedstrijd, sporter, voorkeuren, wedstrijdboog_pks)
            context['sessies'], _, context['leeftijdsklassen'], geslacht = tups

            # kijk of deze sporter al ingeschreven is
            sessie_pk2inschrijving = dict()
            for inschrijving in (KalenderInschrijving
                                 .objects.filter(wedstrijd=wedstrijd,
                                                 sporterboog__sporter=sporter)
                                 .select_related('sessie',
                                                 'sporterboog',
                                                 'sporterboog__sporter')):
                sessie_pk2inschrijving[inschrijving.sessie.pk] = inschrijving
            # for

            kan_aanmelden = False
            al_ingeschreven = False
            for sessie in context['sessies']:
                try:
                    inschrijving = sessie_pk2inschrijving[sessie.pk]
                except KeyError:
                    # sporter is nog niet ingeschreven
                    if sessie.kan_aanmelden:
                        kan_aanmelden = True
                else:
                    # sporter is ingeschreven
                    al_ingeschreven = True
                    context['inschrijving'] = inschrijving
            # for
            context['kan_aanmelden'] = kan_aanmelden
            context['al_ingeschreven'] = al_ingeschreven

            # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
            # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
            if geslacht == '?':
                context['uitleg_geslacht'] = True
                if kan_aanmelden:
                    context['uitleg_geslacht'] = False

        context['menu_toon_mandje'] = True

        context['url_toevoegen'] = reverse('Kalender:inschrijven-toevoegen')

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


class ToevoegenView(UserPassesTestMixin, View):

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):
        wedstrijd_str = request.POST.get('wedstrijd', '')[:6]   # afkappen voor de veiligheid
        sporter_str = request.POST.get('sporter', '')[:6]       # afkappen voor de veiligheid
        sessie_str = request.POST.get('sessie', '')[:6]         # afkappen voor de veiligheid
        boog_str = request.POST.get('boog', '')[:6]             # afkappen voor de veiligheid

        try:
            wedstrijd_pk = int(wedstrijd_str)
            sporter_pk = int(sporter_str)
            sessie_pk = int(sessie_str)
            boog_pk = int(boog_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek')

        try:
            wedstrijd = KalenderWedstrijd.objects.get(pk=wedstrijd_pk)
            sessie = KalenderWedstrijdSessie.objects.get(pk=sessie_pk)
            sporterboog = SporterBoog.objects.get(sporter__pk=sporter_pk, boogtype__pk=boog_pk)
        except ObjectDoesNotExist:
            raise Http404('Onderdeel van verzoek niet gevonden')

        account_koper = request.user

        now = timezone.now()

        # maak de inschrijving aan en voorkom dubbelen
        inschrijving = KalenderInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=sporterboog,
                            koper=account_koper)

        try:
            inschrijving.save()
        except IntegrityError:
            # er is niet voldaan aan de uniqueness constraint (sessie, sporterboog)
            # ga uit van user-error (dubbelklik op knop) en skip de rest gewoon
            pass
        else:
            # zet dit verzoek door naar het mutaties process
            mutatie = KalenderMutatie(
                            code=KALENDER_MUTATIE_INSCHRIJVEN,
                            inschrijving=inschrijving)
            mutatie.save()

            # ping het achtergrond process
            kalender_mutaties_ping.ping()

            snel = str(request.POST.get('snel', ''))[:1]
            if snel != '1':         # pragma: no cover
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = KalenderMutatie.objects.get(pk=mutatie.pk)
                # while

            mandje_is_gewijzigd(self.request)

        url = reverse('Kalender:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(url)

# end of file
