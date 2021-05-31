# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


# leden zijn aspirant tot en met het jaar waarin ze 13 worden
MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT = 13

# leden zijn jeugdlid tot en met het jaar waarin ze 20 worden
MAXIMALE_LEEFTIJD_JEUGD = 20

GESLACHT = [('M', 'Man'), ('V', 'Vrouw')]


class BoogType(models.Model):
    """ boog typen: volledige naam en unique afkorting """
    beschrijving = models.CharField(max_length=50)
    afkorting = models.CharField(max_length=5)

    # sorteervolgorde zodat order_by('volgorde') de juiste sortering oplevert
    volgorde = models.CharField(max_length=1, default='?')

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "(%s) %s" % (self.afkorting,
                            self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Boog type"
        verbose_name_plural = "Boog types"

    objects = models.Manager()      # for the editor only


class TeamType(models.Model):
    """ team type: voor gebruik in de team competities """

    # Recurve team, etc.
    beschrijving = models.CharField(max_length=50)

    # R/C/BB/IB/LB
    afkorting = models.CharField(max_length=2)

    # sorteervolgorde zodat order_by('volgorde') de juiste sortering oplevert
    volgorde = models.CharField(max_length=1, default='?')

    # toegestane boogtypen
    boog_typen = models.ManyToManyField(BoogType)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "(%s) %s" % (self.afkorting,
                            self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Team type"
        verbose_name_plural = "Team typen"

    objects = models.Manager()      # for the editor only


class LeeftijdsKlasse(models.Model):
    """ definitie van een leeftijdsklasse """

    # SH = Senioren mannen, etc.
    afkorting = models.CharField(max_length=5)

    # korte beschrijving: 'Cadet', etc.
    klasse_kort = models.CharField(max_length=30)

    # complete beschrijving: 'Cadetten, meisjes'
    beschrijving = models.CharField(max_length=80)      # CH Cadetten, mannen

    # man of vrouw
    geslacht = models.CharField(max_length=1, choices=GESLACHT)

    # leeftijds grenzen voor de klassen: of ondergrens, of bovengrens
    #   de jeugdklassen hebben een leeftijd bovengrens
    #   de masters en veteranen klassen hebben een leeftijd ondergrens
    #   de senioren klasse heeft helemaal geen grens
    min_wedstrijdleeftijd = models.IntegerField()
    max_wedstrijdleeftijd = models.IntegerField()

    # is dit een definitie volgens World Archery?
    # kan gebruikt om te filteren bij A-status wedstrijden
    volgens_wa = models.BooleanField(default=True)

    # presentatie volgorde: aspirant als laagste, veteraan als hoogste
    volgorde = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s %s" % (self.afkorting,
                          self.beschrijving)

    def is_aspirant_klasse(self):
        return self.max_wedstrijdleeftijd <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT

    def leeftijd_is_compatible(self, wedstrijdleeftijd):

        """ voldoet de wedstrijdleeftijd aan de eisen van deze wedstrijdklasse? """

        if wedstrijdleeftijd < self.min_wedstrijdleeftijd:
            # voldoet niet aan ondergrens
            return False

        if self.max_wedstrijdleeftijd and wedstrijdleeftijd > self.max_wedstrijdleeftijd:
            # voldoet niet aan de bovengrens
            return False

        # voldoet aan de eisen
        return True

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Leeftijdsklasse"
        verbose_name_plural = "Leeftijdsklassen"

    objects = models.Manager()      # for the editor only


class IndivWedstrijdklasse(models.Model):
    """ definitie van een wedstrijdklasse voor de bondscompetities """

    # klassen die verouderd zijn krijgen worden op deze manier eruit gehaald
    # zonder dat referenties die nog in gebruik zijn kapot gaan
    buiten_gebruik = models.BooleanField(default=False)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren Klasse 2
    beschrijving = models.CharField(max_length=80)

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    # lager nummer = betere schutters
    volgorde = models.PositiveIntegerField()

    # de leeftijdsklassen: aspirant, cadet, junior, senior en mannen/vrouwen
    # typisch zijn twee klassen: mannen en vrouwen
    leeftijdsklassen = models.ManyToManyField(LeeftijdsKlasse)

    # wedstrijdklasse wel/niet meenemen naar de RK/BK
    # staat op True voor aspiranten klassen
    niet_voor_rk_bk = models.BooleanField()

    # is dit bedoeld als klasse onbekend?
    # bevat typische ook "Klasse Onbekend" in de titel
    is_onbekend = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Indiv Wedstrijdklasse"
        verbose_name_plural = "Indiv Wedstrijdklassen"

    objects = models.Manager()      # for the editor only


class TeamWedstrijdklasse(models.Model):
    """ definitie van een team wedstrijdklasse voor de bondscompetitie """

    # niet meer gebruiken?
    buiten_gebruik = models.BooleanField(default=False)

    # voor welk team type is deze wedstrijdklasse?
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT,
                                  null=True)                # nodig voor migratie

    # sorteervolgorde
    # lager nummer = betere schutters
    volgorde = models.PositiveIntegerField()

    # voorbeeld: Recurve klasse ERE
    beschrijving = models.CharField(max_length=80)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Team Wedstrijdklasse"
        verbose_name_plural = "Team Wedstrijdklassen"

    objects = models.Manager()      # for the editor only


class KalenderWedstrijdklasse(models.Model):
    """ definitie van de wedstrijdklassen voor de wedstrijdkalender """

    # klassen die verouderd zijn krijgen worden op deze manier eruit gehaald
    # zonder dat referenties die nog in gebruik zijn kapot gaan
    buiten_gebruik = models.BooleanField(default=False)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren
    beschrijving = models.CharField(max_length=80)

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # de leeftijdsklassen: mannen/vrouwen en aspirant, cadet, junior, senior, master, veteraan
    leeftijdsklasse = models.ForeignKey(LeeftijdsKlasse, on_delete=models.PROTECT)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    volgorde = models.PositiveIntegerField()

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "KalenderWedstrijdklasse"
        verbose_name_plural = "KalenderWedstrijdklassen"

    objects = models.Manager()      # for the editor only


# end of file
