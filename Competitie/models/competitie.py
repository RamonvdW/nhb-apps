# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import BLAZOEN_CHOICES, BLAZOEN_40CM
from BasisTypen.models import BoogType, Leeftijdsklasse, TeamType
from Competitie.definities import AFSTANDEN, AFSTAND2URL
from Competitie.tijdlijn import bepaal_fase_indiv, bepaal_fase_teams
from Functie.definities import Rollen
from Locatie.models import Locatie
from Score.models import Uitslag
from Vereniging.models import Vereniging
import logging

my_logger = logging.getLogger('MH.Competitie')


class Competitie(models.Model):
    """ Deze database tabel bevat een van de jaarlijkse competities voor 18m of 25m
        Elke competitie heeft een beschrijving, een aantal belangrijke datums
        en een lijst van wedstrijdklassen met aanvangsgemiddelden
    """
    beschrijving = models.CharField(max_length=40)

    # 18m of 25m
    afstand = models.CharField(max_length=2, choices=AFSTANDEN)

    # seizoen
    begin_jaar = models.PositiveSmallIntegerField()     # 2019

    # alle ondersteunde typen bogen en teams
    teamtypen = models.ManyToManyField(TeamType)
    boogtypen = models.ManyToManyField(BoogType)

    # ---------------
    # Regiocompetitie
    # ---------------

    # fase A: voorbereidingen door RCL en BKO
    #         AG vaststellen (BKO)
    #         klassengrenzen indiv + teams vaststellen (BKO)
    #         instellingen teams (RCL)

    klassengrenzen_vastgesteld = models.BooleanField(default=False)

    # fase B: voorbereidingen door RCL

    begin_fase_C = models.DateField(default='2000-01-01')

    # fase C: aanmelden sporters en teams
    #         teams aanmaken + koppel sporters + handmatig teams AG (HWL)
    #         controle handmatig AG (RCL)
    #         poules voorbereiden

    begin_fase_D_indiv = models.DateField(default='2000-01-01')     # typisch: 15 augustus
    # Regiocompetitie bevat de (regio specifieke) begin_fase_D voor de teamcompetitie

    # fase D: late inschrijvingen individueel
    #         incomplete teams verwijderen (RCL)
    #         alle teams in een poule plaatsen (RCL)

    # eerste datum wedstrijden
    begin_fase_F = models.DateField(default='2000-01-01')
    einde_fase_F = models.DateField(default='2000-01-01')

    # fase F: wedstrijden
    #         RCL hanteert de team rondes

    # fase G: wacht op afsluiten regiocompetitie (RCLs, daarna BKO)
    #         verstuur RK uitnodigingen + vraag bevestigen deelname
    #         deelnemerslijsten RKs opstellen

    # is de regiocompetitie nodig bezig?
    regiocompetitie_is_afgesloten = models.BooleanField(default=False)

    # ---------------------
    # Rayonkampioenschappen
    # ---------------------

    # aantal scores dat een individuele sporter neergezet moet hebben om gerechtigd te zijn voor deelname aan het RK
    aantal_scores_voor_rk_deelname = models.PositiveSmallIntegerField(default=6)

    # RK teams kunnen ingeschreven worden tot deze deadline
    datum_klassengrenzen_rk_bk_teams = models.DateField(default='2000-01-01')

    # fase J: RK deelnemers bevestigen deelname
    #         HWL's kunnen invallers koppelen voor RK teams
    #         RKO's moeten planning wedstrijden afronden
    #         verwijder incomplete RK teams (RKO)

    # zijn de team klassengrenzen voor de RK/BK vastgesteld?
    klassengrenzen_vastgesteld_rk_bk = models.BooleanField(default=False)

    # fase K: RK wedstrijden voorbereiden door vereniging: afmeldingen ontvangen, reserves oproepen
    #         (begint 2 weken voor eerste wedstrijd)

    # RK wedstrijd datums
    begin_fase_L_indiv = models.DateField(default='2000-01-01')
    einde_fase_L_indiv = models.DateField(default='2000-01-01')

    begin_fase_L_teams = models.DateField(default='2000-01-01')
    einde_fase_L_teams = models.DateField(default='2000-01-01')

    # fase L: RK wedstrijden, uitslagen ontvangen, inlezen en publiceren

    # RK uitslag bevestigd?
    rk_indiv_afgesloten = models.BooleanField(default=False)
    rk_teams_afgesloten = models.BooleanField(default=False)

    # fase N: RK uitslag bevestigd

    # automatisch: BK deelnemerslijst vastgesteld (niet openbaar)

    # ----
    # Bondskampioenschappen
    # ----

    # fase N: kleine BK klassen samenvoegen

    # kleine BK klassen samengevoegd?
    bk_indiv_klassen_zijn_samengevoegd = models.BooleanField(default=False)
    bk_teams_klassen_zijn_samengevoegd = models.BooleanField(default=False)

    # fase O: BK deelnemerslijsten openbaar
    #         BK wedstrijden voorbereiden: afmeldingen/oproepen reserves

    # BK wedstrijden datums
    begin_fase_P_indiv = models.DateField(default='2000-01-01')
    einde_fase_P_indiv = models.DateField(default='2000-01-01')

    begin_fase_P_teams = models.DateField(default='2000-01-01')
    einde_fase_P_teams = models.DateField(default='2000-01-01')

    # fase P: BK wedstrijden, uitslagen ontvangen, inlezen en publiceren

    # BK uitslag bevestigd?
    bk_indiv_afgesloten = models.BooleanField(default=False)
    bk_teams_afgesloten = models.BooleanField(default=False)

    # fase Q: BK uitslag bevestigd

    # nog te wijzigen?
    is_afgesloten = models.BooleanField(default=False)

    # fase Z: competitie afgesloten

    # als het RK afgelast is, toon dan deze tekst
    rk_is_afgelast = models.BooleanField(default=False)
    rk_afgelast_bericht = models.TextField(blank=True)

    # als het BK afgelast is, toon dan deze tekst
    bk_is_afgelast = models.BooleanField(default=False)
    bk_afgelast_bericht = models.TextField(blank=True)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        return self.beschrijving

    def is_indoor(self):
        return self.afstand == '18'

    def is_25m1pijl(self):
        return self.afstand == '25'

    def titel(self):
        if self.is_indoor():
            msg = 'Indoor'
        else:
            msg = '25m 1pijl'
        msg += ' %s/%s' % (self.begin_jaar, self.begin_jaar + 1)
        return msg

    def bepaal_fase(self):
        """ bepaalde huidige fase van de competitie en zet self.fase_indiv en self.fase_teams """
        self.fase_indiv = bepaal_fase_indiv(self)
        self.fase_teams = bepaal_fase_teams(self)
        # print('competitie: afstand=%s, fase_indiv=%s, fase_teams=%s' % (
        #           self.afstand, self.fase_indiv, self.fase_teams))

    def is_open_voor_inschrijven(self):
        if not hasattr(self, 'fase_indiv'):
            self.fase_indiv = bepaal_fase_indiv(self)

        # inschrijven mag het hele seizoen, ook tijdens de wedstrijden
        return 'C' <= self.fase_indiv <= 'F'

    def bepaal_openbaar(self, rol_nu):
        """ deze functie bepaalt of de competitie openbaar is voor de huidige rol
            en zet de is_openbaar variabele op het object.
        """
        self.is_openbaar = False

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # BB en BKO zien alles
            self.is_openbaar = True

        elif rol_nu in (Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL):
            # beheerders die de competitie opzetten zien competities die opgestart zijn
            self.is_openbaar = True

        else:
            if not hasattr(self, 'fase_indiv'):
                self.fase_indiv = bepaal_fase_indiv(self)

            if self.fase_indiv >= 'C':
                # modale gebruiker ziet alleen competities vanaf open-voor-inschrijving
                self.is_openbaar = True

    def maak_seizoen_str(self):
        return "%s/%s" % (self.begin_jaar, self.begin_jaar + 1)

    def maak_seizoen_url(self):
        return '%s-%s-%s' % (AFSTAND2URL[self.afstand], self.begin_jaar, self.begin_jaar + 1)

    objects = models.Manager()      # for the editor only


class CompetitieIndivKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor een competitie,
        met de vastgestelde aanvangsgemiddelden

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen::TemplateCompetitieIndivKlasse
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # beschrijving om te presenteren, bijvoorbeeld Recurve Junioren Klasse 2
    beschrijving = models.CharField(max_length=80)

    # volgende voor gebruik bij het presenteren van een lijst van klassen
    # lager nummer = betere / oudere deelnemers
    volgorde = models.PositiveIntegerField()

    # het boogtype, bijvoorbeeld Recurve
    boogtype = models.ForeignKey(BoogType, on_delete=models.PROTECT)

    # klassengrens voor deze competitie
    # individueel: 0.000 - 10.000
    # team som van de 3 beste = 0.003 - 30.000
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # de leeftijdsklassen: aspirant, cadet, junior, senior en mannen/vrouwen
    # typisch zijn twee klassen: mannen en vrouwen
    leeftijdsklassen = models.ManyToManyField(Leeftijdsklasse)

    # is dit bedoeld als klasse onbekend?
    # bevat typische ook "Klasse Onbekend" in de titel
    is_onbekend = models.BooleanField(default=False)

    # is dit een klasse voor aspiranten?
    is_aspirant_klasse = models.BooleanField(default=False)

    # wedstrijdklasse wel/niet meenemen naar de RK/BK
    # staat op False voor aspiranten klassen en klassen 'onbekend'
    is_ook_voor_rk_bk = models.BooleanField(default=False)

    # welke titel krijgt de hoogst geëindigde sport in deze klasse?
    # (regio: Regiokampioen, RK: Rayonkampioen, BK: Bondskampioen of Nederlands Kampioen)
    titel_bk = models.CharField(max_length=30, default='')

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen (geen keuze)
    blazoen_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # krijgt deze wedstrijdklasse een scheidsrechter toegekend op het RK en BK?
    krijgt_scheids_rk = models.BooleanField(default=False)
    krijgt_scheids_bk = models.BooleanField(default=False)

    # FUTURE: standaard limiet toevoegen voor elke klasse: 24

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = self.beschrijving + ' [' + self.boogtype.afkorting + '] (%.3f)' % self.min_ag
        if self.is_ook_voor_rk_bk:
            msg += ' regio+RK'
        else:
            msg += ' regio'
        return msg

    class Meta:
        verbose_name = "Competitie indiv klasse"
        verbose_name_plural = "Competitie indiv klassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


