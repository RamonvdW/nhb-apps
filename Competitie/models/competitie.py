# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from BasisTypen.definities import BLAZOEN_CHOICES, BLAZOEN_40CM
from BasisTypen.models import BoogType, Leeftijdsklasse, TeamType
from Competitie.definities import AFSTANDEN, AFSTAND2URL
from Competitie.tijdlijn import bepaal_fase_indiv, bepaal_fase_teams


class Competitie(models.Model):
    """ Deze database tabel bevat een van de jaarlijkse competities voor 18m of 25m
        Elke competitie heeft een beschrijving, een aantal belangrijke datums
        en een lijst van wedstrijdklassen met aanvangsgemiddelden
    """

    # "Indoor competitie 2024/2025"
    # "25m 1pijl competitie 2024/2025"
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
    # RegioComp bevat de (regio specifieke) begin_fase_D voor de teamcompetitie

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

    def is_openbaar_voor_publiek(self):
        if not hasattr(self, 'fase_indiv'):
            self.fase_indiv = bepaal_fase_indiv(self)

        # openbaar voor het publiek vanaf inschrijving tot einde
        return self.fase_indiv >= 'C'

    def is_open_voor_inschrijven(self):
        if not hasattr(self, 'fase_indiv'):
            self.fase_indiv = bepaal_fase_indiv(self)

        # inschrijven mag het hele seizoen, ook tijdens de wedstrijden
        return 'C' <= self.fase_indiv <= 'F'

    def maak_seizoen_str(self):
        return "%s/%s" % (self.begin_jaar, self.begin_jaar + 1)

    def maak_seizoen_url(self):
        return '%s-%s-%s' % (AFSTAND2URL[self.afstand], self.begin_jaar, self.begin_jaar + 1)

    class Meta:
        ordering = ['begin_jaar', 'afstand']
        verbose_name = 'Competitie'
        verbose_name_plural = 'Competities'

    objects = models.Manager()      # for the editor only


def get_competitie_boog_typen(comp: Competitie):
    """ Geef een lijst van BoogType records terug die gebruikt worden in deze competitie,
        gesorteerd op 'volgorde'.
    """
    return comp.boogtypen.order_by('volgorde')



# end of file
