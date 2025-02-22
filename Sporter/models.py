# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from Account.models import Account
from BasisTypen.definities import (GESLACHT_MVX, GESLACHT_MV, GESLACHT_MAN, ORGANISATIE_IFAA,
                                   SCHEIDS_NIET, SCHEIDS_CHOICES)
from BasisTypen.models import BoogType
# mag niet afhankelijk zijn van Competitie
from Vereniging.models import Vereniging
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
        datum: moet datetime.date() zijn, dus is de combinatie jaar/maand/dag al gecontroleerd
               mag niet in de toekomst liggen
               moet 5 jaar ná het geboortejaar liggen --> geen toegang tot deze info hier
        raises ValidationError als de datum niet goed is
    """
    now = datetime.datetime.now()
    date_now = datetime.date(year=now.year, month=now.month, day=now.day)
    if datum > date_now:
        raise ValidationError('datum van lidmaatschap mag niet in de toekomst liggen')


class Sporter(models.Model):

    """ Tabel om details van een lid bij te houden, zoals overgenomen uit het CRM """

    # het unieke lidmaatschapsnummer
    lid_nr = models.PositiveIntegerField(primary_key=True)

    # World Archery nummer van deze sporter
    wa_id = models.CharField(max_length=8, default='', blank=True)

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

    # officieel geregistreerde para classificatie
    para_classificatie = models.CharField(max_length=30, blank=True)

    # datum van lidmaatschap
    sinds_datum = models.DateField(validators=[validate_sinds_datum])

    # mag gebruik maken van faciliteiten?
    is_actief_lid = models.BooleanField(default=True)   # False = niet meer in import dataset

    # lid bij vereniging
    bij_vereniging = models.ForeignKey(
                                Vereniging,
                                on_delete=models.PROTECT,
                                blank=True,  # allow access input in form
                                null=True)   # allow NULL relation in database

    # indien CRM aangeeft dat lid uitgeschreven is bij vereniging, toch op die vereniging
    # houden tot het einde van het jaar zodat de diensten (waarvoor betaald is) nog gebruikt kunnen worden.
    # dit voorkomt een gat bij overschrijvingen.
    lid_tot_einde_jaar = models.PositiveSmallIntegerField(default=0)

    # koppeling met een account (indien aangemaakt)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)

    # het postadres van deze sporter
    postadres_1 = models.CharField(max_length=100, default='', blank=True)
    postadres_2 = models.CharField(max_length=100, default='', blank=True)
    postadres_3 = models.CharField(max_length=100, default='', blank=True)

    # code waarmee leden die op hetzelfde adres wonen gevonden kunnen worden
    # let op: niet gebruiken als deze leeg is
    adres_code = models.CharField(max_length=30, default='', blank=True)

    # postadres vertaald naar lat/lon
    adres_lat = models.CharField(max_length=10, default='', blank=True)    # 51.5037503
    adres_lon = models.CharField(max_length=10, default='', blank=True)    # 5.3670660

    # om overleden leden eenvoudig speciaal te kunnen behandelen hebben we dit veld als filter optie
    is_overleden = models.BooleanField(default=False)

    # is dit een erelid (voor vermelding op de bondspas)
    is_erelid = models.BooleanField(default=False)

    # is dit een gast-account (minder minder mogelijkheden)?
    is_gast = models.BooleanField(default=False)

    # scheidsrechter status van deze sporter (opleiding gedaan en onderhouden)
    scheids = models.CharField(max_length=2, choices=SCHEIDS_CHOICES, default=SCHEIDS_NIET, blank=True)

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

    def bereken_leeftijd(self):
        """ bereken de leeftijd van de sporter op dit moment """
        now = timezone.localtime(timezone.now())

        # ga uit van de te bereiken leeftijd in dit jaar
        leeftijd = now.year - self.geboorte_datum.year

        # voor of na de verjaardag?
        tup1 = (now.month, now.day)
        tup2 = (self.geboorte_datum.month, self.geboorte_datum.day)
        if tup1 < tup2:
            # nog voor de verjaardag
            leeftijd -= 1

        return leeftijd

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


class Speelsterkte(models.Model):
    """ Deze tabel houdt de behaalde spelden/veren/schilden bij """

    # TODO: verplaats naar Spelden + koppel aan echte Speld records (=reduceer duplicatie)

    # welke sporter heeft deze speelsterkte behaald?
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    datum = models.DateField()

    # beschrijving van de specifieke prestatiespeld (WA: 'award'): "Recurve 1000" of "NHB Graadspelden Schutter"
    beschrijving = models.CharField(max_length=50)

    # beschrijving van de discipline, zoals "Recurve" en "Compound"
    # maar ook "World Archery Target Awards" en "KHSN tussenspelden"
    discipline = models.CharField(max_length=50)

    # Senior / Master / Cadet
    # sommige spelden zijn apart te behalen in verschillende categorieën
    category = models.CharField(max_length=50)

    # afkorting om te tonen op de bondspas
    pas_code = models.CharField(max_length=10, default='', blank=True)

    # sorteervolgorde (lager = eerder tonen)
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

    # notificatie aan de wedstrijdleiding: sporter gebruikt voorwerpen die op de schietlijn blijven staan
    # (hierdoor kunnen er minder sporters op zijn baan)
    para_voorwerpen = models.BooleanField(default=False)

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

    # opt-in voor het delen van contactgegevens met het korps SR
    scheids_opt_in_korps_tel_nr = models.BooleanField(default=False)
    scheids_opt_in_korps_email = models.BooleanField(default=False)

    # opt-in voor het delen van contactgegevens met de organiserende vereniging
    # van een wedstrijd waar de SR voor geselecteerd is
    scheids_opt_in_ver_tel_nr = models.BooleanField(default=False)
    scheids_opt_in_ver_email = models.BooleanField(default=False)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name_plural = verbose_name = "Sporter voorkeuren"

    def __str__(self):
        return "%s" % self.sporter.lid_nr

    objects = models.Manager()      # for the editor only


class SporterBoog(models.Model):
    """ Sporter met een specifiek type boog en zijn voorkeuren
        er is een record voor elk type boog
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

        unique_together = ('sporter', 'boogtype')

        indexes = [
            # ondersteuning voor filteren op voor_wedstrijd=True
            models.Index(fields=['voor_wedstrijd'])
        ]

    def __str__(self):
        # voorkom exceptie als sporter op None staat
        if self.sporter:
            return "%s - %s" % (self.sporter.lid_nr, self.boogtype.beschrijving)
        else:
            # komt voor als we een fake ScoreHist record aanmaken om de background task te kietelen
            return "sporter? - %s" % self.boogtype.beschrijving

    objects = models.Manager()      # for the editor only


def get_sporter(account: Account) -> Sporter:
    """ Centrale methode om de bij een Account behorende Sporter te vinden
        Kan None terug geven, maar dat zou in de praktijk niet voor moeten komen
    """
    return account.sporter_set.select_related('bij_vereniging__regio').first()          # can return None!


# end of file
