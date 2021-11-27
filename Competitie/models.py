# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from BasisTypen.models import BoogType, TeamType, IndivWedstrijdklasse, TeamWedstrijdklasse
from Functie.rol import Rollen
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Functie.models import Functie
from Score.models import Score, ScoreHist
from Sporter.models import SporterBoog
from Wedstrijden.models import CompetitieWedstrijdenPlan, CompetitieWedstrijd
from decimal import Decimal
import datetime
import logging

my_logger = logging.getLogger('NHBApps.Competitie')

AG_NUL = Decimal('0.000')
AG_LAAGSTE_NIET_NUL = Decimal('0.001')

LAAG_REGIO = 'Regio'
LAAG_RK = 'RK'
LAAG_BK = 'BK'

AFSTANDEN = [('18', 'Indoor'),
             ('25', '25m 1pijl')]

DAGDELEN = [('GN', "Geen voorkeur"),
            ('AV', "'s Avonds"),
            ('MA', "Maandag"),
            ('MAa', "Maandagavond"),
            ('DI', "Dinsdag"),
            ('DIa', "Dinsdagavond"),
            ('WO', "Woensdag"),
            ('WOa', "Woensdagavond"),
            ('DO', "Donderdag"),
            ('DOa', "Donderdagavond"),
            ('VR', "Vrijdag"),
            ('VRa', "Vrijdagavond"),
            ('ZAT', "Zaterdag"),
            ('ZAo', "Zaterdagochtend"),
            ('ZAm', "Zaterdagmiddag"),
            ('ZAa', "Zaterdagavond"),
            ('ZON', "Zondag"),
            ('ZOo', "Zondagochtend"),
            ('ZOm', "Zondagmiddag"),
            ('ZOa', "Zondagavond"),
            ('WE', "Weekend")]

# Let op: DAGDEEL_AFKORTINGEN moet in dezelfde volgorde zijn als DAGDELEN
DAGDEEL_AFKORTINGEN = tuple([afk for afk, _ in DAGDELEN])

INSCHRIJF_METHODE_1 = '1'       # direct inschrijven op wedstrijd
INSCHRIJF_METHODE_2 = '2'       # verdeel wedstrijdklassen over locaties
INSCHRIJF_METHODE_3 = '3'       # dagdeel voorkeur en quota-plaatsen

INSCHRIJF_METHODES = (
    (INSCHRIJF_METHODE_1, 'Kies wedstrijden'),
    (INSCHRIJF_METHODE_2, 'Naar locatie wedstrijdklasse'),
    (INSCHRIJF_METHODE_3, 'Voorkeur dagdelen')
)

TEAM_PUNTEN_MODEL_TWEE = '2P'                 # head-to-head, via een poule
TEAM_PUNTEN_MODEL_FORMULE1 = 'F1'
TEAM_PUNTEN_MODEL_SOM_SCORES = 'SS'

TEAM_PUNTEN_F1 = (10, 8, 6, 5, 4, 3, 2, 1)

TEAM_PUNTEN = (
    (TEAM_PUNTEN_MODEL_TWEE, 'Twee punten systeem (2/1/0)'),  # alleen bij head-to-head
    (TEAM_PUNTEN_MODEL_SOM_SCORES, 'Cumulatief: som van team totaal elke ronde'),
    (TEAM_PUNTEN_MODEL_FORMULE1, 'Formule 1 systeem (10/8/6/5/4/3/2/1)'),         # afhankelijk van score
)

DEELNAME_ONBEKEND = '?'
DEELNAME_JA = 'J'
DEELNAME_NEE = 'N'

DEELNAME_CHOICES = [
    (DEELNAME_ONBEKEND, 'Onbekend'),
    (DEELNAME_JA, 'Bevestigd'),
    (DEELNAME_NEE, 'Afgemeld')
]

MUTATIE_COMPETITIE_OPSTARTEN = 1
MUTATIE_AG_VASTSTELLEN_18M = 2
MUTATIE_AG_VASTSTELLEN_25M = 3
MUTATIE_CUT = 10
MUTATIE_INITIEEL = 20
MUTATIE_AFMELDEN = 30
MUTATIE_AANMELDEN = 40
MUTATIE_TEAM_RONDE = 50
MUTATIE_AFSLUITEN_REGIOCOMP = 60

