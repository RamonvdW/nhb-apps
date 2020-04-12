# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.models import WedstrijdKlasse
from NhbStructuur.models import NhbRegio, NhbRayon, ADMINISTRATIEVE_REGIO
from Functie.models import Functie
from decimal import Decimal
from datetime import date


ZERO = Decimal('0.000')


class Competitie(models.Model):
    """ Deze database tabel bevat een van de jaarlijkse competities voor 18m of 25m
        Elke competitie heeft een beschrijving, een aantal belangrijke datums
        en een lijst van wedstrijdklassen met aanvangsgemiddelden
    """
    AFSTAND = [('18', 'Indoor'),
               ('25', '25m 1pijl')]

    beschrijving = models.CharField(max_length=40)

    # 18m of 25m
    afstand = models.CharField(max_length=2, choices=AFSTAND)

    # seizoen
    begin_jaar = models.PositiveSmallIntegerField()     # 2019

    # kalender data
    uiterste_datum_lid = models.DateField()
    begin_aanmeldingen = models.DateField()
    einde_aanmeldingen = models.DateField()
    einde_teamvorming = models.DateField()
    eerste_wedstrijd = models.DateField()

    # nog te wijzigen?
    is_afgesloten = models.BooleanField(default=False)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving


class CompetitieWedstrijdKlasse(models.Model):
    """ Deze database tabel bevat een de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE,
                                    null=True)      # nodig voor migratie

    # definitie
    # (levert beschrijving, niet_voor_rk_bk, is_voor_teams)
    wedstrijdklasse = models.ForeignKey(WedstrijdKlasse, on_delete=models.PROTECT)

    # klassegrens voor deze competitie
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # teamcompetitie of individuele competitie
    is_team = models.BooleanField(default=False)

    # is de RCL klaar?
    is_afgesloten = models.BooleanField(default=False)      # TODO: kan weg??!

    def __str__(self):
        msg = "%s (%s) - " % (self.wedstrijdklasse, self.min_ag)
        if self.competitie:
            msg += self.competitie.beschrijving
        else:
            msg += "?"
        return msg


def maak_competitieklasse_indiv(comp, wedstrijdklasse, min_ag):
    """ Deze functie maakt een nieuwe CompetitieWedstrijdKlasse aan met het gevraagde min_ag
        en koppelt deze aan de gevraagde Competitie
    """
    compkl = CompetitieWedstrijdKlasse()
    compkl.competitie = comp
    compkl.wedstrijdklasse = wedstrijdklasse
    compkl.min_ag = min_ag
    compkl.save()


class DeelCompetitie(models.Model):
    """ Deze database tabel bevat informatie over een deel van een competitie:
        regiocompetitie (16x), rayoncompetitie (4x) of bondscompetitie (1x)
    """
    LAAG = [('Regio', 'Regiocompetitie'),
            ('RK', 'Rayoncompetitie'),
            ('BK', 'Bondscompetitie')]

    laag = models.CharField(max_length=5, choices=LAAG)

    # hoort bij welke competitie?
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # nhb_regio is gezet voor de regioncompetitie
    # nhb_rayon is gezet voor het RK
    # geen van beiden is gezet voor de BK

    # regio, voor regiocompetitie
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Regio

    # rayon, voor RK
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT,
                                  null=True, blank=True)    # optioneel want alleen voor laag Rayon

    # welke beheerder hoort hier bij?
    functie = models.ForeignKey(Functie, on_delete=models.PROTECT,
                                null=True, blank=True)      # optioneel (om migratie toe te staan)

    # is de beheerder klaar?
    is_afgesloten = models.BooleanField(default=False)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        if self.nhb_regio:
            substr = str(self.nhb_regio)
        elif self.nhb_rayon:
            substr = str(self.nhb_rayon)
        else:
            substr = "BK"
        return "%s - %s"  % (self.competitie, substr)


def competitie_aanmaken(jaar):
    """ Deze functie wordt aangeroepen als de BKO de nieuwe competitie op wil starten
        We maken de 18m en 25m competitie aan en daaronder de deelcompetities voor regio, rayon en bond

        Wedstrijdklassen volgen later, tijdens het bepalen van de klassengrenzen
    """
    yearend = date(year=jaar, month=12, day=31)     # 31 december
    udvl = date(year=jaar, month=8, day=1)          # 1 augustus = uiterste datum van lidmaatschap voor deelname teamcompetitie

    # maak de Competitie aan voor 18m en 25m
    for afstand, beschrijving in Competitie.AFSTAND:
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
                        deel.functie = Functie.objects.get(rol="RCL", comp_type=afstand, nhb_regio=obj)
                        deel.save()
                # for
            elif laag == DeelCompetitie.LAAG[1][0]:
                # RK
                for obj in NhbRayon.objects.all():
                    deel.nhb_rayon = obj
                    deel.pk = None
                    deel.functie = Functie.objects.get(rol="RKO", comp_type=afstand, nhb_rayon=obj)
                    deel.save()
                # for
            else:
                # BK
                deel.functie = Functie.objects.get(rol="BKO", comp_type=afstand)
                deel.save()
        # for
    # for

# end of file
