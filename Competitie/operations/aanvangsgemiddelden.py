# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from BasisTypen.definities import MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from BasisTypen.models import TemplateCompetitieTeamKlasse
from Competitie.models import get_competitie_boog_typen
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Logboek.models import schrijf_in_logboek
from Sporter.models import Sporter, SporterBoog
from Score.definities import AG_NUL, AG_DOEL_INDIV
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist


def get_competitie_bogen(comp=None):
    """ geeft een dictionary terug met alle BoogType records die van toepassing zijn op de competitie
    """
    boogtype_dict = dict()  # [afkorting] = BoogType

    # ALLE bogen van de bondscompetitie teams worden ook gebruikt voor de individuele wedstrijdklassen

    if comp:
        for boogtype in get_competitie_boog_typen(comp):
            boogtype_dict[boogtype.afkorting] = boogtype
    else:
        # haal de boogtypen op voor de volgende competitie
        teamtypen_done = list()
        for team_wkl in (TemplateCompetitieTeamKlasse
                         .objects
                         .select_related('team_type')):
            teamtype = team_wkl.team_type
            if teamtype.pk not in teamtypen_done:
                teamtypen_done.append(teamtype.pk)
                for boogtype in teamtype.boog_typen.all():
                    boogtype_dict[boogtype.afkorting] = boogtype
                # for
        # for

    return boogtype_dict