MUTATIE_TO_STR = {
    MUTATIE_AG_VASTSTELLEN_18M: "AG vaststellen 18m",
    MUTATIE_AG_VASTSTELLEN_25M: "AG vaststellen 25m",
    MUTATIE_COMPETITIE_OPSTARTEN: "competitie opstarten",
    MUTATIE_INITIEEL: "initieel",
    MUTATIE_CUT: "limiet aanpassen",
    MUTATIE_AFMELDEN: "afmelden",
    MUTATIE_AANMELDEN: "aanmelden",
    MUTATIE_TEAM_RONDE: "team ronde",
    MUTATIE_AFSLUITEN_REGIOCOMP: "afsluiten regiocomp",
}


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

    # wanneer moet een schutter lid zijn bij de bond om mee te mogen doen aan de teamcompetitie?
    uiterste_datum_lid = models.DateField()

    # fase A: aanmaken competitie, vaststellen klassen
    klassegrenzen_vastgesteld = models.BooleanField(default=False)

    # ----
    # fases en datums regiocompetitie
    # ----

    begin_aanmeldingen = models.DateField()
    # fase B: aanmelden schutters
    einde_aanmeldingen = models.DateField()
    # fase C: samenstellen vaste teams (HWL)
    einde_teamvorming = models.DateField()
    # fase D: aanmaken poules (RCL)
    eerste_wedstrijd = models.DateField()
    # fase E: wedstrijden
    laatst_mogelijke_wedstrijd = models.DateField()
    # fase F: vaststellen uitslagen in elke regio (vaste duur: 1 week)
    # fase G: afsluiten regiocompetitie (BKO)
    #         verstuur RK uitnodigingen + vraag bevestigen deelname
    #         vertaal regio teams naar RK teams
    alle_regiocompetities_afgesloten = models.BooleanField(default=False)

    # ----
    # fases en datums rayonkampioenschappen
    # ----

    # fase J: RK deelnemers bevestigen deelname
    #         HWL's kunnen RK teams te repareren
    #         einde fase J: BKO bevestigd klassegrenzen RK/BK teams
    datum_klassegrenzen_rk_bk_teams = models.DateField()

    klassegrenzen_vastgesteld_rk_bk = models.BooleanField(default=False)

    # fase K: einde: 2 weken voor begin fase L
    #         RK deelnemers bevestigen deelname
    #         HWL's kunnen invallers koppelen voor RK teams
    #         RKO's moeten planning wedstrijden afronden
    rk_eerste_wedstrijd = models.DateField()        # einde fast K moet 2 weken voor de eerste wedstrijd zijn
    # fase L: wedstrijden
    #         stuur emails uitnodiging deelname + locatie details
    rk_laatste_wedstrijd = models.DateField()
    # fase M: vaststellen en publiceren uitslag
    # fase N: afsluiten rayonkampioenschappen
    alle_rks_afgesloten = models.BooleanField(default=False)

    # ----
    # fases en datums bondskampioenschappen
    # ----

    # fase P: bevestig deelnemers; oproepen reserves
    bk_eerste_wedstrijd = models.DateField()
    # fase Q: wedstrijden
    bk_laatste_wedstrijd = models.DateField()
    # fase R: vaststellen en publiceren uitslag
    alle_bks_afgesloten = models.BooleanField(default=False)

    # nog te wijzigen?
    is_afgesloten = models.BooleanField(default=False)

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
        """ bepaalde huidige fase van de competitie en zet self.fase
        """

        # fase A was totdat dit object gemaakt werd

        if self.alle_bks_afgesloten:
            self.fase = 'Z'
            return

        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)

        if self.alle_rks_afgesloten:
            # in BK fases
            if now < self.bk_eerste_wedstrijd:
                # fase P: bevestig deelnemers; oproepen reserves
                self.fase = 'P'
                return

            if now <= self.bk_laatste_wedstrijd:
                # fase Q: wedstrijden
                self.fase = 'Q'
                return

            # fase R: vaststellen uitslagen
            if self.deelcompetitie_set.filter(is_afgesloten=False,
                                              laag=LAAG_BK).count() > 0:
                self.fase = 'R'
                return

            # fase S: afsluiten bondscompetitie
            self.fase = 'S'
            return

        if self.alle_regiocompetities_afgesloten:
            # in RK fase

            if not self.klassegrenzen_vastgesteld_rk_bk:
                # fase J, tot de BKO deze handmatig doorzet
                # datum_klassegrenzen_rk_bk_teams is indicatief
                self.fase = 'J'
                return

            # fase K tot 2 weken voor fase L
            if now < self.rk_eerste_wedstrijd - datetime.timedelta(days=14):
                # fase K: bevestig deelnemers; oproepen reserves
                self.fase = 'K'
                return

            if now <= self.rk_laatste_wedstrijd:
                # fase L: wedstrijden
                self.fase = 'L'
                return

            # fase M: vaststellen uitslag in elk rayon (RKO)
            if self.deelcompetitie_set.filter(is_afgesloten=False,
                                              laag=LAAG_RK).count() > 0:
                self.fase = 'M'
                return

            # fase N: afsluiten rayonkampioenschappen (BKO)
            self.fase = 'N'
            return

        # regiocompetitie fases
        if not self.klassegrenzen_vastgesteld or now < self.begin_aanmeldingen:
            # A = vaststellen klassegrenzen, instellingen regio en planning regiocompetitie wedstrijden
            #     tot aanmeldingen beginnen; nog niet open voor aanmelden
            self.fase = 'A'
            return

        if now <= self.einde_aanmeldingen:
            # B = open voor inschrijvingen en aanmaken teams
            self.fase = 'B'
            return

        if now <= self.einde_teamvorming:
            # C = afronden definitie teams
            self.fase = 'C'
            return

        if now < self.eerste_wedstrijd:
            # D = aanmaken poules en afronden wedstrijdschema's
            self.fase = 'D'
            return

        if now < self.laatst_mogelijke_wedstrijd:
            # E = Begin wedstrijden
            self.fase = 'E'
            return

        # fase F: vaststellen uitslag in elke regio (RCL)
        if self.deelcompetitie_set.filter(is_afgesloten=False,
                                          laag=LAAG_REGIO).count() > 0:
            self.fase = 'F'
            return

        # fase G: afsluiten regiocompetitie (BKO)
        self.fase = 'G'

    def bepaal_openbaar(self, rol_nu):
        """ deze functie bepaalt of de competitie openbaar is voor de gegeven rol
            en zet de is_openbaar variabele op het object.

            let op: self.fase moet gezet zijn
        """
        self.is_openbaar = False

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # IT, BB en BKO zien alles
            self.is_openbaar = True
        else:
            if not hasattr(self, 'fase'):
                self.bepaal_fase()

            if self.fase >= 'B':
                # modale gebruiker ziet alleen competities vanaf open-voor-inschrijving
                self.is_openbaar = True
            elif rol_nu in (Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL):
                # beheerders die de competitie opzetten zien competities die opgestart zijn
                self.is_openbaar = True

    objects = models.Manager()      # for the editor only


class CompetitieKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden
    """
    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # koppeling aan een individuele OF team wedstrijdklasse
    indiv = models.ForeignKey(IndivWedstrijdklasse, on_delete=models.PROTECT, null=True, blank=True)
    team = models.ForeignKey(TeamWedstrijdklasse, on_delete=models.PROTECT, null=True, blank=True)

    # klassegrens voor deze competitie
    # individueel: 0.000 - 10.000
    # team som van de 3 beste = 0.003 - 30.000
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # voor de RK/BK teams worden nieuwe klassegrenzen vastgesteld, dus houd ze uit elkaar
    # niet van toepassing op individuele klassen
    is_voor_teams_rk_bk = models.BooleanField(default=False)

    def __str__(self):
        msg = "?"
        if self.indiv:
            msg = self.indiv.beschrijving
        if self.team:
            msg = self.team.beschrijving
        msg += " (%.3f)" % self.min_ag

        if self.is_voor_teams_rk_bk:
            msg += ' (RK/BK)'
        elif self.team:
            msg += ' (regio)'
        return msg

    class Meta:
        verbose_name = "Competitie klasse"
        verbose_name_plural = "Competitie klassen"

    objects = models.Manager()      # for the editor only


class DeelCompetitie(models.Model):
    """ Deze database tabel bevat informatie over een deel van een competitie:
        regiocompetitie (16x), rayoncompetitie (4x) of bondscompetitie (1x)
    """
    LAAG = [(LAAG_REGIO, 'Regiocompetitie'),
            (LAAG_RK, 'Rayoncompetitie'),
            (LAAG_BK, 'Bondscompetitie')]

    laag = models.CharField(max_length=5, choices=LAAG)

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # nhb_regio is gezet voor de regiocompetitie
    # nhb_rayon is gezet voor het RK
    # geen van beiden is gezet voor de BK

    # regio, voor regiocompetitie
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Regio

    # rayon, voor RK
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Rayon

    # welke beheerder hoort hier bij?
    functie = models.ForeignKey(Functie, on_delete=models.PROTECT,
                                null=True, blank=True)      # optioneel (om migratie toe te staan)

    # is de beheerder klaar?
    is_afgesloten = models.BooleanField(default=False)

    # wedstrijdenplan - alleen voor de RK en BK
    plan = models.ForeignKey(CompetitieWedstrijdenPlan, on_delete=models.PROTECT,
                             null=True, blank=True)         # optioneel (alleen RK en BK)

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

    # doet deze deelcompetitie aan team competitie?
    regio_organiseert_teamcompetitie = models.BooleanField(default=True)

    # vaste teams? zo niet, dan voortschrijdend gemiddelde (VSG)
    regio_heeft_vaste_teams = models.BooleanField(default=True)

    # tot welke datum mogen teams aangemeld aangemaakt worden (verschilt per regio)
    einde_teams_aanmaken = models.DateField(default='2001-01-01')

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
        if self.nhb_regio:
            substr = str(self.nhb_regio)
        elif self.nhb_rayon:
            substr = str(self.nhb_rayon)
        else:
            substr = "BK"
        return "%s - %s" % (self.competitie, substr)

    objects = models.Manager()      # for the editor only


class DeelcompetitieKlasseLimiet(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal deelnemers in een RK of BK
        wedstrijdklasse. De RKO kan dit bijstellen specifiek voor zijn RK.
    """

    # voor welke deelcompetitie (ivm scheiding RKs)
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        return "%s : %s - %s" % (self.limiet,
                                 self.klasse.indiv.beschrijving,
                                 self.deelcompetitie)

    class Meta:
        verbose_name = "Deelcompetitie Klasse Limiet"
        verbose_name_plural = "Deelcompetitie Klasse Limieten"


