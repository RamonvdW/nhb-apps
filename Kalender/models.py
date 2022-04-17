# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.models import (BoogType, KalenderWedstrijdklasse,
                               ORGANISATIES, ORGANISATIE_WA, ORGANISATIE_IFAA, ORGANISATIE_NHB)
from NhbStructuur.models import NhbVereniging
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.models import WedstrijdLocatie
from decimal import Decimal


WEDSTRIJD_DISCIPLINE_OUTDOOR = 'OD'
WEDSTRIJD_DISCIPLINE_INDOOR = 'IN'
WEDSTRIJD_DISCIPLINE_25M1P = '25'
WEDSTRIJD_DISCIPLINE_CLOUT = 'CL'
WEDSTRIJD_DISCIPLINE_VELD = 'VE'
WEDSTRIJD_DISCIPLINE_RUN = 'RA'
WEDSTRIJD_DISCIPLINE_3D = '3D'

WEDSTRIJD_DISCIPLINES = (
    (WEDSTRIJD_DISCIPLINE_OUTDOOR, 'Outdoor'),
    (WEDSTRIJD_DISCIPLINE_INDOOR, 'Indoor'),               # Indoor = 18m/25m 3pijl
    (WEDSTRIJD_DISCIPLINE_25M1P, '25m 1pijl'),
    (WEDSTRIJD_DISCIPLINE_CLOUT, 'Clout'),
    (WEDSTRIJD_DISCIPLINE_VELD, 'Veld'),
    (WEDSTRIJD_DISCIPLINE_RUN, 'Run Archery'),
    (WEDSTRIJD_DISCIPLINE_3D, '3D')
)

# let op: dit is ook de volgorde waarin ze getoond worden
WEDSTRIJD_DISCIPLINE_TO_STR_WA = {
    WEDSTRIJD_DISCIPLINE_OUTDOOR: 'Outdoor',
    WEDSTRIJD_DISCIPLINE_INDOOR: 'Indoor',
    WEDSTRIJD_DISCIPLINE_VELD: 'Veld',
}

WEDSTRIJD_DISCIPLINE_TO_STR_NHB = {
    WEDSTRIJD_DISCIPLINE_OUTDOOR: 'Outdoor',
    WEDSTRIJD_DISCIPLINE_INDOOR: 'Indoor',
    WEDSTRIJD_DISCIPLINE_25M1P: '25m 1pijl',
    WEDSTRIJD_DISCIPLINE_CLOUT: 'Clout',
    WEDSTRIJD_DISCIPLINE_VELD: 'Veld',
    WEDSTRIJD_DISCIPLINE_RUN: 'Run Archery',
    WEDSTRIJD_DISCIPLINE_3D: '3D',
}

WEDSTRIJD_DISCIPLINE_TO_STR_IFAA = {
    WEDSTRIJD_DISCIPLINE_3D: '3D',
}

ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS = {
    ORGANISATIE_WA: WEDSTRIJD_DISCIPLINE_TO_STR_WA,
    ORGANISATIE_NHB: WEDSTRIJD_DISCIPLINE_TO_STR_NHB,
    ORGANISATIE_IFAA: WEDSTRIJD_DISCIPLINE_TO_STR_IFAA
}


WEDSTRIJD_STATUS_ONTWERP = 'O'
WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING = 'W'
WEDSTRIJD_STATUS_GEACCEPTEERD = 'A'
WEDSTRIJD_STATUS_GEANNULEERD = 'X'

WEDSTRIJD_STATUS = (
    (WEDSTRIJD_STATUS_ONTWERP, 'Ontwerp'),
    (WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING, 'Wacht op goedkeuring'),
    (WEDSTRIJD_STATUS_GEACCEPTEERD, 'Geaccepteerd'),
    (WEDSTRIJD_STATUS_GEANNULEERD, 'Geannuleerd')
)

WEDSTRIJD_STATUS_TO_STR = {
    WEDSTRIJD_STATUS_ONTWERP: 'Ontwerp',
    WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING: 'Wacht op goedkeuring',
    WEDSTRIJD_STATUS_GEACCEPTEERD: 'Geaccepteerd',
    WEDSTRIJD_STATUS_GEANNULEERD: 'Geannuleerd'
}

WEDSTRIJD_WA_STATUS_A = 'A'
WEDSTRIJD_WA_STATUS_B = 'B'

WEDSTRIJD_WA_STATUS = (
    (WEDSTRIJD_WA_STATUS_A, 'A-status'),
    (WEDSTRIJD_WA_STATUS_B, 'B-status')
)

