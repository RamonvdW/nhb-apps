# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from Competitie.definities import DAGDELEN
from Competitie.models.competitie import CompetitieMatch, CompetitieIndivKlasse
from Score.models import Score
from Sporter.models import SporterBoog
from Vereniging.models import Vereniging
from .regiocomp import RegioComp


class RegioDeelnemer(models.Model):

    """ Een sporterboog aangemeld bij een regiocompetitie """

    # wanneer is deze aanmelding gedaan?
    # (wordt gebruikt om de delta aan de RCL te melden)
    wanneer_aangemeld = models.DateField(auto_now_add=True)

    # bij welke regiocompetitie hoort deze inschrijving?
    regiocomp = models.ForeignKey(RegioComp, on_delete=models.CASCADE)

    # om wie gaat het?
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT, null=True)

    # vereniging wordt hier apart bijgehouden omdat de sporter over kan stappen midden in het seizoen
    bij_vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT)

    # aanvangsgemiddelde voor de individuele competitie
    # typisch gebaseerd op de uitslag van vorig seizoen
    # is 0,000 voor nieuwe sporters en bij onvoldoende scores in vorig seizoen
    # dan wordt de sporter in een 'klasse onbekend' geplaatst
    ag_voor_indiv = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # aanvangsgemiddelde voor de teamcompetitie (typisch gelijk aan ag_voor_indiv)
    ag_voor_team = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)     # 10,000

    # indien ag_voor_team niet gebaseerd op de uitslag van vorig seizoen,
    # of 0,000 is (voor nieuwe sporters of bij onvoldoende scores in vorig seizoen)
    # dan mag het handmatig aangepast worden
    ag_voor_team_mag_aangepast_worden = models.BooleanField(default=False)

    # individuele klasse
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE)

    # alle scores van deze sporterboog in deze competitie
    scores = models.ManyToManyField(Score,
                                    blank=True)  # mag leeg zijn / gemaakt worden

    score1 = models.PositiveIntegerField(default=0)
    score2 = models.PositiveIntegerField(default=0)
    score3 = models.PositiveIntegerField(default=0)
    score4 = models.PositiveIntegerField(default=0)
    score5 = models.PositiveIntegerField(default=0)
    score6 = models.PositiveIntegerField(default=0)
    score7 = models.PositiveIntegerField(default=0)

    # som van de beste 6 van score1..score7
    totaal = models.PositiveIntegerField(default=0)

    # aantal scores dat tot nu toe neergezet is (om eenvoudig te kunnen filteren)
    aantal_scores = models.PositiveSmallIntegerField(default=0)

    # welke van score1..score7 is de laagste?
    laagste_score_nr = models.PositiveIntegerField(default=0)  # 1..7

    # gemiddelde over de 6 beste scores, dus exclusief laatste_score_nr
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 10,000

    # bovenstaand gemiddelde vastgesteld aan het begin van de huidige team ronde
    gemiddelde_begin_team_ronde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 10,000

    # voorkeuren opgegeven bij het inschrijven:

    # (opt-in) Deelname aan de teamcompetitie gewenst?
    inschrijf_voorkeur_team = models.BooleanField(default=False)

    # (opt-out) Uitnodiging voor deelname aan het RK en BK gewenst?
    inschrijf_voorkeur_rk_bk = models.BooleanField(default=True)

    # opmerking vrije tekst
    inschrijf_notitie = models.TextField(default="", blank=True)

    # voorkeur dagdelen (methode 3)
    inschrijf_voorkeur_dagdeel = models.CharField(max_length=3, choices=DAGDELEN, default="GN")

    # voorkeur schietmomenten (methode 1)
    inschrijf_gekozen_matches = models.ManyToManyField(CompetitieMatch, blank=True)

    # aangemeld door
    aangemeld_door = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)

    # historie over belangrijke acties
    logboekje = models.TextField(default='', blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        # deze naam wordt gebruikt in de admin interface, dus kort houden
        return "%s (%s)" % (self.sporterboog.sporter.lid_nr_en_volledige_naam(),
                            self.sporterboog.boogtype.beschrijving)

    class Meta:
        verbose_name = "Deelnemer"

        indexes = [
            # help de filters op aantal_scores
            models.Index(fields=['aantal_scores']),

            # help sorteren op gemiddelde (hoogste eerst)
            models.Index(fields=['-gemiddelde']),

            # help de specifieke filters op regiocompetitie en aantal_scores
            models.Index(fields=['aantal_scores', 'regiocomp']),
        ]

    objects = models.Manager()      # for the editor only


# end of file
