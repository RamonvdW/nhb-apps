# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from BasisTypen.models import TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse
from Competitie.definities import AFSTANDEN, DEEL_RK, DEEL_BK
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               Regiocompetitie, RegiocompetitieRonde, Kampioenschap)
from Competitie.seizoenen import seizoen_cache
from Functie.models import Functie
from Geo.models import Rayon, Regio
from Score.definities import AG_NUL
from datetime import date
import datetime
import logging

my_logger = logging.getLogger('MH.Competitie')


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


def maak_regiocompetitie_ronde(deelcomp, cluster=None, mag_database_wijzigen=False):
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

        if mag_database_wijzigen:
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
                                     'regio')
                     .filter(competitie__begin_jaar=comp.begin_jaar - 1,
                             competitie__afstand=comp.afstand)):
        vorige_deelcomps[deelcomp.regio.regio_nr] = deelcomp
    # for

    # deadline voor het inschrijven van de teams
    begin_fase_d = comp.begin_fase_F - datetime.timedelta(days=10)

    # maak de regiocompetities aan voor regiocompetities
    bulk = list()
    for obj in regios:
        functie = functies[("RCL", comp.afstand, obj.regio_nr)]
        deel = Regiocompetitie(competitie=comp,
                               regio=obj,
                               functie=functie,
                               begin_fase_D=begin_fase_d)
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

    """ Maak de Kampioenschappen voor een competitie aan """

    bulk = list()

    # RK individueel en teams
    for rayon in rayons:
        functie = functies[("RKO", comp.afstand, rayon.rayon_nr)]
        deelkamp = Kampioenschap(
                            deel=DEEL_RK,
                            competitie=comp,
                            rayon=rayon,
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

    is_18m = comp.is_indoor()

    if True:
        volgorde2lkl_pks = dict()     # [volgorde] = [Leeftijdsklasse.pk, ...]
        bulk = list()

        for template in (TemplateCompetitieIndivKlasse
                         .objects
                         .prefetch_related('leeftijdsklassen')):

            if is_18m:
                if not template.gebruik_18m:
                    continue
            else:
                if not template.gebruik_25m:
                    continue

            klasse = CompetitieIndivKlasse(
                            competitie=comp,
                            volgorde=template.volgorde,
                            beschrijving=template.beschrijving,
                            boogtype=template.boogtype,
                            is_ook_voor_rk_bk=not template.niet_voor_rk_bk,
                            is_onbekend=template.is_onbekend,
                            is_aspirant_klasse=template.is_aspirant_klasse,
                            min_ag=AG_NUL)

            if is_18m:
                klasse.blazoen1_regio = template.blazoen1_18m_regio
                klasse.blazoen2_regio = template.blazoen2_18m_regio
                klasse.blazoen_rk_bk = template.blazoen_18m_rk_bk
                if klasse.is_ook_voor_rk_bk:
                    klasse.titel_bk = template.titel_bk_18m
            else:
                klasse.blazoen1_regio = template.blazoen1_25m_regio
                klasse.blazoen2_regio = template.blazoen2_25m_regio
                klasse.blazoen_rk_bk = template.blazoen_25m_rk_bk
                if klasse.is_ook_voor_rk_bk:
                    klasse.titel_bk = template.titel_bk_25m

            bulk.append(klasse)

            volgorde2lkl_pks[klasse.volgorde] = list(template.leeftijdsklassen.values_list('pk', flat=True))
        # for

        CompetitieIndivKlasse.objects.bulk_create(bulk)

        # zet de leeftijdsklassen
        for klasse in CompetitieIndivKlasse.objects.filter(competitie=comp):
            klasse.leeftijdsklassen.set(volgorde2lkl_pks[klasse.volgorde])
        # for

    if True:

        teamtype_pk2boog_pks = dict()        # [teamtype.pk] = [boogtype.pk, ...]

        bulk = list()
        for template in (TemplateCompetitieTeamKlasse
                         .objects
                         .select_related('team_type')
                         .prefetch_related('team_type__boog_typen')):

            if is_18m:
                if not template.gebruik_18m:
                    continue
            else:
                if not template.gebruik_25m:
                    continue

            boog_pks = list(template.team_type.boog_typen.all().values_list('pk', flat=True))
            teamtype_pk2boog_pks[template.team_type.pk] = boog_pks

            # voor de regiocompetitie teams
            klasse = CompetitieTeamKlasse(
                        competitie=comp,
                        volgorde=template.volgorde,
                        beschrijving=template.beschrijving,
                        team_afkorting=template.team_type.afkorting,
                        team_type=template.team_type,
                        min_ag=AG_NUL,
                        is_voor_teams_rk_bk=False)

            if is_18m:
                klasse.blazoen1_regio = template.blazoen1_18m_regio
                klasse.blazoen2_regio = template.blazoen2_18m_regio
                klasse.blazoen_rk_bk = template.blazoen_18m_rk_bk
            else:
                klasse.blazoen1_regio = template.blazoen1_25m_regio
                klasse.blazoen2_regio = template.blazoen2_25m_regio
                klasse.blazoen_rk_bk = template.blazoen_25m_rk_bk

            bulk.append(klasse)

            # voor de rayonkampioenschappen teams
            klasse = CompetitieTeamKlasse(
                        competitie=comp,
                        volgorde=template.volgorde + 100,
                        beschrijving=template.beschrijving,
                        team_afkorting=template.team_type.afkorting,
                        team_type=template.team_type,
                        min_ag=AG_NUL,
                        is_voor_teams_rk_bk=True)

            if is_18m:
                klasse.blazoen1_regio = template.blazoen1_18m_regio
                klasse.blazoen2_regio = template.blazoen2_18m_regio
                klasse.blazoen_rk_bk = template.blazoen_18m_rk_bk
                klasse.titel_bk = template.titel_bk_18m
            else:
                klasse.blazoen1_regio = template.blazoen1_25m_regio
                klasse.blazoen2_regio = template.blazoen2_25m_regio
                klasse.blazoen_rk_bk = template.blazoen_25m_rk_bk
                klasse.titel_bk = template.titel_bk_25m

            bulk.append(klasse)
        # for

        CompetitieTeamKlasse.objects.bulk_create(bulk)

        # zet de boogtypen
        for template in bulk:
            boog_pks = teamtype_pk2boog_pks[template.team_type.pk]
            template.boog_typen.set(boog_pks)
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

    einde_jaar = date(year=jaar, month=12, day=31)          # 31 december
    begin_rk = date(year=jaar + 1, month=2, day=1)          # 1 februari
    begin_bk = date(year=jaar + 1, month=5, day=1)          # 1 mei
    einde_inschrijving = date(year=jaar, month=8, day=15)   # 15 aug

    rayons = Rayon.objects.all()
    regios = Regio.objects.filter(is_administratief=False)

    functies = dict()   # [rol, afstand, 0/rayon_nr/regio_nr] = functie
    for functie in (Functie
                    .objects
                    .select_related('regio', 'rayon')
                    .filter(rol__in=('RCL', 'RKO', 'BKO'))):
        afstand = functie.comp_type
        if functie.rol == 'RCL':
            nr = functie.regio.regio_nr
        elif functie.rol == 'RKO':
            nr = functie.rayon.rayon_nr
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
                    begin_fase_C=einde_jaar,
                    begin_fase_D_indiv=einde_inschrijving,
                    begin_fase_F=einde_jaar,
                    einde_fase_F=begin_rk,
                    datum_klassengrenzen_rk_bk_teams=begin_rk,
                    begin_fase_L_indiv=begin_rk,
                    einde_fase_L_indiv=begin_rk + datetime.timedelta(days=7),
                    begin_fase_L_teams=begin_rk,
                    einde_fase_L_teams=begin_rk + datetime.timedelta(days=7),
                    begin_fase_P_indiv=begin_bk,
                    einde_fase_P_indiv=begin_bk + datetime.timedelta(days=7),
                    begin_fase_P_teams=begin_bk,
                    einde_fase_P_teams=begin_bk + datetime.timedelta(days=7))

        if afstand == '18':
            comp.einde_fase_F = einde_jaar

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

    seizoen_cache.reset()


# end of file
