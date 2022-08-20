# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.models import (BoogType, KalenderWedstrijdklasse,
                               ORGANISATIES, ORGANISATIE_WA, ORGANISATIE_IFAA, ORGANISATIE_NHB)
from NhbStructuur.models import NhbVereniging
from Score.models import Score, Uitslag
from Sporter.models import Sporter, SporterBoog
from decimal import Decimal


# accommodatie type

BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT = 'O'
BAAN_TYPE_BINNEN_BUITEN = 'H'               # H = half overdekt
BAAN_TYPE_ONBEKEND = 'X'
BAAN_TYPE_BUITEN = 'B'                      # lift mee op binnenbaan voor adres, plaats
BAAN_TYPE_EXTERN = 'E'

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
    WEDSTRIJD_DISCIPLINE_3D: '3D',
    WEDSTRIJD_DISCIPLINE_RUN: 'Run Archery',
    WEDSTRIJD_DISCIPLINE_CLOUT: 'Clout',
    # bewust weggelaten ivm niet gebruikt: flight (ver), ski
}

WEDSTRIJD_DISCIPLINE_TO_STR_NHB = {
    WEDSTRIJD_DISCIPLINE_OUTDOOR: 'Outdoor',
    WEDSTRIJD_DISCIPLINE_INDOOR: 'Indoor',
    WEDSTRIJD_DISCIPLINE_25M1P: '25m 1pijl',
    WEDSTRIJD_DISCIPLINE_VELD: 'Veld',
    WEDSTRIJD_DISCIPLINE_RUN: 'Run Archery',
    WEDSTRIJD_DISCIPLINE_3D: '3D',
    WEDSTRIJD_DISCIPLINE_CLOUT: 'Clout',
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
WEDSTRIJD_DUUR_MAX_UREN = 8         # maximale keuze voor de duur van een sessie

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

INSCHRIJVING_STATUS_RESERVERING_MANDJE = 'R'        # moet nog omgezet worden in een bestelling
INSCHRIJVING_STATUS_RESERVERING_BESTELD = 'B'       # moet nog betaald worden
INSCHRIJVING_STATUS_DEFINITIEF = 'D'                # is betaald
INSCHRIJVING_STATUS_AFGEMELD = 'A'

INSCHRIJVING_STATUS_CHOICES = (
    (INSCHRIJVING_STATUS_RESERVERING_MANDJE, "Reservering"),
    (INSCHRIJVING_STATUS_RESERVERING_BESTELD, "Besteld"),
    (INSCHRIJVING_STATUS_DEFINITIEF, "Definitief"),
    (INSCHRIJVING_STATUS_AFGEMELD, "Afgemeld")
)

INSCHRIJVING_STATUS_TO_STR = {
    INSCHRIJVING_STATUS_RESERVERING_MANDJE: 'Gereserveerd, in mandje',
    INSCHRIJVING_STATUS_RESERVERING_BESTELD: 'Gereserveerd, wacht op betaling',
    INSCHRIJVING_STATUS_DEFINITIEF: 'Inschrijving is definitief',
    INSCHRIJVING_STATUS_AFGEMELD: 'Afgemeld',
}

INSCHRIJVING_STATUS_TO_SHORT_STR = {
    INSCHRIJVING_STATUS_RESERVERING_MANDJE: 'In mandje',
    INSCHRIJVING_STATUS_RESERVERING_BESTELD: 'Besteld',
    INSCHRIJVING_STATUS_DEFINITIEF: 'Definitief',
    INSCHRIJVING_STATUS_AFGEMELD: 'Afgemeld',
}


WEDSTRIJD_KORTING_SPORTER = 's'
WEDSTRIJD_KORTING_VERENIGING = 'v'
WEDSTRIJD_KORTING_COMBI = 'c'

WEDSTRIJD_KORTING_SOORT_CHOICES = (
    (WEDSTRIJD_KORTING_SPORTER, 'Sporter'),
    (WEDSTRIJD_KORTING_VERENIGING, 'Vereniging'),
    (WEDSTRIJD_KORTING_COMBI, 'Combi')
)

WEDSTRIJD_KORTING_SOORT_TO_STR = {
    WEDSTRIJD_KORTING_SPORTER: 'Sporter',
    WEDSTRIJD_KORTING_VERENIGING: 'Vereniging',
    WEDSTRIJD_KORTING_COMBI: 'Combi'
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

    # eigen accommodatie binnenbaan (volledig overdekt of half overdekt), buitenbaan, extern of 'onbekend'
    baan_type = models.CharField(max_length=1, choices=BAAN_TYPE, default=BAAN_TYPE_ONBEKEND)

    # welke disciplines kunnen hier georganiseerd worden?
    discipline_25m1pijl = models.BooleanField(default=False)
    discipline_outdoor = models.BooleanField(default=False)
    discipline_indoor = models.BooleanField(default=False)      # Indoor = 18m/25m 3pijl, True als banen_18m>0 of banen_25m>0
    discipline_clout = models.BooleanField(default=False)
    discipline_veld = models.BooleanField(default=False)
    discipline_run = models.BooleanField(default=False)
    discipline_3d = models.BooleanField(default=False)
    # discipline_flight (zo ver mogelijk schieten)
    # discipline_ski

    # alleen voor indoor: beschikbare banen
    banen_18m = models.PositiveSmallIntegerField(default=0)
    banen_25m = models.PositiveSmallIntegerField(default=0)
    max_dt_per_baan = models.PositiveSmallIntegerField(default=4)       # FUTURE: obsolete

    # het maximum aantal sporters
    # (noodzakelijk voor als max_sporters != banen * 4)
    max_sporters_18m = models.PositiveSmallIntegerField(default=0)
    max_sporters_25m = models.PositiveSmallIntegerField(default=0)

    # alleen voor discipline_outdoor baan
    buiten_banen = models.PositiveSmallIntegerField(default=0)
    buiten_max_afstand = models.PositiveSmallIntegerField(default=0)

    # adresgegevens van de locatie
    adres = models.TextField(max_length=256, blank=True)

    # plaats deze wedstrijdlocatie, om eenvoudig weer te kunnen geven op de wedstrijdkalender
    plaats = models.CharField(max_length=50, blank=True, default='')

    # handmatig ingevoerd of uit de CRM (=bevroren)
    adres_uit_crm = models.BooleanField(default=False)

    # vrije notitiegegevens voor zaken als "verbouwing tot", etc.
    notities = models.TextField(max_length=1024, blank=True)

    def disciplines_str(self):
        disc = list()
        if self.discipline_outdoor:
            disc.append('outdoor')
        if self.discipline_indoor:
            disc.append('indoor(18+25)')
        if self.discipline_25m1pijl:
            disc.append('25m1pijl')
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

        msg += "[baantype: %s] " % BAANTYPE2STR[self.baan_type]

        msg += self.adres.replace('\n', ', ')
        # kost te veel database toegangen in admin interface
        # msg += " (%s verenigingen)" % self.verenigingen.count()

        msg += " [disciplines: %s]" % self.disciplines_str()

        msg += " [banen: 18m=%s, 25m=%s]" % (self.banen_18m, self.banen_25m)

        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Wedstrijd locatie"
        verbose_name_plural = "Wedstrijd locaties"


# class WedstrijdDeeluitslag(models.Model):
#     """ Deel van de uitslag van een wedstrijd """
#
#     # na verwijderen wordt deze vlag gezet, voor opruimen door achtergrondtaak
#     buiten_gebruik = models.BooleanField(default=False)
#
#     # naam van het uitslag-bestand (zonder pad)
#     bestandsnaam = models.CharField(max_length=100, default='', blank=True)
#
#     # wanneer toegevoegd?
#     toegevoegd_op = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         verbose_name = "Wedstrijd deeluitslag"
#         verbose_name_plural = "Wedstrijd deeluitslagen"


class WedstrijdSessie(models.Model):
    """ Een sessie van een wedstrijd """

    # op welke datum is deze sessie?
    datum = models.DateField()

    # hoe laat is deze sessie, hoe laat moet je aanwezig zijn, de geschatte eindtijd
    tijd_begin = models.TimeField()
    tijd_einde = models.TimeField()

    # beschrijving
    beschrijving = models.CharField(max_length=50, default='')

    # toegestane wedstrijdklassen
    wedstrijdklassen = models.ManyToManyField(KalenderWedstrijdklasse, blank=True)

    # maximum aantal deelnemers
    max_sporters = models.PositiveSmallIntegerField(default=1)

    # het aantal inschrijvingen: de som van reserveringen en betaalde deelnemers
    aantal_inschrijvingen = models.PositiveSmallIntegerField(default=0)

    # inschrijvingen: zie WedstrijdInschrijving

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        return "%s %s (%s)" % (self.datum, self.tijd_begin, self.max_sporters)

    class Meta:
        verbose_name = "Wedstrijd sessie"
        verbose_name_plural = "Wedstrijd sessies"


class Wedstrijd(models.Model):

    """ Een wedstrijd voor op de wedstrijdkalender """

    # titel van de wedstrijd
    titel = models.CharField(max_length=50, default='')

    # status van deze wedstrijd: ontwerp --> goedgekeurd --> geannuleerd
    status = models.CharField(max_length=1, choices=WEDSTRIJD_STATUS, default='O')

    # wanneer is de wedstrijd (kan meerdere dagen beslaan)
    datum_begin = models.DateField()
    datum_einde = models.DateField()

    # hoeveel dagen van tevoren de online-inschrijving dicht doen?
    inschrijven_tot = models.PositiveSmallIntegerField(default=7)

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

    # kosten (voor alle sessies van de hele wedstrijd)
    prijs_euro_normaal = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99
    prijs_euro_onder18 = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99

    # de sessies van deze wedstrijd
    sessies = models.ManyToManyField(WedstrijdSessie,
                                     blank=True)        # mag leeg zijn

    # de losse uitslagen van deze wedstrijd
    # deeluitslagen = models.ManyToManyField(WedstrijdDeeluitslag,
    #                                        blank=True)        # mag leeg zijn

    def bepaal_prijs_voor_sporter(self, sporter):
        leeftijd = sporter.bereken_wedstrijdleeftijd(self.datum_begin, self.organisatie)
        if leeftijd < 18:
            prijs = self.prijs_euro_onder18
        else:
            prijs = self.prijs_euro_normaal
        return prijs

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        return "%s [%s] %s" % (self.datum_begin, WEDSTRIJD_STATUS_TO_STR[self.status], self.titel)

    class Meta:
        verbose_name = "Wedstrijd"
        verbose_name_plural = "Wedstrijden"


class WedstrijdKortingscode(models.Model):

    """ Een kortingscode voor een specifieke sporter voor een of meerdere wedstrijden """

    # de te gebruiken code
    code = models.CharField(max_length=20, default='')

    # tot wanneer geldig?
    geldig_tot_en_met = models.DateField()

    # welke vereniging heeft deze code uitgegeven? (en mag deze dus wijzigen)
    uitgegeven_door = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                        null=True, blank=True,
                                        related_name='wedstrijd_korting_uitgever')

    # hoeveel korting (0% .. 100%)
    percentage = models.PositiveSmallIntegerField(default=100)

    # de kortingscode kan voor een specifieke sporter zijn (voorbeeld: winnaar van vorige jaar)
    # de kortingscode kan voor alle leden van een vereniging zijn (voorbeeld: de organiserende vereniging)
    # de kortingscode kan een combinatie-korting geven (meerdere wedstrijden)
    soort = models.CharField(max_length=1, choices=WEDSTRIJD_KORTING_SOORT_CHOICES, default=WEDSTRIJD_KORTING_VERENIGING)

    # voor welke wedstrijden is deze geldig?
    # bij combi-korting: lijst van alle wedstrijden waar op ingeschreven moeten zijn
    voor_wedstrijden = models.ManyToManyField(Wedstrijd)

    # voor welke individuele sporter is deze kortingscode?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.SET_NULL, null=True, blank=True)

    # voor leden van welke vereniging is deze kortingscode?
    voor_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.SET_NULL, null=True, blank=True)

    # bij combi-korting: geldig op deze wedstrijd, indien gecombineerd met ALLE 'voor_wedstrijden'
    combi_basis_wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='wedstrijd_combi_korting')

    def __str__(self):
        return "%s: %s" % (self.pk, self.code)

    class Meta:
        verbose_name = "Wedstrijd kortingscode"


