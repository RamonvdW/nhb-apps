# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.db.models import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import ORGANISATIE_WA
from Bestel.mandje import mandje_tel_inhoud
from Bestel.mutaties import bestel_mutatieverzoek_inschrijven_wedstrijd
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Sporter.models import Sporter, SporterBoog, get_sporter_voorkeuren
from Wedstrijden.models import (Wedstrijd, WedstrijdSessie, WedstrijdInschrijving,
                                INSCHRIJVING_STATUS_AFGEMELD, INSCHRIJVING_STATUS_DEFINITIEF,
                                INSCHRIJVING_STATUS_TO_STR,
                                WEDSTRIJD_ORGANISATIE_TO_STR, WEDSTRIJD_BEGRENZING_TO_STR, WEDSTRIJD_WA_STATUS_TO_STR)
from Kalender.view_maand import MAAND2URL


TEMPLATE_WEDSTRIJDEN_WEDSTRIJD_DETAILS = 'wedstrijden/wedstrijd-details.dtl'
TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_SPORTER = 'wedstrijden/inschrijven-sporter.dtl'
TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_GROEPJE = 'wedstrijden/inschrijven-groepje.dtl'
TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_FAMILIE = 'wedstrijden/inschrijven-familie.dtl'
TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_HANDMATIG = 'wedstrijden/inschrijven-handmatig.dtl'