WEDSTRIJD_WA_STATUS_TO_STR = {
    WEDSTRIJD_WA_STATUS_A: 'A-status',
    WEDSTRIJD_WA_STATUS_B: 'B-status'
}

WEDSTRIJD_DUUR_MAX_DAGEN = 5
WEDSTRIJD_DUUR_MAX_UREN = 5         # maximale keuze voor de duur van een sessie

WEDSTRIJD_BEGRENZING_LANDELIJK = 'L'
WEDSTRIJD_BEGRENZING_VERENIGING = 'V'
WEDSTRIJD_BEGRENZING_REGIO = 'G'
WEDSTRIJD_BEGRENZING_RAYON = 'Y'

WEDSTRIJD_BEGRENZING = (
    (WEDSTRIJD_BEGRENZING_LANDELIJK, 'Landelijk'),
    (WEDSTRIJD_BEGRENZING_RAYON, 'Rayon'),
    (WEDSTRIJD_BEGRENZING_REGIO, 'Regio'),
    (WEDSTRIJD_BEGRENZING_VERENIGING, 'Vereniging'),
)

WEDSTRIJD_BEGRENZING_TO_STR = {
    WEDSTRIJD_BEGRENZING_LANDELIJK: 'Alle sporters (landelijk)',
    WEDSTRIJD_BEGRENZING_RAYON: 'Sporters in het rayon',
    WEDSTRIJD_BEGRENZING_REGIO: 'Sporters in de regio',
    WEDSTRIJD_BEGRENZING_VERENIGING: 'Sporters van de organiserende vereniging',
}

WEDSTRIJD_ORGANISATIE_TO_STR = {
    ORGANISATIE_WA: 'WA',
    ORGANISATIE_NHB: 'NHB',
    ORGANISATIE_IFAA: 'IFAA'
}

INSCHRIJVING_STATUS_RESERVERING = 'R'
INSCHRIJVING_STATUS_DEFINITIEF = 'D'
INSCHRIJVING_STATUS_AFGEMELD = 'A'

INSCHRIJVING_STATUS_CHOICES = (
    (INSCHRIJVING_STATUS_RESERVERING, "Reservering"),
    (INSCHRIJVING_STATUS_DEFINITIEF, "Definitief"),
    (INSCHRIJVING_STATUS_AFGEMELD, "Afgemeld")
)

INSCHRIJVING_STATUS_TO_STR = {
    INSCHRIJVING_STATUS_RESERVERING: 'Reservering',
    INSCHRIJVING_STATUS_DEFINITIEF: 'Definitief',
    INSCHRIJVING_STATUS_AFGEMELD: 'Afgemeld',
}

KALENDER_MUTATIE_INSCHRIJVEN = 1
KALENDER_MUTATIE_AFMELDEN = 2
KALENDER_MUTATIE_KORTING = 3

KALENDER_MUTATIE_TO_STR = {
    KALENDER_MUTATIE_INSCHRIJVEN: "Inschrijven",
    KALENDER_MUTATIE_AFMELDEN: "Afmelden",
    KALENDER_MUTATIE_KORTING: "Korting",
}


KALENDER_KORTING_SPORTER = 's'
KALENDER_KORTING_VERENIGING = 'v'
KALENDER_KORTING_COMBI = 'c'

KALENDER_KORTING_SOORT_CHOICES = (
    (KALENDER_KORTING_SPORTER, 'Sporter'),
    (KALENDER_KORTING_VERENIGING, 'Vereniging'),
    (KALENDER_KORTING_COMBI, 'Combi')
)

KALENDER_KORTING_SOORT_TO_STR = {
    KALENDER_KORTING_SPORTER: 'Sporter',
    KALENDER_KORTING_VERENIGING: 'Vereniging',
    KALENDER_KORTING_COMBI: 'Combi'
}


class KalenderWedstrijdDeeluitslag(models.Model):
    """ Deel van de uitslag van een wedstrijd """

    # na verwijderen wordt deze vlag gezet, voor opruimen door achtergrondtaak
    buiten_gebruik = models.BooleanField(default=False)

    # naam van het uitslag-bestand (zonder pad)
    bestandsnaam = models.CharField(max_length=100, default='', blank=True)

    # wanneer toegevoegd?
    toegevoegd_op = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kalender wedstrijd deeluitslag"
        verbose_name_plural = "Kalender wedstrijd deeluitslagen"


