# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


# leden zijn aspirant tot en met het jaar waarin ze 13 worden (=Onder 14)
MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT = 13

# leden zijn jeugdlid tot en met het jaar waarin ze 20 worden
MAXIMALE_LEEFTIJD_JEUGD = 20

GESLACHT_MAN = 'M'          # geregistreerd geslacht / voor wedstrijdklassen
GESLACHT_VROUW = 'V'        # geregistreerd geslacht / voor wedstrijdklassen
GESLACHT_ANDERS = 'X'       # geregistreerd geslacht
GESLACHT_ALLE = 'A'         # genderneutraal voor wedstrijdklassen

GESLACHT2STR = {GESLACHT_MAN: 'Man',
                GESLACHT_VROUW: 'Vrouw',
                GESLACHT_ANDERS: 'Anders',
                GESLACHT_ALLE: 'Alle'}

# geregistreerde geslacht van sporters: M/V/X
GESLACHT_MVX = [(GESLACHT_MAN, 'Man'),
                (GESLACHT_VROUW, 'Vrouw'),
                (GESLACHT_ANDERS, 'Anders')]

# als voorkeur voor wedstrijden herkennen we alleen M/V
GESLACHT_MV = [(GESLACHT_MAN, 'Man'),
               (GESLACHT_VROUW, 'Vrouw')]

# keuzemogelijkheden bij het instellen van bovenstaande
GESLACHT_MV_MEERVOUD = [(GESLACHT_MAN, 'Mannen'),
                        (GESLACHT_VROUW, 'Vrouwen')]

# mogelijk geslacht van sporters in wedstrijden: M/V/A
WEDSTRIJDGESLACHT_MVA = [(GESLACHT_MAN, 'Man'),
                         (GESLACHT_VROUW, 'Vrouw'),
                         (GESLACHT_ALLE, 'Genderneutraal')]

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

# organisatie, om boogtype, leeftijdsklassen etc. uit elkaar te kunnen houden binnen 1 tabel
ORGANISATIE_WA = 'W'      # World Archery
ORGANISATIE_NHB = 'N'     # NHB
ORGANISATIE_IFAA = 'F'    # International Field Archery Association

ORGANISATIES = [
    (ORGANISATIE_WA, 'World Archery'),
    (ORGANISATIE_NHB, 'NHB'),
    (ORGANISATIE_IFAA, 'IFAA'),
]

ORGANISATIES2SHORT_STR = {
    ORGANISATIE_WA: 'WA',
    ORGANISATIE_NHB: 'NHB',
    ORGANISATIE_IFAA: 'IFAA',
}

# wordt gebruikt in de zin:
# Beschikbare disciplines van ...
ORGANISATIES2LONG_STR = {
    ORGANISATIE_WA: 'World Archery',
    ORGANISATIE_NHB: 'de NHB',
    ORGANISATIE_IFAA: 'de IFAA',
}

BOOGTYPE_AFKORTING_RECURVE = 'R'


