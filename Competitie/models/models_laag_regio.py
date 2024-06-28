# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.models import TeamType
from Competitie.definities import (INSCHRIJF_METHODES, INSCHRIJF_METHODE_2,
                                   TEAM_PUNTEN, TEAM_PUNTEN_MODEL_TWEE,
                                   DAGDELEN)
from Competitie.models.models_competitie import Competitie, CompetitieMatch, CompetitieIndivKlasse, CompetitieTeamKlasse
from Functie.models import Functie
from Geo.models import Regio, Cluster
from Score.models import Score, ScoreHist
from Sporter.models import SporterBoog
from Vereniging.models import Vereniging

__all__ = ['Regiocompetitie', 'RegiocompetitieRonde', 'RegiocompetitieSporterBoog', 'RegiocompetitieTeam',
           'RegiocompetitieTeamPoule', 'RegiocompetitieRondeTeam']


class Regiocompetitie(models.Model):
    """ Deze database tabel bevat informatie over een deel van een competitie:
        regiocompetitie (16x), rayoncompetitie (4x) of bondscompetitie (1x)
    """

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # regio, voor regiocompetitie
    regio = models.ForeignKey(Regio, on_delete=models.PROTECT)

    # welke beheerder hoort hier bij?
    functie = models.ForeignKey(Functie, on_delete=models.PROTECT)

    # is de beheerder klaar?
    is_afgesloten = models.BooleanField(default=False)

    # specifieke instellingen voor deze regio
    inschrijf_methode = models.CharField(max_length=1,
                                         default=INSCHRIJF_METHODE_2,
                                         choices=INSCHRIJF_METHODES)

    # methode 3: toegestane dagdelen
    # komma-gescheiden lijstje met DAGDEEL: GE,AV
    # LET OP: leeg = alles toegestaan!
    toegestane_dagdelen = models.CharField(max_length=40, default='', blank=True)

    # heeft deze RK/BK al een vastgestelde deelnemerslijst?
    heeft_deelnemerslijst = models.BooleanField(default=False)

    # keuzes van de RCL voor de regiocompetitie teams

    # doet deze regiocompetitie aan team competitie?
    regio_organiseert_teamcompetitie = models.BooleanField(default=True)

    # vaste teams? zo niet, dan voortschrijdend gemiddelde (VSG)
    regio_heeft_vaste_teams = models.BooleanField(default=True)

    # tot welke datum mogen teams aangemeld aangemaakt worden (verschilt per regio)
    begin_fase_D = models.DateField(default='2001-01-01')

    # punten model
    regio_team_punten_model = models.CharField(max_length=2,
                                               default=TEAM_PUNTEN_MODEL_TWEE,
                                               choices=TEAM_PUNTEN)

    # de RCL bepaalt in welke ronde van de competitie we zijn
    #    0 = initieel
    # 1..7 = wedstrijd ronde
    #    8 = afgesloten
    huidige_team_ronde = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "%s - %s" % (self.competitie, self.regio)

    objects = models.Manager()      # for the editor only


