# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import GESLACHT_ALLE
from Competitie.definities import MUTATIE_EXTRA_RK_DEELNEMER, DEEL_RK, DEELNAME_JA, DEELNAME_NEE, KAMP_RANK_BLANCO
from Competitie.models import (Competitie, CompetitieMutatie,
                               RegiocompetitieSporterBoog,
                               Kampioenschap, KampioenschapSporterBoog)
from Competitie.operations import KlasseBepaler
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek
from Site.core.background_sync import BackgroundSync
import time


TEMPLATE_COMPRAYON_EXTRA_DEELNEMER = 'complaagrayon/bko-extra-deelnemer.dtl'
TEMPLATE_COMPRAYON_BLANCO_RESULTAAT = 'complaagrayon/bko-blanco-resultaat.dtl'

competitie_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class ExtraDeelnemerView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO een extra deelnemer toevoegen vanuit de regiocompetitie,
        bijvoorbeeld een aspirant of na correctie score van een sporter (toch nog gekwalificeerd).
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_EXTRA_DEELNEMER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .exclude(is_afgesloten=True)
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu.comp_type != comp.afstand:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste BKO

        # check competitie fase
        comp.bepaal_fase()
        if comp.fase_indiv not in ('J', 'K'):
            raise Http404('Verkeerde fase')

        context['comp'] = comp

        # voorbereiden voor het bepalen van de nieuwe RK wedstrijdklasse
        bepaler = KlasseBepaler(comp)
        bepaler.begrens_to_rk()
        wedstrijdgeslacht = GESLACHT_ALLE       # competitie RK/BK is allemaal gender-neutraal

        # bepaal de SporterBoog die al in het RK zitten
        sb_pks = list(KampioenschapSporterBoog
                      .objects
                      .filter(kampioenschap__competitie=comp)
                      .values_list('sporterboog__pk', flat=True))

        # zoek kandidaten met genoeg scores
        context['kandidaten'] = kandidaten = list()
        prev_klasse = None
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .filter(regiocompetitie__competitie=comp,
                                  aantal_scores__gte=comp.aantal_scores_voor_rk_deelname)
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging',
                                          'sporterboog__sporter__bij_vereniging__regio',
                                          'sporterboog__sporter__bij_vereniging__regio__rayon',
                                          'indiv_klasse')
                          .order_by('indiv_klasse__volgorde',
                                    'sporterboog__sporter__lid_nr')):

            pk = deelnemer.sporterboog.pk
            if pk not in sb_pks:
                if prev_klasse != deelnemer.indiv_klasse:
                    prev_klasse = deelnemer.indiv_klasse
                    deelnemer.break_klasse = True

                sporter = deelnemer.sporterboog.sporter
                deelnemer.lid_nr_naam = sporter.lid_nr_en_volledige_naam()
                deelnemer.competitie_leeftijd = sporter.bereken_wedstrijdleeftijd_wa(comp.begin_jaar + 1)

                ver = sporter.bij_vereniging
                if ver:
                    deelnemer.ver = ver
                    deelnemer.regio_nr = ver.regio.regio_nr
                    deelnemer.rayon_nr = ver.regio.rayon_nr

                    vorige_indiv_klasse = deelnemer.indiv_klasse
                    try:
                        bepaler.bepaal_klasse_deelnemer(deelnemer, wedstrijdgeslacht)
                    except LookupError:
                        # geen klasse gevonden --> kan niet meedoen aan het RK
                        pass
                    else:
                        deelnemer.nieuwe_klasse = deelnemer.indiv_klasse
                        deelnemer.indiv_klasse = vorige_indiv_klasse

                        deelnemer.url = reverse('CompLaagRayon:rayon-extra-deelnemer-toevoegen',
                                                kwargs={'comp_pk': comp.pk, 'deelnemer_pk': deelnemer.pk})
                else:
                    deelnemer.geen_ver = True
                kandidaten.append(deelnemer)
        # for

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Extra deelnemer')
        )

        return context

    def post(self, request, *args, **kwargs):

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .exclude(is_afgesloten=True)
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu.comp_type != comp.afstand:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste BKO

        # check competitie fase
        comp.bepaal_fase()
        if comp.fase_indiv not in ('J', 'K'):
            raise Http404('Verkeerde fase')

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (RegiocompetitieSporterBoog
                         .objects
                         .select_related('sporterboog',
                                         'sporterboog__sporter',
                                         'sporterboog__sporter__bij_vereniging',
                                         'sporterboog__sporter__bij_vereniging__regio',
                                         'sporterboog__sporter__bij_vereniging__regio__rayon',
                                         'indiv_klasse')
                         .get(pk=deelnemer_pk))
        except (KeyError, ValueError, RegiocompetitieSporterBoog.DoesNotExist):
            raise Http404('Sporter niet gevonden')

        sporterboog = deelnemer.sporterboog
        ver = sporterboog.sporter.bij_vereniging
        if not ver:
            raise Http404('Geen vereniging')

        try:
            kampioenschap = (Kampioenschap
                             .objects
                             .get(competitie=comp,
                                  deel=DEEL_RK,
                                  rayon=ver.regio.rayon))
        except Kampioenschap.DoesNotExist:
            raise Http404('Geen RK')

        # bepaal de wedstrijdklasse voor het RK
        bepaler = KlasseBepaler(comp)
        bepaler.begrens_to_rk()
        try:
            bepaler.bepaal_klasse_deelnemer(deelnemer, GESLACHT_ALLE)
        except LookupError:
            # geen klasse gevonden --> kan niet meedoen aan het RK
            raise Http404('Geen klasse')

        scores = [deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4,
                  deelnemer.score5, deelnemer.score6, deelnemer.score7]
        scores.sort(reverse=True)      # beste score eerst
        regio_scores = "%03d%03d%03d%03d%03d%03d%03d" % tuple(scores)

        kampioen, created = KampioenschapSporterBoog.objects.get_or_create(
                                    kampioenschap=kampioenschap,
                                    sporterboog=sporterboog,
                                    indiv_klasse=deelnemer.indiv_klasse,
                                    bij_vereniging=ver,
                                    deelname=DEELNAME_JA,
                                    gemiddelde=deelnemer.gemiddelde,
                                    gemiddelde_scores=regio_scores)
        if created:
            # dit is geen dupe
            account = get_account(request)
            schrijf_in_logboek(account, 'Competitie', 'Extra RK deelnemer %s toevoegen aan %s' % (deelnemer, comp))

            # laat de achtergrondtaak de volgorde bijwerken
            mutatie = CompetitieMutatie(
                            mutatie=MUTATIE_EXTRA_RK_DEELNEMER,
                            deelnemer=kampioen,
                            door="BKO %s" % account.volledige_naam())
            mutatie.save()

            # ping de achtergrondtaak
            competitie_mutaties_ping.ping()

            snel = str(request.POST.get('snel', ''))[:1]
            if snel != '1':         # pragma: no cover
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2  # om steeds te verdubbelen
                total = 0.0  # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval  # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2  # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk})
        return HttpResponseRedirect(url)


