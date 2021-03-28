# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.conf import settings
from Account.models import Account
from BasisTypen.models import GESLACHT
import datetime


# global
maximum_geboortejaar = datetime.datetime.now().year - settings.MINIMUM_LEEFTIJD_LID

GEBRUIK = [('18', 'Indoor'),
           ('25', '25m 1pijl')]

GEBRUIK2STR = {'18': 'Indoor',
               '25': '25m 1pijl'}


class NhbRayon(models.Model):
    """ Tabel waarin de Rayon definities """

    # 1-digit nummer van dit rayon
    rayon_nr = models.PositiveIntegerField(primary_key=True)

    # korte naam van het rayon (Rayon 1)
    naam = models.CharField(max_length=20)      # Rayon 3

    # beschrijving van het gebied dat dit rayon dekt
    geografisch_gebied = models.CharField(max_length=50)        # FUTURE: verwijderen

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # geografisch gebied klopt niet helemaal en wordt nu niet meer getoond
        # return self.naam + ' ' + self.geografisch_gebied
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb rayon"
        verbose_name_plural = "Nhb rayons"

    objects = models.Manager()      # for the editor only


class NhbRegio(models.Model):
    """ Tabel waarin de Regio definities """

    # 3-cijferige NHB nummer van deze regio
    regio_nr = models.PositiveIntegerField(primary_key=True)

    # beschrijving van de regio
    naam = models.CharField(max_length=50)

    # rayon waar deze regio bij hoort
    rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT)

    # is dit een administratieve regio die niet mee doet voor de wedstrijden / competities?
    is_administratief = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return self.naam

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb regio"
        verbose_name_plural = "Nhb regios"

    objects = models.Manager()      # for the source code editor only


class NhbCluster(models.Model):
    """ Tabel waarin de definitie van een cluster staat """

    # regio waar dit cluster bij hoort
    regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)

    # letter voor unieke identificatie van het cluster
    letter = models.CharField(max_length=1, default='x')

    # beschrijving het cluster
    naam = models.CharField(max_length=50, default='', blank=True)

    # aparte clusters voor 18m en 25m
    gebruik = models.CharField(max_length=2, choices=GEBRUIK)

    def cluster_code(self):
        return "%s%s" % (self.regio.regio_nr, self.letter)

    def cluster_code_str(self):
        msg = "%s voor " % self.cluster_code()
        try:
            msg += GEBRUIK2STR[self.gebruik]
        except KeyError:
            msg = "?"
        return msg

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = self.cluster_code_str()
        if self.naam:
            msg += " (%s)" % self.naam
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb cluster"
        verbose_name_plural = "Nhb clusters"

        # zorg dat elk cluster uniek is
        unique_together = ('regio', 'letter')

    objects = models.Manager()      # for the source code editor only


class NhbVereniging(models.Model):
    """ Tabel waarin gegevens van de Verenigingen van de NHB staan """

    # 4-cijferige nummer van de vereniging
    ver_nr = models.PositiveIntegerField(primary_key=True)

    # naam van de vereniging
    naam = models.CharField(max_length=200)

    # locatie van het doel van de vereniging
    plaats = models.CharField(max_length=100, blank=True)

    contact_email = models.CharField(max_length=150, blank=True)    # FUTURE: not used, can be removed

    # de regio waarin de vereniging zit
    regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT)

    # de optionele clusters waar deze vereniging bij hoort
    clusters = models.ManyToManyField(NhbCluster,
                                      blank=True)   # mag leeg zijn / gemaakt worden

    # wie is de secretaris van de vereniging
    secretaris_lid = models.ForeignKey('NhbLid', on_delete=models.SET_NULL,
                                       blank=True,  # allow access input in form
                                       null=True)   # allow NULL relation in database

    # er is een vereniging voor persoonlijk lidmaatschap
    # deze leden mogen geen wedstrijden schieten
    geen_wedstrijden = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        # selectie in de admin interface gaat op deze string, dus nhb_nr eerst
        return "[%s] %s" % (self.ver_nr, self.naam)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Nhb vereniging"
        verbose_name_plural = "Nhb verenigingen"

    objects = models.Manager()      # for the editor only


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
    """ Tabel om gegevens van een lid van de NHB bij te houden """

    # het unieke NHB nummer
    nhb_nr = models.PositiveIntegerField(primary_key=True)

    # volledige naam
    # let op: voornaam kan ook een afkorting zijn
    voornaam = models.CharField(max_length=100)
    achternaam = models.CharField(max_length=100)

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
        verbose_name = 'Nhb lid'
        verbose_name_plural = 'Nhb leden'

    objects = models.Manager()      # for the editor only


# end of file
