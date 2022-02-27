# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from Competitie.models import (AG_NUL, LAAG_REGIO, LAAG_RK, AFSTANDEN,
                               Competitie, CompetitieKlasse, DeelCompetitie, DeelcompetitieRonde)
from Functie.models import Functie
from NhbStructuur.models import NhbRayon, NhbRegio
from Wedstrijden.models import CompetitieWedstrijdenPlan
from datetime import date
import datetime
import logging

my_logger = logging.getLogger('NHBApps.Competitie')


def competitie_week_nr_to_date(jaar, week_nr):
    # de competitie begin na de zomer
    # dus als het weeknummer voor de zomer valt, dan is het in het volgende jaar
    if week_nr <= 26:
        jaar += 1

    # conversie volgen ISO 8601
    # details: https://docs.python.org/3/library/datetime.html
    # %G = jaar
    # %V = met maandag als eerste dag van de week + week 1 bevat 4 januari
    # %u = dag van de week met 1=maandag
    when = datetime.datetime.strptime("%s-%s-1" % (jaar, week_nr), "%G-%V-%u")
    when2 = datetime.date(year=when.year, month=when.month, day=when.day)
    return when2


def bepaal_volgende_week_nummer(deelcomp, cluster):
    """ bepaalt het nieuwe week nummer, opvolgend op de al gekozen week nummers
        hanteer wrap-around aan het einde van het jaar.

        Retourneert het nieuwe week nummer of None als de limiet van 16 rondes bereikt is.
        De eerste keer wordt week 37 terug gegeven.
    """

    begin_jaar = deelcomp.competitie.begin_jaar

    last_week_in_year = 52
    when_wk53 = competitie_week_nr_to_date(begin_jaar, 53)
    when_wk1 = competitie_week_nr_to_date(begin_jaar, 1)        # doet jaar+1 omdat week_nr <= 26
    if when_wk53 != when_wk1:
        # wk53 does exist
        last_week_in_year = 53

    # zoek de bestaande records
    objs = (DeelcompetitieRonde
            .objects
            .filter(deelcompetitie=deelcomp,
                    cluster=cluster))

    nrs = list()
    for obj in objs:
        nr = obj.week_nr
        # compenseer voor wrap-around aan het einde van het jaar
        # waardoor week 1..26 na week 37..52 moeten komen
        if nr < 26:
            nr += 100
        nrs.append(nr)
    # for

    # maximum bereikt?
    if len(nrs) >= 16:
        nieuwe_week_nr = None
    else:
        if len(nrs) > 0:
            max_nr = max(nrs)
            if max_nr > 100:
                max_nr -= 100
            nieuwe_week_nr = max_nr + 1
            if nieuwe_week_nr > last_week_in_year:
                nieuwe_week_nr = 1
        else:
            nieuwe_week_nr = 37

    return nieuwe_week_nr


def maak_deelcompetitie_ronde(deelcomp, cluster=None):
    """ Maak een nieuwe deelcompetitie ronde object aan
        geef er een uniek week nummer aan.
    """

    nieuwe_week_nr = bepaal_volgende_week_nummer(deelcomp, cluster)

    if nieuwe_week_nr:
        # maak een eigen wedstrijdenplan aan voor deze ronde
        plan = CompetitieWedstrijdenPlan()
        plan.save()

        ronde = DeelcompetitieRonde()
        ronde.deelcompetitie = deelcomp
        ronde.cluster = cluster
        ronde.week_nr = nieuwe_week_nr
        ronde.plan = plan
        ronde.save()
    else:
        # maximum aantal rondes is al aangemaakt
        ronde = None

    return ronde


def _maak_deelcompetities(comp, rayons, regios, functies):

    """ Maak de deelcompetities van een competitie aan """

    # zoek de voorgaande deelcompetities erbij om settings over te kunnen nemen
    vorige_deelcomps = dict()   # [regio_nr] = DeelCompetitie()
    for deelcomp in (DeelCompetitie
                     .objects
                     .select_related('competitie',
                                     'nhb_regio')
                     .filter(laag=LAAG_REGIO,
                             competitie__begin_jaar=comp.begin_jaar - 1,
                             competitie__afstand=comp.afstand)):
        vorige_deelcomps[deelcomp.nhb_regio.regio_nr] = deelcomp
    # for

    # maak wedstrijdplannen aan: voor de 4x LAAG_RK en 1x voor LAAG_BK
    plannen = [CompetitieWedstrijdenPlan(),
               CompetitieWedstrijdenPlan(),
               CompetitieWedstrijdenPlan(),
               CompetitieWedstrijdenPlan(),
               CompetitieWedstrijdenPlan()]
    CompetitieWedstrijdenPlan.objects.bulk_create(plannen)

    # maak de Deelcompetities aan voor Regio, RK, BK
    bulk = list()
    for laag, _ in DeelCompetitie.LAAG:
        if laag == LAAG_REGIO:
            # Regio
            for obj in regios:
                functie = functies[("RCL", comp.afstand, obj.regio_nr)]
                deel = DeelCompetitie(competitie=comp,
                                      laag=laag,
                                      nhb_regio=obj,
                                      functie=functie,
                                      einde_teams_aanmaken=comp.einde_teamvorming)
                try:
                    vorige = vorige_deelcomps[obj.regio_nr]
                except KeyError:
                    pass
                else:
                    deel.inschrijf_methode = vorige.inschrijf_methode
                    deel.toegestane_dagdelen = vorige.toegestane_dagdelen
                    deel.regio_organiseert_teamcompetitie = vorige.regio_organiseert_teamcompetitie
                    deel.regio_heeft_vaste_teams = vorige.regio_heeft_vaste_teams
                    deel.regio_team_punten_model = vorige.regio_team_punten_model

                bulk.append(deel)
            # for
        elif laag == LAAG_RK:
            # RK
            for obj in rayons:
                functie = functies[("RKO", comp.afstand, obj.rayon_nr)]
                deel = DeelCompetitie(competitie=comp,
                                      laag=laag,
                                      nhb_rayon=obj,
                                      functie=functie,
                                      plan=plannen[obj.rayon_nr])
                bulk.append(deel)
            # for
        else:
            # BK
            functie = functies[("BKO", comp.afstand, 0)]
            deel = DeelCompetitie(competitie=comp,
                                  laag=laag,
                                  functie=functie,
                                  plan=plannen[0])
            bulk.append(deel)
    # for

    DeelCompetitie.objects.bulk_create(bulk)


