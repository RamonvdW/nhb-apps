# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import (DEEL_BK,
                                   DEELNAME_JA, DEELNAME_NEE,
                                   MUTATIE_KAMP_AFMELDEN_INDIV, MUTATIE_KAMP_AANMELDEN_INDIV)
from Competitie.models import Kampioenschap, KampioenschapSporterBoog, KampioenschapIndivKlasseLimiet, CompetitieMutatie
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Site.core.background_sync import BackgroundSync
from Sporter.models import SporterVoorkeuren
from codecs import BOM_UTF8
import textwrap
import time
import csv


TEMPLATE_COMPBOND_BK_SELECTIE = 'complaagbond/bk-selectie.dtl'
TEMPLATE_COMPBOND_WIJZIG_STATUS_BK_DEELNEMER = 'complaagbond/wijzig-status-bk-deelnemer.dtl'

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class LijstBkSelectieView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de (kandidaat) deelnemers van en BK zien,
        met mogelijkheid voor de BKO om deze te bevestigen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBOND_BK_SELECTIE
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
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise PermissionDenied('Niet de beheerder')

        context['deelkamp'] = deelkamp

        comp = deelkamp.competitie
        comp.bepaal_fase()

        if comp.fase_indiv not in ('N', 'O', 'P'):
            raise Http404('Verkeerde competitie fase')

        # TODO: wel inzichtelijk maar readonly maken tijdens fase P

        deelnemers = (KampioenschapSporterBoog
                      .objects
                      .select_related('kampioenschap',
                                      'indiv_klasse',
                                      'sporterboog',
                                      'sporterboog__sporter',
                                      'bij_vereniging')
                      .filter(kampioenschap=deelkamp,
                              volgorde__lte=48)             # max 48 schutters per klasse tonen
                      .order_by('indiv_klasse__volgorde',   # groepeer per klasse
                                'volgorde',                 # oplopend op volgorde (dubbelen mogelijk)
                                '-gemiddelde'))             # aflopend op gemiddelde

        context['url_download'] = reverse('CompLaagBond:bk-selectie-als-bestand',
                                          kwargs={'deelkamp_pk': deelkamp.pk})

        lid2voorkeuren = dict()  # [lid_nr] = SporterVoorkeuren
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            lid2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
        # for

        wkl2limiet = dict()    # [pk] = aantal
        for limiet in (KampioenschapIndivKlasseLimiet
                       .objects
                       .select_related('indiv_klasse')
                       .filter(kampioenschap=deelkamp)):
            wkl2limiet[limiet.indiv_klasse.pk] = limiet.limiet
        # for

        aantal_afgemeld = 0
        aantal_bevestigd = 0
        aantal_onbekend = 0
        aantal_klassen = 0
        aantal_attentie = 0

        klasse = -1
        limiet = 24
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
            if deelnemer.break_klasse:
                aantal_klassen += 1
                deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving
                klasse = deelnemer.indiv_klasse.volgorde
                try:
                    limiet = wkl2limiet[deelnemer.indiv_klasse.pk]
                except KeyError:
                    limiet = 24

            sporter = deelnemer.sporterboog.sporter
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

            deelnemer.notitie_str = deelnemer.kampioen_label

            if deelnemer.deelname != DEELNAME_NEE:
                para_notities = ''
                try:
                    voorkeuren = lid2voorkeuren[sporter.lid_nr]
                except KeyError:        # pragma: no cover
                    pass
                else:
                    if voorkeuren.para_voorwerpen:
                        para_notities = 'Sporter laat voorwerpen op de schietlijn staan'

                    if voorkeuren.opmerking_para_sporter:
                        if para_notities != '':
                            para_notities += '\n'
                        para_notities += textwrap.fill(voorkeuren.opmerking_para_sporter, 40)

                if para_notities:
                    if deelnemer.notitie_str:
                        deelnemer.notitie_str += '\n'
                    deelnemer.notitie_str += para_notities

            if not deelnemer.bij_vereniging:
                aantal_attentie += 1

            deelnemer.url_wijzig = reverse('CompLaagBond:wijzig-status-bk-deelnemer',
                                           kwargs={'deelnemer_pk': deelnemer.pk})

            if deelnemer.rank > limiet:
                deelnemer.is_reserve = True

            # tel de status van de deelnemers en eerste 8 reserveschutters
            if deelnemer.rank <= limiet+8:
                if deelnemer.deelname == DEELNAME_NEE:
                    aantal_afgemeld += 1
                elif deelnemer.deelname == DEELNAME_JA:
                    aantal_bevestigd += 1
                else:
                    aantal_onbekend += 1
        # for

        context['deelnemers'] = deelnemers
        context['aantal_klassen'] = aantal_klassen

        context['aantal_afgemeld'] = aantal_afgemeld
        context['aantal_onbekend'] = aantal_onbekend
        context['aantal_bevestigd'] = aantal_bevestigd
        context['aantal_attentie'] = aantal_attentie

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'BK selectie')
        )

        return context


