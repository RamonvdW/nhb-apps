# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from BasisTypen.models import (BoogType, LeeftijdsKlasse, TeamType, IndivWedstrijdklasse, TeamWedstrijdklasse,
                               BLAZOEN_CHOICES, BLAZOEN_40CM)
from Functie.models import Functie
from Functie.rol import Rollen
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Score.models import Score, ScoreHist, Uitslag
from Sporter.models import SporterBoog
from Wedstrijden.models import WedstrijdLocatie
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

DAGDEEL2LABEL = {
    'GN': ("Geen", "Geen voorkeur"),
    'AV': ("Avond", "'s Avonds"),
    'MA': ("M", "Maandag"),
    'MAa': ("M-Av", "Maandagavond"),
    'DI': ("Di", "Dinsdag"),
    'DIa': ("Di-Av", "Dinsdagavond"),
    'WO': ("W", "Woensdag"),
    'WOa': ("W-Av", "Woensdagavond"),
    'DO': ("Do", "Donderdag"),
    'DOa': ("Do-Av", "Donderdagavond"),
    'VR': ("V", "Vrijdag"),
    'VRa': ("V-Av", "Vrijdagavond"),
    'ZAT': ("Za", "Zaterdag"),
    'ZAo': ("Za-Och", "Zaterdagochtend"),
    'ZAm': ("Zo-Mi", "Zaterdagmiddag"),
    'ZAa': ("Za-Av", "Zaterdagavond"),
    'ZON': ("Zo", "Zondag"),
    'ZOo': ("Zo-Och", "Zondagochtend"),
    'ZOm': ("Zo-Mi", "Zondagmiddag"),
    'ZOa': ("Zo-Av", "Zondagavond"),
    'WE': ("Weekend", "Weekend")
}


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

DEELNAME2STR = {
    DEELNAME_ONBEKEND: 'Onbekend',
    DEELNAME_JA: 'Bevestigd',
    DEELNAME_NEE: 'Afgemeld'
}

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

    # alle ondersteunde typen bogen en teams
    teamtypen = models.ManyToManyField(TeamType)
    boogtypen = models.ManyToManyField(BoogType)

    # fase A: aanmaken competitie, vaststellen klassen
    klassengrenzen_vastgesteld = models.BooleanField(default=False)

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

    # aantal scores dat een individuele sporter neergezet moet hebben om gerechtigd te zijn voor deelname aan het RK
    aantal_scores_voor_rk_deelname = models.PositiveSmallIntegerField(default=6)

    # fase J: RK deelnemers bevestigen deelname
    #         HWL's kunnen RK teams te repareren
    #         einde fase J: BKO bevestigd klassengrenzen RK/BK teams
    datum_klassengrenzen_rk_bk_teams = models.DateField()

    klassengrenzen_vastgesteld_rk_bk = models.BooleanField(default=False)

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

    # als het RK afgelast is, toon dan deze tekst
    rk_is_afgelast = models.BooleanField(default=False)
    rk_afgelast_bericht = models.TextField(blank=True)

    # ----
    # fases en datums bondskampioenschappen
    # ----

    # fase P: bevestig deelnemers; oproepen reserves
    bk_eerste_wedstrijd = models.DateField()
    # fase Q: wedstrijden
    bk_laatste_wedstrijd = models.DateField()
    # fase R: vaststellen en publiceren uitslag
    alle_bks_afgesloten = models.BooleanField(default=False)

    # als het BK afgelast is, toon dan deze tekst
    bk_is_afgelast = models.BooleanField(default=False)
    bk_afgelast_bericht = models.TextField(blank=True)

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

            if not self.klassengrenzen_vastgesteld_rk_bk:
                # fase J, tot de BKO deze handmatig doorzet
                # datum_klassengrenzen_rk_bk_teams is indicatief
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
        if not self.klassengrenzen_vastgesteld or now < self.begin_aanmeldingen:
            # A = vaststellen klassengrenzen, instellingen regio en planning regiocompetitie wedstrijden
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


class CompetitieIndivKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen::IndivWedstrijdklasse
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
    is_voor_rk_bk = models.BooleanField(default=False)

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen (geen keuze)
    blazoen_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    def __str__(self):
        return self.beschrijving + ' [' + self.boogtype.afkorting + '] (%.3f)' % self.min_ag

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

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen::TeamWedstrijdklasse
        en de gerefereerde TeamType wordt hierin ook plat geslagen om het aantal database accesses te begrenzen.
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # sorteervolgorde
    # lager nummer = betere schutters
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
    for klasse in (CompetitieKlasse
                   .objects
                   .filter(competitie=comp)
                   .exclude(indiv=None)
                   .prefetch_related('indiv__leeftijdsklassen')):
        for lkl in klasse.indiv.leeftijdsklassen.all():
            if lkl.pk not in pks:
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

    # wedstrijden - alleen voor de RK en BK
    rk_bk_matches = models.ManyToManyField(CompetitieMatch, blank=True)

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