class BoogType(models.Model):
    """ boog typen: volledige naam en unique afkorting """

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

    # R, C, etc.
    afkorting = models.CharField(max_length=5)

    # Recurve, etc.
    beschrijving = models.CharField(max_length=50)

    # sorteervolgorde zodat order_by('volgorde') de juiste sortering oplevert
    volgorde = models.PositiveSmallIntegerField(default=0)

    # is dit boogtype nog actueel?
    # zolang in gebruik blijft een boogtype bestaan
    # True = niet meer gebruiken voor nieuwe wedstrijden
    buiten_gebruik = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "(%s) %s" % (self.afkorting,
                            self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Boog type"
        verbose_name_plural = "Boog typen"

        ordering = ['volgorde']

        indexes = [
            # help vinden op afkorting
            models.Index(fields=['afkorting']),

            # FUTURE: extra index voor organisatie, in combinatie met afkorting/volgorde??
        ]

    objects = models.Manager()      # for the editor only


class TeamType(models.Model):
    """ team type: voor gebruik in de team competities """

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

    # R/R2/C/BB/BB2/IB/TR/LB
    afkorting = models.CharField(max_length=3)

    # Recurve team, etc.
    beschrijving = models.CharField(max_length=50)

    # sorteervolgorde zodat order_by('volgorde') de juiste sortering oplevert
    volgorde = models.PositiveSmallIntegerField(default=0)

    # toegestane boogtypen
    boog_typen = models.ManyToManyField(BoogType)

    # is dit team type nog actueel?
    # zolang in gebruik blijft een teamtype bestaan
    # True = niet meer gebruiken voor nieuwe wedstrijden
    buiten_gebruik = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "(%s) %s" % (self.afkorting,
                            self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Team type"
        verbose_name_plural = "Team typen"

        ordering = ['volgorde']

        indexes = [
            # help vinden op afkorting
            models.Index(fields=['afkorting']),

            # help sorteren op volgorde
            models.Index(fields=['volgorde']),

            # FUTURE: extra index voor organisatie, in combinatie met afkorting/volgorde??
        ]

    objects = models.Manager()      # for the editor only


class LeeftijdsKlasse(models.Model):
    """ definitie van een leeftijdsklasse """

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

    # SH = Senioren mannen, etc.
    afkorting = models.CharField(max_length=5)

    # complete beschrijving: 'Onder 18, meisjes'
    beschrijving = models.CharField(max_length=80)      # CH Cadetten, mannen

    # korte beschrijving: 'Onder 18', etc.
    klasse_kort = models.CharField(max_length=30)

    # man, vrouw of genderneutraal
    wedstrijd_geslacht = models.CharField(max_length=1, choices=WEDSTRIJDGESLACHT_MVA)

    # leeftijdsgrenzen voor de klassen: of ondergrens, of bovengrens
    #   de jeugdklassen hebben een leeftijd bovengrens
    #   de masters en veteranen klassen hebben een leeftijd ondergrens
    #   de senioren klasse heeft helemaal geen grens
    min_wedstrijdleeftijd = models.IntegerField()
    max_wedstrijdleeftijd = models.IntegerField()

    # presentatie volgorde: aspirant als laagste, veteraan als hoogste
    #  gender sub-volgorde: neutraal, man, vrouw
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

    def geslacht_is_compatible(self, wedstrijd_geslacht):
        """ past het wedstrijdgeslacht van de sporter bij deze leeftijdsklasse?

            leeftijdsklasse 'A' (alle) past bij alle wedstrijdgeslachten
            anders moet het een 'M'/'V' match zijn
        """
        return (self.wedstrijd_geslacht == GESLACHT_ALLE) or (wedstrijd_geslacht == self.wedstrijd_geslacht)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Leeftijdsklasse"
        verbose_name_plural = "Leeftijdsklassen"

        ordering = ['volgorde']

        # FUTURE: index voor organisatie, in combinatie met afkorting/volgorde??

    objects = models.Manager()      # for the editor only


class TemplateCompetitieIndivKlasse(models.Model):
    """ definitie van een individuele klasse voor de volgende bondscompetities """

    # toepasselijkheid
    gebruik_18m = models.BooleanField(default=True)
    gebruik_25m = models.BooleanField(default=True)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren Klasse 2
    beschrijving = models.CharField(max_length=80)

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    # lager nummer = betere / oudere deelnemers
    volgorde = models.PositiveIntegerField()

    # de leeftijdsklassen: Onder 12 Jongens/Meisjes, Onder 14 Jongens/Meisjes, Onder 18, Onder 21, 21+
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
        return "%s [%s]" % (self.beschrijving, self.boogtype.afkorting)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Template Competitie Indiv Klasse"
        verbose_name_plural = "Template Competitie Indiv Klassen"

        ordering = ['volgorde']

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


class TemplateCompetitieTeamKlasse(models.Model):
    """ definitie van een team klasse voor de volgende bondscompetities """

    # toepasselijkheid
    gebruik_18m = models.BooleanField(default=True)
    gebruik_25m = models.BooleanField(default=True)

    # voor welk team type is deze wedstrijdklasse?
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT, null=True)

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
    blazoen_18m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen_25m_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_60CM)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        msg = self.beschrijving
        if self.team_type:
            msg += ' [%s]' % self.team_type.afkorting
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Template Competitie Team Klasse"
        verbose_name_plural = "Template Competitie Team Klassen"

        ordering = ['volgorde']

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


class KalenderWedstrijdklasse(models.Model):
    """ definitie van de wedstrijdklassen voor de wedstrijdkalender """

    # WA, IFAA of nationaal
    organisatie = models.CharField(max_length=1, choices=ORGANISATIES, default=ORGANISATIE_WA)

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

    # officiële (internationale) afkorting voor deze wedstrijdklasse
    afkorting = models.CharField(max_length=10, default='?')

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return self.beschrijving

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Kalender Wedstrijdklasse"
        verbose_name_plural = "Kalender Wedstrijdklassen"

        ordering = ['volgorde']

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


# end of file
