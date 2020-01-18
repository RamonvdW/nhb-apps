# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from BasisTypen.models import WedstrijdKlasse
from NhbStructuur.models import NhbRegio, NhbRayon, ADMINISTRATIEVE_REGIO
from datetime import date
from decimal import Decimal


ZERO = Decimal('0.000')


class CompetitieWedstrijdKlasse(models.Model):
    """ Deze database tabel bevat een de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden
    """
    wedstrijdklasse = models.ForeignKey(WedstrijdKlasse, on_delete=models.PROTECT)
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000
    is_afgesloten = models.BooleanField(default=False)

    def __str__(self):
        return "%s (%s)" % (self.wedstrijdklasse, self.min_ag)


class Competitie(models.Model):
    """ Deze database tabel bevat een van de jaarlijkste competities voor 18m of 25m
        Elke competitie heeft een beschrijving, een aantal belangrijke datums
        en een lijst van wedstrijdklassen met aanvangsgemiddelden
    """
    AFSTAND = [('18', 'Indoor'),
               ('25', '25m 1pijl')]

    beschrijving = models.CharField(max_length=40)
    afstand = models.CharField(max_length=2, choices=AFSTAND)
    begin_jaar = models.PositiveSmallIntegerField()     # 2019
    uiterste_datum_lid = models.DateField()
    begin_aanmeldingen = models.DateField()
    einde_aanmeldingen = models.DateField()
    einde_teamvorming = models.DateField()
    eerste_wedstrijd = models.DateField()
    klassen_indiv = models.ManyToManyField(CompetitieWedstrijdKlasse, related_name='indiv')
    klassen_team = models.ManyToManyField(CompetitieWedstrijdKlasse, related_name='team')
    is_afgesloten = models.BooleanField(default=False)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving


class DeelCompetitie(models.Model):
    """ Deze database tabel bevat informatie over een deel van een competitie:
        regiocompetitie (16x), rayoncompetitie (4x) of bondscompetitie (1x)
    """
    LAAG = [('Regio', 'Regiocompetitie'),
            ('RK', 'Rayoncompetitie'),
            ('BK', 'Bondscompetitie')]
    laag = models.CharField(max_length=5, choices=LAAG)
    competitie = models.ForeignKey(Competitie, on_delete=models.PROTECT)
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Regio
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Rayon
    is_afgesloten = models.BooleanField(default=False)
    functies = models.ManyToManyField(Group)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.nhb_regio:
            substr = str(self.nhb_regio)
        elif self.nhb_rayon:
            substr = str(self.nhb_rayon)
        else:
            substr = "BK"
        return "%s - %s"  % (self.competitie, substr)


def models_bepaal_startjaar_nieuwe_competitie():
    """ bepaal het start jaar van de nieuwe competitie """
    return timezone.now().year


def get_competitie_fase(afstand):
    # volgens tabel in hoofdstuk 1.3.1

    # A = initieel
    objs = Competitie.objects.filter(is_afgesloten=False, afstand=afstand)
    if len(objs) == 0:
        return 'A', Competitie()

    comp = objs[0]
    now = timezone.now()
    now = date(year=now.year, month=now.month, day=now.day)

    # A1 = competitie is aangemaakt en mag nog getuned worden
    if now < comp.begin_aanmeldingen:
        # zijn de aanvangsgemiddelden bepaald?
        if len(comp.klassen_indiv.all()) == 0:
            return 'A1', comp
        # A2 = klassengrenzen zijn bepaald
        return 'A2', comp

    # B = open voor inschrijvingen
    if now < comp.einde_aanmeldingen:
        return 'B', comp

    # C = aanmaken teams; gesloten voor individuele inschrijvingen
    if now < comp.einde_teamvorming:
        return 'C', comp

    # D = aanmaken poules en afronden wedstrijdschema's
    if now < comp.eerste_wedstrijd:
        return 'D', comp

    # E = Begin wedstrijden
    return 'E', comp


def competitie_aanmaken():
    """ Deze functie wordt aangeroepen als de BKO de nieuwe competitie op wil starten
        We maken de 18m en 25m competitie aan en daaronder de deelcompetities voor regio, rayon en bond
    """
    jaar = models_bepaal_startjaar_nieuwe_competitie()
    yearend = date(year=jaar, month=12, day=31)     # 31 december
    udvl = date(year=jaar, month=8, day=1)          # 1 augustus = uiterste datum van lidmaatschap voor deelname teamcompetitie

    # maak de Competitie aan voor 18m en 25m
    for afstand, beschrijving in Competitie.AFSTAND:
        fase, _ = get_competitie_fase(afstand)
        if fase == 'A':
            comp = Competitie()
            comp.beschrijving = '%s competitie %s/%s' % (beschrijving, jaar, jaar+1)
            comp.afstand = afstand      # 18/25
            comp.begin_jaar = jaar
            comp.uiterste_datum_lid = udvl
            comp.begin_aanmeldingen = comp.einde_aanmeldingen = comp.einde_teamvorming = comp.eerste_wedstrijd = yearend
            comp.save()

            # maak de Deelcompetities aan voor Regio, RK, BK
            for laag, _ in DeelCompetitie.LAAG:
                deel = DeelCompetitie()
                deel.laag = laag
                deel.competitie = comp
                if laag == DeelCompetitie.LAAG[0][0]:
                    # Regio
                    for obj in NhbRegio.objects.all():
                        if obj.regio_nr != ADMINISTRATIEVE_REGIO:
                            deel.nhb_regio = obj
                            deel.pk = None
                            deel.save()
                    # for
                elif laag == DeelCompetitie.LAAG[1][0]:
                    # RK
                    for obj in NhbRayon.objects.all():
                        deel.nhb_rayon = obj
                        deel.pk = None
                        deel.save()
                else:
                    # BK
                    deel.save()
            # for
        # if
    # for

    # wedstrijdklassen volgens later, tijdens het bepalen van de klassengrenzen


def maak_competitieklasse_indiv(comp, wedstrijdklasse, min_ag):
    """ Deze functie maakt een nieuwe CompetitieWedstrijdKlasse aan met het gevraagde min_ag
        en koppelt deze aan de gevraagde Competitie
    """
    compkl = CompetitieWedstrijdKlasse()
    compkl.wedstrijdklasse = wedstrijdklasse
    compkl.min_ag = min_ag
    compkl.save()
    comp.klassen_indiv.add(compkl)

# end of file