class LijstBkSelectieAlsBestandView(LijstBkSelectieView):

    """ Deze klasse wordt gebruikt om de BK selectie lijst
        te downloaden als csv bestand
    """

    def get(self, request, *args, **kwargs):

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # laat alleen de juiste BKO de lijst ophalen
        if self.functie_nu != deelkamp.functie:
            raise PermissionDenied('Niet de beheerder')     # niet de juiste BKO

        if not deelkamp.heeft_deelnemerslijst:
            raise Http404('Geen deelnemerslijst')

        deelnemers = (KampioenschapSporterBoog
                      .objects
                      .select_related('kampioenschap',
                                      'indiv_klasse',
                                      'sporterboog__sporter',
                                      'bij_vereniging')
                      .exclude(deelname=DEELNAME_NEE)
                      .filter(kampioenschap=deelkamp,
                              volgorde__lte=48)             # max 48 schutters
                      .order_by('indiv_klasse__volgorde',   # groepeer per klasse
                                'volgorde',                 # oplopend op volgorde (dubbelen mogelijk)
                                '-gemiddelde'))             # aflopend op gemiddelde

        lid2voorkeuren = dict()  # [lid_nr] = SporterVoorkeuren
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            lid2voorkeuren[voorkeuren.sporter.lid_nr] = voorkeuren
        # for

        wkl2limiet = dict()    # [pk] = aantal
        for limiet in (KampioenschapIndivKlasseLimiet
                       .objects
                       .select_related('indiv_klasse')
                       .filter(kampioenschap=deelkamp)):
            wkl2limiet[limiet.indiv_klasse.pk] = limiet.limiet
        # for

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="bond_alle.csv"'

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings
        writer.writerow(['Rank', 'Bondsnummer', 'Naam', 'Vereniging', 'Label', 'Klasse', 'RK score', 'Notities'])

        if deelkamp.competitie.is_indoor():
            aantal_pijlen = 2 * 30
        else:
            aantal_pijlen = 2 * 25

        for deelnemer in deelnemers:

            try:
                limiet = wkl2limiet[deelnemer.indiv_klasse.pk]
            except KeyError:
                limiet = 24

            # database query was voor 48 schutters
            # voor kleinere klassen moeten we minder reservisten tonen
            if deelnemer.rank <= 2*limiet:
                sporter = deelnemer.sporterboog.sporter
                ver = deelnemer.bij_vereniging
                ver_str = str(ver)

                label = deelnemer.kampioen_label
                if deelnemer.rank > limiet:
                    label = 'Reserve'

                if deelnemer.deelname != DEELNAME_JA:
                    if label != "":
                        label += " "
                    label += "(deelname onzeker)"

                rk_score = round(deelnemer.gemiddelde * aantal_pijlen)

                para_notities = ''

                try:
                    voorkeuren = lid2voorkeuren[sporter.lid_nr]
                except KeyError:  # pragma: no cover
                    pass
                else:
                    if voorkeuren.para_voorwerpen:
                        para_notities = 'Sporter laat voorwerpen op de schietlijn staan\n'

                    if voorkeuren.opmerking_para_sporter:
                        para_notities += voorkeuren.opmerking_para_sporter

                writer.writerow([deelnemer.rank,
                                 sporter.lid_nr,
                                 sporter.volledige_naam(),
                                 ver_str,                  # [nnnn] Naam
                                 label,
                                 deelnemer.indiv_klasse.beschrijving,
                                 rk_score,
                                 para_notities])
        # for

        return response


class WijzigStatusBkDeelnemerView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO de status van een BK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBOND_WIJZIG_STATUS_BK_DEELNEMER
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
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap',
                                         'kampioenschap__functie',
                                         'kampioenschap__competitie',
                                         'sporterboog__sporter',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk,
                              kampioenschap__deel=DEEL_BK))
        except (ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        if self.functie_nu != deelnemer.kampioenschap.functie:
            raise PermissionDenied('Niet de beheerder')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('N', 'O', 'P'):
            raise Http404('Mag nog niet wijzigen')

        sporter = deelnemer.sporterboog.sporter
        deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

        if deelnemer.bij_vereniging:
            deelnemer.ver_str = str(deelnemer.bij_vereniging)
        else:
            deelnemer.ver_str = "?"

        context['deelnemer'] = deelnemer

        context['url_wijzig'] = reverse('CompLaagBond:wijzig-status-bk-deelnemer',
                                        kwargs={'deelnemer_pk': deelnemer.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagBond:bk-selectie',
                     kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk}), 'BK selectie'),
            (None, 'Wijzig sporter status')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruiker op de knop OPSLAAN druk """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap',
                                         'kampioenschap__functie',
                                         'kampioenschap__competitie')
                         .get(pk=deelnemer_pk,
                              kampioenschap__deel=DEEL_BK))
        except (ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        if self.functie_nu != deelnemer.kampioenschap.functie:
            raise PermissionDenied('Niet de beheerder')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('N', 'O', 'P'):
            raise Http404('Mag niet meer wijzigen')

        bevestig = str(request.POST.get('bevestig', ''))[:2]
        afmelden = str(request.POST.get('afmelden', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        account = get_account(request)
        door_str = "BKO %s" % account.volledige_naam()

        if bevestig == "1":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Sporter moet lid zijn bij een vereniging')
            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_AANMELDEN_INDIV,
                                        deelnemer=deelnemer,
                                        door=door_str)
        elif afmelden == "1":
            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_AFMELDEN_INDIV,
                                        deelnemer=deelnemer,
                                        door=door_str)
        else:
            mutatie = None

        if mutatie:
            mutatie.save()
            mutatie_ping.ping()

            if snel != '1':         # pragma: no cover
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        url = reverse('CompLaagBond:bk-selectie',
                      kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk})

        return HttpResponseRedirect(url)


# end of file