class CompetitieTeamKlasse(models.Model):
    """ Deze database tabel bevat de klassen voor de teamcompetitie,
        met de vastgestelde aanvangsgemiddelden.

        Deze tabel wordt aangemaakt aan de hand van de templates: BasisTypen.TemplateCompetitieTeamKlasse
        en de gerefereerde TeamType wordt hierin ook plat geslagen om het aantal database accesses te begrenzen.
    """

    # hoort bij
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # sorteervolgorde
    # lager nummer = betere sporter
    volgorde = models.PositiveIntegerField()

    # voorbeeld: Recurve klasse ERE
    beschrijving = models.CharField(max_length=80)

    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    # R/R2/C/BB/BB2/IB/TR/LB
    team_afkorting = models.CharField(max_length=3)

    # toegestane boogtypen in dit type team
    boog_typen = models.ManyToManyField(BoogType)

    # klassengrens voor deze competitie
    # individueel: 0.000 - 10.000
    # team som van de 3 beste = 0.003 - 30.000
    min_ag = models.DecimalField(max_digits=5, decimal_places=3)    # 10.000

    # voor de RK/BK teams worden nieuwe klassengrenzen vastgesteld, dus houd ze uit elkaar
    # niet van toepassing op individuele klassen
    is_voor_teams_rk_bk = models.BooleanField(default=False)

    # welke titel krijgt de hoogst geëindigde sport in deze klasse?
    # (regio: Regiokampioen, RK: Rayonkampioen, BK: Bondskampioen of Nederlands Kampioen)
    titel_bk = models.CharField(max_length=30, default='')

    # op welk soort blazoen schiet deze klasse in de regiocompetitie
    # als er meerdere opties zijn dan is blazoen1 != blazoen2
    blazoen1_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)
    blazoen2_regio = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # op welk soort blazoen schiet deze klasse in de kampioenschappen
    blazoen_rk_bk = models.CharField(max_length=2, choices=BLAZOEN_CHOICES, default=BLAZOEN_40CM)

    # krijgt deze wedstrijdklasse een scheidsrechter toegekend op het RK en BK?
    krijgt_scheids_rk = models.BooleanField(default=False)
    krijgt_scheids_bk = models.BooleanField(default=False)

    # FUTURE: standaard limiet toevoegen voor elke klasse: ERE=12, rest=8

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = self.beschrijving + ' [' + self.team_afkorting + '] (%.3f)' % self.min_ag
        if self.is_voor_teams_rk_bk:
            msg += ' (RK/BK)'
        else:
            msg += ' (regio)'
        return msg

    class Meta:
        verbose_name = "Competitie team klasse"
        verbose_name_plural = "Competitie team klassen"

        indexes = [
            # help sorteren op volgorde
            models.Index(fields=['volgorde']),
        ]

    objects = models.Manager()      # for the editor only