class KalenderWedstrijdSessie(models.Model):
    """ Een sessie van een wedstrijd """

    # op welke datum is deze sessie?
    datum = models.DateField()

    # hoe laat is deze sessie, hoe laat moet je aanwezig zijn, de geschatte eindtijd
    tijd_begin = models.TimeField()
    tijd_einde = models.TimeField()

    # prijs
    prijs_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99

    # toegestane wedstrijdklassen
    wedstrijdklassen = models.ManyToManyField(KalenderWedstrijdklasse, blank=True)

    # maximum aantal deelnemers
    max_sporters = models.PositiveSmallIntegerField(default=1)

    # het aantal inschrijvingen: de som van reserveringen en betaalde deelnemers
    aantal_inschrijvingen = models.PositiveSmallIntegerField(default=0)

    # inschrijvingen: zie KalenderInschrijving

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        return "%s %s (%s)" % (self.datum, self.tijd_begin, self.max_sporters)

    class Meta:
        verbose_name = "Kalender wedstrijd sessie"
        verbose_name_plural = "Kalender wedstrijd sessies"


class KalenderWedstrijd(models.Model):

    """ Een wedstrijd voor op de wedstrijdkalender """

    # titel van de wedstrijd voor op de wedstrijdkalender
    titel = models.CharField(max_length=50, default='')

    # status van deze wedstrijd: ontwerp --> goedgekeurd --> geannuleerd
    status = models.CharField(max_length=1, choices=WEDSTRIJD_STATUS, default='O')

    # wanneer is de wedstrijd (kan meerdere dagen beslaan)
    datum_begin = models.DateField()
    datum_einde = models.DateField()

    # waar wordt de wedstrijd gehouden
    locatie = models.ForeignKey(WedstrijdLocatie, on_delete=models.PROTECT)

    # begrenzing
    begrenzing = models.CharField(max_length=1, default=WEDSTRIJD_BEGRENZING_LANDELIJK, choices=WEDSTRIJD_BEGRENZING)

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

    # welke discipline is dit? (indoor/outdoor/veld, etc.)
    discipline = models.CharField(max_length=2, choices=WEDSTRIJD_DISCIPLINES, default=WEDSTRIJD_DISCIPLINE_OUTDOOR)

    # wat de WA-status van deze wedstrijd (A of B)
    wa_status = models.CharField(max_length=1, default=WEDSTRIJD_WA_STATUS_B, choices=WEDSTRIJD_WA_STATUS)

    # contactgegevens van de organisatie
    organiserende_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT)
    contact_naam = models.CharField(max_length=50, default='', blank=True)
    contact_email = models.CharField(max_length=150, default='', blank=True)
    contact_website = models.CharField(max_length=100, default='', blank=True)
    contact_telefoon = models.CharField(max_length=50, default='', blank=True)

    # acceptatie voorwaarden WA A-status
    voorwaarden_a_status_acceptatie = models.BooleanField(default=False)
    voorwaarden_a_status_when = models.DateTimeField()
    voorwaarden_a_status_who = models.CharField(max_length=100, default='',          # [BondsNr] Volledige Naam
                                                blank=True)     # mag leeg zijn

    # wordt deze wedstrijd door de organiserende vereniging buiten deze website om beheerd?
    # (inschrijvingen, betalingen)
    extern_beheerd = models.BooleanField(default=False)

    # boog typen die aan deze wedstrijd deel mogen nemen
    boogtypen = models.ManyToManyField(BoogType, blank=True)

    # gekozen wedstrijdklassen voor de deze wedstrijd
    # deze kunnen gebruikt worden in de sessies
    wedstrijdklassen = models.ManyToManyField(KalenderWedstrijdklasse, blank=True)

    # aantal banen voor deze wedstrijd
    aantal_banen = models.PositiveSmallIntegerField(default=1)

    # hoe lang voor het begin van hun sessie moeten de sporters aanwezig zijn
    minuten_voor_begin_sessie_aanwezig_zijn = models.PositiveSmallIntegerField(default=45)

    # tekstveld voor namen scheidsrechters door organisatie aangedragen
    scheidsrechters = models.TextField(max_length=500, default='',
                                       blank=True)      # mag leeg zijn

    # eventuele opmerkingen vanuit de organisatie
    bijzonderheden = models.TextField(max_length=1000, default='',
                                      blank=True)      # mag leeg zijn

    # de sessies van deze wedstrijd
    sessies = models.ManyToManyField(KalenderWedstrijdSessie,
                                     blank=True)        # mag leeg zijn

    # de losse uitslagen van deze wedstrijd
    deeluitslagen = models.ManyToManyField(KalenderWedstrijdDeeluitslag,
                                           blank=True)        # mag leeg zijn

    class Meta:
        verbose_name = "Kalender wedstrijd"
        verbose_name_plural = "Kalender wedstrijden"

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        return "%s [%s] %s" % (self.datum_begin, WEDSTRIJD_STATUS_TO_STR[self.status], self.titel)


