# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import IndivWedstrijdklasse, BoogType
from NhbStructuur.models import NhbVereniging, NhbLid
from Schutter.models import SchutterBoog
from Wedstrijden.models import WedstrijdLocatie


WEDSTRIJD_DISCIPLINES_OUTDOOR = 'OD'
WEDSTRIJD_DISCIPLINES_INDOOR = 'IN'
WEDSTRIJD_DISCIPLINES_25M1P = '25'
WEDSTRIJD_DISCIPLINES_CLOUT = 'CL'
WEDSTRIJD_DISCIPLINES_VELD = 'VE'
WEDSTRIJD_DISCIPLINES_RUN = 'RA'
WEDSTRIJD_DISCIPLINES_3D = '3D'

WEDSTRIJD_DISCIPLINES = (
    (WEDSTRIJD_DISCIPLINES_OUTDOOR, 'Outdoor'),
    (WEDSTRIJD_DISCIPLINES_INDOOR, 'Indoor'),               # Indoor = 18m/25m 3pijl
    (WEDSTRIJD_DISCIPLINES_25M1P, '25m 1pijl'),
    (WEDSTRIJD_DISCIPLINES_CLOUT, 'Clout'),
    (WEDSTRIJD_DISCIPLINES_VELD, 'Veld'),
    (WEDSTRIJD_DISCIPLINES_RUN, 'Run Archery'),
    (WEDSTRIJD_DISCIPLINES_3D, '3D')
)

WEDSTRIJD_DISCIPLINE_TO_STR = {
    WEDSTRIJD_DISCIPLINES_OUTDOOR: 'Outdoor',
    WEDSTRIJD_DISCIPLINES_INDOOR: 'Indoor',
    WEDSTRIJD_DISCIPLINES_25M1P: '25m 1pijl',
    WEDSTRIJD_DISCIPLINES_CLOUT: 'Clout',
    WEDSTRIJD_DISCIPLINES_VELD: 'Veld',
    WEDSTRIJD_DISCIPLINES_RUN: 'Run Archery',
    WEDSTRIJD_DISCIPLINES_3D: '3D',
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


class KalenderWedstrijdDeeluitslag(models.Model):
    """  deel van de uitslag van een wedstrijd """

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
    tijd_aanwezig_zijn = models.TimeField()
    tijd_einde = models.TimeField()

    # toegestane wedstrijdklassen
    klassen = models.ManyToManyField(IndivWedstrijdklasse,
                                     blank=True)        # mag leeg zijn / gemaakt worden

    # maximum aantal deelnemers
    max_sporters = models.PositiveSmallIntegerField(default=1)

    # aangemelde sporters
    aanmeldingen = models.ManyToManyField(SchutterBoog,
                                          blank=True)  # mag leeg zijn / gemaakt worden

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

    # welke discipline is dit? (indoor/outdoor/veld, etc.)
    discipline = models.CharField(max_length=2, choices=WEDSTRIJD_DISCIPLINES, default='OD')

    # wat de WA-status van deze wedstrijd (A of B)
    wa_status = models.CharField(max_length=1, default=WEDSTRIJD_WA_STATUS_B, choices=WEDSTRIJD_WA_STATUS)

    # contactgegevens van de organisatie
    organiserende_vereniging = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT)
    contact_naam = models.CharField(max_length=50, default='')
    contact_email = models.CharField(max_length=150, default='')
    contact_website = models.CharField(max_length=100, default='')
    contact_telefoon = models.CharField(max_length=50, default='')

    # acceptatie voorwaarden WA A-status
    voorwaarden_a_status_acceptatie = models.BooleanField(default=False)
    voorwaarden_a_status_when = models.DateTimeField()
    voorwaarden_a_status_who = models.CharField(max_length=100, default='')     # [BondsNr] Volledige Naam

    # als deze wedstrijd door de organiserende vereniging buiten deze website om gehanteerd wordt
    # dan is dit veld ingevuld en wordt de sporter doorgestuurd
    unmanaged_url = models.CharField(max_length=100, default='')

    # samenvatting van de boogtypen die voorkomen in de wedstrijdklassen
    # hiermee kan de kalender gefilterd worden op de ingestelde boogtypen van de sporter
    boogtypen = models.ManyToManyField(BoogType, blank=True)

    # aantal banen voor deze wedstrijd
    aantal_banen = models.PositiveSmallIntegerField(default=1)

    # tekstveld voor namen scheidsrechters door organisatie aangedragen
    scheidsrechters = models.TextField(max_length=500, default='')

    # de sessies van deze wedstrijd
    sessies = models.ManyToManyField(KalenderWedstrijdSessie,
                                     blank=True)        # mag leeg zijn

    # de losse uitslagen van deze wedstrijd
    deeluitslagen = models.ManyToManyField(KalenderWedstrijdDeeluitslag,
                                           blank=True)        # mag leeg zijn

    class Meta:
        verbose_name = "Kalender wedstrijd"
        verbose_name_plural = "Kalender wedstrijden"


# end of file