class WedstrijdInfoView(TemplateView):

    """ Via deze view krijgen gebruikers en sporters de wedstrijdkalender te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_WEDSTRIJD_DETAILS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        wedstrijd.organisatie_str = WEDSTRIJD_ORGANISATIE_TO_STR[wedstrijd.organisatie]

        wedstrijd.begrenzing_str = WEDSTRIJD_BEGRENZING_TO_STR[wedstrijd.begrenzing]

        if wedstrijd.organisatie == ORGANISATIE_WA:
            context['toon_wa_status'] = True
            wedstrijd.wa_status_str = WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]

        sessie_pks = list(wedstrijd.sessies.values_list('pk', flat=True))
        context['sessies'] = sessies = (WedstrijdSessie
                                        .objects
                                        .filter(pk__in=sessie_pks)
                                        .prefetch_related('wedstrijdklassen')
                                        .order_by('datum',
                                                  'tijd_begin',
                                                  'pk'))

        for sessie in sessies:
            sessie.aantal_beschikbaar = sessie.max_sporters - sessie.aantal_inschrijvingen
            sessie.klassen = sessie.wedstrijdklassen.all()
        # for

        # om aan te melden is een account nodig
        context['kan_aanmelden'] = self.request.user.is_authenticated

        # inschrijven kan alleen op een wedstrijd in de toekomst
        context['kan_inschrijven'] = wedstrijd.datum_begin > timezone.now().date()

        if context['kan_aanmelden']:
            context['menu_toon_mandje'] = True

            if context['kan_inschrijven']:
                context['url_inschrijven_sporter'] = reverse('Wedstrijden:inschrijven-sporter',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})
                context['url_inschrijven_groepje'] = reverse('Wedstrijden:inschrijven-groepje',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})
                context['url_inschrijven_familie'] = reverse('Wedstrijden:inschrijven-familie',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})
        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (None, 'Wedstrijd details'),
        )

        menu_dynamics(self.request, context)
        return context


def get_sessies(wedstrijd, sporter, voorkeuren, wedstrijdboog_pk):
    """ geef de mogelijke sessies terug waarop de sporter zich in kan schrijven

        Input: wedstrijd:        de wedstrijd waar het om gaat (verplicht)
               sporter:          de sporter waar het om gaat (optioneel; mag None zijn)
               voorkeuren:       de voorkeuren van de sporter (optioneel; mag None zijn)
               wedstrijdboog_pk  het boogtype waar het om gaat (optioneel; mag -1 zijn)

        Output: sessies (qset), wedstrijdleeftijd, wedstrijdklassen (list), wedstrijd_geslacht

                wedstrijdleeftijd is None als deze niet bepaald kon worden
                wedstrijd_geslacht is '?' als deze niet bepaald kon worden
    """

    wedstrijdleeftijd = sporter.bereken_wedstrijdleeftijd(wedstrijd.datum_begin, wedstrijd.organisatie)

    wedstrijd_geslacht = '?'
    if voorkeuren.wedstrijd_geslacht_gekozen:
        wedstrijd_geslacht = voorkeuren.wedstrijd_geslacht

    sessie_pks = list(wedstrijd.sessies.values_list('pk', flat=True))
    sessies = (WedstrijdSessie
               .objects
               .filter(pk__in=sessie_pks)
               .prefetch_related('wedstrijdklassen')
               .order_by('datum',
                         'tijd_begin',
                         'pk'))

    # kijk of de sporter al ingeschreven is
    sessie_pk2inschrijving = dict()       # [sessie.pk] = inschrijving
    for inschrijving in (WedstrijdInschrijving
                         .objects
                         .select_related('sessie',
                                         'sporterboog',
                                         'sporterboog__sporter')
                         .filter(sessie__pk__in=sessie_pks,
                                 sporterboog__sporter=sporter)
                         .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)):

        sessie_pk = inschrijving.sessie.pk
        sessie_pk2inschrijving[sessie_pk] = inschrijving
    # for

    wedstrijdklassen = list()
    for sessie in sessies:
        sessie.aantal_beschikbaar = sessie.max_sporters - sessie.aantal_inschrijvingen
        sessie.klassen = sessie.wedstrijdklassen.select_related('leeftijdsklasse', 'boogtype').all()

        sessie.kan_aanmelden = False

        compatible_boog = False
        compatible_geslacht = False
        compatible_leeftijd = False

        for klasse in sessie.klassen:
            lkl = klasse.leeftijdsklasse

            klasse_compat_boog = klasse_compat_geslacht = klasse_compat_leeftijd = False

            if klasse.boogtype.pk == wedstrijdboog_pk:
                compatible_boog = klasse_compat_boog = True
                sessie.boogtype_pk = klasse.boogtype.id

            # check geslacht is compatible
            if lkl.geslacht_is_compatible(wedstrijd_geslacht):
                compatible_geslacht = klasse_compat_geslacht = True

            # check leeftijd is compatible
            if lkl.leeftijd_is_compatible(wedstrijdleeftijd):
                compatible_leeftijd = klasse_compat_leeftijd = True

                # verzamel een lijstje van compatibele wedstrijdklassen om te tonen
                if lkl.beschrijving not in wedstrijdklassen:
                    if lkl.geslacht_is_compatible(wedstrijd_geslacht):
                        wedstrijdklassen.append(lkl.beschrijving)

            if klasse_compat_boog and klasse_compat_geslacht and klasse_compat_leeftijd:
                klasse.is_compat = True
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

        sessie.prijs_euro_sporter = wedstrijd.bepaal_prijs_voor_sporter(sporter)
    # for

    return sessies, wedstrijdleeftijd, wedstrijdklassen, wedstrijd_geslacht


class WedstrijdInschrijvenSporter(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf inschrijven voor een wedstrijd """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_SPORTER
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
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        wedstrijd_boogtype_pks = list(wedstrijd.boogtypen.all().values_list('pk', flat=True))

        account = self.request.user
        try:
            lid_nr = int(account.username)
        except ValueError:
            raise Http404('Bondsnummer ontbreekt')

        try:
            boog_afk = str(kwargs['boog_afk'])[:3]              # afkappen voor de veiligheid
            boog_afk = boog_afk.lower()
        except KeyError:
            # val terug op "geen keuze"
            boog_afk = ''

        context['sportersboog'] = list(SporterBoog
                                       .objects
                                       .filter(sporter__lid_nr=lid_nr,
                                               voor_wedstrijd=True,
                                               boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                       .select_related('sporter',
                                                       'sporter__bij_vereniging',
                                                       'boogtype')
                                       .order_by('boogtype__volgorde'))

        geselecteerd = None
        for sporterboog in context['sportersboog']:
            sporterboog.is_geselecteerd = False

            sporterboog.url_selecteer = reverse('Wedstrijden:inschrijven-sporter-boog',
                                                kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                        'boog_afk': sporterboog.boogtype.afkorting.lower()})

            if boog_afk == sporterboog.boogtype.afkorting.lower():
                geselecteerd = sporterboog
        # for

        if not geselecteerd and len(context['sportersboog']) > 0:
            geselecteerd = context['sportersboog'][0]

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wissel knop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            voorkeuren = get_sporter_voorkeuren(geselecteerd.sporter)
            tups = get_sessies(wedstrijd, geselecteerd.sporter, voorkeuren, geselecteerd.boogtype.pk)
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

            context['prijs_euro_sporter'] = wedstrijd.bepaal_prijs_voor_sporter(geselecteerd.sporter)

        context['menu_toon_mandje'] = True

        context['url_toevoegen'] = reverse('Wedstrijden:inschrijven-toevoegen-aan-mandje')

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Inschrijven sporter')
        )

        menu_dynamics(self.request, context)
        return context


