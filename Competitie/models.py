# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Functie.models import Functie
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist
from Wedstrijden.models import WedstrijdenPlan
from decimal import Decimal
from datetime import date
import datetime
import logging

my_logger = logging.getLogger('NHBApps.Competitie')

AG_NUL = Decimal('0.000')
AG_LAAGSTE_NIET_NUL = Decimal('0.001')

LAAG_REGIO = 'Regio'
LAAG_RK = 'RK'
LAAG_BK = 'BK'

AFSTAND = [('18', 'Indoor'),
           ('25', '25m 1pijl')]

DAGDEEL = [('GN', "Geen voorkeur"),
           ('AV', "'s Avonds"),
           ('ZA', "Zaterdag"),
           ('ZO', "Zondag"),
           ('WE', "Weekend")]

DAGDEEL_AFKORTINGEN = ('GN', 'AV', 'ZA', 'ZO', 'WE')

INSCHRIJF_METHODE_1 = '1'       # direct inschrijven op wedstrijd
INSCHRIJF_METHODE_2 = '2'       # verdeel wedstrijdklassen over locaties
INSCHRIJF_METHODE_3 = '3'       # dagdeel voorkeur en quota-plaatsen

INSCHRIJF_METHODES = (
    (INSCHRIJF_METHODE_1, 'Kies wedstrijden'),
    (INSCHRIJF_METHODE_2, 'Naar locatie wedstrijdklasse'),
    (INSCHRIJF_METHODE_3, 'Voorkeur dagdelen')
)


class Competitie(models.Model):
    """ Deze database tabel bevat een van de jaarlijkse competities voor 18m of 25m
        Elke competitie heeft een beschrijving, een aantal belangrijke datums
        en een lijst van wedstrijdklassen met aanvangsgemiddelden
    """
    beschrijving = models.CharField(max_length=40)

    # 18m of 25m
    afstand = models.CharField(max_length=2, choices=AFSTAND)

    # seizoen
    begin_jaar = models.PositiveSmallIntegerField()     # 2019

    # wanneer moet een schutter lid zijn bij de bond om mee te mogen doen aan de teamcompetitie?
    uiterste_datum_lid = models.DateField()

    # fases en datums regiocompetitie
    # fase A: aanmaken competitie, vaststellen klassen
    begin_aanmeldingen = models.DateField()
    # fase B: aanmelden schutters
    einde_aanmeldingen = models.DateField()
    # fase C: samenstellen vaste teams (HWL)
    einde_teamvorming = models.DateField()
    # fase D: aanmaken poules (RCL)
    eerste_wedstrijd = models.DateField()
    # fase E: wedstrijden
    laatst_mogelijke_wedstrijd = models.DateField()
    # fase F: vaststellen en publiceren uitslag
    alle_regiocompetities_afgesloten = models.BooleanField(default=False)

    # fases en datums rayonkampioenschappen
    # fase K: bevestig deelnemers; oproepen reserves
    rk_eerste_wedstrijd = models.DateField()
    # fase L: wedstrijden
    rk_laatste_wedstrijd = models.DateField()
    # fase M: vaststellen en publiceren uitslag
    alle_rks_afgesloten = models.BooleanField(default=False)

    # fases en datums bondskampioenschappen
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

    def zet_fase(self):
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
            if now < self.rk_eerste_wedstrijd:
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
        if self.competitieklasse_set.count() == 0:
            # fase A1: wedstrijdklassen zijn nog niet vastgesteld
            self.fase = 'A1'
            return

        if now < self.begin_aanmeldingen:
            # A2 = instellingen regio, tot aanmeldingen beginnen; nog niet open voor aanmelden
            self.fase = 'A2'
            return

        if now <= self.einde_aanmeldingen:
            # B = open voor inschrijvingen, tot sluiten inschrijvingen
            self.fase = 'B'
            return

        if now <= self.einde_teamvorming:
            # C = aanmaken teams; gesloten voor individuele inschrijvingen
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
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    def __str__(self):
        msg = "?"
        if self.indiv:
            msg = self.indiv.beschrijving
        if self.team:
            msg = self.team.beschrijving
        msg += " (%s)" % self.min_ag
        return msg

    class Meta:
        verbose_name = "Competitie klasse"
        verbose_name_plural = "Competitie klassen"

    objects = models.Manager()      # for the editor only


