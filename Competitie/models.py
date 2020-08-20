# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from NhbStructuur.models import NhbRayon, NhbRegio, NhbCluster, NhbVereniging
from Functie.models import Functie
from Schutter.models import SchutterBoog
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

    # kalender data
    uiterste_datum_lid = models.DateField()
    begin_aanmeldingen = models.DateField()
    einde_aanmeldingen = models.DateField()
    einde_teamvorming = models.DateField()
    eerste_wedstrijd = models.DateField()

    # nog te wijzigen?
    is_afgesloten = models.BooleanField(default=False)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving

    def zet_fase(self):
        # fase A was totdat dit object gemaakt werd

        now = timezone.now()
        now = datetime.date(year=now.year, month=now.month, day=now.day)

        # A1 totdat aanvangsgemiddelden en klassegrenzen zijn vastgesteld
        self.fase = 'A1'
        if self.competitieklasse_set.count() == 0:
            # wedstrijdklassen zijn nog niet vastgesteld
            return

        # A2 = instellingen regio, tot aanmeldingen beginnen
        self.fase = 'A2'
        if now < self.begin_aanmeldingen:
            # nog niet open voor aanmelden
            return

        # B = open voor inschrijvingen, tot sluiten inschrijvingen
        self.fase = 'B'
        if now < self.einde_aanmeldingen:
            return

        # C = aanmaken teams; gesloten voor individuele inschrijvingen
        self.fase = 'C'
        if now < self.einde_teamvorming:
            return

        # D = aanmaken poules en afronden wedstrijdschema's
        self.fase = 'D'
        if now < self.eerste_wedstrijd:
            return

        # E = Begin wedstrijden
        self.fase = 'E'

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

    # TODO: VSG/Vast, etc.

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
    beschrijving = models.CharField(max_length=20)

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


def maak_deelcompetitie_ronde(deelcomp, cluster=None):
    """ Maak een nieuwe deelcompetitie ronde object aan
        geef er een uniek week nummer aan.
    """

    # zoek de bestaande records
    objs = (DeelcompetitieRonde
            .objects
            .filter(deelcompetitie=deelcomp, cluster=cluster)
            .order_by('-week_nr'))

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
    udvl = date(year=jaar, month=8, day=1)          # 1 augustus = uiterste datum van lidmaatschap voor deelname teamcompetitie

    # maak de Competitie aan voor 18m en 25m
    for afstand, beschrijving in AFSTAND:
        comp = Competitie()
        comp.beschrijving = '%s competitie %s/%s' % (beschrijving, jaar, jaar+1)
        comp.afstand = afstand      # 18/25
        comp.begin_jaar = jaar
        comp.uiterste_datum_lid = udvl
        comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = comp.eerste_wedstrijd = yearend
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
    """ Een schutterboog aangemeld bij een competitie """

    deelcompetitie = models.ForeignKey(DeelCompetitie, on_delete=models.CASCADE)

    schutterboog = models.ForeignKey(SchutterBoog, on_delete=models.CASCADE)

    # vereniging wordt hier apart bijgehouden omdat de schutter over kan stappen
    # midden in het seizoen
    bij_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT)

    is_handmatig_ag = models.BooleanField(default=False)
    aanvangsgemiddelde = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)    # 10,000
    klasse = models.ForeignKey(CompetitieKlasse, on_delete=models.CASCADE)

    score1 = models.PositiveIntegerField(default=0)
    score2 = models.PositiveIntegerField(default=0)
    score3 = models.PositiveIntegerField(default=0)
    score4 = models.PositiveIntegerField(default=0)
    score5 = models.PositiveIntegerField(default=0)
    score6 = models.PositiveIntegerField(default=0)
    score7 = models.PositiveIntegerField(default=0)

    # som van score1..score7
    totaal = models.PositiveIntegerField(default=0)

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

        return "%s - %s (%s) - %s (%s) - %s" % (
                    substr,
                    msg,
                    self.klasse.min_ag,
                    self.schutterboog.nhblid.volledige_naam(),
                    self.aanvangsgemiddelde,
                    self.deelcompetitie.competitie.beschrijving)

    class Meta:
        verbose_name = "Regiocompetitie Schutterboog"
        verbose_name_plural = "Regiocompetitie Schuttersboog"

    objects = models.Manager()      # for the editor only


# end of file
