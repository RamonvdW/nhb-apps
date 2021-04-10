# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import IndivWedstrijdklasse, TeamWedstrijdklasse
from NhbStructuur.models import NhbVereniging
from Score.models import Score


# accommodatie type
BAAN_TYPE = (('X', 'Onbekend'),
             ('O', 'Volledig overdekte binnenbaan'),
             ('H', 'Binnen-buiten schieten'),
             ('B', 'Buitenbaan'),
             ('E', 'Extern'))

BAANTYPE2STR = {
    'X': 'Onbekend',
    'O': 'Volledig overdekte binnenbaan',
    'H': 'Binnen-buiten schieten',
    'B': 'Buitenbaan',                  # buitenbaan bij de eigen accommodatie
    'E': 'Extern'                       # externe locatie
}


class WedstrijdLocatie(models.Model):
    """ Een locatie waarop een wedstrijd gehouden kan worden.

        Naast de accommodatie van de vereniging (binnen / buiten) ook externe locaties
        waar de vereniging een wedstrijd kan organiseren.
    """

    # naam waaronder deze locatie getoond wordt
    naam = models.CharField(max_length=50, blank=True)

    # zichtbaar maakt het mogelijk een baan uit het systeem te halen
    # zonder deze helemaal te verwijderen
    zichtbaar = models.BooleanField(default=True)

    # verenigingen die deze locatie gebruiken (kan gedeeld doel zijn)
    verenigingen = models.ManyToManyField(NhbVereniging,
                                          blank=True)       # mag leeg zijn / gemaakt worden

    # eigen accommodatie baan of extern
    baan_type = models.CharField(max_length=1, choices=BAAN_TYPE, default='X')

    # welke disciplines kunnen hier georganiseerd worden?
    discipline_25m1pijl = models.BooleanField(default=False)
    discipline_outdoor = models.BooleanField(default=False)
    discipline_indoor = models.BooleanField(default=False)      # Indoor = 18m/25m 3pijl
    discipline_clout = models.BooleanField(default=False)
    discipline_veld = models.BooleanField(default=False)
    discipline_run = models.BooleanField(default=False)
    discipline_3d = models.BooleanField(default=False)
    # discipline_flight (zo ver mogelijk schieten)
    # discipline_ski

    # alleen voor indoor: beschikbare banen
    banen_18m = models.PositiveSmallIntegerField(default=0)
    banen_25m = models.PositiveSmallIntegerField(default=0)
    max_dt_per_baan = models.PositiveSmallIntegerField(default=4)

    # alleen voor discipline_outdoor baan
    buiten_banen = models.PositiveSmallIntegerField(default=0)
    buiten_max_afstand = models.PositiveSmallIntegerField(default=0)

    # adresgegevens van de locatie
    adres = models.TextField(max_length=256, blank=True)

    # handmatig ingevoerd of uit de CRM (=bevroren)
    adres_uit_crm = models.BooleanField(default=False)

    # vrije notitiegegevens voor zaken als "verbouwing tot", etc.
    notities = models.TextField(max_length=1024, blank=True)

    def disciplines_str(self):
        disc = list()
        if self.discipline_25m1pijl:
            disc.append('25m1pijl')
        if self.discipline_outdoor:
            disc.append('outdoor')
        if self.discipline_indoor:
            disc.append('indoor')
        if self.discipline_clout:
            disc.append('clout')
        if self.discipline_veld:
            disc.append('veld')
        if self.discipline_run:
            disc.append('run')
        if self.discipline_3d:
            disc.append('3d')
        return ", ".join(disc)

    def __str__(self):
        if not self.zichtbaar:
            msg = "(hidden) "
        else:
            msg = ""

        msg += "{%s} " % BAANTYPE2STR[self.baan_type]

        msg += "[%s] " % self.disciplines_str()

        msg += self.adres.replace('\n', ', ')
        # kost te veel database toegangen in admin interface
        # msg += " (%s verenigingen)" % self.verenigingen.count()
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijd locatie"
        verbose_name_plural = "Wedstrijd locaties"


class CompetitieWedstrijdUitslag(models.Model):

    # de maximale score die gehaald (en ingevoerd) mag worden
    # dit afhankelijk van het type wedstrijd
    max_score = models.PositiveSmallIntegerField()      # max = 32767

    # 18, 25, 70, etc.
    afstand_meter = models.PositiveSmallIntegerField()

    # scores bevat SchutterBoog en komt met ScoreHist
    scores = models.ManyToManyField(Score, blank=True)  # mag leeg zijn / gemaakt worden

    # False = uitslag mag door WL ingevoerd worden
    # True  = uitslag is gecontroleerd en mag niet meer aangepast worden
    is_bevroren = models.BooleanField(default=False)

    def __str__(self):
        msg = "(%s) afstand %s, max score %s" % (self.pk, self.afstand_meter, self.max_score)
        if self.is_bevroren:
            msg += " (bevroren)"
        return msg

    # hier houden we geen klassen bij - het is geen inschrijflijst
    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Competitie Wedstrijd Uitslag"
        verbose_name_plural = "Competitie Wedstrijd Uitslagen"


class Wedstrijd(models.Model):
    """ Wedstrijd is de kleinste planbare eenheid """

    # beschrijving
    beschrijving = models.CharField(max_length=100, blank=True)

    # plan status
    preliminair = models.BooleanField(default=True)

    # organiserende vereniging
    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)   # mag later ingevuld worden

    # waar
    locatie = models.ForeignKey(WedstrijdLocatie, on_delete=models.PROTECT,
                                blank=True, null=True)      # mag later ingevuld worden

    # datum en tijdstippen
    datum_wanneer = models.DateField()
    tijd_begin_aanmelden = models.TimeField()
    tijd_begin_wedstrijd = models.TimeField()
    tijd_einde_wedstrijd = models.TimeField()

    # wedstrijdklassen individueel en teams
    indiv_klassen = models.ManyToManyField(IndivWedstrijdklasse,
                                           blank=True)  # mag leeg zijn / gemaakt worden

    team_klassen = models.ManyToManyField(TeamWedstrijdklasse,
                                          blank=True)  # mag leeg zijn / gemaakt worden

    uitslag = models.ForeignKey(CompetitieWedstrijdUitslag, on_delete=models.PROTECT,
                                blank=True, null=True)

    def __str__(self):
        extra = ""
        if self.vereniging:
            extra = " bij %s" % self.vereniging
        return "(%s) %s %s%s: %s" % (self.pk, self.datum_wanneer, self.tijd_begin_wedstrijd, extra, self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijd"
        verbose_name_plural = "Wedstrijden"


class WedstrijdenPlan(models.Model):
    """ Planning voor een serie wedstrijden, zoals de competitierondes """

    # lijst van wedstrijden
    wedstrijden = models.ManyToManyField(Wedstrijd,
                                         blank=True)  # mag leeg zijn / gemaakt worden

    # de hiaat vlag geeft snel weer of er een probleem in de planning zit
    bevat_hiaat = models.BooleanField(default=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijdenplan"
        verbose_name_plural = "Wedstrijdenplannen"


# end of file
