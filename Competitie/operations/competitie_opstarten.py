# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from BasisTypen.models import TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse
from Competitie.definities import AFSTANDEN, DEEL_RK, DEEL_BK
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               Regiocompetitie, Kampioenschap, RegiocompetitieRonde)
from Functie.models import Functie
from NhbStructuur.models import NhbRayon, NhbRegio
from Score.definities import AG_NUL
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
    objs = (RegiocompetitieRonde
            .objects
            .filter(regiocompetitie=deelcomp,
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


def maak_regiocompetitie_ronde(deelcomp, cluster=None):
    """ Maak een nieuwe regiocompetitie ronde object aan
        geef er een uniek week nummer aan.
    """

    nieuwe_week_nr = bepaal_volgende_week_nummer(deelcomp, cluster)

    if nieuwe_week_nr:
        # maak een eigen wedstrijdenplan aan voor deze ronde
        ronde = RegiocompetitieRonde()
        ronde.regiocompetitie = deelcomp
        ronde.cluster = cluster
        ronde.week_nr = nieuwe_week_nr
        ronde.save()
    else:
        # maximum aantal rondes is al aangemaakt
        ronde = None

    return ronde


def _maak_regiocompetities(comp, regios, functies):

    """ Maak de DeelCompetities voor een competitie aan """

    # zoek de voorgaande regiocompetities erbij om instellingen over te kunnen nemen
    vorige_deelcomps = dict()   # [regio_nr] = DeelCompetitie()
    for deelcomp in (Regiocompetitie
                     .objects
                     .select_related('competitie',
                                     'nhb_regio')
                     .filter(competitie__begin_jaar=comp.begin_jaar - 1,
                             competitie__afstand=comp.afstand)):
        vorige_deelcomps[deelcomp.nhb_regio.regio_nr] = deelcomp
    # for

    # maak de regiocompetities aan voor regiocompetities
    bulk = list()
    for obj in regios:
        functie = functies[("RCL", comp.afstand, obj.regio_nr)]
        deel = Regiocompetitie(competitie=comp,
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

    Regiocompetitie.objects.bulk_create(bulk)


def _maak_kampioenschappen(comp, rayons, functies):

    """ Maak de DeelKampioenschappen voor een competitie aan """

    bulk = list()

    # RK individueel en teams
    for rayon in rayons:
        functie = functies[("RKO", comp.afstand, rayon.rayon_nr)]
        deelkamp = Kampioenschap(
                            deel=DEEL_RK,
                            competitie=comp,
                            nhb_rayon=rayon,
                            functie=functie)
        bulk.append(deelkamp)
    # for

    # BK individueel en teams
    functie = functies[("BKO", comp.afstand, 0)]
    deelkamp = Kampioenschap(
                    deel=DEEL_BK,
                    competitie=comp,
                    functie=functie)
    bulk.append(deelkamp)

    Kampioenschap.objects.bulk_create(bulk)


def _maak_competitieklassen(comp):
    """ Maak de competitie klassen aan voor een nieuwe competitie
        het min_ag per klasse wordt later ingevuld
    """

    is_18m = comp.afstand == '18'

    if True:
        volgorde2lkl_pks = dict()     # [volgorde] = [LeeftijdsKlasse.pk, ...]
        bulk = list()

        for indiv in (TemplateCompetitieIndivKlasse
                      .objects
                      .prefetch_related('leeftijdsklassen')):

            if is_18m:
                if not indiv.gebruik_18m:
                    continue
            else:
                if not indiv.gebruik_25m:
                    continue

            klasse = CompetitieIndivKlasse(
                            competitie=comp,
                            volgorde=indiv.volgorde,
                            beschrijving=indiv.beschrijving,
                            boogtype=indiv.boogtype,
                            is_voor_rk_bk=not indiv.niet_voor_rk_bk,
                            is_onbekend=indiv.is_onbekend,
                            is_aspirant_klasse=indiv.is_aspirant_klasse,
                            min_ag=AG_NUL)

            if is_18m:
                klasse.blazoen1_regio = indiv.blazoen1_18m_regio
                klasse.blazoen2_regio = indiv.blazoen2_18m_regio
                klasse.blazoen_rk_bk = indiv.blazoen_18m_rk_bk
            else:
                klasse.blazoen1_regio = indiv.blazoen1_25m_regio
                klasse.blazoen2_regio = indiv.blazoen2_25m_regio
                klasse.blazoen_rk_bk = indiv.blazoen_25m_rk_bk

            bulk.append(klasse)

            volgorde2lkl_pks[klasse.volgorde] = list(indiv.leeftijdsklassen.values_list('pk', flat=True))
        # for

        CompetitieIndivKlasse.objects.bulk_create(bulk)

        # zet de leeftijdsklassen
        for klasse in CompetitieIndivKlasse.objects.filter(competitie=comp):
            klasse.leeftijdsklassen.set(volgorde2lkl_pks[klasse.volgorde])
        # for

    if True:

        teamtype_pk2boog_pks = dict()        # [teamtype.pk] = [boogtype.pk, ...]

        bulk = list()
        for team in (TemplateCompetitieTeamKlasse
                     .objects
                     .select_related('team_type')
                     .prefetch_related('team_type__boog_typen')):

            if is_18m:
                if not team.gebruik_18m:
                    continue
            else:
                if not team.gebruik_25m:
                    continue

            boog_pks = list(team.team_type.boog_typen.all().values_list('pk', flat=True))
            teamtype_pk2boog_pks[team.team_type.pk] = boog_pks

            # voor de regiocompetitie teams
            klasse = CompetitieTeamKlasse(
                        competitie=comp,
                        volgorde=team.volgorde,
                        beschrijving=team.beschrijving,
                        team_afkorting=team.team_type.afkorting,
                        team_type=team.team_type,
                        min_ag=AG_NUL,
                        is_voor_teams_rk_bk=False)

            if is_18m:
                klasse.blazoen1_regio = team.blazoen1_18m_regio
                klasse.blazoen2_regio = team.blazoen2_18m_regio
                klasse.blazoen_rk_bk = team.blazoen_18m_rk_bk
            else:
                klasse.blazoen1_regio = team.blazoen1_25m_regio
                klasse.blazoen2_regio = team.blazoen2_25m_regio
                klasse.blazoen_rk_bk = team.blazoen_25m_rk_bk

            bulk.append(klasse)

            # voor de rayonkampioenschappen teams
            klasse = CompetitieTeamKlasse(
                        competitie=comp,
                        volgorde=team.volgorde + 100,
                        beschrijving=team.beschrijving,
                        team_afkorting=team.team_type.afkorting,
                        team_type=team.team_type,
                        min_ag=AG_NUL,
                        is_voor_teams_rk_bk=True)

            if is_18m:
                klasse.blazoen1_regio = team.blazoen1_18m_regio
                klasse.blazoen2_regio = team.blazoen2_18m_regio
                klasse.blazoen_rk_bk = team.blazoen_18m_rk_bk
            else:
                klasse.blazoen1_regio = team.blazoen1_25m_regio
                klasse.blazoen2_regio = team.blazoen2_25m_regio
                klasse.blazoen_rk_bk = team.blazoen_25m_rk_bk

            bulk.append(klasse)
        # for

        CompetitieTeamKlasse.objects.bulk_create(bulk)

        # zet de boogtypen
        for team in bulk:
            boog_pks = teamtype_pk2boog_pks[team.team_type.pk]
            team.boog_typen.set(boog_pks)
        # for


def bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


def competities_aanmaken(jaar=None):
    """ Deze functie wordt aangeroepen als de BKO de nieuwe competitie op wil starten
        We maken de 18m en 25m competitie aan en daaronder de regiocompetities voor regio, rayon en bond

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

    now = timezone.now()
    if now.month == 12 and now.day == 31:               # pragma: no cover
        # avoid failing test cases one day per year
        yearend = date(year=jaar+1, month=1, day=1)     # 31 december + 1 day

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
                    rk_indiv_eerste_wedstrijd=begin_rk,
                    rk_indiv_laatste_wedstrijd=begin_rk + datetime.timedelta(days=7),
                    rk_teams_eerste_wedstrijd=begin_rk,
                    rk_teams_laatste_wedstrijd=begin_rk + datetime.timedelta(days=7),
                    bk_indiv_eerste_wedstrijd=begin_bk,
                    bk_indiv_laatste_wedstrijd=begin_bk + datetime.timedelta(days=7),
                    bk_teams_eerste_wedstrijd=begin_bk,
                    bk_teams_laatste_wedstrijd = begin_bk + datetime.timedelta(days=7))

        if afstand == '18':
            comp.einde_fase_F = yearend

        comp.save()

        indiv_klassen = TemplateCompetitieIndivKlasse.objects.all()
        pks = list(indiv_klassen.values_list('boogtype__pk', flat=True))
        comp.boogtypen.set(pks)

        teams_klassen = TemplateCompetitieTeamKlasse.objects.all()
        pks = list(teams_klassen.values_list('team_type__pk', flat=True))
        comp.teamtypen.set(pks)

        _maak_regiocompetities(comp, regios, functies)
        _maak_kampioenschappen(comp, rayons, functies)

        _maak_competitieklassen(comp)
    # for


# end of file
