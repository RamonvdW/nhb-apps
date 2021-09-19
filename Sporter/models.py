# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from Account.models import Account
from BasisTypen.models import BoogType, GESLACHT
# mag niet afhankelijk zijn van Competitie
from NhbStructuur.models import NhbVereniging
import datetime


# global
maximum_geboortejaar = datetime.datetime.now().year - settings.MINIMUM_LEEFTIJD_LID


class SporterGeenEmail(Exception):
    """ Specifieke foutmelding omdat sporter geen e-mail adres heeft in het CRM """

    def __init__(self, sporter):
        self.sporter = sporter


class SporterInactief(Exception):
    """ Specifieke foutmelding omdat de sporter inactief is volgens het CRM """
    pass


def validate_geboorte_datum(datum):
    """ controleer of het geboortejaar redelijk is
        wordt alleen aangeroepen om de input op een formulier te checken
        jaar: Moet tussen 1900 en 5 jaar geleden liggen (jongste lid = 5 jaar)
        raises ValidationError als het jaartal niet goed is
    """
    global maximum_geboortejaar
    if datum.year < 1900 or datum.year > maximum_geboortejaar:
        raise ValidationError(
                'Geboortejaar %(jaar)s is niet valide (min=1900, max=%(max)s)',
                params={'jaar': datum.year,
                        'max': maximum_geboortejaar})


def validate_sinds_datum(datum):
    """ controleer of de sinds_datum redelijk is
        wordt alleen aangeroepen om de input op een formulier te checken
        datum: moet datetime.date() zijn, dus is al een gevalideerde jaar/maand/dag combinatie
               mag niet in de toekomst liggen
               moet 5 jaar ná het geboortejaar liggen --> geen toegang tot deze info hier
        raises ValidationError als de datum niet goed is
    """
    now = datetime.datetime.now()
    date_now = datetime.date(year=now.year, month=now.month, day=now.day)
    if datum > date_now:
        raise ValidationError('datum van lidmaatschap mag niet in de toekomst liggen')


class Sporter(models.Model):

    """ Tabel om details van een lid bij te houden """

    # het unieke lidmaatschapsnummer
    lid_nr = models.PositiveIntegerField(primary_key=True)

    # volledige naam
    # let op: voornaam kan ook een afkorting zijn
    voornaam = models.CharField(max_length=100)
    achternaam = models.CharField(max_length=100)

    # voor zoekfunctie: de namen aan elkaar; speciale tekens vervangen
    unaccented_naam = models.CharField(max_length=200, default='', blank=True)

    # het e-mailadres van dit lid
    email = models.CharField(max_length=150)

    geboorte_datum = models.DateField(validators=[validate_geboorte_datum])
    geslacht = models.CharField(max_length=1, choices=GESLACHT)

    # officieel geregistreerde para classificatie
    para_classificatie = models.CharField(max_length=30, blank=True)

    # mag gebruik maken van NHB faciliteiten?
    is_actief_lid = models.BooleanField(default=True)   # False = niet meer in import dataset

    # datum van lidmaatschap NHB
    sinds_datum = models.DateField(validators=[validate_sinds_datum])

    # lid bij vereniging
    bij_vereniging = models.ForeignKey(
                                NhbVereniging,
                                on_delete=models.PROTECT,
                                blank=True,  # allow access input in form
                                null=True)   # allow NULL relation in database

    # indien CRM aangeeft dat lid uitgeschreven is bij vereniging, toch op die vereniging
    # houden tot het einde van het jaar zodat de diensten (waarvoor betaald is) nog gebruikt kunnen worden.
    # dit voorkomt een gat bij overschrijvingen.
    lid_tot_einde_jaar = models.PositiveSmallIntegerField(default=0)

    # koppeling met een account (indien aangemaakt)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # selectie in de admin interface gaat op deze string, dus lid_nr eerst
        return '%s %s %s [%s, %s]' % (
            self.lid_nr, self.voornaam, self.achternaam, self.geslacht, self.geboorte_datum.year)

    def clean(self):
        """ controleer of alle velden een redelijke combinatie zijn
            wordt alleen aangeroepen om de input op een formulier te checken
            raises ValidationError als er problemen gevonden zijn
        """
        # sinds_datum moet 5 jaar ná het geboortejaar liggen
        if self.sinds_datum.year - self.geboorte_datum.year < 5:
            raise ValidationError('datum van lidmaatschap moet minimaal 5 jaar na geboortejaar zijn')

    def bereken_wedstrijdleeftijd(self, jaar):
        """ Bereken de wedstrijdleeftijd voor dit lid in het opgegeven jaar
            De wedstrijdleeftijd is de leeftijd die je bereikt in dat jaar
        """
        # voorbeeld: geboren 2001, huidig jaar = 2019 --> leeftijd 18 wordt bereikt
        return jaar - self.geboorte_datum.year

    def volledige_naam(self):
        return self.voornaam + " " + self.achternaam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = 'Sporter'

    objects = models.Manager()      # for the editor only


