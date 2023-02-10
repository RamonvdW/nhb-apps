# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.definities import BLAZOEN_CHOICES, BLAZOEN_40CM
from BasisTypen.models import (BoogType, LeeftijdsKlasse, TeamType,
                               TemplateCompetitieIndivKlasse, TemplateCompetitieTeamKlasse)
from Competitie.definities import (AFSTANDEN,
                                   DEEL_BK, DEEL_RK,
                                   INSCHRIJF_METHODES, INSCHRIJF_METHODE_2,
                                   TEAM_PUNTEN, TEAM_PUNTEN_MODEL_TWEE,
                                   DAGDELEN,
                                   DEELNAME_CHOICES, DEELNAME_ONBEKEND,
                                   MUTATIE_TO_STR, MUTATIE_KAMP_AANMELDEN, MUTATIE_KAMP_AFMELDEN, MUTATIE_KAMP_CUT)
from Competitie.tijdlijn import bepaal_fase_indiv, bepaal_fase_teams
from Functie.definities import Rollen
from Functie.models import Functie
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Score.models import Score, ScoreHist, Uitslag
from Sporter.models import SporterBoog
from Wedstrijden.models import WedstrijdLocatie
import logging

my_logger = logging.getLogger('NHBApps.Competitie')


class Competitie(models.Model):
    """ Deze database tabel bevat een van de jaarlijkse competities voor 18m of 25m
        Elke competitie heeft een beschrijving, een aantal belangrijke datums
        en een lijst van wedstrijdklassen met aanvangsgemiddelden
    """
    beschrijving = models.CharField(max_length=40)

    # 18m of 25m
    afstand = models.CharField(max_length=2, choices=AFSTANDEN)

    # seizoen
    begin_jaar = models.PositiveSmallIntegerField()     # 2019

    # alle ondersteunde typen bogen en teams
    teamtypen = models.ManyToManyField(TeamType)
    boogtypen = models.ManyToManyField(BoogType)

    # ---------------
    # Regiocompetitie
    # ---------------

    # fase A: voorbereidingen door RCL en BKO
    #         AG vaststellen (BKO)
    #         klassengrenzen indiv + teams vaststellen (BKO)
    #         instellingen teams (RCL)

    klassengrenzen_vastgesteld = models.BooleanField(default=False)

    # fase B: voorbereidingen door RCL

    begin_fase_C = models.DateField(default='2000-01-01')

    # fase C: aanmelden sporters en teams
    #         teams aanmaken + koppel sporters + handmatig teams AG (HWL)
    #         controle handmatig AG (RCL)
    #         poules voorbereiden

    # Regiocompetitie bevat de (regio specifieke) begin_fase_D

    # fase D: incomplete teams verwijderen (RCL)
    #         alle teams in een poule plaatsen (RCL)

    # eerste datum wedstrijden
    begin_fase_F = models.DateField(default='2000-01-01')
    einde_fase_F = models.DateField(default='2000-01-01')

    # fase F: wedstrijden
    #         RCL hanteert de team rondes

    # fase G: wacht op afsluiten regiocompetitie (RCLs, daarna BKO)
    #         verstuur RK uitnodigingen + vraag bevestigen deelname
    #         deelnemerslijsten RKs opstellen

    # is de regiocompetitie nodig bezig?
    regiocompetitie_is_afgesloten = models.BooleanField(default=False)

    # ---------------------
    # Rayonkampioenschappen
    # ---------------------

    # aantal scores dat een individuele sporter neergezet moet hebben om gerechtigd te zijn voor deelname aan het RK
    aantal_scores_voor_rk_deelname = models.PositiveSmallIntegerField(default=6)

    # RK teams kunnen ingeschreven worden tot deze deadline
    datum_klassengrenzen_rk_bk_teams = models.DateField(default='2000-01-01')

    # fase J: RK deelnemers bevestigen deelname
    #         HWL's kunnen invallers koppelen voor RK teams
    #         RKO's moeten planning wedstrijden afronden
    #         verwijder incomplete RK teams (RKO)

    # zijn de team klassengrenzen voor de RK/BK vastgesteld?
    klassengrenzen_vastgesteld_rk_bk = models.BooleanField(default=False)

    # fase K: RK wedstrijden voorbereiden door vereniging: afmeldingen ontvangen, reserves oproepen
    #         (begint 2 weken voor eerste wedstrijd)

    # RK wedstrijd datums
    begin_fase_L_indiv = models.DateField(default='2000-01-01')
    einde_fase_L_indiv = models.DateField(default='2000-01-01')

    begin_fase_L_teams = models.DateField(default='2000-01-01')
    einde_fase_L_teams = models.DateField(default='2000-01-01')

    # fase L: RK wedstrijden, uitslagen ontvangen, inlezen en publiceren

    # RK uitslag bevestigd?
    rk_indiv_afgesloten = models.BooleanField(default=False)
    rk_teams_afgesloten = models.BooleanField(default=False)

    # fase N: RK uitslag bevestigd

    # automatisch: BK deelnemerslijst vastgesteld (niet openbaar)

    # ----
    # Bondskampioenschappen
    # ----

    # fase N: kleine BK klassen samenvoegen

    # kleine BK klassen samengevoegd?
    bk_indiv_klassen_zijn_samengevoegd = models.BooleanField(default=False)
    bk_teams_klassen_zijn_samengevoegd = models.BooleanField(default=False)

    # fase O: BK deelnemerslijsten openbaar
    #         BK wedstrijden voorbereiden: afmeldingen/oproepen reserves

    # BK wedstrijden datums
    begin_fase_P_indiv = models.DateField(default='2000-01-01')
    einde_fase_P_indiv = models.DateField(default='2000-01-01')

    begin_fase_P_teams = models.DateField(default='2000-01-01')
    einde_fase_P_teams = models.DateField(default='2000-01-01')

    # fase P: BK wedstrijden, uitslagen ontvangen, inlezen en publiceren

    # BK uitslag bevestigd?
    bk_indiv_afgesloten = models.BooleanField(default=False)
    bk_teams_afgesloten = models.BooleanField(default=False)

    # fase Q: BK uitslag bevestigd

    # nog te wijzigen?
    is_afgesloten = models.BooleanField(default=False)

    # fase Z: competitie afgesloten

    # als het RK afgelast is, toon dan deze tekst
    rk_is_afgelast = models.BooleanField(default=False)
    rk_afgelast_bericht = models.TextField(blank=True)

    # als het BK afgelast is, toon dan deze tekst
    bk_is_afgelast = models.BooleanField(default=False)
    bk_afgelast_bericht = models.TextField(blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving

    def titel(self):
        if self.afstand == '18':
            msg = 'Indoor'
        else:
            msg = '25m 1pijl'
        msg += ' %s/%s' % (self.begin_jaar, self.begin_jaar + 1)
        return msg

    def bepaal_fase(self):
        """ bepaalde huidige fase van de competitie en zet self.fase_indiv en self.fase_teams """
        self.fase_indiv = bepaal_fase_indiv(self)
        self.fase_teams = bepaal_fase_teams(self)
        # print('competitie: afstand=%s, fase_indiv=%s, fase_teams=%s' % (self.afstand, self.fase_indiv, self.fase_teams))

    def is_open_voor_inschrijven(self):
        if not hasattr(self, 'fase_indiv'):
            self.fase_indiv = bepaal_fase_indiv(self)

        # inschrijven mag het hele seizoen, ook tijdens de wedstrijden
        return 'C' <= self.fase_indiv <= 'F'

    def bepaal_openbaar(self, rol_nu):
        """ deze functie bepaalt of de competitie openbaar is voor de huidige rol
            en zet de is_openbaar variabele op het object.
        """
        self.is_openbaar = False

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # IT, BB en BKO zien alles
            self.is_openbaar = True

        elif rol_nu in (Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL):
            # beheerders die de competitie opzetten zien competities die opgestart zijn
            self.is_openbaar = True

        else:
            if not hasattr(self, 'fase_indiv'):
                self.fase_indiv = bepaal_fase_indiv(self)

            if self.fase_indiv >= 'C':
                # modale gebruiker ziet alleen competities vanaf open-voor-inschrijving
                self.is_openbaar = True

    def maak_seizoen_str(self):
        return "%s/%s" % (self.begin_jaar, self.begin_jaar + 1)

    objects = models.Manager()      # for the editor only


class CompetitieIndivKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen::TemplateCompetitieIndivKlasse
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren Klasse 2
    beschrijving = models.CharField(max_length=80)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    # lager nummer = betere / oudere deelnemers
    volgorde = models.PositiveIntegerField()

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # klassengrens voor deze competitie
    # individueel: 0.000 - 10.000
    # team som van de 3 beste = 0.003 - 30.000
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # de leeftijdsklassen: aspirant, cadet, junior, senior en mannen/vrouwen
    # typisch zijn twee klassen: mannen en vrouwen
    leeftijdsklassen = models.ManyToManyField(LeeftijdsKlasse)

    # is dit bedoeld als klasse onbekend?
    # bevat typische ook "Klasse Onbekend" in de titel
    is_onbekend = models.BooleanField(default=False)

    # is dit een klasse voor aspiranten?
    is_aspirant_klasse = models.BooleanField(default=False)

    # wedstrijdklasse wel/niet meenemen naar de RK/BK
    # staat op False voor aspiranten klassen en klassen 'onbekend'
    is_voor_rk_bk = models.BooleanField(default=False)      # TODO: is_ook_voor_rk_bk

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen (geen keuze)
    blazoen_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    def __str__(self):
        msg = self.beschrijving + ' [' + self.boogtype.afkorting + '] (%.3f)' % self.min_ag
        if self.is_voor_rk_bk:
            msg += ' regio+RK'
        else:
            msg += ' regio'
        return msg

    class Meta:
        verbose_name = "Competitie indiv klasse"
        verbose_name_plural = "Competitie indiv klassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


class CompetitieTeamKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor de teamcompetitie,
        met de vastgestelde aanvangsgemiddelden.

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen.TemplateCompetitieTeamKlasse
        en de gerefereerde TeamType wordt hierin ook plat geslagen om het aantal database accesses te begrenzen.
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # sorteervolgorde
    # lager nummer = betere sporter
    volgorde = models.PositiveIntegerField()

    # voorbeeld: Recurve klasse ERE
    beschrijving = models.CharField(max_length=80)

    # R/R2/C/BB/BB2/IB/TR/LB
    team_afkorting = models.CharField(max_length=3)

    # toegestane boogtypen in dit type team
    boog_typen = models.ManyToManyField(BoogType)

    # klassengrens voor deze competitie
    # individueel: 0.000 - 10.000
    # team som van de 3 beste = 0.003 - 30.000
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # voor de RK/BK teams worden nieuwe klassengrenzen vastgesteld, dus houd ze uit elkaar
    # niet van toepassing op individuele klassen
    is_voor_teams_rk_bk = models.BooleanField(default=False)

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen
    blazoen_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    def __str__(self):
        msg = self.beschrijving + ' [' + self.team_afkorting + '] (%.3f)' % self.min_ag
        if self.is_voor_teams_rk_bk:
            msg += ' (RK/BK)'
        else:
            msg += ' (regio)'
        return msg

    class Meta:
        verbose_name = "Competitie team klasse"
        verbose_name_plural = "Competitie team klassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


def get_competitie_indiv_leeftijdsklassen(comp):
    lijst = list()
    pks = list()
    for klasse in (CompetitieIndivKlasse
                   .objects
                   .filter(competitie=comp)
                   .prefetch_related('leeftijdsklassen')):
        for lkl in klasse.leeftijdsklassen.all():
            if lkl.pk not in pks:
                # verwijder "Gemengd" uit de klasse beschrijving omdat dit niet relevant is voor de bondscompetitie
                lkl.beschrijving = lkl.beschrijving.replace(' Gemengd', '')
                pks.append(lkl.pk)
                tup = (lkl.volgorde, lkl.pk, lkl)
                lijst.append(tup)
        # for
    # for

    lijst.sort()        # op volgorde
    return [lkl for _, _, lkl in lijst]


def get_competitie_boog_typen(comp):
    """ Geef een lijst van BoogType records terug die gebruikt worden in deze competitie,
        gesorteerd op 'volgorde'.
    """
    return comp.boogtypen.order_by('volgorde')


class CompetitieMatch(models.Model):
    """ CompetitieMatch is de kleinste planbare eenheid in de bondscompetitie """

    # hoort bij welke competitie?
    # (ook nuttig voor filteren toepasselijke indiv_klassen / team_klassen)
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # beschrijving
    beschrijving = models.CharField(max_length=100, blank=True)

    # organiserende vereniging
    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)   # mag later ingevuld worden

    # waar
    locatie = models.ForeignKey(WedstrijdLocatie, on_delete=models.PROTECT,
                                blank=True, null=True)      # mag later ingevuld worden

    # datum en tijdstippen
    datum_wanneer = models.DateField()
    tijd_begin_wedstrijd = models.TimeField()

    # competitie klassen individueel en teams
    indiv_klassen = models.ManyToManyField(CompetitieIndivKlasse,
                                           blank=True)  # mag leeg zijn / gemaakt worden

    team_klassen = models.ManyToManyField(CompetitieTeamKlasse,
                                          blank=True)  # mag leeg zijn / gemaakt worden

    # uitslag / scores
    uitslag = models.ForeignKey(Uitslag, on_delete=models.PROTECT,
                                blank=True, null=True)

    def __str__(self):
        extra = ""
        if self.vereniging:
            extra = " bij %s" % self.vereniging
        return "(%s) %s %s%s: %s" % (self.pk, self.datum_wanneer, self.tijd_begin_wedstrijd, extra, self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Competitie Match"
        verbose_name_plural = "Competitie Matches"


class Regiocompetitie(models.Model):
    """ Deze database tabel bevat informatie over een deel van een competitie:
        regiocompetitie (16x), rayoncompetitie (4x) of bondscompetitie (1x)
    """

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # regio, voor regiocompetitie
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)

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

    def heeft_poules_nodig(self):
        # centrale plek om de poules behoefte te controleren
        # poule zijn onafhankelijk van punten model: 10 teams zijn te verdelen over 2 poules
        return self.regio_organiseert_teamcompetitie

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return "%s - %s" % (self.competitie, self.nhb_regio)

    objects = models.Manager()      # for the editor only


