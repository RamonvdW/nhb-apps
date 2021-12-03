# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (LAAG_REGIO, LAAG_RK, DeelCompetitie,
                               DeelcompetitieKlasseLimiet,
                               KampioenschapSchutterBoog, CompetitieMutatie,
                               MUTATIE_AFMELDEN, MUTATIE_AANMELDEN, DEELNAME_JA, DEELNAME_NEE)
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie
from Handleiding.views import reverse_handleiding
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
import time
import csv


TEMPLATE_COMPRAYON_LIJST_RK = 'comprayon/rko-rk-selectie.dtl'
TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_SCHUTTER = 'comprayon/wijzig-status-rk-deelnemer.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class LijstRkSelectieView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de (kandidaat) schutters van en RK zien,
        met mogelijkheid voor de RKO om deze te bevestigen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_LIJST_RK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RKO

    @staticmethod
    def _get_regio_status(competitie):
        # schutter moeten uit LAAG_REGIO gehaald worden, uit de 4 regio's van het rayon
        regio_deelcomps = (DeelCompetitie
                           .objects
                           .filter(laag=LAAG_REGIO,
                                   competitie=competitie)
                           .select_related('nhb_regio',
                                           'nhb_regio__rayon')
                           .order_by('nhb_regio__regio_nr'))

        alles_afgesloten = True
        for obj in regio_deelcomps:
            obj.regio_str = str(obj.nhb_regio.regio_nr)
            obj.rayon_str = str(obj.nhb_regio.rayon.rayon_nr)

            if obj.is_afgesloten:
                obj.status_str = "Afgesloten"
                obj.status_groen = True
            else:
                alles_afgesloten = False
                obj.status_str = "Actief"
        # for

        return alles_afgesloten, regio_deelcomps

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # er zijn 2 situaties:
        # 1) regiocompetities zijn nog niet afgesloten --> verwijst naar pagina tussenstand rayon
        # 2) deelnemers voor RK zijn vastgesteld --> toon lijst

        try:
            rk_deelcomp_pk = int(kwargs['rk_deelcomp_pk'][:6])  # afkappen voor veiligheid
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=rk_deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        # controleer dat de juiste RKO aan de knoppen zit
        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelcomp_rk.functie:
            raise PermissionDenied()     # niet de juiste RKO

        alles_afgesloten, regio_status = self._get_regio_status(deelcomp_rk.competitie)
        context['regio_status'] = regio_status

        context['deelcomp_rk'] = deelcomp_rk

        if not deelcomp_rk.heeft_deelnemerslijst:
            # situatie 1)
            context['url_uitslagen'] = reverse('CompUitslagen:uitslagen-rayon-indiv-n',
                                               kwargs={'comp_pk': deelcomp_rk.competitie.pk,
                                                       'comp_boog': 'r',
                                                       'rayon_nr': deelcomp_rk.nhb_rayon.rayon_nr})
            deelnemers = list()
        else:
            # situatie 2)
            deelnemers = (KampioenschapSchutterBoog
                          .objects
                          .select_related('deelcompetitie',
                                          'klasse__indiv',
                                          'sporterboog__sporter',
                                          'bij_vereniging')
                          .filter(deelcompetitie=deelcomp_rk,
                                  volgorde__lte=48)             # max 48 schutters per klasse tonen
                          .order_by('klasse__indiv__volgorde',  # groepeer per klasse
                                    'volgorde',                 # oplopend op volgorde (dubbelen mogelijk)
                                    '-gemiddelde'))             # aflopend op gemiddelde

            context['url_download'] = reverse('CompRayon:lijst-rk-als-bestand',
                                              kwargs={'rk_deelcomp_pk': deelcomp_rk.pk})

        wkl2limiet = dict()    # [pk] = aantal
        for limiet in (DeelcompetitieKlasseLimiet
                       .objects
                       .select_related('klasse')
                       .filter(deelcompetitie=deelcomp_rk)):
            wkl2limiet[limiet.klasse.pk] = limiet.limiet
        # for

        aantal_afgemeld = 0
        aantal_bevestigd = 0
        aantal_onbekend = 0
        aantal_klassen = 0
        aantal_attentie = 0

        klasse = -1
        limiet = 24
        for deelnemer in deelnemers:
            deelnemer.break_klasse = (klasse != deelnemer.klasse.indiv.volgorde)
            if deelnemer.break_klasse:
                aantal_klassen += 1
                deelnemer.klasse_str = deelnemer.klasse.indiv.beschrijving
                klasse = deelnemer.klasse.indiv.volgorde
                try:
                    limiet = wkl2limiet[deelnemer.klasse.pk]
                except KeyError:
                    limiet = 24

            sporter = deelnemer.sporterboog.sporter
            deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

            if not deelnemer.bij_vereniging:
                aantal_attentie += 1

            deelnemer.url_wijzig = reverse('CompRayon:wijzig-status-rk-deelnemer',
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

        if deelcomp_rk.heeft_deelnemerslijst:
            context['aantal_afgemeld'] = aantal_afgemeld
            context['aantal_onbekend'] = aantal_onbekend
            context['aantal_bevestigd'] = aantal_bevestigd
            context['aantal_attentie'] = aantal_attentie

        context['wiki_rk_schutters'] = reverse_handleiding(self.request, settings.HANDLEIDING_RK_SELECTIE)

        menu_dynamics_competitie(self.request, context, comp_pk=deelcomp_rk.competitie.pk)
        return context


class LijstRkSelectieAlsBestandView(LijstRkSelectieView):

    """ Deze klasse wordt gebruikt om de RK selectie lijst
        te downloaden als csv bestand
    """

    def get(self, request, *args, **kwargs):

        try:
            rk_deelcomp_pk = int(kwargs['rk_deelcomp_pk'][:6])  # afkappen voor veiligheid
            deelcomp_rk = (DeelCompetitie
                           .objects
                           .select_related('competitie', 'nhb_rayon')
                           .get(pk=rk_deelcomp_pk, laag=LAAG_RK))
        except (ValueError, DeelCompetitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        if not deelcomp_rk.heeft_deelnemerslijst:
            raise Http404('Geen deelnemerslijst')

        # laat alleen de juiste RKO de lijst ophalen
        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelcomp_rk.functie:
            raise PermissionDenied()     # niet de juiste RKO

        deelnemers = (KampioenschapSchutterBoog
                      .objects
                      .select_related('deelcompetitie',
                                      'klasse__indiv',
                                      'sporterboog__sporter',
                                      'bij_vereniging')
                      .exclude(deelname=DEELNAME_NEE)
                      .filter(deelcompetitie=deelcomp_rk,
                              rank__lte=48)                 # max 48 schutters
                      .order_by('klasse__indiv__volgorde',  # groepeer per klasse
                                'volgorde',                 # oplopend op volgorde (dubbelen mogelijk)
                                '-gemiddelde'))             # aflopend op gemiddelde

        wkl2limiet = dict()    # [pk] = aantal
        for limiet in (DeelcompetitieKlasseLimiet
                       .objects
                       .select_related('klasse')
                       .filter(deelcompetitie=deelcomp_rk)):
            wkl2limiet[limiet.klasse.pk] = limiet.limiet
        # for

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rayon%s_alle.csv"' % deelcomp_rk.nhb_rayon.rayon_nr

        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings
        writer.writerow(['Rank', 'NHB nummer', 'Naam', 'Vereniging', 'Label', 'Klasse', 'Gemiddelde'])

        for deelnemer in deelnemers:

            try:
                limiet = wkl2limiet[deelnemer.klasse.pk]
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

                writer.writerow([deelnemer.rank,
                                 sporter.lid_nr,
                                 sporter.volledige_naam(),
                                 ver_str,                  # [nnnn] Naam
                                 label,
                                 deelnemer.klasse.indiv.beschrijving,
                                 deelnemer.gemiddelde])
        # for

        return response


class WijzigStatusRkSchutterView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO de status van een RK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_SCHUTTER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_RKO, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor veiligheid
            deelnemer = (KampioenschapSchutterBoog
                         .objects
                         .select_related('deelcompetitie__competitie',
                                         'deelcompetitie__nhb_rayon',
                                         'sporterboog__sporter',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk))
        except (ValueError, KampioenschapSchutterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL and deelnemer.bij_vereniging != self.functie_nu.nhb_ver:
            raise PermissionDenied('Geen sporter van jouw vereniging')

        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelnemer.deelcompetitie.functie:
            raise PermissionDenied('Geen toegang tot deze competitie')

        comp = deelnemer.deelcompetitie.competitie
        comp.bepaal_fase()
        if comp.fase < 'J':
            raise Http404('Mag nog niet wijzigen')

        if comp.fase > 'K':
            raise Http404('Mag niet meer wijzigen')

        sporter = deelnemer.sporterboog.sporter
        deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

        if deelnemer.bij_vereniging:
            deelnemer.ver_str = str(deelnemer.bij_vereniging)
        else:
            deelnemer.ver_str = "?"

        context['deelnemer'] = deelnemer

        context['url_wijzig'] = reverse('CompRayon:wijzig-status-rk-deelnemer',
                                        kwargs={'deelnemer_pk': deelnemer.pk})

        if self.rol_nu == Rollen.ROL_RKO:
            context['url_terug'] = reverse('CompRayon:lijst-rk',
                                           kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk})
        else:
            # HWL
            context['url_terug'] = reverse('CompRayon:lijst-rk-ver',
                                           kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk})

        menu_dynamics_competitie(self.request, context, comp_pk=deelnemer.deelcompetitie.competitie.pk)
        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruik op de knop OPSLAAN druk """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor veiligheid
            deelnemer = (KampioenschapSchutterBoog
                         .objects
                         .select_related('klasse',
                                         'deelcompetitie',
                                         'deelcompetitie__competitie')
                         .get(pk=deelnemer_pk))
        except (ValueError, KampioenschapSchutterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        bevestig = str(request.POST.get('bevestig', ''))[:2]
        afmelden = str(request.POST.get('afmelden', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        if self.rol_nu == Rollen.ROL_HWL and deelnemer.bij_vereniging != self.functie_nu.nhb_ver:
            raise PermissionDenied('Geen sporter van jouw vereniging')

        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelnemer.deelcompetitie.functie:
            raise PermissionDenied('Geen toegang tot deze competitie')

        account = request.user
        door_str = "RKO %s" % account.volledige_naam()

        if bevestig == "1":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Sporter moet lid zijn bij een vereniging')
            mutatie = CompetitieMutatie(mutatie=MUTATIE_AANMELDEN,
                                        deelnemer=deelnemer,
                                        door=door_str)
        elif afmelden == "1":
            mutatie = CompetitieMutatie(mutatie=MUTATIE_AFMELDEN,
                                        deelnemer=deelnemer,
                                        door=door_str)
        else:
            mutatie = None

        if mutatie:
            mutatie.save()
            mutatie_ping.ping()

            if snel != '1':
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        if self.rol_nu == Rollen.ROL_RKO:
            url = reverse('CompRayon:lijst-rk',
                          kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk})
        else:
            url = reverse('CompRayon:lijst-rk-ver',
                          kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk})

        return HttpResponseRedirect(url)


# end of file