class DeelcompetitieRonde(models.Model):
    """ Definitie van een competitieronde """

    # bij welke deelcompetitie hoort deze (geeft 18m / 25m) + regio_nr + functie + is_afgesloten
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

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
    plan = models.ForeignKey(CompetitieWedstrijdenPlan, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.cluster:
            msg = str(self.cluster)
        else:
            msg = str(self.deelcompetitie.nhb_regio)

        msg += " week %s" % self.week_nr

        msg += " (%s)" % self.beschrijving
        return msg


class RegioCompetitieSchutterBoog(models.Model):
    """ Een sporterboog aangemeld bij een regiocompetitie """

    # bij welke deelcompetitie hoort deze inschrijving?
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    # om wie gaat het?
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT, null=True)

    # vereniging wordt hier apart bijgehouden omdat de schutter over kan stappen
    # midden in het seizoen
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
    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE)

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

    # bovenstaande gemiddelde vastgesteld aan het begin van de huidige team ronde
    gemiddelde_begin_team_ronde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 10,000

    # voorkeuren opgegeven bij het inschrijven
    inschrijf_voorkeur_team = models.BooleanField(default=False)

    # opmerking vrije tekst
    inschrijf_notitie = models.TextField(default="", blank=True)

    # voorkeur dagdelen (methode 3)
    inschrijf_voorkeur_dagdeel = models.CharField(max_length=3, choices=DAGDELEN, default="GN")

    # voorkeur schietmomenten (methode 1)
    inschrijf_gekozen_wedstrijden = models.ManyToManyField(CompetitieWedstrijd, blank=True)

    def __str__(self):
        # deze naam wordt gebruikt in de admin interface, dus kort houden
        sporter = self.sporterboog.sporter
        return "[%s] %s (%s)" % (sporter.lid_nr, sporter.volledige_naam(),
                                 self.sporterboog.boogtype.beschrijving)

    class Meta:
        verbose_name = "Regiocompetitie Schutterboog"
        verbose_name_plural = "Regiocompetitie Schuttersboog"

    objects = models.Manager()      # for the editor only


