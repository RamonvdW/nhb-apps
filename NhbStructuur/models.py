# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import datetime


# global
maximum_geboortejaar = datetime.datetime.now().year - settings.MINIMUM_LEEFTIJD_LID


class NhbRayon(models.Model):
    """Tabel waarin de Rayon definities van de NHB staan"""
    rayon_nr = models.PositiveIntegerField(primary_key=True)
    naam = models.CharField(max_length=20)      # Rayon 3
    geografisch_gebied = models.CharField(max_length=50)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb rayon"
        verbose_name_plural = "Nhb rayons"


class NhbRegio(models.Model):
    """Tabel waarin de Regio definities van de NHB staan"""
    regio_nr = models.PositiveIntegerField(primary_key=True)
    naam = models.CharField(max_length=20)      # Regio 111
    rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb regio"
        verbose_name_plural = "Nhb regios"


class NhbVereniging(models.Model):
    """Tabel waarin gegevens van de Verenigingen van de NHB staan"""
    nhb_nr = models.PositiveIntegerField(primary_key=True)
    naam = models.CharField(max_length=200)
    regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)
    secretaris_lid = models.ForeignKey('NhbLid', on_delete=models.PROTECT,
                                       blank=True,  # allow access input in form
                                       null=True)   # allow NULL relation in database

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # selectie in de admin interface gaat op deze string, dus nhb_nr eerst
        return "%s %s" % (self.nhb_nr, self.naam)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb vereniging"
        verbose_name_plural = "Nhb verenigingen"


def validate_geboorte_datum(datum):
    """ controleer of het geboortejaar redelijk is
        wordt alleen aangeroepen om de input op een formulier te checken
        jaar: Moet tussen 1900 en 5 jaar geleden liggen (jongste lid = 5 jaar)
        raises ValidationError als het jaartal niet goed is
    """
    global maximum_geboortejaar
    if datum.year < 1900 or datum.year > maximum_geboortejaar:
        raise ValidationError(
                'geboortejaar %(jaar)s is niet valide (min=1900, max=%(max)s)',
                params={'jaar': datum.year,
                        'max': maximum_geboortejaar}
                )


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


class NhbLid(models.Model):
    """Tabel om gegevens van een lid van de NHB bij te houden"""

    GESLACHT = [('M', 'Man'), ('V', 'Vrouw')]

    nhb_nr = models.PositiveIntegerField(primary_key=True)
    voornaam = models.CharField(max_length=100)
    achternaam = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    geboorte_datum = models.DateField(validators=[validate_geboorte_datum,])
    postcode = models.CharField(max_length=10)
    huisnummer = models.CharField(max_length=10)
    geslacht = models.CharField(max_length=1, choices=GESLACHT)
    para_classificatie = models.CharField(max_length=30, blank=True)
    is_actief_lid = models.BooleanField(default=True)   # False = niet meer in import dataset
    sinds_datum = models.DateField(validators=[validate_sinds_datum,])
    bij_vereniging = models.ForeignKey(
                                NhbVereniging,
                                on_delete=models.PROTECT,
                                blank=True,  # allow access input in form
                                null=True)  # allow NULL relation in database

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # selectie in de admin interface gaat op deze string, dus nhb_nr eerst
        return '%s %s %s [%s, %s]' % (self.nhb_nr, self.voornaam, self.achternaam, self.geslacht, self.geboorte_datum.year)

    def clean(self):
        """ controleer of alle velden een redelijke combinatie zijn
            wordt alleen aangeroepen om de input op een formulier te checken
            raises ValidationError als er problemen gevonden zijn
        """
        # sinds_datum moet 5 jaar ná het geboortejaar liggen
        if self.sinds_datum.year - self.geboorte_datum.year < 5:
            raise ValidationError('datum van lidmaatschap moet minimaal 5 jaar na geboortejaar zijn')

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = 'Nhb lid'
        verbose_name_plural = 'Nhb leden'


# end of file