class GeefBlancoResultaatView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO een extra deelnemer toevoegen vanuit de regiocompetitie,
        bijvoorbeeld een aspirant of na correctie score van een sporter (toch nog gekwalificeerd).
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_BLANCO_RESULTAAT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .exclude(is_afgesloten=True)
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu.comp_type != comp.afstand:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste BKO

        # check competitie fase
        comp.bepaal_fase()
        if comp.fase_indiv != 'L':
            raise Http404('Verkeerde fase')

        context['comp'] = comp

        # zoek kandidaten zonder resultaat
        context['kandidaten'] = kandidaten = list()
        prev_klasse = None
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie=comp,
                                  result_rank=0)
                          .exclude(deelname=DEELNAME_NEE)
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging',
                                          'sporterboog__sporter__bij_vereniging__regio',
                                          'sporterboog__sporter__bij_vereniging__regio__rayon',
                                          'indiv_klasse')
                          .order_by('kampioenschap__rayon',
                                    'indiv_klasse__volgorde',
                                    'volgorde')):

            if prev_klasse != deelnemer.indiv_klasse:
                prev_klasse = deelnemer.indiv_klasse
                deelnemer.break_klasse = True

            sporter = deelnemer.sporterboog.sporter
            deelnemer.lid_nr_naam = sporter.lid_nr_en_volledige_naam()
            deelnemer.competitie_leeftijd = sporter.bereken_wedstrijdleeftijd_wa(comp.begin_jaar + 1)

            ver = sporter.bij_vereniging
            if ver:
                deelnemer.ver = ver
                deelnemer.regio_nr = ver.regio.regio_nr
                deelnemer.rayon_nr = ver.regio.rayon_nr
                deelnemer.url = reverse('CompLaagRayon:geef-deelnemer-blanco-resultaat',
                                        kwargs={'comp_pk': comp.pk, 'deelnemer_pk': deelnemer.pk})
            else:
                deelnemer.geen_ver = True

            kandidaten.append(deelnemer)
        # for

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Extra deelnemer')
        )

        return context

    def post(self, request, *args, **kwargs):

        try:
            comp_pk = int(kwargs['comp_pk'][:6])  # afkappen voor de veiligheid
            comp = (Competitie
                    .objects
                    .exclude(is_afgesloten=True)
                    .get(pk=comp_pk))
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu.comp_type != comp.afstand:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste BKO

        # check competitie fase
        comp.bepaal_fase()
        if comp.fase_indiv != 'L':
            raise Http404('Verkeerde fase')

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .exclude(deelname=DEELNAME_NEE)
                         .get(pk=deelnemer_pk,
                              result_rank=0))
        except (KeyError, ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        sporterboog = deelnemer.sporterboog
        ver = sporterboog.sporter.bij_vereniging
        if not ver:
            raise Http404('Geen vereniging')

        deelnemer.result_rank = KAMP_RANK_BLANCO
        deelnemer.save(update_fields=['result_rank'])

        account = get_account(request)
        schrijf_in_logboek(account, 'Competitie', 'Blanco score voor RK deelnemer %s van %s' % (deelnemer, comp))

        url = reverse('CompLaagRayon:geef-blanco-resultaat', kwargs={'comp_pk': comp.pk})
        return HttpResponseRedirect(url)

# end of file
