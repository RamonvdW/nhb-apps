# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Deze plugin geeft relevant informatie over de bondscompetities voor gebruik op Mijn pagina.
"""

from django.urls import reverse
from django.utils.formats import localize
from BasisTypen.models import BoogType
from Competitie.definities import INSCHRIJF_METHODE_1, DEEL_RK, DEELNAME_NEE
from Competitie.models import (Competitie,
                               Regiocompetitie, RegiocompetitieSporterBoog,
                               Kampioenschap, KampioenschapSporterBoog)
from Functie.definities import Rollen
from Sporter.models import Sporter
import copy


FASE_PREP = 0
FASE_INSCHRIJVEN = 1
FASE_REGIOWEDSTRIJDEN = 2
# FASE_RK_TEAMS_INSCHRIJVEN = 3
FASE_RK = 4
FASE_BK = 5

FASE2STR = {
    FASE_PREP: "Prep",
    FASE_INSCHRIJVEN: "Inschrijven",
    FASE_REGIOWEDSTRIJDEN: "Regiocompetitie",
    FASE_RK: "Rayonkampioenschappen",
    FASE_BK: "Bondskampioenschappen",
}


def get_sporter_competities(sporter: Sporter,
                            wedstrijdbogen: list,
                            boog_afk2sporterboog: dict):
    """
        wedstrijdbogen: lijst van afkortingen van de bogen waarmee deze sporter wil schieten
        boog_afk2sporterboog: de SporterBoog van dit lid voor elk relevant boogtype

        returns: comps
            lijst_competities = lijst van actieve competities + fase informatie
            lijst_inschrijven = lijst van Regiocompetitie waar de sporter op in kan schrijven

            lijst_regio       = lijst van Regiocompetitie waar de sporter op in kan schrijven
                                heeft:
                                    is_ingeschreven = True/False: al ingeschreven?      # TODO: niet meer nodig?
                                    boog_niet_meer = True/False: boog niet meer gekozen?
                                    boog_beschrijving = boog_dict[afk].beschrijving
                                    url_afmelden = URL om af te melden - gebruik POST
                                    url_aanmelden       # TODO: niet meer nodig?
                                    url_schietmomenten

            lijst_rk          = lijst van KampioenschapSporterBoog RK waar de sporter voor gekwalificeerd is
            lijst_bk          = lijst van KampioenschapSporterBoog BK waar de sporter voor gekwalificeerd is
    """

    # bepaal de competities die we willen tonen
    pk2comp = dict()        # [comp.pk] = Competitie
    lijst_competities = list()
    for comp in (Competitie
                 .objects
                 .exclude(is_afgesloten=True)
                 .prefetch_related('boogtypen')
                 .order_by('begin_jaar',
                           'afstand')):

        comp.bepaal_fase()
        comp.bepaal_openbaar(Rollen.ROL_SPORTER)

        if comp.is_openbaar:
            # fase B of later
            comp.inschrijven = 'De inschrijving is gesloten'
            comp.fase = FASE_PREP

            if comp.rk_indiv_afgesloten and comp.rk_teams_afgesloten:
                comp.fase = FASE_BK
            elif comp.regiocompetitie_is_afgesloten:
                comp.fase = FASE_RK
            else:
                if comp.fase_indiv == 'C':
                    comp.fase = FASE_INSCHRIJVEN
                    comp.inschrijven = 'De inschrijving is open tot %s' % localize(comp.begin_fase_D_indiv)
                elif comp.fase_indiv <= 'F':
                    # tijdens de hele wedstrijden fase kan er aangemeld worden
                    comp.fase = FASE_REGIOWEDSTRIJDEN
                    comp.inschrijven = 'Aanmelden kan nog tot %s' % localize(comp.einde_fase_F)

            comp.fase_str = FASE2STR[comp.fase]

            comp.boog_afk = [boogtype.afkorting for boogtype in comp.boogtypen.all()]

            lijst_competities.append(comp)
            pk2comp[comp.pk] = comp
    # for

    # stel vast welke boogtypen de sporter mee wil schieten (opt-in)
    boog_dict = dict()  # [afkorting] = BoogType()
    for boogtype in BoogType.objects.all():
        boog_dict[boogtype.afkorting] = boogtype
    # for

    # zoek alle inschrijvingen van deze sporter erbij
    inschrijvingen = list(RegiocompetitieSporterBoog
                          .objects
                          .select_related('regiocompetitie',
                                          'sporterboog')
                          .filter(sporterboog__sporter=sporter,
                                  regiocompetitie__competitie__in=lijst_competities)
                          .order_by('regiocompetitie__competitie__afstand'))

    lijst_inschrijven = list()
    lijst_regio = list()

    # zoek regiocompetities in deze regio (typisch zijn er 2 in de regio: 18m en 25m)
    regio = sporter.bij_vereniging.regio
    for deelcomp in (Regiocompetitie
                     .objects
                     .select_related('competitie')
                     .filter(competitie__in=lijst_competities,
                             regio=regio)
                     .order_by('competitie__afstand')):

        comp_pk = deelcomp.competitie.pk
        if comp_pk in pk2comp:
            comp = pk2comp[comp_pk]

            # doorloop elk boogtype waar de sporter informatie/wedstrijden voorkeur voor heeft
            for afk in wedstrijdbogen:
                if afk in comp.boog_afk:
                    obj = copy.copy(deelcomp)

                    obj.boog_afkorting = afk
                    obj.boog_beschrijving = boog_dict[afk].beschrijving
                    obj.boog_niet_meer = False
                    obj.is_ingeschreven = False

                    if obj.is_ingeschreven:
                        # TODO: niet te bereiken
                        lijst_regio.append(obj)
                    else:
                        lijst_inschrijven.append(obj)

                    # zoek uit of de sporter al ingeschreven is
                    inschrijving = None
                    sporterboog = boog_afk2sporterboog[afk]
                    for zoek in inschrijvingen:
                        if zoek.sporterboog == sporterboog and zoek.regiocompetitie == obj:
                            inschrijving = zoek
                            break   # from the for
                    # for

                    if inschrijving:
                        inschrijvingen.remove(inschrijving)     # afgehandeld

                        obj.is_ingeschreven = True
                        obj.afgemeld_voorkeur_rk = not inschrijving.inschrijf_voorkeur_rk_bk

                        if comp.fase == FASE_INSCHRIJVEN:
                            obj.url_afmelden = reverse('CompInschrijven:afmelden',
                                                       kwargs={'deelnemer_pk': inschrijving.pk})

                        if obj.inschrijf_methode == INSCHRIJF_METHODE_1:
                            if comp.fase in (FASE_INSCHRIJVEN, FASE_REGIOWEDSTRIJDEN):
                                obj.url_schietmomenten = reverse('CompLaagRegio:keuze-zeven-wedstrijden',
                                                                 kwargs={'deelnemer_pk': inschrijving.pk})

                    if comp.is_open_voor_inschrijven():
                        # niet ingeschreven?
                        if not obj.is_ingeschreven:
                            obj.url_aanmelden = reverse('CompInschrijven:bevestig-aanmelden',
                                                        kwargs={'sporterboog_pk': sporterboog.pk,
                                                                'deelcomp_pk': obj.pk})
            # for wedstrijdboog
    # for

    # voeg alle inschrijvingen toe waar geen boog meer voor gekozen is,
    # zodat er afgemeld kan worden
    for inschrijving in inschrijvingen:
        afk = inschrijving.sporterboog.boogtype.afkorting
        obj = inschrijving.regiocompetitie

        obj.is_ingeschreven = True
        obj.boog_niet_meer = True
        obj.boog_beschrijving = boog_dict[afk].beschrijving

        comp_pk = obj.competitie.pk
        if comp_pk in pk2comp:
            comp = pk2comp[comp_pk]
            if comp.fase_indiv <= 'C':
                obj.url_afmelden = reverse('CompInschrijven:afmelden',
                                           kwargs={'deelnemer_pk': inschrijving.pk})

            lijst_regio.append(obj)
    # for

    # RK en BK
    lijst_rk = list()
    lijst_bk = list()

    deelnemers = list(KampioenschapSporterBoog
                      .objects
                      .select_related('kampioenschap',
                                      'kampioenschap__competitie',
                                      'kampioenschap__rayon',
                                      'sporterboog')
                      .filter(sporterboog__sporter=sporter,
                              kampioenschap__competitie__in=lijst_competities)
                      .order_by('kampioenschap__competitie__afstand',
                                'sporterboog__boogtype__afkorting'))

    for kamp in (Kampioenschap
                 .objects
                 .filter(competitie__in=lijst_competities)
                 .select_related('competitie')
                 .order_by('competitie__afstand')):

        comp_pk = kamp.competitie.pk
        if comp_pk in pk2comp:
            comp = pk2comp[comp_pk]

            # zoek de deelnemer erbij
            for deelnemer in deelnemers:
                if deelnemer.kampioenschap == kamp:

                    if kamp.deel == DEEL_RK:
                        # RK
                        lijst_rk.append(deelnemer)

                        if deelnemer.deelname != DEELNAME_NEE:
                            boog_afk = deelnemer.sporterboog.boogtype.afkorting
                            deelnemer.url_rk_deelnemers = reverse('CompUitslagen:uitslagen-rk-indiv-n',
                                                                  kwargs={
                                                                      'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                                                      'comp_boog': boog_afk.lower(),
                                                                      'rayon_nr': kamp.rayon.rayon_nr})
                        # TODO: knop aanmelden/afmelden RK
                        # TODO: team

                    else:
                        # BK
                        lijst_bk.append(deelnemer)

                        # TODO: knop aanmelden/afmelden BK
                        # TODO: team
    # for

    return lijst_competities, lijst_inschrijven, lijst_regio, lijst_rk, lijst_bk


# end of file