class WedstrijdInschrijvenGroepje(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter een groepje inschrijven """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_GROEPJE
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
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        wedstrijd_boogtype_pks = list(wedstrijd.boogtypen.all().values_list('pk', flat=True))

        try:
            lid_nr = str(kwargs['lid_nr'])[:6]                  # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
        except (KeyError, TypeError, ValueError):
            # val terug op de ingelogde gebruiker
            lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= lid_nr <= 999999):
                # val terug op de ingelogde gebruiker
                lid_nr = -1

        try:
            boog_afk = str(kwargs['boog_afk'])[:3]              # afkappen voor de veiligheid
            boog_afk = boog_afk.lower()
        except KeyError:
            # val terug op "geen keuze"
            boog_afk = ''

        try:
            zoek_lid_nr = self.request.GET['bondsnummer']
            zoek_lid_nr = str(zoek_lid_nr)[:6]      # afkappen voor de veiligheid
            zoek_lid_nr = int(zoek_lid_nr)
        except (KeyError, TypeError, ValueError):
            # geen zoekparameter of slechte zoekterm
            zoek_lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= zoek_lid_nr <= 999999):
                zoek_lid_nr = -1

        if zoek_lid_nr != -1:
            context['sportersboog'] = list(SporterBoog
                                           .objects
                                           .filter(sporter__lid_nr=zoek_lid_nr,
                                                   voor_wedstrijd=True,
                                                   boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                           .select_related('sporter',
                                                           'sporter__bij_vereniging',
                                                           'boogtype')
                                           .order_by('boogtype__volgorde'))
        elif lid_nr != -1:
            context['sportersboog'] = list(SporterBoog
                                           .objects
                                           .filter(sporter__lid_nr=lid_nr,
                                                   voor_wedstrijd=True,
                                                   boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                           .select_related('sporter',
                                                           'sporter__bij_vereniging',
                                                           'boogtype')
                                           .order_by('boogtype__volgorde'))
        else:
            # toon alleen het zoekveld
            context['sportersboog'] = list()

        geselecteerd = None
        for sporterboog in context['sportersboog']:
            sporterboog.is_geselecteerd = False

            sporterboog.url_selecteer = reverse('Wedstrijden:inschrijven-groepje-lid-boog',
                                                kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                        'lid_nr': sporterboog.sporter.lid_nr,
                                                        'boog_afk': sporterboog.boogtype.afkorting.lower()})

            if boog_afk == sporterboog.boogtype.afkorting.lower():
                geselecteerd = sporterboog
        # for

        if not geselecteerd and len(context['sportersboog']) > 0:
            geselecteerd = context['sportersboog'][0]

        if len(context['sportersboog']) > 1:
            context['toon_sportersboog'] = True

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wissel knop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            voorkeuren = get_sporter_voorkeuren(geselecteerd.sporter)
            tups = get_sessies(wedstrijd, geselecteerd.sporter, voorkeuren, geselecteerd.boogtype.pk)
            context['sessies'], context['leeftijd'], context['leeftijdsklassen'], geslacht = tups

            # kijk of deze sporter al ingeschreven is
            sessie_pk2inschrijving = dict()
            for inschrijving in (WedstrijdInschrijving
                                 .objects
                                 .filter(wedstrijd=wedstrijd,
                                         sporterboog__sporter=geselecteerd.sporter)
                                 .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)
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
                    inschrijving.status_str = INSCHRIJVING_STATUS_TO_STR[inschrijving.status]
            # for
            context['kan_aanmelden'] = kan_aanmelden
            context['al_ingeschreven'] = al_ingeschreven

            # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
            # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
            if geslacht == '?':
                context['uitleg_geslacht'] = True
                if kan_aanmelden:
                    context['uitleg_geslacht'] = False

            context['prijs_euro_sporter'] = wedstrijd.bepaal_prijs_voor_sporter(geselecteerd.sporter)

        context['menu_toon_mandje'] = True

        context['url_toevoegen'] = reverse('Wedstrijden:inschrijven-toevoegen-aan-mandje')

        context['url_zoek'] = reverse('Wedstrijden:inschrijven-groepje', kwargs={'wedstrijd_pk': wedstrijd.pk})

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Inschrijven groepje')
        )

        menu_dynamics(self.request, context)
        return context


class WedstrijdInschrijvenFamilie(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf en familie inschrijven """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_FAMILIE
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
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        wedstrijd_boogtype_pks = list(wedstrijd.boogtypen.all().values_list('pk', flat=True))

        # begrens de mogelijkheden tot leden met dezelfde adres_code als de ingelogde gebruiker
        account = self.request.user
        sporter = Sporter.objects.get(account=account)
        adres_code = sporter.adres_code

        # fall-back als dit de geselecteerde sporter is
        context['sporter'] = sporter

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

        try:
            boog_afk = str(kwargs['boog_afk'])[:3]              # afkappen voor de veiligheid
            boog_afk = boog_afk.lower()
        except KeyError:
            # val terug op "geen keuze"
            boog_afk = ''

        context['familie'] = list(SporterBoog
                                  .objects
                                  .filter(sporter__adres_code=adres_code,
                                          voor_wedstrijd=True,
                                          boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                  .select_related('sporter',
                                                  'sporter__bij_vereniging',
                                                  'boogtype')
                                  .order_by('sporter__sinds_datum',
                                            'sporter__lid_nr',
                                            'boogtype__volgorde')[:50])

        sporter_pks = list()
        geselecteerd = None
        for sporterboog in context['familie']:
            sporterboog.is_geselecteerd = False

            sporterboog.url_selecteer = reverse('Wedstrijden:inschrijven-familie-lid-boog',
                                                kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                        'lid_nr': sporterboog.sporter.lid_nr,
                                                        'boog_afk': sporterboog.boogtype.afkorting.lower()})

            if sporterboog.sporter.pk not in sporter_pks:
                sporter_pks.append(sporterboog.sporter.pk)

            if sporterboog.sporter.lid_nr == lid_nr:
                if boog_afk == sporterboog.boogtype.afkorting.lower():
                    geselecteerd = sporterboog
        # for

        if not geselecteerd and len(context['familie']) > 0:
            geselecteerd = context['familie'][0]

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wissel knop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            voorkeuren = get_sporter_voorkeuren(geselecteerd.sporter)
            tups = get_sessies(wedstrijd, geselecteerd.sporter, voorkeuren, geselecteerd.boogtype.pk)
            context['sessies'], _, context['leeftijdsklassen'], geslacht = tups

            # kijk of deze sporter al ingeschreven is, want maximaal aanmelden met 1 boog
            sessie_pk2inschrijving = dict()
            for inschrijving in (WedstrijdInschrijving
                                 .objects
                                 .filter(wedstrijd=wedstrijd,
                                         sporterboog__sporter=geselecteerd.sporter)
                                 .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)
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
                    inschrijving.status_str = INSCHRIJVING_STATUS_TO_STR[inschrijving.status]
            # for
            context['al_ingeschreven'] = al_ingeschreven

            # toon ook de sessie als de sporter geen compatibele boog heeft
            context['kan_aanmelden'] = not al_ingeschreven  # kan_aanmelden

            # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
            # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
            if geslacht == '?':
                context['uitleg_geslacht'] = True
                if kan_aanmelden:
                    context['uitleg_geslacht'] = False

            context['prijs_euro_sporter'] = wedstrijd.bepaal_prijs_voor_sporter(geselecteerd.sporter)
        else:
            # sporter heeft geen boog voorkeur, dus mag waarschijnlijk niet schieten
            # context['sporter'] is al ingevuld (nodig in de template)
            pass

        # voeg niet-schietende sporters toe aan de lijst
        for sporter in (Sporter
                        .objects
                        .filter(adres_code=adres_code)
                        .order_by('sinds_datum',
                                  'lid_nr'))[:10]:
            if sporter.pk not in sporter_pks:
                dummy = SporterBoog(sporter=sporter)
                dummy.geen_boog = True
                dummy.is_geselecteerd = False
                context['familie'].append(dummy)
        # for

        context['menu_toon_mandje'] = True

        context['url_toevoegen'] = reverse('Wedstrijden:inschrijven-toevoegen-aan-mandje')

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Wedstrijd details'),
        )

        menu_dynamics(self.request, context)
        return context


