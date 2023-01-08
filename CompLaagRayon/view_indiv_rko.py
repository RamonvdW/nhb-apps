# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponse, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (DeelCompetitie, KampioenschapIndivKlasseLimiet,
                               DeelKampioenschap, DEEL_RK,
                               KampioenschapSporterBoog, DEELNAME_JA, DEELNAME_NEE)
from Functie.models import Rollen
from Functie.rol import rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Sporter.models import SporterVoorkeuren
from codecs import BOM_UTF8
import textwrap
import csv


TEMPLATE_COMPRAYON_LIJST_RK = 'complaagrayon/rko-rk-selectie.dtl'


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
        return self.rol_nu == Rollen.ROL_RKO

    @staticmethod
    def _get_regio_status(competitie):
        # deelnemers komen uit de 4 regio's van het rayon
        regio_deelcomps = (DeelCompetitie
                           .objects
                           .filter(competitie=competitie)
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
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (DeelKampioenschap
                        .objects
                        .select_related('competitie',
                                        'nhb_rayon')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_RK))
        except (ValueError, DeelKampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste RKO aan de knoppen zit
        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelkamp.functie:
            raise PermissionDenied()     # niet de juiste RKO

        alles_afgesloten, regio_status = self._get_regio_status(deelkamp.competitie)
        context['regio_status'] = regio_status

        context['deelkamp'] = deelkamp

        comp = deelkamp.competitie
        # TODO: check competitie fase

        if not deelkamp.heeft_deelnemerslijst:
            # situatie 1)
            context['url_uitslagen'] = reverse('CompUitslagen:uitslagen-rayon-indiv-n',
                                               kwargs={'comp_pk': deelkamp.competitie.pk,
                                                       'comp_boog': 'r',
                                                       'rayon_nr': deelkamp.nhb_rayon.rayon_nr})
            deelnemers = list()
        else:
            # situatie 2)
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

            context['url_download'] = reverse('CompLaagRayon:lijst-rk-als-bestand',
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

            deelnemer.url_wijzig = reverse('CompLaagRayon:wijzig-status-rk-deelnemer',
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

        if deelkamp.heeft_deelnemerslijst:
            context['aantal_afgemeld'] = aantal_afgemeld
            context['aantal_onbekend'] = aantal_onbekend
            context['aantal_bevestigd'] = aantal_bevestigd
            context['aantal_attentie'] = aantal_attentie

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'RK selectie')
        )

        menu_dynamics(self.request, context)
        return context


class LijstRkSelectieAlsBestandView(LijstRkSelectieView):

    """ Deze klasse wordt gebruikt om de RK selectie lijst
        te downloaden als csv bestand
    """

    def get(self, request, *args, **kwargs):

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (DeelKampioenschap
                        .objects
                        .select_related('competitie',
                                        'nhb_rayon')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_RK))
        except (ValueError, DeelKampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        if not deelkamp.heeft_deelnemerslijst:
            raise Http404('Geen deelnemerslijst')

        # laat alleen de juiste RKO de lijst ophalen
        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelkamp.functie:
            raise PermissionDenied()     # niet de juiste RKO

        deelnemers = (KampioenschapSporterBoog
                      .objects
                      .select_related('kampioenschap',
                                      'indiv_klasse',
                                      'sporterboog__sporter',
                                      'bij_vereniging')
                      .exclude(deelname=DEELNAME_NEE)
                      .filter(kampioenschap=deelkamp,
                              rank__lte=48)                 # max 48 schutters
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

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rayon%s_alle.csv"' % deelkamp.nhb_rayon.rayon_nr

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings
        writer.writerow(['Rank', 'NHB nummer', 'Naam', 'Vereniging', 'Label', 'Klasse', 'Gemiddelde', 'Notities'])

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

                gem_str = "%.3f" % deelnemer.gemiddelde
                gem_str = gem_str.replace('.', ',')     # nederlands

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
                                 gem_str,
                                 para_notities])
        # for

        return response

# end of file