class RegiocompetitieRonde(models.Model):
    """ Definitie van een competitieronde """

    # bij welke regiocompetitie hoort deze (geeft 18m / 25m) + regio_nr + functie + is_afgesloten
    regiocompetitie = models.ForeignKey(Regiocompetitie, on_delete=models.CASCADE)

    # het cluster waar deze planning specifiek bij hoort (optioneel)
    cluster = models.ForeignKey(NhbCluster, on_delete=models.PROTECT,
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
            msg = str(self.regiocompetitie.nhb_regio)

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
    bij_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT)

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
    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT)

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
    logboek = models.TextField(max_length=1024, blank=True)     # TODO: max_length is not enforced, so can be removed

    def __str__(self):
        return "Ronde %s, team %s" % (self.ronde_nr, self.team)


class Kampioenschap(models.Model):
    """ Deze tabel bevat informatie over een deel van de kampioenschappen 4xRK / 1xBK en Indiv/Teams:
    """
    DEEL = [(DEEL_RK, 'RK'),
            (DEEL_BK, 'BK')]

    deel = models.CharField(max_length=2, choices=DEEL)

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # nhb_rayon is gezet voor het RK
    # geen van beiden is gezet voor de BK

    # rayon, voor RK
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor RK

    # welke beheerder hoort hier bij?
    functie = models.ForeignKey(Functie, on_delete=models.PROTECT)

    # is de beheerder klaar?
    is_klaar_indiv = models.BooleanField(default=False)
    is_klaar_teams = models.BooleanField(default=False)
    is_afgesloten = models.BooleanField(default=False)

    # wedstrijden
    rk_bk_matches = models.ManyToManyField(CompetitieMatch, blank=True)

    # heeft deze RK/BK al een vastgestelde deelnemerslijst?
    heeft_deelnemerslijst = models.BooleanField(default=False)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        deel2str = {code: beschrijving for code, beschrijving in self.DEEL}
        msg = deel2str[self.deel]
        if self.nhb_rayon:
            msg += ' Rayon %s' % self.nhb_rayon.rayon_nr
        return msg

    class Meta:
        verbose_name = "Deel kampioenschap"
        verbose_name_plural = "Deel kampioenschappen"

    objects = models.Manager()      # for the editor only