class Secretaris(models.Model):

    """ de secretaris van een vereniging """

    # deze constructie voorkomt een circulaire dependency

    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.CASCADE)

    sporter = models.ForeignKey(Sporter, on_delete=models.SET_NULL, null=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Secretaris Vereniging"

    def __str__(self):
        return "[%s] %s: %s" % (self.vereniging.ver_nr, self.vereniging.naam, self.sporter)


class Speelsterkte(models.Model):
    """ Deze tabel houdt de behaalde spelden/veren/schilden bij """

    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    datum = models.DateField()

    # beschrijving van de specifieke prestatiespeld (WA: 'award'): "Recurve 1000" of "NHB Graadspelden Schutter"
    beschrijving = models.CharField(max_length=50)

    # beschrijving van de discipline, zoals "Recurve" en "Compound"
    # maar ook "World Archery Target Awards" en "NHB tussenspelden"
    discipline = models.CharField(max_length=50)

    # Senior / Master / Cadet
    # sommige spelden zijn apart te behalen in verschillende categorieën
    category = models.CharField(max_length=50)

    # sorteer volgorde (lager = eerder tonen)
    volgorde = models.PositiveSmallIntegerField()

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Speelsterkte"

    def __str__(self):
        return "[%s] %s - %s - %s - %s (%s) " % (self.datum, self.sporter.volledige_naam(),
                                                 self.category, self.discipline, self.beschrijving, self.volgorde)


class SporterVoorkeuren(models.Model):
    """ Globale voorkeuren voor een sporter, onafhankelijk van zijn boog """

    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # (opt-in) voorkeur voor eigen blazoen: Dutch Target (Recurve) of 60cm 4spot (Compound)
    voorkeur_eigen_blazoen = models.BooleanField(default=False)

    # (opt-out) wel/niet aanbieden om mee te doen met de competitie
    voorkeur_meedoen_competitie = models.BooleanField(default=True)

    # sporters met para-classificatie mogen een opmerking toevoegen voor de wedstrijdleiding
    opmerking_para_sporter = models.CharField(max_length=256, default='')

    # (opt-out) voorkeur voor wedstrijden van specifieke disciplines
    voorkeur_discipline_25m1pijl = models.BooleanField(default=True)
    voorkeur_discipline_outdoor = models.BooleanField(default=True)
    voorkeur_discipline_indoor = models.BooleanField(default=True)      # Indoor = 18m/25m 3pijl
    voorkeur_discipline_clout = models.BooleanField(default=True)
    voorkeur_discipline_veld = models.BooleanField(default=True)
    voorkeur_discipline_run = models.BooleanField(default=True)
    voorkeur_discipline_3d = models.BooleanField(default=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Sporter voorkeuren"

    def __str__(self):
        return "%s" % self.sporter.lid_nr

    objects = models.Manager()      # for the editor only


class SporterBoog(models.Model):
    """ Sporter met een specifiek type boog en zijn voorkeuren
        voor elk type boog waar de sporter interesse in heeft is er een record
    """
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE, null=True)

    # het type boog waar dit record over gaat
    boogtype = models.ForeignKey(BoogType, on_delete=models.CASCADE)

    # voorkeuren van de sporter: alleen interesse, of ook actief schieten?
    heeft_interesse = models.BooleanField(default=True)
    voor_wedstrijd = models.BooleanField(default=False)

    # aanvangsgemiddelde is opgeslagen in een Score en ScoreHist record

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SporterBoog"
        verbose_name_plural = "SporterBoog"

    def __str__(self):
        # voorkom exceptie als nhblid op None staat
        if self.sporter:
            return "%s - %s" % (self.sporter.lid_nr, self.boogtype.beschrijving)
        else:
            # komt voor als we een fake ScoreHist record aanmaken om de background task te kietelen
            return "sporter? - %s" % self.boogtype.beschrijving

    objects = models.Manager()      # for the editor only


# end of file