def _maak_competitieklassen(comp):
    """ Maak de competitieklassen aan voor een nieuwe competitie
        het min_ag per klasse wordt later ingevuld
    """

    bulk = list()

    for indiv in (IndivWedstrijdklasse
                  .objects
                  .prefetch_related('leeftijdsklassen')
                  .exclude(buiten_gebruik=True)):

        klasse = CompetitieKlasse(
                        competitie=comp,
                        indiv=indiv,
                        min_ag=AG_NUL)

        # bepaal of deze klasse voor aspiranten is
        for lkl in indiv.leeftijdsklassen.all():
            if lkl.is_aspirant_klasse():
                klasse.is_aspirant_klasse = True
        # for

        bulk.append(klasse)
    # for

    teams = (TeamWedstrijdklasse
             .objects
             .exclude(buiten_gebruik=True))

    # team klassen voor de regiocompetitie
    for team in teams:
        klasse = CompetitieKlasse(
                        competitie=comp,
                        team=team,
                        min_ag=AG_NUL,
                        is_voor_teams_rk_bk=False)
        bulk.append(klasse)
    # for

    # team klassen voor RK/BK
    for team in teams:
        klasse = CompetitieKlasse(
                        competitie=comp,
                        team=team,
                        min_ag=AG_NUL,
                        is_voor_teams_rk_bk=True)
        bulk.append(klasse)
    # for

    CompetitieKlasse.objects.bulk_create(bulk)


def bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


def competities_aanmaken(jaar=None):
    """ Deze functie wordt aangeroepen als de BKO de nieuwe competitie op wil starten
        We maken de 18m en 25m competitie aan en daaronder de deelcompetities voor regio, rayon en bond

        Wedstrijdklassen worden ook aangemaakt, maar het minimale AG wordt nog niet ingevuld
    """

    if not jaar:
        jaar = bepaal_startjaar_nieuwe_competitie()

    yearend = date(year=jaar, month=12, day=31)     # 31 december
    udvl = date(year=jaar, month=8, day=1)          # 1 augustus
    begin_rk = date(year=jaar + 1, month=2, day=1)  # 1 februari
    begin_bk = date(year=jaar + 1, month=5, day=1)  # 1 mei

    rayons = NhbRayon.objects.all()
    regios = NhbRegio.objects.filter(is_administratief=False)

    functies = dict()   # [rol, afstand, 0/rayon_nr/regio_nr] = functie
    for functie in (Functie
                    .objects
                    .select_related('nhb_regio', 'nhb_rayon')
                    .filter(rol__in=('RCL', 'RKO', 'BKO'))):
        afstand = functie.comp_type
        if functie.rol == 'RCL':
            nr = functie.nhb_regio.regio_nr
        elif functie.rol == 'RKO':
            nr = functie.nhb_rayon.rayon_nr
        else:  # elif functie.rol == 'BKO':
            nr = 0

        functies[(functie.rol, afstand, nr)] = functie
    # for

    # maak de Competitie aan voor 18m en 25m
    for afstand, beschrijving in AFSTANDEN:
        comp = Competitie(
                    beschrijving='%s competitie %s/%s' % (beschrijving, jaar, jaar+1),
                    afstand=afstand,      # 18/25
                    begin_jaar=jaar,
                    uiterste_datum_lid=udvl,
                    begin_aanmeldingen=yearend,
                    einde_aanmeldingen=yearend,
                    einde_teamvorming=yearend,
                    eerste_wedstrijd=yearend,
                    laatst_mogelijke_wedstrijd=begin_rk,
                    datum_klassengrenzen_rk_bk_teams=begin_rk,
                    rk_eerste_wedstrijd=begin_rk,
                    rk_laatste_wedstrijd=begin_rk + datetime.timedelta(days=7),
                    bk_eerste_wedstrijd=begin_bk,
                    bk_laatste_wedstrijd=begin_bk + datetime.timedelta(days=7))

        if afstand == '18':
            comp.laatst_mogelijke_wedstrijd = yearend

        comp.save()

        _maak_deelcompetities(comp, rayons, regios, functies)

        _maak_competitieklassen(comp)
    # for


# end of file