class KalenderWedstrijdKortingscode(models.Model):

    """ Een kortingscode voor een specifieke sporter voor een of meerdere wedstrijden """

    # de te gebruiken code
    code = models.CharField(max_length=20, default='')

    # tot wanneer geldig?
    geldig_tot_en_met = models.DateField()

    # welke vereniging heeft deze code uitgegeven? (en mag deze dus wijzigen)
    uitgegeven_door = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                        null=True, blank=True,
                                        related_name='korting_uitgever')

    # hoeveel korting (0% .. 100%)
    percentage = models.PositiveSmallIntegerField(default=100)

    # de kortingscode kan voor een specifieke sporter zijn (voorbeeld: winnaar van vorige jaar)
    # de kortingscode kan voor alle leden van een vereniging zijn (voorbeeld: de organiserende vereniging)
    # de kortingscode kan een combinatie-korting geven (meerdere wedstrijden)
    soort = models.CharField(max_length=1, choices=KALENDER_KORTING_SOORT_CHOICES, default=KALENDER_KORTING_VERENIGING)

    # voor welke wedstrijden is deze geldig?
    # bij combi-korting: lijst van alle wedstrijden waar op ingeschreven moeten zijn
    voor_wedstrijden = models.ManyToManyField(KalenderWedstrijd)

    # voor welke individuele sporter is deze kortingscode?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.SET_NULL, null=True, blank=True)

    # voor leden van welke vereniging is deze kortingscode?
    voor_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.SET_NULL, null=True, blank=True)

    # bij combi-korting: geldig op deze wedstrijd, indien gecombineerd met ALLE 'voor_wedstrijden'
    combi_basis_wedstrijd = models.ForeignKey(KalenderWedstrijd, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='combi_korting')

    def __str__(self):
        return "%s: %s" % (self.pk, self.code)

    class Meta:
        verbose_name = "Kalender kortingscode"


class KalenderInschrijving(models.Model):

    """ Een inschrijving op een wedstrijd sessie, inclusief koper, betaal-status en gebruikte kortingscode """

    # wanneer is deze inschrijving aangemaakt?
    wanneer = models.DateTimeField()

    # status
    status = models.CharField(max_length=2, default=INSCHRIJVING_STATUS_RESERVERING, choices=INSCHRIJVING_STATUS_CHOICES)

    # voor welke wedstrijd is dit?
    wedstrijd = models.ForeignKey(KalenderWedstrijd, on_delete=models.PROTECT)

    # voor welke sessie?
    sessie = models.ForeignKey(KalenderWedstrijdSessie, on_delete=models.PROTECT)

    # voor wie is deze inschrijving
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT)

    # wie is de koper?
    koper = models.ForeignKey(Account, on_delete=models.PROTECT)

    # welke kortingscode is gebruikt
    gebruikte_code = models.ForeignKey(KalenderWedstrijdKortingscode, on_delete=models.SET_NULL, blank=True, null=True)

    # bedragen ontvangen en terugbetaald
    ontvangen_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    retour_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # TODO: boekingsnummer toevoegen

    # TODO: traceer de gestuurde emails

    def __str__(self):
        """ beschrijving voor de admin interface """
        return "Inschrijving voor %s" % self.sporterboog.sporter.lid_nr_en_volledige_naam()

    class Meta:
        verbose_name = "Kalender inschrijving"
        verbose_name_plural = "Kalender inschrijvingen"

        constraints = [
            models.UniqueConstraint(fields=('sessie', 'sporterboog'), name='Geen dubbele inschrijving'),
        ]


class KalenderMutatie(models.Model):
    """ Deze tabel voedt de achtergrondtaak die de mutaties op de inschrijvingen doet
        waardoor alles netjes geserialiseerd wordt.
    """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie KALENDER_MUTATIE_*)
    code = models.PositiveSmallIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # waar heeft mutatie op betrekking?
    inschrijving = models.ForeignKey(KalenderInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # kortingscode om toe te passen
    korting = models.ForeignKey(KalenderWedstrijdKortingscode, on_delete=models.SET_NULL, null=True, blank=True)
    korting_voor_koper = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Kalender mutatie"

    def __str__(self):
        msg = "[%s]" % self.when
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        try:
            msg += " %s (%s)" % (self.code, KALENDER_MUTATIE_TO_STR[self.code])
        except KeyError:
            msg += " %s (???)" % self.code

        return msg


# end of file
