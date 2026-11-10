# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from Account.models import Account
from BasisTypen.definities import GESLACHT_MVX, ORGANISATIE_IFAA, SCHEIDS_NIET, SCHEIDS_CHOICES
from Vereniging.models import Vereniging
from .validators import validate_geboorte_datum, validate_sinds_datum


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
    email = models.CharField(max_length=150, blank=True)

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
            raise ValidationError(
                        {'geboorte_datum': 'datum van lidmaatschap moet minimaal 5 jaar na geboortejaar zijn'})

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


# end of file