class RegiocompetitieRonde(models.Model):
    """ Definitie van een competitieronde """

    # bij welke regiocompetitie hoort deze (geeft 18m / 25m) + regio_nr + functie + is_afgesloten
    regiocompetitie = models.ForeignKey(Regiocompetitie, on_delete=models.CASCADE)

    # het cluster waar deze planning specifiek bij hoort (optioneel)
    cluster = models.ForeignKey(Cluster, on_delete=models.PROTECT,
                                null=True, blank=True)      # cluster is optioneel

    # het week nummer van deze ronde
    # moet liggen in een toegestane reeks (afhankelijk van 18m/25m)
    week_nr = models.PositiveSmallIntegerField()

    # een eigen beschrijving van deze ronde
    # om gewone rondes en inhaalrondes uit elkaar te houden
    beschrijving = models.CharField(max_length=40)

    # wedstrijdenplan voor deze competitie ronde
    matches = models.ManyToManyField(CompetitieMatch, blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.cluster:
            msg = str(self.cluster)
        else:
            msg = str(self.regiocompetitie.regio)

        msg += " week %s" % self.week_nr

        msg += " (%s)" % self.beschrijving
        return msg


class RegiocompetitieSporterBoog(models.Model):
    """ Een sporterboog aangemeld bij een regiocompetitie """

    # wanneer is deze aanmelding gedaan?
    # (wordt gebruikt om de delta aan de RCL te melden)
    wanneer_aangemeld = models.DateField(auto_now_add=True)

    # bij welke regiocompetitie hoort deze inschrijving?
    regiocompetitie = models.ForeignKey(Regiocompetitie, on_delete=models.CASCADE)

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

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        # deze naam wordt gebruikt in de admin interface, dus kort houden
        return "%s (%s)" % (self.sporterboog.sporter.lid_nr_en_volledige_naam(),
                            self.sporterboog.boogtype.beschrijving)

    class Meta:
        verbose_name = "Regiocompetitie sporterboog"
        verbose_name_plural = "Regiocompetitie sportersboog"

        indexes = [
            # help de filters op aantal_scores
            models.Index(fields=['aantal_scores']),

            # help sorteren op gemiddelde (hoogste eerst)
            models.Index(fields=['-gemiddelde']),

            # help de specifieke filters op regiocompetitie en aantal_scores
            models.Index(fields=['aantal_scores', 'regiocompetitie']),
        ]

    objects = models.Manager()      # for the editor only


class RegiocompetitieTeam(models.Model):
    """ Een team zoals aangemaakt door de HWL van de vereniging, voor de regiocompetitie """

    # bij welke seizoen en regio hoort dit team
    regiocompetitie = models.ForeignKey(Regiocompetitie, on_delete=models.CASCADE)

    # bij welke vereniging hoort dit team
    vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT)

    # een volgnummer van het team binnen de vereniging
    volg_nr = models.PositiveSmallIntegerField(default=0)

    # team type bepaalt welke boogtypen toegestaan zijn
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    # de naam van dit team (wordt getoond in plaats van team volgnummer)
    team_naam = models.CharField(max_length=50, default='')

    # initiële leden van het team
    leden = models.ManyToManyField(RegiocompetitieSporterBoog,
                                   blank=True)    # mag leeg zijn

    # de berekende team sterkte / team gemiddelde
    # LET OP: dit is zonder de vermenigvuldiging met aantal pijlen, dus 30,000 voor Indoor i.p.v. 900,0
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 30,000

    # de klasse waarin dit team ingedeeld is
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    blank=True, null=True)

    def maak_team_naam(self):
        msg = "%s-%s" % (self.vereniging.ver_nr, self.volg_nr)
        if self.team_naam:
            msg += " (%s)" % self.team_naam
        return msg

    def maak_team_naam_kort(self):
        if self.team_naam:
            return self.team_naam
        return self.maak_team_naam()

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.maak_team_naam()

    class Meta:
        ordering = ['vereniging__ver_nr', 'volg_nr']


class RegiocompetitieTeamPoule(models.Model):
    """ Een poule wordt gebruikt om teams direct tegen elkaar uit te laten komen.
        Tot 8 teams kunnen in een poule geplaatst worden; verder aangevuld met dummies.
    """

    # bij welke regiocompetitie hoort deze poule?
    regiocompetitie = models.ForeignKey(Regiocompetitie, on_delete=models.CASCADE)

    # naam van de poule, bijvoorbeeld "ERE + A"
    beschrijving = models.CharField(max_length=100, default='')

    # welke teams zijn in deze poule geplaatst?
    teams = models.ManyToManyField(RegiocompetitieTeam,
                                   blank=True)      # mag leeg zijn

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving


class RegiocompetitieRondeTeam(models.Model):
    """ Deze tabel houdt bij wat de samenstelling was van een team in een ronde van de regiocompetitie
        Bij VSG teams wordt de samenstelling aan het einde van de voorgaande ronde vastgesteld
        Bij vaste teams wordt de RegiocompetitieTeam gebruikt
        Eventuele invaller kan geadministreerd worden
    """

    # over welk team gaat dit
    team = models.ForeignKey(RegiocompetitieTeam, on_delete=models.CASCADE)

    # welke van de 7 rondes is dit
    ronde_nr = models.PositiveSmallIntegerField(default=0)

    # leden die (automatisch) gekoppeld zijn aan het team
    deelnemers_geselecteerd = models.ManyToManyField(RegiocompetitieSporterBoog,
                                                     related_name='teamronde_geselecteerd',
                                                     blank=True)

    # feitelijke leden, inclusief invallers
    deelnemers_feitelijk = models.ManyToManyField(RegiocompetitieSporterBoog,
                                                  related_name='teamronde_feitelijk',
                                                  blank=True)

    # gekozen scores van de feitelijke leden
    # in geval van keuze zijn deze specifiek gekozen door de RCL
    scores_feitelijk = models.ManyToManyField(Score,
                                              related_name='teamronde_feitelijk',
                                              blank=True)

    # bevroren scores van de feitelijke leden op het moment dat de teamronde afgesloten werd
    scorehist_feitelijk = models.ManyToManyField(ScoreHist,
                                                 related_name='teamronde_feitelijk',
                                                 blank=True)

    # beste 3 scores van leden in het team
    team_score = models.PositiveSmallIntegerField(default=0)

    # toegekende punten in deze ronde
    team_punten = models.PositiveSmallIntegerField(default=0)

    # logboek voor noteren gemiddelde van de invallers
    logboek = models.TextField(blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "Ronde %s, team %s" % (self.ronde_nr, self.team)


# end of file