def maak_competitieklasse_indiv(comp, indiv_wedstrijdklasse, min_ag):
    """ Deze functie maakt een nieuwe CompetitieWedstrijdklasse aan met het gevraagde min_ag
        en koppelt deze aan de gevraagde Competitie
    """
    compkl = CompetitieKlasse()
    compkl.competitie = comp
    compkl.indiv = indiv_wedstrijdklasse
    compkl.min_ag = min_ag
    compkl.save()


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
    plan = models.ForeignKey(WedstrijdenPlan, on_delete=models.PROTECT,
                             null=True, blank=True)         # optioneel (alleen RK en BK)

    # specifieke instellingen voor deze regio
    inschrijf_methode = models.CharField(max_length=1, default='2', choices=INSCHRIJF_METHODES)

    # methode 3: toegestane dagdelen
    # komma-gescheiden lijstje met DAGDEEL: GE,AV
    # LET OP: leeg = alles toegestaan!
    toegestane_dagdelen = models.CharField(max_length=20, default='', blank=True)

    # FUTURE: VSG/Vast, etc.

    # heeft deze RK/BK al een vastgestelde deelnemerslijst?
    heeft_deelnemerslijst = models.BooleanField(default=False)

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
    plan = models.ForeignKey(WedstrijdenPlan, on_delete=models.PROTECT)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.cluster:
            msg = str(self.cluster)
        else:
            msg = str(self.deelcompetitie.nhb_regio)

        msg += " week %s" % self.week_nr

        msg += " (%s)" % self.beschrijving
        return msg

    def is_voor_import_oude_programma(self):
        # beetje zwak, maar correcte functioneren van de import uit het oude programma
        # is afhankelijk van de beschrijving, dus mag niet aangepast worden
        # "Ronde 1 oude programma" .. "Ronde 7 oude programma"
        return self.beschrijving[:6] == 'Ronde ' and self.beschrijving[-15:] == ' oude programma'


def maak_deelcompetitie_ronde(deelcomp, cluster=None):
    """ Maak een nieuwe deelcompetitie ronde object aan
        geef er een uniek week nummer aan.
    """

    # zoek de bestaande records
    objs = (DeelcompetitieRonde
            .objects
            .filter(deelcompetitie=deelcomp, cluster=cluster)
            .order_by('-week_nr'))

    # filter de import rondes eruit
    objs = [obj for obj in objs if not obj.is_voor_import_oude_programma()]

    if len(objs) > 0:
        nieuwe_week_nr = objs[0].week_nr + 1

        # maximum bereikt?
        if len(objs) >= 10:
            return
    else:
        nieuwe_week_nr = 37

    # maak een eigen wedstrijdenplan aan voor deze ronde
    plan = WedstrijdenPlan()
    plan.save()

    ronde = DeelcompetitieRonde()
    ronde.deelcompetitie = deelcomp
    ronde.cluster = cluster
    ronde.week_nr = nieuwe_week_nr
    ronde.plan = plan
    ronde.save()

    return ronde