class RegiocompetitieTeam(models.Model):
    """ Een team zoals aangemaakt door de HWL van de vereniging, voor de regiocompetitie """

    # bij welke seizoen en regio hoort dit team
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    # bij welke vereniging hoort dit team
    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)

    # een volgnummer van het team binnen de vereniging
    volg_nr = models.PositiveSmallIntegerField(default=0)

    # team type bepaalt welke boogtypen toegestaan zijn
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    # de naam van dit team (wordt getoond in plaats van team volgnummer)
    team_naam = models.CharField(max_length=50, default='')

    # initiële schutters in het team
    gekoppelde_schutters = models.ManyToManyField(RegioCompetitieSchutterBoog,
                                                  blank=True)    # mag leeg zijn

    # de berekende team sterkte / team gemiddelde
    # LET OP: dit is zonder de vermenigvuldiging met aantal pijlen, dus 30,000 voor Indoor ipv 900,0
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 30,000

    # de klasse waarin dit team ingedeeld is
    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE,
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


class RegiocompetitieTeamPoule(models.Model):
    """ Een poule wordt gebruikt om teams direct tegen elkaar uit te laten komen.
        Tot 8 teams kunnen in een poule geplaatst worden; verder aangevuld met dummies.
    """

    # bij welke deelcompetitie hoort deze poule?
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

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

    # schutters die (automatisch) gekoppeld zijn aan het team
    deelnemers_geselecteerd = models.ManyToManyField(RegioCompetitieSchutterBoog,
                                                     related_name='teamronde_geselecteerd',
                                                     blank=True)

    # feitelijke schutters, inclusief invallers
    deelnemers_feitelijk = models.ManyToManyField(RegioCompetitieSchutterBoog,
                                                  related_name='teamronde_feitelijk',
                                                  blank=True)

    # gekozen scores van de feitelijke schutters
    # ingeval van keuze zijn deze specifiek gekozen door de RCL
    scores_feitelijk = models.ManyToManyField(Score,
                                              related_name='teamronde_feitelijk',
                                              blank=True)

    # bevroren scores van de feitelijke schutters op het moment dat de teamronde afgesloten werd
    scorehist_feitelijk = models.ManyToManyField(ScoreHist,
                                                 related_name='teamronde_feitelijk',
                                                 blank=True)

    # beste 3 scores van schutters in het team
    team_score = models.PositiveSmallIntegerField(default=0)

    # toegekende punten in deze ronde
    team_punten = models.PositiveSmallIntegerField(default=0)

    # logboek voor noteren gemiddelde van de invallers
    logboek = models.TextField(max_length=1024, blank=True)     # TODO: max_length is not enforced, so can be removed

    def __str__(self):
        return "Ronde %s, team %s" % (self.ronde_nr, self.team)


class KampioenschapSchutterBoog(models.Model):

    """ Een sporterboog aangemeld bij een rayon- of bondskampioenschap """

    # bij welke deelcompetitie hoort deze inschrijving?
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    # om wie gaat het?
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT, null=True)

    # de individuele wedstrijdklasse (zelfde als voor de regio)
    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE)

    # vereniging wordt hier apart bijgehouden omdat de schutter over kan stappen
    # tijdens het seizoen.
    # Tijdens fase G wordt de vereniging bevroren voor het RK.
    bij_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                       blank=True, null=True)

    # kampioenen hebben een label
    kampioen_label = models.CharField(max_length=50, default='', blank=True)

    # positie van deze schutter in de lijst
    # de eerste 24 zijn deelnemers; daarna reserveschutters
    volgorde = models.PositiveSmallIntegerField(default=0)  # inclusief afmeldingen
    rank = models.PositiveSmallIntegerField(default=0)      # exclusief afmeldingen

    # wanneer hebben we een bevestiging gevraagd hebben via e-mail
    # fase K: aan het begin van fase K wordt een uitnodiging gestuurd om deelname te bevestigen
    # fase K: twee weken voor begin van de wedstrijden wordt een herinnering gestuurd
    bevestiging_gevraagd_op = models.DateTimeField(null=True, blank=True)

    # kan deze schutter deelnemen, of niet?
    deelname = models.CharField(max_length=1, choices=DEELNAME_CHOICES, default=DEELNAME_ONBEKEND)

    # gemiddelde uit de voorgaande regiocompetitie
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    def __str__(self):
        if self.deelcompetitie.nhb_rayon:
            substr = "RK rayon %s" % self.deelcompetitie.nhb_rayon.rayon_nr
        else:
            substr = "BK"

        return "%s [%s] %s (%s)" % (
                    substr,
                    self.sporterboog.sporter.lid_nr,
                    self.sporterboog.sporter.volledige_naam(),
                    self.sporterboog.boogtype.beschrijving)

    class Meta:
        verbose_name = "Kampioenschap Schutterboog"
        verbose_name_plural = "Kampioenschap Schuttersboog"

    objects = models.Manager()      # for the editor only