def get_competitie_indiv_leeftijdsklassen(comp):
    lijst = list()
    pks = list()
    for klasse in (CompetitieIndivKlasse
                   .objects
                   .filter(competitie=comp)
                   .prefetch_related('leeftijdsklassen')):
        for lkl in klasse.leeftijdsklassen.all():
            if lkl.pk not in pks:
                # verwijder "Gemengd" uit de klasse beschrijving omdat dit niet relevant is voor de bondscompetitie
                lkl.beschrijving = lkl.beschrijving.replace(' Gemengd', '')
                pks.append(lkl.pk)
                tup = (lkl.volgorde, lkl.pk, lkl)
                lijst.append(tup)
        # for
    # for

    lijst.sort()        # op volgorde
    return [lkl for _, _, lkl in lijst]


def get_competitie_boog_typen(comp):
    """ Geef een lijst van BoogType records terug die gebruikt worden in deze competitie,
        gesorteerd op 'volgorde'.
    """
    return comp.boogtypen.order_by('volgorde')


class CompetitieMatch(models.Model):
    """ CompetitieMatch is de kleinste planbare eenheid in de bondscompetitie """

    # hoort bij welke competitie?
    # (ook nuttig voor filteren toepasselijke indiv_klassen / team_klassen)
    competitie = models.ForeignKey(Competitie, on_delete=models.CASCADE)

    # beschrijving
    beschrijving = models.CharField(max_length=100, blank=True)

    # organiserende vereniging
    vereniging = models.ForeignKey(Vereniging, on_delete=models.PROTECT,
                                   blank=True, null=True)   # mag later ingevuld worden

    # waar
    locatie = models.ForeignKey(Locatie, on_delete=models.PROTECT,
                                blank=True, null=True)      # mag later ingevuld worden

    # datum en tijdstippen
    datum_wanneer = models.DateField()
    tijd_begin_wedstrijd = models.TimeField()

    # competitie klassen individueel en teams
    indiv_klassen = models.ManyToManyField(CompetitieIndivKlasse,
                                           blank=True)  # mag leeg zijn / gemaakt worden

    team_klassen = models.ManyToManyField(CompetitieTeamKlasse,
                                          blank=True)  # mag leeg zijn / gemaakt worden

    # uitslag / scores
    uitslag = models.ForeignKey(Uitslag, on_delete=models.PROTECT,
                                blank=True, null=True)

    # benodigde scheidsrechters
    aantal_scheids = models.IntegerField(default=0)

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        extra = ""
        if self.vereniging:
            extra = " bij %s" % self.vereniging
        return "(%s) %s %s%s: %s" % (self.pk, self.datum_wanneer, self.tijd_begin_wedstrijd, extra, self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Competitie match"
        verbose_name_plural = "Competitie matches"


# end of file