def competitie_aanmaken(jaar):
    """ Deze functie wordt aangeroepen als de BKO de nieuwe competitie op wil starten
        We maken de 18m en 25m competitie aan en daaronder de deelcompetities voor regio, rayon en bond

        Wedstrijdklassen volgen later, tijdens het bepalen van de klassegrenzen
    """
    yearend = date(year=jaar, month=12, day=31)     # 31 december
    udvl = date(year=jaar, month=8, day=1)          # 1 augustus
    begin_rk = date(year=jaar + 1, month=2, day=1)  # 1 februari
    begin_bk = date(year=jaar + 1, month=5, day=1)  # 1 mei

    # maak de Competitie aan voor 18m en 25m
    for afstand, beschrijving in AFSTAND:
        comp = Competitie()
        comp.beschrijving = '%s competitie %s/%s' % (beschrijving, jaar, jaar+1)
        comp.afstand = afstand      # 18/25
        comp.begin_jaar = jaar
        comp.uiterste_datum_lid = udvl
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = comp.eerste_wedstrijd = yearend
        if afstand == '18':
            comp.laatst_mogelijke_wedstrijd = yearend
        else:
            comp.laatst_mogelijke_wedstrijd = begin_rk
        comp.rk_selecteer_deelnemers = begin_rk
        comp.rk_eerste_wedstrijd = begin_rk
        comp.rk_laatste_wedstrijd = begin_rk + datetime.timedelta(days=7)
        comp.bk_selecteer_deelnemers = begin_bk
        comp.bk_eerste_wedstrijd = begin_bk
        comp.bk_laatste_wedstrijd = begin_bk + datetime.timedelta(days=7)
        comp.save()

        # maak de Deelcompetities aan voor Regio, RK, BK
        for laag, _ in DeelCompetitie.LAAG:
            deel = DeelCompetitie()
            deel.laag = laag
            deel.competitie = comp
            if laag == LAAG_REGIO:
                # Regio
                for obj in NhbRegio.objects.filter(is_administratief=False):
                    deel.nhb_regio = obj
                    deel.pk = None
                    deel.functie = Functie.objects.get(rol="RCL", comp_type=afstand, nhb_regio=obj)
                    deel.save()
                # for
            elif laag == LAAG_RK:
                # RK
                for obj in NhbRayon.objects.all():
                    deel.nhb_rayon = obj
                    deel.pk = None
                    deel.functie = Functie.objects.get(rol="RKO", comp_type=afstand, nhb_rayon=obj)
                    deel.save()
                # for
            else:
                # BK
                deel.functie = Functie.objects.get(rol="BKO", comp_type=afstand)
                deel.save()
        # for
    # for


class RegioCompetitieSchutterBoog(models.Model):
    """ Een schutterboog aangemeld bij een regiocompetitie """

    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    schutterboog = models.ForeignKey(SchutterBoog, on_delete=models.CASCADE)

    # vereniging wordt hier apart bijgehouden omdat de schutter over kan stappen
    # midden in het seizoen
    bij_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT)

    is_handmatig_ag = models.BooleanField(default=False)
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000
    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE)

    # alle scores van deze schutterboog in deze competitie
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

    # voorkeuren opgegeven bij het inschrijven
    inschrijf_voorkeur_team = models.BooleanField(default=False)

    # opmerking vrije tekst
    inschrijf_notitie = models.TextField(default="", blank=True)

    # voorkeur dagdelen
    inschrijf_voorkeur_dagdeel = models.CharField(max_length=2, choices=DAGDEEL, default="GN")

    # alternatieve uitslag - dit is tijdelijk
    alt_score1 = models.PositiveIntegerField(default=0)
    alt_score2 = models.PositiveIntegerField(default=0)
    alt_score3 = models.PositiveIntegerField(default=0)
    alt_score4 = models.PositiveIntegerField(default=0)
    alt_score5 = models.PositiveIntegerField(default=0)
    alt_score6 = models.PositiveIntegerField(default=0)
    alt_score7 = models.PositiveIntegerField(default=0)
    alt_totaal = models.PositiveIntegerField(default=0)
    alt_aantal_scores = models.PositiveSmallIntegerField(default=0)
    alt_laagste_score_nr = models.PositiveIntegerField(default=0)  # 1..7
    alt_gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)  # 10,000

    def __str__(self):
        # deelcompetitie (komt achteraan)
        if self.deelcompetitie.nhb_regio:
            substr = str(self.deelcompetitie.nhb_regio)
        elif self.deelcompetitie.nhb_rayon:
            substr = str(self.deelcompetitie.nhb_rayon)
        else:
            substr = "BK"

        # klasse
        msg = "?"
        if self.klasse.indiv:
            msg = self.klasse.indiv.beschrijving
        if self.klasse.team:
            msg = self.klasse.team.beschrijving

        return "%s - %s (%s) - %s (%s) %s - %s" % (
                    substr,
                    msg,
                    self.klasse.min_ag,
                    self.schutterboog,
                    self.schutterboog.nhblid.volledige_naam(),
                    self.aanvangsgemiddelde,
                    self.deelcompetitie.competitie.beschrijving)

    class Meta:
        verbose_name = "Regiocompetitie Schutterboog"
        verbose_name_plural = "Regiocompetitie Schuttersboog"

    objects = models.Manager()      # for the editor only


