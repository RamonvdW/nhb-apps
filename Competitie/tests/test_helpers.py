# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import DEEL_RK
from Competitie.models import Competitie, Kampioenschap
from Competitie.operations import (competities_aanmaken, aanvangsgemiddelden_vaststellen_voor_afstand,
                                   competitie_klassengrenzen_vaststellen)
import datetime


def zet_competitie_fase(comp, fase):
    """ deze helper weet hoe de competitie datums gemanipuleerd moeten worden
        zodat models.Competitie.bepaal_fase() de gevraagde fase terug zal geven
    """

    if fase == 'Z':
        comp.is_afgesloten = True
        comp.save()
        return

    comp.is_afgesloten = False

    if fase == 'S':
        comp.alle_bks_afgesloten = True
        comp.save()
        return

    comp.alle_bks_afgesloten = False

    now = timezone.now()
    vandaag = datetime.date(year=now.year, month=now.month, day=now.day)
    gister = vandaag - datetime.timedelta(days=1)
    morgen = vandaag + datetime.timedelta(days=1)

    if fase >= 'P':
        # BK fases
        comp.alle_rks_afgesloten = True
        if fase == 'P':
            comp.bk_eerste_wedstrijd = morgen
            comp.save()
            return

        comp.bk_eerste_wedstrijd = gister

        if fase == 'Q':
            comp.bk_laatste_wedstrijd = morgen  # vandaag mag ook
            comp.save()
            return

        # fase R of S: vaststellen uitslagen + afsluiten BK
        comp.bk_laatste_wedstrijd = gister
        comp.save()
        return

    comp.alle_rks_afgesloten = False

    if fase >= 'J':
        # RK fases
        comp.alle_regiocompetities_afgesloten = True

        for deelkamp in (Kampioenschap
                         .objects
                         .filter(competitie=comp,
                                 deel=DEEL_RK)):
            deelkamp.heeft_deelnemerslijst = True
            deelkamp.save(update_fields=['heeft_deelnemerslijst'])
        # for

        if fase == 'J':
            comp.klassengrenzen_vastgesteld_rk_bk = False
            comp.datum_klassengrenzen_rk_bk_teams = morgen
            comp.save()
            return

        comp.klassengrenzen_vastgesteld_rk_bk = True

        if fase == 'K':
            comp.rk_eerste_wedstrijd = morgen + datetime.timedelta(days=14)
            comp.save()
            return

        comp.rk_eerste_wedstrijd = gister

        if fase == 'L':
            comp.rk_laatste_wedstrijd = morgen  # vandaag mag ook
            comp.save()
            return

        # fase M of N: vaststellen uitslag in elk rayon + afsluiten RK
        comp.rk_laatste_wedstrijd = gister
        comp.save()
        return

    comp.alle_regiocompetities_afgesloten = False

    # fase A begon toen de competitie werd aangemaakt

    if fase == 'A':
        comp.begin_aanmeldingen = morgen
        comp.klassengrenzen_vastgesteld = False
        comp.save()
        return

    if comp.competitieindivklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar fase %s zonder competitie indiv klassen!" % fase)

    if comp.competitieteamklasse_set.count() == 0:      # pragma: no cover
        raise NotImplementedError("Kan niet naar fase %s zonder competitie team klassen!" % fase)

    comp.klassengrenzen_vastgesteld = True
    comp.begin_aanmeldingen = gister

    if fase == 'B':
        comp.einde_aanmeldingen = morgen
        comp.save()
        return

    comp.einde_aanmeldingen = gister

    if fase == 'C':
        comp.einde_teamvorming = morgen     # vandaag mag ook
        comp.save()
        return

    comp.einde_teamvorming = gister

    if fase == 'D':
        comp.eerste_wedstrijd = morgen
        comp.save()
        return

    comp.eerste_wedstrijd = gister

    if fase == 'E':
        comp.laatst_mogelijke_wedstrijd = morgen
        comp.save()
        return

    comp.laatst_mogelijke_wedstrijd = gister

    if fase == 'G':
        # alle regios afsluiten
        for deelcomp in comp.regiocompetitie_set.filter(is_afgesloten=False):
            deelcomp.is_afgesloten = True
            deelcomp.save(update_fields=['is_afgesloten'])
        comp.save()
        return

    # fase F: vaststellen uitslag in elke regio + afsluiten regiocompetitie
    comp.save()
    return


def maak_competities_en_zet_fase_b(startjaar=None):
    """ Competities 18m en 25m aanmaken, AG vaststellen, klassengrenzen vaststelen, instellen op fase B """

    # dit voorkomt kennis en afhandelen van achtergrondtaken in alle applicatie test suites

    # competitie aanmaken
    competities_aanmaken(startjaar)

    comp_18 = Competitie.objects.get(afstand='18')
    comp_25 = Competitie.objects.get(afstand='25')

    # aanvangsgemiddelden vaststellen
    aanvangsgemiddelden_vaststellen_voor_afstand(18)
    aanvangsgemiddelden_vaststellen_voor_afstand(25)

    # klassengrenzen vaststellen
    competitie_klassengrenzen_vaststellen(comp_18)
    competitie_klassengrenzen_vaststellen(comp_25)

    zet_competitie_fase(comp_18, 'B')
    zet_competitie_fase(comp_25, 'B')

    return comp_18, comp_25


# end of file