class KampioenschapIndivKlasseLimiet(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal deelnemers in een RK of BK
        wedstrijdklasse. De RKO kan dit bijstellen specifiek voor zijn RK.
    """

    # voor welk kampioenschap (i.v.m. scheiding RKs)
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE,
                                     blank=True, null=True)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        return "%s - %s: %s" % (self.kampioenschap, self.indiv_klasse.beschrijving, self.limiet)

    class Meta:
        verbose_name = "Kampioenschap IndivKlasse Limiet"
        verbose_name_plural = "Kampioenschap IndivKlasse Limieten"


class KampioenschapTeamKlasseLimiet(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal teams in een RK of BK
        wedstrijdklasse. De RKO kan dit bijstellen specifiek voor zijn RK.
    """

    # voor welk kampioenschap (i.v.m. scheiding RKs)
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    blank=True, null=True)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        msg = "%s : " % self.limiet
        if self.team_klasse:
            msg += "%s - " % self.team_klasse.beschrijving
        msg += "%s" % self.kampioenschap
        return msg

    class Meta:
        verbose_name = "Kampioenschap TeamKlasse Limiet"
        verbose_name_plural = "Kampioenschap TeamKlasse Limieten"


class KampioenschapSporterBoog(models.Model):

    """ Een sporterboog aangemeld bij een rayon- of bondskampioenschap """

    # bij welke kampioenschap hoort deze inschrijving?
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)

    # om wie gaat het?
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT, null=True)

    # de individuele wedstrijdklasse (zelfde als voor de regio)
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE)

    # vereniging wordt hier apart bijgehouden omdat leden over kunnen stappen
    # tijdens het seizoen.
    # Tijdens fase G wordt de vereniging bevroren voor het RK.
    bij_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                       blank=True, null=True)

    # kampioenen hebben een label
    kampioen_label = models.CharField(max_length=50, default='', blank=True)

    # positie van deze sporter in de lijst zoals vastgesteld aan het begin van het RK
    # dit is de originele volgorde, welke nooit meer wijzigt ook al meldt de sporter zich af
    # wordt gebruikt om de sporters in originele volgorde te tonen aan de RKO, inclusief afmeldingen
    # bij aanpassing van de cut kan de volgorde aangepast worden zodat kampioenen boven de cut staan
    volgorde = models.PositiveSmallIntegerField(default=0)  # inclusief afmeldingen

    # deelname positie van de sporter in de meest up-to-date lijst
    # de eerste N (tot de limiet/cut, standaard 24) zijn deelnemers; daarna reserve sporters
    # afmeldingen hebben rank 0
    rank = models.PositiveSmallIntegerField(default=0)

    # wanneer hebben we een bevestiging gevraagd hebben via e-mail
    # fase K: aan het begin van fase K wordt een uitnodiging gestuurd om deelname te bevestigen
    # fase K: twee weken voor begin van de wedstrijden wordt een herinnering gestuurd
    bevestiging_gevraagd_op = models.DateTimeField(null=True, blank=True)

    # kan deze sporter deelnemen, of niet?
    deelname = models.CharField(max_length=1, choices=DEELNAME_CHOICES, default=DEELNAME_ONBEKEND)

    # gemiddelde uit de voorgaande regiocompetitie
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # sporters met gelijk gemiddelde moeten in de juiste volgorde gehouden worden door te kijken naar
    # de regio scores: hoogste score gaat voor
    # de RK scores: hoogste score gaat voor
    # scores zijn als string opgeslagen zodat er gesorteerd kan worden
    # "AAABBBCCCDDDEEEFFFGGG" met AAA..GGG=7 scores van 3 cijfers, gesorteerd van beste naar slechtste score
    gemiddelde_scores = models.CharField(max_length=24, default='', blank=True)

    # resultaat van het individuele kampioenschap
    result_score_1 = models.PositiveSmallIntegerField(default=0)                # max = 32767
    result_score_2 = models.PositiveSmallIntegerField(default=0)
    result_counts = models.CharField(max_length=20, default='', blank=True)     # 25m1pijl: 5x10 3x9

    # 0 = niet meegedaan (default)
    # 1..24 = plaats op RK deelnemer, voor zover bekend
    # KAMP_RANK_UNKNOWN = wel meegedaan, uiteindelijke rank niet precies bekend
    # KAMP_RANK_RESERVE = niet afgemeld, reserve, niet meegedaan
    # KAMP_RANK_NO_SHOW = niet afgemeld, wel uitgenodigd, niet meegedaan. Waarschijnlijk een no-show.
    result_rank = models.PositiveSmallIntegerField(default=0)
    result_volgorde = models.PositiveSmallIntegerField(default=99)   # gesorteerde uitslag, inclusief alle 5e plekken

    # resultaat van de RK teams deelname van deze sporter
    result_teamscore_1 = models.PositiveSmallIntegerField(default=0)                # max = 32767
    result_teamscore_2 = models.PositiveSmallIntegerField(default=0)

    # resultaat van de BK teams deelname van deze sporter
    result_bk_teamscore_1 = models.PositiveSmallIntegerField(default=0)            # max = 32767
    result_bk_teamscore_2 = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        if self.kampioenschap.deel == DEEL_BK:
            substr = "BK"
        else:
            substr = "RK rayon %s" % self.kampioenschap.nhb_rayon.rayon_nr

        return "%s [%s] %s (%s)" % (
                    substr,
                    self.sporterboog.sporter.lid_nr,
                    self.sporterboog.sporter.volledige_naam(),
                    self.sporterboog.boogtype.beschrijving)

    class Meta:
        verbose_name = "Kampioenschap sporterboog"
        verbose_name_plural = "Kampioenschap sportersboog"

        indexes = [
            # help sorteren op gemiddelde (hoogste eerst)
            models.Index(fields=['-gemiddelde']),

            # help sorteren op volgorde
            models.Index(fields=['volgorde']),

            # help sorteren op rank
            models.Index(fields=['rank']),

            # help sorteren op volgorde en gemiddelde
            models.Index(fields=['volgorde', '-gemiddelde']),
        ]

    objects = models.Manager()      # for the editor only


