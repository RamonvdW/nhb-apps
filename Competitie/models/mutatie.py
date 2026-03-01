# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Competitie.definities import (MUTATIE_TO_STR,
                                   MUTATIE_KAMP_AANMELDEN_RK_INDIV, MUTATIE_KAMP_AFMELDEN_RK_INDIV,
                                   MUTATIE_KAMP_AANMELDEN_BK_INDIV, MUTATIE_KAMP_AFMELDEN_BK_INDIV,
                                   MUTATIE_KAMP_CUT)
from Competitie.models.competitie import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.models.laag_regio import Regiocompetitie
from CompLaagBond.models import KampBK, DeelnemerBK
from CompLaagRayon.models import KampRK, DeelnemerRK
from Score.models import ScoreHist


class CompetitieMutatie(models.Model):
    """ Deze tabel houdt de mutaties bij aangevraagd zijn en door de achtergrond taak afgehandeld moeten worden.
        Alle verzoeken tot mutaties worden hier aan toegevoegd en na afhandelen bewaard zodat er geschiedenis is.
    """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie MUTATIE_*)
    mutatie = models.PositiveSmallIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # door wie is de mutatie geïnitieerd
    # als het een account is, dan volledige naam + rol
    # als er geen account is (sporter zonder account) dan lid details
    door = models.CharField(max_length=150, default='')

    # op welke competitie heeft deze mutatie betrekking?
    competitie = models.ForeignKey(Competitie,
                                   on_delete=models.CASCADE,
                                   null=True, blank=True)

    # op welke regiocompetitie heeft deze mutatie betrekking?
    regiocompetitie = models.ForeignKey(Regiocompetitie,
                                        on_delete=models.CASCADE,
                                        null=True, blank=True)

    # op welke kampioenschap heeft deze mutatie betrekking?
    kamp_rk = models.ForeignKey(KampRK,
                                on_delete=models.CASCADE,
                                null=True, blank=True)
    kamp_bk = models.ForeignKey(KampBK,
                                on_delete=models.CASCADE,
                                null=True, blank=True)

    # op welke klasse heeft deze mutatie betrekking?
    indiv_klasse = models.ForeignKey(CompetitieIndivKlasse,
                                     on_delete=models.CASCADE,
                                     null=True, blank=True)
    team_klasse = models.ForeignKey(CompetitieTeamKlasse,
                                    on_delete=models.CASCADE,
                                    null=True, blank=True)

    # op welke RK/BK deelnemer heeft de mutatie betrekking (aanmelden/afmelden)
    deelnemer_rk = models.ForeignKey(DeelnemerRK,
                                     on_delete=models.CASCADE,
                                     null=True, blank=True)
    deelnemer_bk = models.ForeignKey(DeelnemerBK,
                                     on_delete=models.CASCADE,
                                     null=True, blank=True)

    # alleen voor MUTATIE_CUT
    cut_oud = models.PositiveSmallIntegerField(default=0)
    cut_nieuw = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Competitie mutatie"

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = "[%s]" % timezone.localtime(self.when).strftime('%Y-%m-%d %H:%M:%S')
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        try:
            msg += " %s (%s)" % (self.mutatie, MUTATIE_TO_STR[self.mutatie])
        except KeyError:
            msg += " %s (???)" % self.mutatie

        if self.mutatie in (MUTATIE_KAMP_AANMELDEN_RK_INDIV, MUTATIE_KAMP_AFMELDEN_RK_INDIV):
            msg += " - %s" % self.deelnemer_rk

        if self.mutatie in (MUTATIE_KAMP_AANMELDEN_BK_INDIV, MUTATIE_KAMP_AFMELDEN_BK_INDIV):
            msg += " - %s" % self.deelnemer_bk

        if self.mutatie == MUTATIE_KAMP_CUT:
            msg += " (%s --> %s)" % (self.cut_oud, self.cut_nieuw)

        return msg


class CompetitieTaken(models.Model):

    """ simpele tabel om bij te houden hoe het met de achtergrond taken gaat """

    # wat is de hoogste ScoreHist tot nu toe verwerkt in de tussenstand?
    hoogste_scorehist = models.ForeignKey(ScoreHist,
                                          null=True, blank=True,        # mag leeg in admin interface
                                          on_delete=models.SET_NULL)

    # wat is de hoogste mutatie tot nu toe verwerkt in de deelnemerslijst?
    hoogste_mutatie = models.ForeignKey(CompetitieMutatie,              # TODO: afschaffen, zie BetaalMutatie
                                        null=True, blank=True,
                                        on_delete=models.SET_NULL)


def update_uitslag_teamcompetitie():
    # regiocomp_tussenstand moet gekieteld worden
    # maak daarvoor een ScoreHist record aan
    ScoreHist(score=None,
              oude_waarde=0,
              nieuwe_waarde=0,
              notitie="Trigger background task").save()


# end of file
