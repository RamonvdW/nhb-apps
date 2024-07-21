# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Deze plugin geeft relevant informatie over de bondscompetities voor gebruik op Mijn pagina.
"""

from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from BasisTypen.models import BoogType
from Competitie.definities import INSCHRIJF_METHODE_1, DEEL_RK, DEELNAME_NEE
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieSporterBoog, KampioenschapSporterBoog
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

        returns:
            lijst_competities:
                lijst van actieve competitie
                basis: Competitie
                heeft:
                    fase: een van de FASE_* (zie hierboven)
                    fase_str: Zie hierboven
                    status_str: Beschrijving van de status, specifiek voor de fase

            lijst_kan_inschrijven:
                    lijst van regiocompetitie waar de sporter op in kan schrijven
                    basis: Regiocompetitie()
                    heeft:
                        boog_beschrijving = Tekstuele beschrijving van de boog, zoals "Recurve"
                        url_aanmelden = URL om aan te melden - gebruik POST

            lijst_inschrijvingen:
                    lijst van competities waar de sporter op ingeschreven is
                    basis: RegiocompetitieSporterBoog()
                    heeft:
                        competitie = Competitie
                        competitie.fase
                        competitie.fase_str
                        is_fase_rk = True als de competitie in de RK fase is
                        is_fase_bk = True als de competitie in de BK fase is
                        boog_niet_meer: True = boog niet meer gekozen
                        boog_beschrijving = Tekstuele beschrijving van de boog, zoals "Recurve"
                        url_afmelden = POST URL om af te melden van de regiocompetitie
                        id_afmelden = unieke identificatie string voor gebruik als html "id"
                        is_afgemeld_voor_rk = True als sporter alvast afgemeld is voor RK
                        url_voorkeur_rk = POST URL om voorkeur RK in te stellen tijdens regio fase
                        url_schietmomenten = URL om 7 schietmomenten te kiezen (inschrijfmethode 1)
                        rk_inschrijving: KampioenschapSporterBoog voor RK waar sporter voor gekwalificeerd is
                        url_rk_deelnemers = URL naar pagina met hele RK deelnemers lijst
                        url_status_rk_deelname = URL om deelname RK aan te passen (gebruik POST)
                        id_deelname_rk = unieke identificatie string voor gebruik als html "id"
                        bk_inschrijving: KampioenschapSporterBoog voor BK waar sporter individueel voor gekwalificeerd is
    """

    now = timezone.now().date()

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
        comp.fase = FASE_PREP

        if comp.is_openbaar:
            # fase B of later

            comp.status_str = 'tbd'

            if comp.rk_indiv_afgesloten and comp.rk_teams_afgesloten:
                comp.fase = FASE_BK
            elif comp.regiocompetitie_is_afgesloten:
                comp.fase = FASE_RK
            else:
                comp.status_str = 'De inschrijving is gesloten'

                if comp.fase_indiv == 'C':
                    comp.fase = FASE_INSCHRIJVEN
                    comp.status_str = 'De inschrijving is open tot %s' % localize(comp.begin_fase_D_indiv)
                elif 'C' < comp.fase_indiv <= 'F':
                    # tijdens de hele wedstrijden fase kan er aangemeld worden
                    comp.fase = FASE_REGIOWEDSTRIJDEN
                    if now <= comp.einde_fase_F:
                        comp.status_str = 'Aanmelden kan nog tot %s' % localize(comp.einde_fase_F)

            comp.fase_str = FASE2STR[comp.fase]

            # maak een lijst van boog afkortingen om verderop te matches tegen een SporterBoog
            comp.boog_afkortingen = [boogtype.afkorting for boogtype in comp.boogtypen.all()]

        # als de competitie nog in de prep fase is, dan nog niet tonen
        if comp.fase != FASE_PREP:
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

    lijst_kan_inschrijven = list()
    lijst_inschrijvingen = list()
    sb2inschrijving = dict()        # [sporterboog.pk] = RegiocompetitieSporterBoog

    # zoek regiocompetities in deze regio (typisch zijn er 2 in de regio: 18m en 25m)
    regio = sporter.bij_vereniging.regio
    for deelcomp in (Regiocompetitie
                     .objects
                     .select_related('competitie')
                     .filter(competitie__in=lijst_competities,
                             regio=regio)
                     .order_by('competitie__afstand')):

        comp = pk2comp[deelcomp.competitie.pk]

        # doorloop elk boogtype waar de sporter informatie/wedstrijden voorkeur voor heeft
        for afk in wedstrijdbogen:
            if afk in comp.boog_afkortingen:
                obj = copy.copy(deelcomp)

                obj.boog_afkorting = afk
                obj.boog_beschrijving = boog_dict[afk].beschrijving     # TODO: nodig?
                obj.boog_niet_meer = False

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

                    # maak informatie makkelijk beschikbaar
                    inschrijving.competitie = comp
                    inschrijving.boog_beschrijving = boog_dict[afk].beschrijving

                    lijst_inschrijvingen.append(inschrijving)

                    tup = (sporterboog.pk, comp.pk)
                    sb2inschrijving[tup] = inschrijving

                    if comp.fase == FASE_INSCHRIJVEN:
                        inschrijving.url_afmelden = reverse('CompInschrijven:afmelden',
                                                            kwargs={'deelnemer_pk': inschrijving.pk})
                        inschrijving.id_afmelden = 'bevestig_uitschrijven_%s' % inschrijving.pk

                    if comp.fase in (FASE_INSCHRIJVEN, FASE_REGIOWEDSTRIJDEN):
                        inschrijving.is_afgemeld_voor_rk = not inschrijving.inschrijf_voorkeur_rk_bk
                        inschrijving.url_voorkeur_rk = reverse('CompLaagRegio:voorkeur-rk')

                        if obj.inschrijf_methode == INSCHRIJF_METHODE_1:
                            inschrijving.url_schietmomenten = reverse('CompLaagRegio:keuze-zeven-wedstrijden',
                                                                      kwargs={'deelnemer_pk': inschrijving.pk})

                else:
                    # niet ingeschreven
                    if comp.is_open_voor_inschrijven():
                        lijst_kan_inschrijven.append(obj)
                        obj.url_aanmelden = reverse('CompInschrijven:bevestig-aanmelden',
                                                    kwargs={'sporterboog_pk': sporterboog.pk,
                                                            'deelcomp_pk': obj.pk})

            # for wedstrijdboog
    # for

    # voeg alle inschrijvingen toe waar geen boog meer voor gekozen is,
    # zodat er afgemeld kan worden
    for inschrijving in inschrijvingen:
        afk = inschrijving.sporterboog.boogtype.afkorting

        inschrijving.boog_niet_meer = True
        inschrijving.boog_beschrijving = boog_dict[afk].beschrijving

        comp = pk2comp[inschrijving.regiocompetitie.competitie.pk]
        inschrijving.competitie = comp

        if comp.fase_indiv == 'C':
            inschrijving.url_afmelden = reverse('CompInschrijven:afmelden',
                                                kwargs={'deelnemer_pk': inschrijving.pk})
            inschrijving.id_afmelden = 'bevestig_uitschrijven_%s' % inschrijving.pk

        lijst_inschrijvingen.append(inschrijving)
    # for

    # RK en BK
    for deelnemer in (KampioenschapSporterBoog
                      .objects
                      .select_related('kampioenschap',
                                      'kampioenschap__competitie',
                                      'kampioenschap__rayon',
                                      'sporterboog')
                      .filter(sporterboog__sporter=sporter,
                              kampioenschap__competitie__in=lijst_competities)
                      .order_by('kampioenschap__competitie__afstand',
                                'sporterboog__boogtype__afkorting')):

        try:
            kamp = deelnemer.kampioenschap
            tup = (deelnemer.sporterboog.pk, kamp.competitie.pk)
            inschrijving = sb2inschrijving[tup]
        except KeyError:
            # unexpected
            pass
        else:
            comp = inschrijving.competitie
            if kamp.deel == DEEL_RK:
                # RK
                inschrijving.rk_inschrijving = deelnemer

                if deelnemer.deelname != DEELNAME_NEE:
                    boog_afk = deelnemer.sporterboog.boogtype.afkorting
                    inschrijving.url_rk_deelnemers = reverse('CompUitslagen:uitslagen-rk-indiv-n',
                                                             kwargs={
                                                                 'comp_pk_of_seizoen': comp.maak_seizoen_url(),
                                                                 'comp_boog': boog_afk.lower(),
                                                                 'rayon_nr': kamp.rayon.rayon_nr})

                inschrijving.url_status_rk_deelname = reverse('CompLaagRayon:wijzig-status-rk-deelname')
                inschrijving.id_deelname_rk = 'deelname_rk_%s' % deelnemer.pk

                # TODO: team

            else:
                # BK
                inschrijving.bk_inschrijving = deelnemer

                # TODO: knop aanmelden/afmelden BK
                # TODO: team
    # for

    for inschrijving in lijst_inschrijvingen:
        inschrijving.is_fase_bk = inschrijving.is_fase_rk = inschrijving.is_fase_regio = False

        if inschrijving.competitie.fase == FASE_BK:
            inschrijving.is_fase_bk = True
        elif inschrijving.competitie.fase == FASE_RK:
            inschrijving.is_fase_rk = True
        else:
            inschrijving.is_fase_regio = True
    # for

    return lijst_competities, lijst_kan_inschrijven, lijst_inschrijvingen


# end of file