class KampioenschapTeam(models.Model):
    """ Een team zoals aangemaakt door de HWL van de vereniging, voor een RK en doorstroming naar BK """

    # bij welke seizoen en RK hoort dit team?
    kampioenschap = models.ForeignKey(Kampioenschap, on_delete=models.CASCADE)        # nodig voor de migratie

    # bij welke vereniging hoort dit team
    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)

    # een volgnummer van het team binnen de vereniging
    volg_nr = models.PositiveSmallIntegerField(default=0)

    # team type bepaalt welke boogtypen toegestaan zijn
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT, null=True)

    # de naam van dit team (wordt getoond in plaats van team volgnummer)
    team_naam = models.CharField(max_length=50, default='')

    # preliminaire leden van het team (gekozen tijdens de regiocompetitie)
    tijdelijke_leden = models.ManyToManyField(RegiocompetitieSporterBoog,
                                              related_name='kampioenschapteam_tijdelijke_leden',
                                              blank=True)    # mag leeg zijn

    # de voor het kampioenschap geplaatste sporters die ook lid zijn van het team
    gekoppelde_leden = models.ManyToManyField(KampioenschapSporterBoog,
                                              related_name='kampioenschapteam_gekoppelde_leden',
                                              blank=True)   # mag leeg zijn

    # de feitelijke sporters die tijdens de kampioenschappen in het team stonden (invallers)
    feitelijke_leden = models.ManyToManyField(KampioenschapSporterBoog,
                                              related_name='kampioenschapteam_feitelijke_leden',
                                              blank=True)   # mag leeg zijn

    # de berekende team sterkte
    # LET OP: dit is zonder de vermenigvuldiging met aantal pijlen, dus 30,000 voor Indoor i.p.v. 900,0
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # de klasse waarin dit team ingedeeld is
    # dit is preliminair tijdens het inschrijven van de teams tijdens de regiocompetitie
    # wordt op None gezet tijdens het doorzetten van de RK deelnemers (fase G)
    # wordt ingevuld na het vaststellen van de RK/BK klassengrenzen (einde fase K)
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    blank=True, null=True)

    # kampioenschap uitslag: score en ranking
    # volgorde wordt gebruikt om binnen plek 5 en 9 de volgorde vast te houden
    result_rank = models.PositiveSmallIntegerField(default=0)
    result_volgorde = models.PositiveSmallIntegerField(default=0)

    result_teamscore = models.PositiveSmallIntegerField(default=0)          # max = 32767

    def __str__(self):
        return "%s: %s" % (self.vereniging, self.team_naam)


