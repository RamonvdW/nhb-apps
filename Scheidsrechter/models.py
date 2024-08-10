# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.db.models.constraints import UniqueConstraint
from Competitie.models import CompetitieMatch
from Scheidsrechter.definities import BESCHIKBAAR_CHOICES, BESCHIKBAAR2STR, BESCHIKBAAR_LEEG, SCHEIDS_MUTATIE_TO_STR
from Sporter.models import Sporter
from Wedstrijden.models import Wedstrijd


class ScheidsBeschikbaarheid(models.Model):
    """ Bijhouden van de beschikbaarheid van een scheidsrechter voor een specifieke datum """

    # over welke scheidsrechter gaat dit?
    scheids = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # voor welke wedstrijd is de behoefte?
    # (dit is nodig om meerdere wedstrijden per dag te ondersteunen)
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.CASCADE)

    # over welke datum gaat dit?
    # deze zetten we hier vast voor het geval de wedstrijd verplaatst wordt
    datum = models.DateField()

    # de laatste keuze voor de beschikbaarheid
    opgaaf = models.CharField(max_length=1, choices=BESCHIKBAAR_CHOICES, default=BESCHIKBAAR_LEEG)

    opmerking = models.CharField(max_length=100, default='', blank=True)

    # logboekje van de gemaakte wijzigingen
    log = models.TextField(default='', blank=True)

    def __str__(self):
        return "%s  %s: %s (%s)" % (self.scheids.lid_nr, self.datum, BESCHIKBAAR2STR[self.opgaaf], self.wedstrijd.titel)

    class Meta:
        verbose_name_plural = verbose_name = "Scheids beschikbaarheid"

        constraints = [
            UniqueConstraint(
                fields=['scheids', 'wedstrijd', 'datum'],
                name='Een per scheidsrechter en wedstrijd dag')
        ]


class WedstrijdDagScheidsrechters(models.Model):
    """ Bijhouden van de gekozen scheidsrechters voor een specifieke wedstrijd
        en de communicatie daarover.
    """

    # voor welke wedstrijd gaat dit?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.CASCADE)

    # voor elke dag van de wedstrijd een specifieke behoefte
    # eerste dag is 0
    dag_offset = models.SmallIntegerField(default=0)

    # welke hoofdscheidsrechter is gekozen?
    gekozen_hoofd_sr = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_hoofd_sr',
                                         null=True, blank=True)              # mag leeg zijn

    # welke scheidsrechters zijn er nog meer gekozen?
    gekozen_sr1 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr1',
                                    null=True, blank=True)

    gekozen_sr2 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr2',
                                    null=True, blank=True)

    gekozen_sr3 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr3',
                                    null=True, blank=True)

    gekozen_sr4 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr4',
                                    null=True, blank=True)

    gekozen_sr5 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr5',
                                    null=True, blank=True)

    gekozen_sr6 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr6',
                                    null=True, blank=True)

    gekozen_sr7 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr7',
                                    null=True, blank=True)

    gekozen_sr8 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr8',
                                    null=True, blank=True)

    gekozen_sr9 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='gekozen_sr9',
                                    null=True, blank=True)

    # welke scheidsrechters hebben een mailtje gekregen dat ze gekozen zijn voor een wedstrijd?
    # wordt gebruikt om de juiste mailtjes te sturen (je bent gekozen / niet meer gekozen) en geen dubbele mailtjes
    notified_srs = models.ManyToManyField(to=Sporter, related_name='notified_sr')

    # wanneer is de laatste ronde van notificatie mails gestuurd en door wie werd dat gevraagd?
    notified_laatste = models.CharField(max_length=100, default='', blank=True)

    def __str__(self):
        return "[%s +%s]" % (self.wedstrijd.datum_begin, self.dag_offset)

    class Meta:
        verbose_name_plural = verbose_name = "Wedstrijddag scheidsrechters"


class MatchScheidsrechters(models.Model):
    """ Bijhouden van de gekozen scheidsrechters voor een specifieke bondscompetitie wedstrijd
        en de communicatie daarover.
    """

    # voor welke bondscompetitie RK/BK wedstrijd gaat dit
    match = models.ForeignKey(CompetitieMatch, on_delete=models.CASCADE)

    # welke hoofdscheidsrechter is gekozen?
    gekozen_hoofd_sr = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='match_gekozen_hoofd_sr',
                                         null=True, blank=True)              # mag leeg zijn

    # welke scheidsrechters zijn er nog meer gekozen?
    gekozen_sr1 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='match_gekozen_sr1',
                                    null=True, blank=True)

    gekozen_sr2 = models.ForeignKey(Sporter, on_delete=models.SET_NULL, related_name='match_gekozen_sr2',
                                    null=True, blank=True)

    # welke scheidsrechters hebben een mailtje gekregen dat ze gekozen zijn voor een wedstrijd?
    # wordt gebruikt om de juiste mailtjes te sturen (je bent gekozen / niet meer gekozen) en geen dubbele mailtjes
    notified_srs = models.ManyToManyField(to=Sporter, related_name='match_notified_sr')

    # wanneer is de laatste ronde van notificatie mails gestuurd en door wie werd dat gevraagd?
    notified_laatste = models.CharField(max_length=100, default='', blank=True)

    def __str__(self):
        return "[%s]" % self.match.datum_wanneer

    class Meta:
        verbose_name_plural = verbose_name = "Match scheidsrechters"


class ScheidsMutatie(models.Model):
    """ Deze tabel houdt de mutaties bij aangevraagd zijn en door de achtergrond taak afgehandeld moeten worden.
        Alle verzoeken tot mutaties worden hier aan toegevoegd en na afhandelen bewaard zodat er geschiedenis is.
    """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie SCHEIDS_MUTATIE_*)
    mutatie = models.PositiveSmallIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # door wie is de mutatie geïnitieerd
    # als het een account is, dan volledige naam + rol
    # als er geen account is (sporter zonder account) dan lid details
    door = models.CharField(max_length=50, default='')

    # voor welke wedstrijd is dit verzoek?
    wedstrijd = models.ForeignKey(Wedstrijd, on_delete=models.CASCADE, null=True, blank=True)

    # voor welke bondscompetitie match is dit verzoek?
    match = models.ForeignKey(CompetitieMatch, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "Scheids mutatie"

    def __str__(self):
        """ geef een tekstuele afkorting van dit object, voor in de admin interface """
        msg = "[%s]" % self.when
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        try:
            msg += " %s (%s)" % (self.mutatie, SCHEIDS_MUTATIE_TO_STR[self.mutatie])
        except KeyError:
            msg += " %s (???)" % self.mutatie

        return msg


# end of file