class WedstrijdInschrijving(models.Model):

    """ Een inschrijving op een wedstrijd sessie, inclusief koper, betaal-status en gebruikte kortingscode """

    # TODO: afmeldingen verplaatsen naar een andere tabel, voor de geschiedenis

    # wanneer is deze inschrijving aangemaakt?
    wanneer = models.DateTimeField()

    # status
    status = models.CharField(max_length=2, choices=INSCHRIJVING_STATUS_CHOICES,
                              default=INSCHRIJVING_STATUS_RESERVERING_MANDJE)

    # voor welke wedstrijd is dit?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.PROTECT)

    # voor welke sessie?
    sessie = models.ForeignKey(WedstrijdSessie, on_delete=models.PROTECT)

    # voor wie is deze inschrijving
    sporterboog = models.ForeignKey(SporterBoog, on_delete=models.PROTECT)

    # wie is de koper?
    koper = models.ForeignKey(Account, on_delete=models.PROTECT)

    # welke kortingscode is gebruikt
    gebruikte_code = models.ForeignKey(WedstrijdKortingscode, on_delete=models.SET_NULL, blank=True, null=True)

    # bedragen ontvangen en terugbetaald
    ontvangen_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    retour_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # TODO: boekingsnummer toevoegen

    # TODO: traceer de gestuurde emails

    def __str__(self):
        """ beschrijving voor de admin interface """
        return "Inschrijving voor %s" % self.sporterboog.sporter.lid_nr_en_volledige_naam()

    def korte_beschrijving(self):
        """ geef een one-liner terug met een korte beschrijving van deze inschrijving """

        titel = self.wedstrijd.titel
        if len(titel) > 30:
            titel = titel[:28] + '..'

        return "%s - %s" % (self.sporterboog.sporter.lid_nr, titel)

    class Meta:
        verbose_name = "Wedstrijd inschrijving"
        verbose_name_plural = "Wedstrijd inschrijvingen"

        constraints = [
            models.UniqueConstraint(fields=('sessie', 'sporterboog'), name='Geen dubbele wedstrijd inschrijving'),
        ]

# end of file