class CompetitieMutatie(models.Model):
    """ Deze tabel houdt de mutaties bij de lijst van (reserve-)sporters van
        de RK en BK wedstrijden.
        Alle verzoeken tot mutaties worden hier aan toegevoegd en na afhandelen bewaard
        zodat er een geschiedenis is.
    """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie MUTATIE_*)
    mutatie = models.PositiveSmallIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # door wie is de mutatie geïnitieerd
    # als het een account is, dan volledige naam + rol
    # als er geen account is (sporter zonder account) dan NHB lid details
    door = models.CharField(max_length=50, default='')

    # op welke competitie heeft deze mutatie betrekking?
    competitie = models.ForeignKey(Competitie,
                                   on_delete=models.CASCADE,
                                   null=True, blank=True)

    # op welke regiocompetitie heeft deze mutatie betrekking?
    regiocompetitie = models.ForeignKey(Regiocompetitie,
                                        on_delete=models.CASCADE,
                                        null=True, blank=True)

    # op welke kampioenschap heeft deze mutatie betrekking?
    kampioenschap = models.ForeignKey(Kampioenschap,
                                      on_delete=models.CASCADE,
                                      null=True, blank=True)

    # op welke klasse heeft deze mutatie betrekking?
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE,
                                     null=True, blank=True)
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    null=True, blank=True)

    # op welke kampioenschap deelnemer heeft de mutatie betrekking (aanmelden/afmelden)
    deelnemer = models.ForeignKey(KampioenschapSporterBoog,
                                  on_delete=models.CASCADE,
                                  null=True, blank=True)

    # alleen voor MUTATIE_CUT
    cut_oud = models.PositiveSmallIntegerField(default=0)
    cut_nieuw = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Competitie mutatie"

    def __str__(self):
        msg = "[%s]" % self.when
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        try:
            msg += " %s (%s)" % (self.mutatie, MUTATIE_TO_STR[self.mutatie])
        except KeyError:
            msg += " %s (???)" % self.mutatie

        if self.mutatie in (MUTATIE_KAMP_AANMELDEN, MUTATIE_KAMP_AFMELDEN):
            msg += " - %s" % self.deelnemer

        if self.mutatie == MUTATIE_KAMP_CUT:
            msg += " (%s --> %s)" % (self.cut_oud, self.cut_nieuw)

        return msg


class CompetitieTaken(models.Model):

    """ simpele tabel om bij te houden hoe het met de achtergrond taken gaat """

    # wat is de hoogste ScoreHist tot nu toe verwerkt in de tussenstand?
    hoogste_scorehist = models.ForeignKey(ScoreHist,
                                          null=True, blank=True,        # mag leeg in admin interface
                                          on_delete=models.SET_NULL)

    # wat is de hoogste mutatie tot nu toe verwerkt in de deelnemerslijst?
    hoogste_mutatie = models.ForeignKey(CompetitieMutatie,
                                        null=True, blank=True,
                                        on_delete=models.SET_NULL)


def update_uitslag_teamcompetitie():
    # regiocomp_tussenstand moet gekieteld worden
    # maak daarvoor een ScoreHist record aan
    ScoreHist(score=None,
              oude_waarde=0,
              nieuwe_waarde=0,
              notitie="Trigger background task").save()


# end of file
