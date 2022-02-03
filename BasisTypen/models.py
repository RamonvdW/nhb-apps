# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


# leden zijn aspirant tot en met het jaar waarin ze 13 worden
MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT = 13

# leden zijn jeugdlid tot en met het jaar waarin ze 20 worden
MAXIMALE_LEEFTIJD_JEUGD = 20

GESLACHT_MAN = 'M'
GESLACHT_VROUW = 'V'
GESLACHT_ANDERS = 'X'

# geregistreerde geslacht van sporters: M/V/X
GESLACHT_MVX = [(GESLACHT_MAN, 'Man'),
                (GESLACHT_VROUW, 'Vrouw'),
                (GESLACHT_ANDERS, 'Anders')]

# voor wedstrijdklassen herkennen we alleen M/V
GESLACHT_MV = [(GESLACHT_MAN, 'Man'),
               (GESLACHT_VROUW, 'Vrouw')]

BLAZOEN_40CM = '40'
BLAZOEN_60CM = '60'
BLAZOEN_60CM_4SPOT = '4S'
BLAZOEN_DT = 'DT'
BLAZOEN_WENS_DT = 'DTw'
BLAZOEN_WENS_4SPOT = '4Sw'

BLAZOEN2STR = {
    BLAZOEN_40CM: '40cm',
    BLAZOEN_60CM: '60cm',
    BLAZOEN_60CM_4SPOT: '60cm 4-spot',
    BLAZOEN_DT: 'Dutch Target',
    BLAZOEN_WENS_DT: 'Dutch Target (wens)',
    BLAZOEN_WENS_4SPOT: '60cm 4-spot (wens)'
}

BLAZOEN2STR_COMPACT = {
    BLAZOEN_40CM: '40cm',
    BLAZOEN_60CM: '60cm',
    BLAZOEN_60CM_4SPOT: '60cm 4spot',
    BLAZOEN_DT: 'DT',
    BLAZOEN_WENS_DT: 'DT wens',
    BLAZOEN_WENS_4SPOT: '4spot wens'
}

COMPETITIE_BLAZOENEN = {
    '18': (BLAZOEN_40CM, BLAZOEN_DT, BLAZOEN_WENS_DT, BLAZOEN_60CM),
    '25': (BLAZOEN_60CM, BLAZOEN_60CM_4SPOT)
}

BLAZOEN_CHOICES = [
    (BLAZOEN_40CM, '40cm'),
    (BLAZOEN_60CM, '60cm'),
    (BLAZOEN_60CM_4SPOT, '60cm 4-spot'),
    (BLAZOEN_DT, 'Dutch Target')
]


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

        indexes = [
            # help vinden op afkorting
            models.Index(fields=['afkorting']),

            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

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

        indexes = [
            # help vinden op afkorting
            models.Index(fields=['afkorting']),

            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

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
    geslacht = models.CharField(max_length=1, choices=GESLACHT_MV)

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
        # <senior  heeft min = 0 en max <21
        # senior   heeft min = 0 en max = 0
        # >senior  heeft min >49 en max = 0     (komt niet voor in de competitie)
        return 0 < self.max_wedstrijdleeftijd <= MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT

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

    # is dit een klasse voor aspiranten?
    is_aspirant_klasse = models.BooleanField(default=False)

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    blazoen1_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)
    blazoen2_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen
    # (maar 1 keuze mogelijk)
    blazoen_18m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen_25m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Indiv Wedstrijdklasse"
        verbose_name_plural = "Indiv Wedstrijdklassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

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

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_18m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    blazoen1_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)
    blazoen2_25m_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen
    blazoen1_18m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_18m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    blazoen_25m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Team Wedstrijdklasse"
        verbose_name_plural = "Team Wedstrijdklassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

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

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


# end of file