def aanvangsgemiddelden_vaststellen_voor_afstand(afstand: int):
    """ deze functie gooit de huidige aanvangsgemiddelden van alle sporters voor gegeven afstand weg
        en bepaalt daarna de nieuwe AG's aan de hand van de meest recente historische competitie uitslag
    """
    # zoek uit wat de meest recente HistComp is
    seizoenen_qset = (HistCompSeizoen
                      .objects
                      .filter(comp_type=afstand)
                      .order_by('-seizoen'))
    if len(seizoenen_qset) == 0:
        schrijf_in_logboek(None, 'Competitie',
                           'Geen historisch uitslag om aanvangsgemiddelden vast te stellen voor %sm' % afstand)
        return

    seizoen = seizoenen_qset[0].seizoen
    schrijf_in_logboek(None, 'Competitie',
                       'Aanvangsgemiddelden vaststellen voor de %sm met uitslag seizoen %s' % (afstand, seizoen))

    seizoenen_qset = seizoenen_qset.filter(seizoen=seizoen)

    # het eindjaar van de competitie was bepalend voor de klasse
    # daarmee kunnen we bepalen of de sporter aspirant was
    eindjaar = int(seizoen.split('/')[1])

    # maak een cache aan van boogtype
    boogtype_dict = get_competitie_bogen()

    # maak een cache aan van leden
    # we filteren hier niet op inactieve leden
    sporter_dict = dict()  # [lid_nr] = Sporter
    for obj in Sporter.objects.all():
        sporter_dict[obj.lid_nr] = obj
    # for

    # maak een cache aan van sporter-boog
    sporterboog_cache = dict()         # [lid_nr, boogtype_afkorting] = SporterBoog
    for sporterboog in SporterBoog.objects.select_related('sporter', 'boogtype'):
        tup = (sporterboog.sporter.lid_nr, sporterboog.boogtype.afkorting)
        sporterboog_cache[tup] = sporterboog
    # for

    # verwijder alle bestaande aanvangsgemiddelden
    Aanvangsgemiddelde.objects.filter(doel=AG_DOEL_INDIV, afstand_meter=afstand).all().delete()

    minimum_aantal_scores = {
        18: settings.COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG,
        25: settings.COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG
    }

    # doorloop alle individuele histcomp records die bij dit seizoen horen
    hist_seizoen = None
    bulk_ag = list()
    for hist_seizoen in seizoenen_qset:
        for obj in (HistCompRegioIndiv
                    .objects
                    .select_related('seizoen')
                    .filter(seizoen=hist_seizoen)):

            # gebruik scores van IB voor gemiddelde van TR (overgang 2021/2022 --> 2022/2023)
            # if obj.boogtype == 'IB':
            #     obj.boogtype = 'TR'

            if (obj.gemiddelde > AG_NUL
                    and obj.boogtype in boogtype_dict
                    and obj.tel_aantal_scores() >= minimum_aantal_scores[afstand]):

                # haal het sporterboog record op, of maak een nieuwe aan
                try:
                    tup = (obj.sporter_lid_nr, obj.boogtype)
                    sporterboog = sporterboog_cache[tup]
                except KeyError:
                    # nieuw record nodig
                    sporterboog = SporterBoog()
                    sporterboog.boogtype = boogtype_dict[obj.boogtype]
                    sporterboog.voor_wedstrijd = True

                    try:
                        sporterboog.sporter = sporter_dict[obj.sporter_lid_nr]
                    except KeyError:
                        # geen lid meer - skip
                        sporterboog = None
                    else:
                        sporterboog.save()
                        # zet het nieuwe record in de cache, anders krijgen we dupes
                        tup = (sporterboog.sporter.lid_nr, sporterboog.boogtype.afkorting)
                        sporterboog_cache[tup] = sporterboog
                else:
                    if not sporterboog.voor_wedstrijd:
                        sporterboog.voor_wedstrijd = True
                        sporterboog.save(update_fields=['voor_wedstrijd'])

                if sporterboog:
                    # aspiranten schieten op een grotere kaart en altijd op 18m
                    # daarom AG van aspirant niet overnemen als deze cadet wordt
                    # aangezien er maar 1 klasse is, is het AG niet nodig
                    # voorbeeld: eindjaar = 2019
                    #       geboortejaar = 2006 --> leeftijd was 13, dus aspirant
                    #       geboortejaar = 2005 --> leeftijd was 14, dus cadet
                    leeftijd = (eindjaar - sporterboog.sporter.geboorte_datum.year)
                    was_aspirant = (leeftijd <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT)

                    if not was_aspirant:
                        # aanvangsgemiddelde voor deze afstand aanmaken
                        waarde = obj.gemiddelde

                        ag = Aanvangsgemiddelde(
                                    sporterboog=sporterboog,
                                    boogtype=sporterboog.boogtype,
                                    doel=AG_DOEL_INDIV,
                                    waarde=waarde,
                                    afstand_meter=afstand)
                        bulk_ag.append(ag)

                        if len(bulk_ag) >= 500:
                            Aanvangsgemiddelde.objects.bulk_create(bulk_ag)
                            bulk_ag = list()
        # for
    # for

    if len(bulk_ag) > 0:                         # pragma: no branch
        Aanvangsgemiddelde.objects.bulk_create(bulk_ag)
    del bulk_ag

    # maak nu alle ScoreHist entries in 1x aan
    # (dit kost de meeste tijd)

    # hiervoor hebben we Score.pk nodig en die kregen we niet uit bovenstaande Score.objects.bulk_create
    bulk_ag_hist = list()
    notitie = "Uitslag competitie seizoen %s" % hist_seizoen.seizoen
    for ag in (Aanvangsgemiddelde
               .objects
               .filter(doel=AG_DOEL_INDIV,
                       afstand_meter=afstand)):

        ag_hist = AanvangsgemiddeldeHist(
                            ag=ag,
                            oude_waarde=0,
                            nieuwe_waarde=ag.waarde,
                            door_account=None,
                            notitie=notitie)
        bulk_ag_hist.append(ag_hist)

        if len(bulk_ag_hist) > 250:
            AanvangsgemiddeldeHist.objects.bulk_create(bulk_ag_hist)
            bulk_ag_hist = list()
    # for
    if len(bulk_ag_hist) > 0:                             # pragma: no branch
        AanvangsgemiddeldeHist.objects.bulk_create(bulk_ag_hist)


# end of file
