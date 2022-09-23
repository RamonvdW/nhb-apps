# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from Account.models import Account
from BasisTypen.models import BoogType, GESLACHT_MVX, GESLACHT_MV, GESLACHT_MAN, GESLACHT_ANDERS, ORGANISATIE_IFAA
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

    # het e-mailadres waarop dit lid te bereiken is
    email = models.CharField(max_length=150)

    # het telefoonnummer waarop dit lid te bereiken is
    # komt uit CRM: mobiel (indien aanwezig), anders vaste nummer (indien aanwezig)
    telefoon = models.CharField(max_length=25, default='', blank=True)

    # geboortedatum van de sporter
    geboorte_datum = models.DateField(validators=[validate_geboorte_datum])

    # geboorteplaats van de sporter
    # alleen nodig voor op het certificaat van een genoten opleiding
    geboorteplaats = models.CharField(max_length=100, default='', blank=True)

    # geslacht (M/V/X)
    geslacht = models.CharField(max_length=1, choices=GESLACHT_MVX)

    # code waarmee leden die op hetzelfde adres wonen gevonden kunnen worden
    # let op: niet gebruiken als deze leeg is
    adres_code = models.CharField(max_length=30, default='', blank=True)

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

    def bereken_wedstrijdleeftijd_wa(self, jaar):
        """ Bereken de wedstrijdleeftijd voor dit lid volgens de WA regels
            De wedstrijdleeftijd is de leeftijd die je bereikt in het opgegeven jaar
        """
        # voorbeeld: geboren 2001, huidig jaar = 2019 --> leeftijd 18 wordt bereikt
        return jaar - self.geboorte_datum.year

    def bereken_wedstrijdleeftijd_ifaa(self, datum_eerste_wedstrijddag):
        """ Bereken de wedstrijdleeftijd voor dit lid volgens de IFAA regels
            De wedstrijdleeftijd is je leeftijd op de eerste dag van de wedstrijd
        """
        # voorbeeld: geboren 2001-10-08, datum_eerste_wedstrijddag = 2019-10-07 --> wedstrijdleeftijd is 17
        # voorbeeld: geboren 2001-10-08, datum_eerste_wedstrijddag = 2019-10-08 --> wedstrijdleeftijd is 18

        # ga uit van de te bereiken leeftijd dit jaar
        wedstrijdleeftijd = datum_eerste_wedstrijddag.year - self.geboorte_datum.year

        # vergelijk de wedstrijd datum en de verjaardag
        tup1 = (datum_eerste_wedstrijddag.month, datum_eerste_wedstrijddag.day)
        tup2 = (self.geboorte_datum.month, self.geboorte_datum.day)
        if tup1 < tup2:
            # nog voor de verjaardag
            wedstrijdleeftijd -= 1

        return wedstrijdleeftijd

    def bereken_wedstrijdleeftijd(self, datum_eerste_wedstrijd, organisatie):
        if organisatie == ORGANISATIE_IFAA:
            wedstrijdleeftijd = self.bereken_wedstrijdleeftijd_ifaa(datum_eerste_wedstrijd)
        else:
            wedstrijdleeftijd = self.bereken_wedstrijdleeftijd_wa(datum_eerste_wedstrijd.year)
        return wedstrijdleeftijd

    def volledige_naam(self):
        return self.voornaam + " " + self.achternaam

    def lid_nr_en_volledige_naam(self):
        return "[%s] %s" % (self.lid_nr, self.voornaam + " " + self.achternaam)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = 'Sporter'

    objects = models.Manager()      # for the editor only


class Secretaris(models.Model):

    """ de secretaris van een vereniging """

    # deze constructie voorkomt een circulaire dependency

    # FUTURE: dit record is dupe met Functie SEC? (gekoppeld aan Account)

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

    # open notitie aan de wedstrijdleiding
    opmerking_para_sporter = models.CharField(max_length=256, default='', blank=True)

    # notificatie aan de wedstrijdleiding: sporter gebruikt een rolstoel
    # (hierdoor kunnen er minder sporters op zijn baan)
    para_met_rolstoel = models.BooleanField(default=False)      # TODO: para_voorwerpen (die blijven staan op de schietlijn)

    # (opt-out) voorkeur voor wedstrijden van specifieke disciplines
    voorkeur_discipline_25m1pijl = models.BooleanField(default=True)
    voorkeur_discipline_outdoor = models.BooleanField(default=True)
    voorkeur_discipline_indoor = models.BooleanField(default=True)      # Indoor = 18m/25m 3pijl
    voorkeur_discipline_clout = models.BooleanField(default=True)
    voorkeur_discipline_veld = models.BooleanField(default=True)
    voorkeur_discipline_run = models.BooleanField(default=True)
    voorkeur_discipline_3d = models.BooleanField(default=True)

    # het geslacht voor wedstrijden
    # alleen te kiezen voor sporters met geslacht='X'
    # automatisch gelijk gesteld aan het geslacht voor sporters met geslacht='M' of 'V'
    wedstrijd_geslacht_gekozen = models.BooleanField(default=True)
    wedstrijd_geslacht = models.CharField(max_length=1, choices=GESLACHT_MV, default=GESLACHT_MAN)

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

    # aanvangsgemiddelde is opgeslagen in een Aanvangsgemiddelde en AanvangsgemiddeldeHist record

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SporterBoog"
        verbose_name_plural = "SporterBoog"

        ordering = ['sporter__lid_nr', 'boogtype__volgorde']

        indexes = [
            # ondersteuning voor filteren op voor_wedstrijd=True
            models.Index(fields=['voor_wedstrijd'])
        ]

    def __str__(self):
        # voorkom exceptie als nhblid op None staat
        if self.sporter:
            return "%s - %s" % (self.sporter.lid_nr, self.boogtype.beschrijving)
        else:
            # komt voor als we een fake ScoreHist record aanmaken om de background task te kietelen
            return "sporter? - %s" % self.boogtype.beschrijving

    objects = models.Manager()      # for the editor only


def get_sporter_voorkeuren(sporter):
    """ zoek het SporterVoorkeuren object erbij, of maak een nieuwe aan
    """

    voorkeuren, was_created = SporterVoorkeuren.objects.get_or_create(sporter=sporter)
    if was_created:
        # default voor wedstrijd_geslacht_gekozen = True
        if sporter.geslacht != GESLACHT_ANDERS:
            if sporter.geslacht != voorkeuren.wedstrijd_geslacht:  # default is Man
                voorkeuren.wedstrijd_geslacht = sporter.geslacht
                voorkeuren.save(update_fields=['wedstrijd_geslacht'])
        else:
            voorkeuren.wedstrijd_geslacht_gekozen = False  # laat de sporter kiezen
            voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen'])

    return voorkeuren


def get_sporter_voorkeuren_wedstrijdbogen(lid_nr):
    """ retourneer de sporter, voorkeuren en pk's van de boogtypen geselecteerd voor wedstrijden """
    pks = list()
    sporter = None
    voorkeuren = None
    try:
        sporter = (Sporter
                   .objects
                   .prefetch_related('sportervoorkeuren_set')
                   .get(lid_nr=lid_nr))
    except Sporter.DoesNotExist:
        pass
    else:
        voorkeuren = get_sporter_voorkeuren(sporter)

        for sporterboog in (SporterBoog
                            .objects
                            .select_related('boogtype')
                            .filter(sporter__lid_nr=lid_nr,
                                    voor_wedstrijd=True)):
            pks.append(sporterboog.boogtype.id)
        # for

    return sporter, voorkeuren, pks


# end of file