class DeelcompetitieIndivKlasseLimiet(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal deelnemers in een RK of BK
        wedstrijdklasse. De RKO kan dit bijstellen specifiek voor zijn RK.
    """

    # voor welke deelcompetitie (ivm scheiding RKs)
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE,
                                     blank=True, null=True)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        return "%s : %s - %s" % (self.limiet, self.indiv_klasse.beschrijving, self.deelcompetitie)

    class Meta:
        verbose_name = "Deelcompetitie IndivKlasse Limiet"
        verbose_name_plural = "Deelcompetitie IndivKlasse Limieten"


class DeelcompetitieTeamKlasseLimiet(models.Model):
    """ Deze database tabel bevat de limieten voor het aantal teams in een RK of BK
        wedstrijdklasse. De RKO kan dit bijstellen specifiek voor zijn RK.
    """

    # voor welke deelcompetitie (ivm scheiding RKs)
    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    # voor welke klasse is deze limiet
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    blank=True, null=True)

    # maximum aantal deelnemers in deze klasse
    limiet = models.PositiveSmallIntegerField(default=24)

    def __str__(self):
        return "%s : %s - %s" % (self.limiet, self.team_klasse.beschrijving, self.deelcompetitie)

    class Meta:
        verbose_name = "Deelcompetitie TeamKlasse Limiet"
        verbose_name_plural = "Deelcompetitie TeamKlasse Limieten"


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
    matches = models.ManyToManyField(CompetitieMatch, blank=True)

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

    # bovenstaande gemiddelde vastgesteld aan het begin van de huidige team ronde
    gemiddelde_begin_team_ronde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 10,000

    # voorkeuren opgegeven bij het inschrijven
    inschrijf_voorkeur_team = models.BooleanField(default=False)

    # opmerking vrije tekst
    inschrijf_notitie = models.TextField(default="", blank=True)

    # voorkeur dagdelen (methode 3)
    inschrijf_voorkeur_dagdeel = models.CharField(max_length=3, choices=DAGDELEN, default="GN")

    # voorkeur schietmomenten (methode 1)
    inschrijf_gekozen_matches = models.ManyToManyField(CompetitieMatch, blank=True)

    def __str__(self):
        # deze naam wordt gebruikt in de admin interface, dus kort houden
        sporter = self.sporterboog.sporter
        return "[%s] %s (%s)" % (sporter.lid_nr, sporter.volledige_naam(),
                                 self.sporterboog.boogtype.beschrijving)

    class Meta:
        verbose_name = "Regiocompetitie Schutterboog"
        verbose_name_plural = "Regiocompetitie Schuttersboog"

        indexes = [
            # help de filters op aantal_scores
            models.Index(fields=['aantal_scores']),

            # help sorteren op gemiddelde (hoogste eerst)
            models.Index(fields=['-gemiddelde']),

            # help de specifieke filters op deelcompetitie en aantal_scores
            models.Index(fields=['aantal_scores', 'deelcompetitie']),
        ]

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
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE)

    # vereniging wordt hier apart bijgehouden omdat de schutter over kan stappen
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

    # deelname positie van de sporter in de meest up to date lijst
    # de eerste N (tot de limiet/cut, standaard 24) zijn deelnemers; daarna reserveschutters
    # afmeldingen hebben rank 0
    rank = models.PositiveSmallIntegerField(default=0)

    # wanneer hebben we een bevestiging gevraagd hebben via e-mail
    # fase K: aan het begin van fase K wordt een uitnodiging gestuurd om deelname te bevestigen
    # fase K: twee weken voor begin van de wedstrijden wordt een herinnering gestuurd
    bevestiging_gevraagd_op = models.DateTimeField(null=True, blank=True)

    # kan deze schutter deelnemen, of niet?
    deelname = models.CharField(max_length=1, choices=DEELNAME_CHOICES, default=DEELNAME_ONBEKEND)

    # gemiddelde uit de voorgaande regiocompetitie
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    # sporters met gelijk gemiddelde moeten in de juiste volgorde gehouden worden door te kijken naar
    # de regio scores: hoogste score gaat voor
    # scores zijn als string opgeslagen zodat er gesorteerd kan worden
    # "AAABBBCCCDDDEEEFFFGGG" met AAA..GGG=7 scores van 3 cijfers, gesorteerd van beste naar slechtste score
    regio_scores = models.CharField(max_length=24, default='', blank=True)

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
    # wordt ingevuld na het vaststellen van de RK/BK klassengrenzen (einde fase K)
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    blank=True, null=True)

    # TODO: RK uitslag scores en ranking toevoegen

    def __str__(self):
        return "%s: %s" % (self.vereniging, self.team_naam)


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
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE,
                                     null=True, blank=True)
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
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