class KampioenschapTeam(models.Model):
    """ Een team zoals aangemaakt door de HWL van de vereniging, voor een RK en doorstroming naar BK """

    # bij welke seizoen en RK hoort dit team
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

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
    tijdelijke_schutters = models.ManyToManyField(RegioCompetitieSchutterBoog,
                                                  related_name='kampioenschapteam_tijdelijke_schutters',
                                                  blank=True)    # mag leeg zijn

    # de voor het kampioenschap geplaatste sporters die ook lid zijn van het team
    gekoppelde_schutters = models.ManyToManyField(KampioenschapSchutterBoog,
                                                  related_name='kampioenschapteam_gekoppelde_schutters',
                                                  blank=True)   # mag leeg zijn

    # de feitelijke sporters die tijdens de kampioenschappen in het team stonden (invallers)
    feitelijke_schutters = models.ManyToManyField(KampioenschapSchutterBoog,
                                                  related_name='kampioenschapteam_feitelijke_schutters',
                                                  blank=True)   # mag leeg zijn

    # de berekende team sterkte
    # LET OP: dit is zonder de vermenigvuldiging met aantal pijlen, dus 30,000 voor Indoor ipv 900,0
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # de klasse waarin dit team ingedeeld is
    # dit is preliminair tijdens het inschrijven van de teams tijdens de regiocompetitie
    # wordt op None gezet tijdens het doorzetten van de RK deelnemers (fase G)
    # wordt ingevuld na het vaststellen van de RK/BK klassegrenzen (einde fase K)
    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE,
                               blank=True, null=True)

    def __str__(self):
        return "%s: %s (%s)" % (self.vereniging, self.team_naam, self.gekoppelde_schutters.count())


class CompetitieMutatie(models.Model):
    """ Deze tabel houdt de mutaties bij de lijst van (reserve-)schutters van
        de RK en BK wedstrijden.
        Alle verzoeken tot mutaties worden hier aan toegevoegd en na afhandelen bewaard
        zodat er een geschiedenis is.
    """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie MUTATIE_*)
    mutatie = models.PositiveSmallIntegerField(default=0)

    # zijn de lijsten bijgewerkt?
    is_verwerkt = models.BooleanField(default=False)

    # door wie is de mutatie geïnitieerd
    # als het een account is, dan volledige naam + rol
    # als er geen account is (schutter zonder account) dan NHB lid details
    door = models.CharField(max_length=50, default='')

    # op welke competitie heeft deze mutatie betrekking?
    competitie = models.ForeignKey(Competitie,
                                   on_delete=models.CASCADE,
                                   null=True, blank=True)

    # op welke deelcompetitie heeft deze mutatie betrekking?
    deelcompetitie = models.ForeignKey(DeelCompetitie,
                                       on_delete=models.CASCADE,
                                       null=True, blank=True)

    # op welke klasse heeft deze mutatie betrekking?
    klasse = models.ForeignKey(CompetitieKlasse,
                               on_delete=models.CASCADE,
                               null=True, blank=True)

    # op welke kampioenschap deelnemer heeft de mutatie betrekking (aanmelden/afmelden)
    deelnemer = models.ForeignKey(KampioenschapSchutterBoog,
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

        if self.mutatie in (MUTATIE_AANMELDEN, MUTATIE_AFMELDEN):
            msg += " - %s" % self.deelnemer

        if self.mutatie == MUTATIE_CUT:
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