class WedstrijdInschrijvenHandmatig(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL een sporter inschrijven """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_HANDMATIG
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

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

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.nhb_ver.ver_nr:
            raise PermissionDenied('Wedstrijd van andere vereniging')

        wedstrijd_boogtype_pks = list(wedstrijd.boogtypen.all().values_list('pk', flat=True))

        try:
            lid_nr = str(kwargs['lid_nr'])[:6]                  # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
        except (KeyError, TypeError, ValueError):
            # val terug op de ingelogde gebruiker
            lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= lid_nr <= 999999):
                # val terug op de ingelogde gebruiker
                lid_nr = -1

        try:
            boog_afk = str(kwargs['boog_afk'])[:3]              # afkappen voor de veiligheid
            boog_afk = boog_afk.lower()
        except KeyError:
            # val terug op "geen keuze"
            boog_afk = ''

        try:
            zoek_lid_nr = self.request.GET['bondsnummer']
            zoek_lid_nr = str(zoek_lid_nr)[:6]                  # afkappen voor de veiligheid
            zoek_lid_nr = int(zoek_lid_nr)
        except (KeyError, TypeError, ValueError):
            # geen zoekparameter of slechte zoekterm
            zoek_lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= zoek_lid_nr <= 999999):
                zoek_lid_nr = -1

        if zoek_lid_nr != -1:
            context['sportersboog'] = list(SporterBoog
                                           .objects
                                           .filter(sporter__lid_nr=zoek_lid_nr,
                                                   voor_wedstrijd=True,
                                                   boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                           .select_related('sporter',
                                                           'sporter__bij_vereniging',
                                                           'boogtype')
                                           .order_by('boogtype__volgorde'))
        elif lid_nr != -1:
            context['sportersboog'] = list(SporterBoog
                                           .objects
                                           .filter(sporter__lid_nr=lid_nr,
                                                   voor_wedstrijd=True,
                                                   boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                           .select_related('sporter',
                                                           'sporter__bij_vereniging',
                                                           'boogtype')
                                           .order_by('boogtype__volgorde'))
        else:
            # toon alleen het zoekveld
            context['sportersboog'] = list()

        geselecteerd = None
        for sporterboog in context['sportersboog']:
            sporterboog.is_geselecteerd = False

            sporterboog.url_selecteer = reverse('Wedstrijden:inschrijven-handmatig-lid-boog',
                                                kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                        'lid_nr': sporterboog.sporter.lid_nr,
                                                        'boog_afk': sporterboog.boogtype.afkorting.lower()})
            if boog_afk == sporterboog.boogtype.afkorting.lower():
                geselecteerd = sporterboog
        # for

        if not geselecteerd and len(context['sportersboog']) > 0:
            geselecteerd = context['sportersboog'][0]

        if len(context['sportersboog']) > 1:
            context['toon_sportersboog'] = True

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wissel knop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            voorkeuren = get_sporter_voorkeuren(geselecteerd.sporter)
            tups = get_sessies(wedstrijd, geselecteerd.sporter, voorkeuren, geselecteerd.boogtype.pk)
            context['sessies'], context['leeftijd'], context['leeftijdsklassen'], geslacht = tups

            # kijk of deze sporter al ingeschreven is
            sessie_pk2inschrijving = dict()
            for inschrijving in (WedstrijdInschrijving
                                 .objects
                                 .filter(wedstrijd=wedstrijd,
                                         sporterboog__sporter=geselecteerd.sporter)
                                 .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)
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
                    inschrijving.status_str = INSCHRIJVING_STATUS_TO_STR[inschrijving.status]
            # for
            context['kan_aanmelden'] = kan_aanmelden
            context['al_ingeschreven'] = al_ingeschreven

            # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
            # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
            if geslacht == '?':
                context['uitleg_geslacht'] = True
                if kan_aanmelden:
                    context['uitleg_geslacht'] = False

            context['prijs_euro_sporter'] = wedstrijd.bepaal_prijs_voor_sporter(geselecteerd.sporter)

        context['url_zoek'] = reverse('Wedstrijden:inschrijven-handmatig',
                                      kwargs={'wedstrijd_pk': wedstrijd.pk})

        context['url_toevoegen'] = context['url_zoek']

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (reverse('Wedstrijden:aanmeldingen', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Aanmeldingen'),
            (None, 'Handmatig toevoegen'),
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):

        try:

            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.nhb_ver.ver_nr:
            raise PermissionDenied('Wedstrijd van andere vereniging')

        sporterboog_str = request.POST.get('sporterboog', '')[:6]   # afkappen voor de veiligheid
        sessie_str = request.POST.get('sessie', '')[:6]             # afkappen voor de veiligheid

        try:
            sporterboog_pk = int(sporterboog_str)
            sessie_pk = int(sessie_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek')

        try:
            sessie = wedstrijd.sessies.get(pk=sessie_pk)
            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter')
                           .get(pk=sporterboog_pk))
        except ObjectDoesNotExist:
            raise Http404('Onderdeel van verzoek niet gevonden')

        # TODO: check wedstrijd geslacht gekozen

        account_koper = request.user

        now = timezone.now()

        # misschien dat de sporter al ingeschreven staat, maar afgemeld is
        # verwijder deze inschrijving omdat het nu een andere koper kan zijn
        # TODO: afmeldingen verplaatsen naar een andere tabel
        qset = (WedstrijdInschrijving
                .objects
                .filter(wedstrijd=wedstrijd,
                        sporterboog=sporterboog,
                        status=INSCHRIJVING_STATUS_AFGEMELD))
        if qset.count() > 0:
            qset.delete()

        # maak de inschrijving aan en voorkom dubbelen
        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=sporterboog,
                            koper=account_koper,
                            status=INSCHRIJVING_STATUS_DEFINITIEF)

        try:
            with transaction.atomic():
                inschrijving.save()
        except IntegrityError:          # pragma: no cover
            # er is niet voldaan aan de uniqueness constraint (sessie, sporterboog)
            # ga uit van user-error (dubbelklik op knop) en skip de rest gewoon
            pass
        else:
            # zet dit verzoek door naar de achtergrondtaak
            snel = str(request.POST.get('snel', ''))[:1]
            bestel_mutatieverzoek_inschrijven_wedstrijd(account_koper, inschrijving, snel == '1')

        url = reverse('Wedstrijden:aanmeldingen', kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(url)


class ToevoegenAanMandjeView(UserPassesTestMixin, View):

    # TODO: verplaats naar Bestel

    """ Met deze view wordt het toevoegen van een wedstrijd aan het mandje van de koper afgehandeld """

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
        wedstrijd_str = request.POST.get('wedstrijd', '')[:6]       # afkappen voor de veiligheid
        sporterboog_str = request.POST.get('sporterboog', '')[:6]   # afkappen voor de veiligheid
        sessie_str = request.POST.get('sessie', '')[:6]             # afkappen voor de veiligheid
        goto_str = request.POST.get('goto', '')[:6]                 # afkappen voor de veiligheid

        try:
            wedstrijd_pk = int(wedstrijd_str)
            sporterboog_pk = int(sporterboog_str)
            sessie_pk = int(sessie_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek')

        try:
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
            sessie = WedstrijdSessie.objects.get(pk=sessie_pk)
            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter')
                           .get(pk=sporterboog_pk))
        except ObjectDoesNotExist:
            raise Http404('Onderdeel van verzoek niet gevonden')

        account_koper = request.user

        now = timezone.now()

        # misschien dat de sporter al ingeschreven staat, maar afgemeld is
        # verwijder deze inschrijving omdat het nu een andere koper kan zijn
        # TODO: afmeldingen verplaatsen naar een andere tabel
        qset = (WedstrijdInschrijving
                .objects
                .filter(wedstrijd=wedstrijd,
                        sporterboog=sporterboog,
                        status=INSCHRIJVING_STATUS_AFGEMELD))
        if qset.count() > 0:
            qset.delete()

        # maak de inschrijving aan en voorkom dubbelen
        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=sporterboog,
                            koper=account_koper)

        try:
            with transaction.atomic():
                inschrijving.save()
        except IntegrityError:          # pragma: no cover
            # er is niet voldaan aan de uniqueness constraint (sessie, sporterboog)
            # ga uit van user-error (dubbelklik op knop) en skip de rest gewoon
            pass
        else:
            # zet dit verzoek door naar de achtergrondtaak
            snel = str(request.POST.get('snel', ''))[:1]
            bestel_mutatieverzoek_inschrijven_wedstrijd(account_koper, inschrijving, snel == '1')

            mandje_tel_inhoud(self.request)

        if goto_str == 'F':
            # ga terug naar de familie pagina met dezelfde sporter geselecteerd
            url = reverse('Wedstrijden:inschrijven-familie-lid-boog',
                          kwargs={'wedstrijd_pk': wedstrijd.pk,
                                  'lid_nr': sporterboog.sporter.lid_nr,
                                  'boog_afk': sporterboog.boogtype.afkorting.lower()})
        else:
            url = reverse('Wedstrijden:wedstrijd-info', kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(url)

# end of file