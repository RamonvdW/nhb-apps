# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from BasisTypen.definities import ORGANISATIES, ORGANISATIE_WA
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from NhbStructuur.models import NhbVereniging
from Score.models import Score, Uitslag
from Sporter.models import Sporter, SporterBoog
from Wedstrijden.definities import (BAAN_TYPE, BAAN_TYPE_ONBEKEND, BAANTYPE2STR,
                                    WEDSTRIJD_STATUS, WEDSTRIJD_STATUS_TO_STR,
                                    WEDSTRIJD_BEGRENZING, WEDSTRIJD_BEGRENZING_LANDELIJK,
                                    WEDSTRIJD_DISCIPLINES, WEDSTRIJD_DISCIPLINE_OUTDOOR,
                                    WEDSTRIJD_WA_STATUS, WEDSTRIJD_WA_STATUS_B,
                                    WEDSTRIJD_KORTING_SOORT_CHOICES, WEDSTRIJD_KORTING_VERENIGING,
                                    WEDSTRIJD_KORTING_SOORT_TO_STR,
                                    INSCHRIJVING_STATUS_CHOICES, INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                    INSCHRIJVING_STATUS_TO_STR)
from decimal import Decimal


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
        return "(pk=%s) %s %s (%s plekken)" % (self.pk, self.datum, self.tijd_begin, self.max_sporters)

    class Meta:
        verbose_name = "Wedstrijd sessie"
        verbose_name_plural = "Wedstrijd sessies"


class Wedstrijd(models.Model):

    """ Een wedstrijd voor op de wedstrijdkalender """

    # titel van de wedstrijd
    titel = models.CharField(max_length=50, default='')

    # status van deze wedstrijd: ontwerp --> goedgekeurd --> geannuleerd
    status = models.CharField(max_length=1, choices=WEDSTRIJD_STATUS, default='O')

    # ter info op de kalender = niet op in te schrijven, dus geen inschrijf deadline tonen
    is_ter_info = models.BooleanField(default=False)

    # mogelijkheid om een wedstrijd niet op de kalender te tonen
    # use case: 2-daagse wedstrijd wordt geannuleerd en vervangen door twee 1-daagse wedstrijden
    #           als er inschrijvingen aan hangen dan wil je de wedstrijd niet verwijderen
    toon_op_kalender = models.BooleanField(default=True)

    # wanneer is de wedstrijd (kan meerdere dagen beslaan)
    datum_begin = models.DateField()
    datum_einde = models.DateField()

    # hoeveel dagen van tevoren de online-inschrijving dicht doen?
    inschrijven_tot = models.PositiveSmallIntegerField(default=7)

    # waar wordt de wedstrijd gehouden
    organiserende_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT)

    # bondsbureau kan wedstrijd verleggen bij gekozen vereniging
    uitvoerende_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                               related_name='uitvoerend',
                                               blank=True, null=True)
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
    contact_naam = models.CharField(max_length=50, default='', blank=True)
    contact_email = models.CharField(max_length=150, default='', blank=True)
    contact_website = models.CharField(max_length=100, default='', blank=True)
    contact_telefoon = models.CharField(max_length=50, default='', blank=True)

    # acceptatie verkoopvoorwaarden wedstrijdkalender
    verkoopvoorwaarden_status_acceptatie = models.BooleanField(default=False)
    verkoopvoorwaarden_status_when = models.DateTimeField(auto_now=True)
    verkoopvoorwaarden_status_who = models.CharField(max_length=100, default='',          # [BondsNr] Volledige Naam
                                                     blank=True)     # mag leeg zijn

    # acceptatie voorwaarden WA A-status
    voorwaarden_a_status_acceptatie = models.BooleanField(default=False)
    voorwaarden_a_status_when = models.DateTimeField(auto_now=True)
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


class WedstrijdKorting(models.Model):

    """ Een korting voor een specifieke sporter, leden van een vereniging of voor een combinatie van wedstrijden """

    # de korting kan voor een specifieke sporter zijn (voorbeeld: winnaar van vorige jaar)
    # de korting kan voor alle leden van een vereniging zijn (voorbeeld: de organiserende vereniging)
    # de korting kan een combinatie-korting geven (meerdere wedstrijden)
    soort = models.CharField(max_length=1, choices=WEDSTRIJD_KORTING_SOORT_CHOICES, default=WEDSTRIJD_KORTING_VERENIGING)

    # tot wanneer geldig?
    geldig_tot_en_met = models.DateField()

    # welke vereniging heeft deze korting uitgegeven? (en mag deze dus wijzigen)
    uitgegeven_door = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT,
                                        null=True, blank=True,
                                        related_name='wedstrijd_korting_uitgever')

    # hoeveel korting (0% .. 100%)
    percentage = models.PositiveSmallIntegerField(default=100)

    # voor welke wedstrijden is deze geldig?
    # bij combi-korting: lijst van alle wedstrijden waar op ingeschreven moeten zijn
    voor_wedstrijden = models.ManyToManyField(Wedstrijd)

    # voor welke individuele sporter is deze korting?
    voor_sporter = models.ForeignKey(Sporter, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return "[%s] %s %d%%" % (self.uitgegeven_door.pk, WEDSTRIJD_KORTING_SOORT_TO_STR[self.soort], self.percentage)

    class Meta:
        verbose_name = "Wedstrijd korting"
        verbose_name_plural = "Wedstrijd kortingen"


class WedstrijdInschrijving(models.Model):

    """ Een inschrijving op een wedstrijd sessie, inclusief koper, betaal-status en gebruikte korting """

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

    # in welke klasse komt deze sporterboog uit?
    wedstrijdklasse = models.ForeignKey(KalenderWedstrijdklasse, on_delete=models.PROTECT)

    # wie is de koper?
    # (BestelProduct verwijst naar deze inschrijving)
    koper = models.ForeignKey(Account, on_delete=models.PROTECT)

    # welke korting is gebruikt
    korting = models.ForeignKey(WedstrijdKorting, on_delete=models.SET_NULL, blank=True, null=True)

    # bedragen ontvangen en terugbetaald
    ontvangen_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))
    retour_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))

    # log van bestelling, betalingen en eventuele wijzigingen van klasse en sessie
    log = models.TextField(blank=True)

    # TODO: traceer de gestuurde emails

    def __str__(self):
        """ beschrijving voor de admin interface """
        return "Inschrijving voor %s: [%s]" % (self.sporterboog.sporter.lid_nr_en_volledige_naam(),
                                               INSCHRIJVING_STATUS_TO_STR[self.status])

    def korte_beschrijving(self):
        """ geef een one-liner terug met een korte beschrijving van deze inschrijving """

        titel = self.wedstrijd.titel
        if len(titel) > 60:
            titel = titel[:58] + '..'

        return "%s - %s" % (self.sporterboog.sporter.lid_nr, titel)

    class Meta:
        verbose_name = "Wedstrijd inschrijving"
        verbose_name_plural = "Wedstrijd inschrijvingen"

        constraints = [
            # constraint op een sessie i.p.v. wedstrijd zodat sporter mee kan doen met meerdere sessies,
            # bijvoorbeeld zaterdag/zondag of ochtend/middag
            models.UniqueConstraint(fields=('sessie', 'sporterboog'),
                                    name='Geen dubbele wedstrijd inschrijving'),
        ]

# end of file