class KampioenschapSchutterBoog(models.Model):

    """ Een schutterboog aangemeld bij een rayon- of bondskampioenschap """

    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    schutterboog = models.ForeignKey(SchutterBoog, on_delete=models.CASCADE)

    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE)

    # vereniging wordt hier apart bijgehouden omdat de schutter over kan stappen
    # tijdens het seizoen
    bij_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                       blank=True, null=True)

    # kampioenen hebben een label
    kampioen_label = models.CharField(max_length=50, default='', blank=True)

    # positie van deze schutter in de lijst
    # de eerste 24 zijn deelnemers; daarna reserveschutters
    volgorde = models.PositiveSmallIntegerField(default=0)  # inclusief afmeldingen
    rank = models.PositiveSmallIntegerField(default=0)      # exclusief afmeldingen

    # wanneer hebben we een bevestiging gevraagd hebben via e-mail
    bevestiging_gevraagd_op = models.DateTimeField(null=True, blank=True)

    # heeft deze schutter bevestigd dat deelname gaat lukken?
    # (voor deelnemers en reserves)
    deelname_bevestigd = models.BooleanField(default=False)

    # heeft deze schutter zich afgemeld?
    is_afgemeld = models.BooleanField(default=False)

    # gemiddelde uit de voorgaande competitie
    gemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000

    def __str__(self):
        # deelcompetitie (komt achteraan)
        if self.deelcompetitie.nhb_rayon:
            substr = str(self.deelcompetitie.nhb_rayon)
        else:
            substr = "BK"

        # klasse
        msg = "?"
        if self.klasse.indiv:
            msg = self.klasse.indiv.beschrijving
        if self.klasse.team:
            msg = self.klasse.team.beschrijving

        return "%s - %s - %s (%s) %s - %s" % (
                    substr,
                    msg,
                    self.schutterboog,
                    self.schutterboog.nhblid.volledige_naam(),
                    self.gemiddelde,
                    self.deelcompetitie.competitie.beschrijving)

    class Meta:
        verbose_name = "Kampioenschap Schutterboog"
        verbose_name_plural = "Kampioenschap Schuttersboog"

    objects = models.Manager()      # for the editor only


MUTATIE_CUT = 10
MUTATIE_INITIEEL = 20
MUTATIE_AFMELDEN = 30
MUTATIE_AANMELDEN = 40

mutatie2descr = {
    MUTATIE_INITIEEL: "initieel",
    MUTATIE_CUT: "nieuwe limiet",
    MUTATIE_AFMELDEN: "afmelden",
    MUTATIE_AANMELDEN: "aanmelden",
}


class KampioenschapMutatie(models.Model):

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

    # op wie heeft de mutatie betrekking (aanmelden/afmelden)
    # voor sommige mutaties verwijst deze deelnemer naar de hele deelcompetitie (MUTATIE_INITIEEL)
    # of naar een specifieke klasse (MUTATIE_CUT)
    deelnemer = models.ForeignKey(KampioenschapSchutterBoog,
                                  on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Kampioenschap Mutatie"
        verbose_name_plural = "Kampioenschap Mutaties"

    def __str__(self):
        msg = "[%s]" % self.when
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        msg += " %s (%s)" % (self.mutatie, mutatie2descr[self.mutatie])

        if self.mutatie not in (MUTATIE_INITIEEL, MUTATIE_CUT):
            msg += " - %s" % self.deelnemer

        return msg


class CompetitieTaken(models.Model):

    """ simpele tabel om bij te houden hoe het met de achtergrond taken gaat """

    # wat is de hoogste ScoreHist tot nu toe verwerkt in de tussenstand?
    hoogste_scorehist = models.ForeignKey(ScoreHist,
                                          null=True, blank=True,        # mag leeg in admin interface
                                          on_delete=models.SET_NULL)

    # wat is de hoogste KampioenschapMutatie tot nu toe verwerkt in de deelnemerslijst?
    hoogste_mutatie = models.ForeignKey(KampioenschapMutatie,
                                        null=True, blank=True,
                                        on_delete=models.SET_NULL)

# end of file
