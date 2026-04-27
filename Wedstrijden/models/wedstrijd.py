# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import ORGANISATIES, ORGANISATIE_WA
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Locatie.models import WedstrijdLocatie
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_STATUS_CHOICES, WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_STATUS_TO_STR,
                                    WEDSTRIJD_BEGRENZING, WEDSTRIJD_BEGRENZING_WERELD,
                                    WEDSTRIJD_DISCIPLINES, WEDSTRIJD_DISCIPLINE_OUTDOOR,
                                    WEDSTRIJD_WA_STATUS, WEDSTRIJD_WA_STATUS_B, AANTAL_SCHEIDS_GEEN_KEUZE)
from .sessie import WedstrijdSessie
from decimal import Decimal


class Wedstrijd(models.Model):

    """ Een wedstrijd voor op de wedstrijdkalender """

    # titel van de wedstrijd
    titel = models.CharField(max_length=75, default='')

    # status van deze wedstrijd: ontwerp --> goedgekeurd --> geannuleerd
    status = models.CharField(max_length=1, choices=WEDSTRIJD_STATUS_CHOICES, default=WEDSTRIJD_STATUS_ONTWERP)

    # ter info op de kalender = niet op in te schrijven, dus geen inschrijf deadline tonen
    is_ter_info = models.BooleanField(default=False)

    # mogelijkheid om een wedstrijd niet op de kalender te tonen
    # use case: 2-daagse wedstrijd wordt geannuleerd en vervangen door twee 1-daagse wedstrijden
    #           als er inschrijvingen aan hangen dan wil je de wedstrijd niet verwijderen
    toon_op_kalender = models.BooleanField(default=True)

    # voor intern gebruik (scheidsrechter beschikbaarheid RK/BK competitie)?
    verstop_voor_mwz = models.BooleanField(default=False)

    # wanneer is de wedstrijd (kan meerdere dagen beslaan)
    datum_begin = models.DateField()
    datum_einde = models.DateField()

    # hoeveel dagen van tevoren de online-inschrijving dicht doen?
    inschrijven_tot = models.PositiveSmallIntegerField(default=7)

    # wie beheert deze wedstrijd?
    # wordt ook gebruikt voor betalingen
    organiserende_vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT)

    # bondsbureau kan wedstrijd verleggen bij gekozen vereniging
    uitvoerende_vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT,
                                               related_name='uitvoerend',
                                               blank=True, null=True)
    locatie = models.ForeignKey(WedstrijdLocatie, on_delete=models.PROTECT)

    # begrenzing
    begrenzing = models.CharField(max_length=1, default=WEDSTRIJD_BEGRENZING_WERELD, choices=WEDSTRIJD_BEGRENZING)

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
    verkoopvoorwaarden_status_when = models.DateTimeField(auto_now_add=True)
    verkoopvoorwaarden_status_who = models.CharField(max_length=100, default='',          # [lid_nr] Volledige Naam
                                                     blank=True)     # mag leeg zijn

    # acceptatie voorwaarden WA A-status
    voorwaarden_a_status_acceptatie = models.BooleanField(default=False)
    voorwaarden_a_status_when = models.DateTimeField(auto_now_add=True)
    voorwaarden_a_status_who = models.CharField(max_length=100, default='',               # [lid_nr] Volledige Naam
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

    # benodigde scheidsrechters
    aantal_scheids = models.IntegerField(default=AANTAL_SCHEIDS_GEEN_KEUZE)

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

    # moeten kwalificatie-scores opgegeven worden voor deze wedstrijd?
    eis_kwalificatie_scores = models.BooleanField(default=False)

    # links naar de uitslagen
    url_uitslag_1 = models.CharField(max_length=200, default='', blank=True)
    url_uitslag_2 = models.CharField(max_length=200, default='', blank=True)
    url_uitslag_3 = models.CharField(max_length=200, default='', blank=True)
    url_uitslag_4 = models.CharField(max_length=200, default='', blank=True)

    # link naar een webpagina of pdf met informatie over de wedstrijd
    url_flyer = models.CharField(max_length=200, default='', blank=True)

    # extern geadministreerde deelnemerslijst
    url_deelnemerslijst = models.CharField(max_length=200, default='', blank=True)

    def bepaal_prijs_voor_sporter(self, sporter):
        leeftijd = sporter.bereken_wedstrijdleeftijd(self.datum_begin, self.organisatie)
        prijs = self.prijs_euro_onder18 if leeftijd < 18 else self.prijs_euro_normaal
        return prijs

    def __str__(self):
        """ geef een beschrijving terug voor de admin interface """
        msg = str(self.datum_begin)
        msg += ' [%s]' % self.organiserende_vereniging.ver_nr
        msg += ' %s %s' % (WEDSTRIJD_STATUS_TO_STR[self.status], self.titel)
        return msg

    class Meta:
        verbose_name = "Wedstrijd"
        verbose_name_plural = "Wedstrijden"

    objects = models.Manager()      # for the editor only


# end of file
