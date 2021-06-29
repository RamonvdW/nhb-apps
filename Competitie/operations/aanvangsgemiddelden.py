# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from BasisTypen.models import BoogType, MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from Competitie.models import AG_NUL
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Logboek.models import schrijf_in_logboek
from NhbStructuur.models import NhbLid
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, SCORE_TYPE_INDIV_AG


def aanvangsgemiddelden_vaststellen_voor_afstand(afstand: int):
    """ deze functie gooit de huidige aanvangsgemiddelden van alle sporters voor gegeven afstand weg
        en bepaalt daarna de nieuwe AG's aan de hand van de meest recente historische competitie uitslag
    """
    # zoek uit wat de meest recente HistComp is
    histcomps = (HistCompetitie
                 .objects
                 .filter(comp_type=afstand)
                 .order_by('-seizoen'))
    if len(histcomps) == 0:
        schrijf_in_logboek(None, 'Competitie',
                           'Geen historisch uitslag om aanvangsgemiddelden vast te stellen voor %sm' % afstand)
        return

    seizoen = histcomps[0].seizoen
    schrijf_in_logboek(None, 'Competitie',
                       'Aanvangsgemiddelden vaststellen voor de %sm met uitslag seizoen %s' % (afstand, seizoen))

    # het eindjaar van de competitie was bepalend voor de klasse
    # daarmee kunnen we bepalen of de schutter aspirant was
    eindjaar = int(seizoen.split('/')[1])

    # maak een cache aan van boogtype
    boogtype_dict = dict()  # [afkorting] = BoogType
    for obj in BoogType.objects.all():
        boogtype_dict[obj.afkorting] = obj
    # for

    # maak een cache aan van nhb leden
    # we filteren hier niet op inactieve leden
    nhblid_dict = dict()  # [nhb_nr] = NhbLid
    for obj in NhbLid.objects.all():
        nhblid_dict[obj.nhb_nr] = obj
    # for

    # maak een cache aan van schutter-boog
    schutterboog_cache = dict()         # [schutter_nr, boogtype_afkorting] = SchutterBoog
    for schutterboog in SchutterBoog.objects.select_related('nhblid', 'boogtype'):
        tup = (schutterboog.nhblid.nhb_nr, schutterboog.boogtype.afkorting)
        schutterboog_cache[tup] = schutterboog
    # for

    # verwijder alle bestaande aanvangsgemiddelden
    Score.objects.filter(type=SCORE_TYPE_INDIV_AG, afstand_meter=afstand).all().delete()

    minimum_aantal_scores = {18: settings.COMPETITIE_18M_MINIMUM_SCORES_VOOR_AG,
                             25: settings.COMPETITIE_25M_MINIMUM_SCORES_VOOR_AG}

    # doorloop alle individuele histcomp records die bij dit seizoen horen
    bulk_score = list()
    for histcomp in histcomps:
        print('histcomp: %s' % histcomp)
        for obj in (HistCompetitieIndividueel
                    .objects
                    .select_related('histcompetitie')
                    .filter(histcompetitie=histcomp)):

            if (obj.gemiddelde > AG_NUL
                    and obj.boogtype in boogtype_dict
                    and obj.tel_aantal_scores() >= minimum_aantal_scores[afstand]):

                # haal het schutterboog record op, of maak een nieuwe aan
                try:
                    tup = (obj.schutter_nr, obj.boogtype)
                    schutterboog = schutterboog_cache[tup]
                except KeyError:
                    # nieuw record nodig
                    schutterboog = SchutterBoog()
                    schutterboog.boogtype = boogtype_dict[obj.boogtype]
                    schutterboog.voor_wedstrijd = True

                    try:
                        schutterboog.nhblid = nhblid_dict[obj.schutter_nr]
                    except KeyError:
                        # geen lid meer - skip
                        schutterboog = None
                    else:
                        schutterboog.save()
                        # zet het nieuwe record in de cache, anders krijgen we dupes
                        tup = (schutterboog.nhblid.nhb_nr, schutterboog.boogtype.afkorting)
                        schutterboog_cache[tup] = schutterboog
                else:
                    if not schutterboog.voor_wedstrijd:
                        schutterboog.voor_wedstrijd = True
                        schutterboog.save(update_fields=['voor_wedstrijd'])

                if schutterboog:
                    # aspiranten schieten op een grotere kaart en altijd op 18m
                    # daarom AG van aspirant niet overnemen als deze cadet wordt
                    # aangezien er maar 1 klasse is, is het AG niet nodig
                    # voorbeeld: eindjaar = 2019
                    #       geboortejaar = 2006 --> leeftijd was 13, dus aspirant
                    #       geboortejaar = 2005 --> leeftijd was 14, dus cadet
                    was_aspirant = (eindjaar - schutterboog.nhblid.geboorte_datum.year) <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT

                    # zoek het score record erbij
                    if not was_aspirant:
                        # aanvangsgemiddelde voor deze afstand
                        waarde = int(obj.gemiddelde * 1000)

                        score = Score(schutterboog=schutterboog,
                                      type=SCORE_TYPE_INDIV_AG,
                                      waarde=waarde,
                                      afstand_meter=afstand)
                        bulk_score.append(score)

                        if len(bulk_score) >= 500:
                            Score.objects.bulk_create(bulk_score)
                            bulk_score = list()

        # for
    # for

    if len(bulk_score) > 0:                         # pragma: no branch
        Score.objects.bulk_create(bulk_score)
    del bulk_score

    # maak nu alle ScoreHist entries in 1x aan
    # (dit kost de meeste tijd)

    # hiervoor hebben we Score.pk nodig en die kregen we niet uit bovenstaande Score.objects.bulk_create
    bulk_scorehist = list()
    notitie = "Uitslag competitie seizoen %s" % histcomp.seizoen
    for score in (Score
                  .objects
                  .filter(type=SCORE_TYPE_INDIV_AG,
                          afstand_meter=afstand)):

        scorehist = ScoreHist(score=score,
                              oude_waarde=0,
                              nieuwe_waarde=score.waarde,
                              door_account=None,
                              notitie=notitie)
        bulk_scorehist.append(scorehist)

        if len(bulk_scorehist) > 250:
            ScoreHist.objects.bulk_create(bulk_scorehist)
            bulk_scorehist = list()
    # for
    if len(bulk_scorehist) > 0:                             # pragma: no branch
        ScoreHist.objects.bulk_create(bulk_scorehist)


# end of file
