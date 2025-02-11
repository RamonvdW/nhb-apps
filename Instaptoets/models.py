# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils.timezone import localtime
from Sporter.models import Sporter
import datetime


class Categorie(models.Model):
    """ categorie van een vraag """

    # categorie van de vraag
    beschrijving = models.CharField(max_length=100, default='', blank=True)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "[%s] %s" % (self.pk, self.beschrijving)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Categorie"
        verbose_name_plural = "Categorieën"

    objects = models.Manager()      # for the editor only


class Vraag(models.Model):
    """ een vraag die bruikbaar is voor de instaptoets en de quiz """

    # mag de vraag getoond worden?
    is_actief = models.BooleanField(default=True)

    # selectief gebruik van de vragen
    gebruik_voor_toets = models.BooleanField(default=True)
    gebruik_voor_quiz = models.BooleanField(default=False)

    # categorie van de vraag
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True)

    # de tekst van de vraag
    vraag_tekst = models.TextField(blank=True)

    # de vier mogelijke antwoorden
    antwoord_a = models.TextField(blank=True)
    antwoord_b = models.TextField(blank=True)
    antwoord_c = models.TextField(blank=True)
    antwoord_d = models.TextField(blank=True)

    # welk van de antwoorden is de juiste?
    juiste_antwoord = models.CharField(default='A', max_length=1,
                                       choices=(('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')))

    # geschiedenis
    logboek = models.TextField(blank=True)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "[%s] %s.." % (self.pk, self.vraag_tekst[:60])

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Vraag"
        verbose_name_plural = "Vragen"

    objects = models.Manager()      # for the editor only


class ToetsAntwoord(models.Model):

    # TODO: cleanup toevoegen, want bij verwijderen quiz/toets blijven deze records achter

    """ vraag en bijbehorend antwoord
        wordt gebruikt voor Instaptoets en Quiz
    """

    # over welke vraag gaat dit?
    vraag = models.ForeignKey(Vraag, on_delete=models.CASCADE)

    # wat is het opgegeven antwoord?
    antwoord = models.CharField(default='?', max_length=1)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "[%s] %s : %s" % (self.pk, self.vraag.id, self.antwoord)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Toets antwoord"
        verbose_name_plural = "Toets antwoorden"

    objects = models.Manager()      # for the editor only


class Instaptoets(models.Model):

    # wanneer opgestart en afgerond
    opgestart = models.DateTimeField(auto_now_add=True)
    afgerond = models.DateTimeField(default=datetime.datetime(year=9999,
                                                              month=12,
                                                              day=31).replace(tzinfo=datetime.timezone.utc))

    # wie maakt deze toets?
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # hoeveel vragen zijn er geselecteerd?
    aantal_vragen = models.PositiveSmallIntegerField(default=0)

    # hoeveel antwoorden zijn er al ingevuld?
    aantal_antwoorden = models.PositiveSmallIntegerField(default=0)

    # de gekozen vragen (initieel met antwoord "?")
    # en de opgegeven antwoorden
    vraag_antwoord = models.ManyToManyField(ToetsAntwoord, blank=True)

    # actieve vraag
    huidige_vraag = models.ForeignKey(ToetsAntwoord, blank=True, null=True,
                                      on_delete=models.SET_NULL, related_name='toets_huidige')

    # eindresultaat
    is_afgerond = models.BooleanField(default=False)
    aantal_goed = models.PositiveSmallIntegerField(default=0)
    geslaagd = models.BooleanField(default=False)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "%s [%s]" % (localtime(self.opgestart).strftime('%Y-%m-%d %H:%M:%S'), self.sporter.pk)
        if self.is_afgerond:
            msg += " geslaagd: " if self.geslaagd else " gezakt: "
            msg += str(self.aantal_goed)
        else:
            msg += " nog niet af: %s" % self.aantal_antwoorden
        msg += '/%s' % self.aantal_vragen
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Instaptoets"
        verbose_name_plural = "Instaptoetsen"

    objects = models.Manager()      # for the editor only


class Quiz(models.Model):

    # wanneer opgestart
    opgestart = models.DateTimeField(auto_now_add=True)

    # wie maakt deze toets?
    sporter = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # hoeveel vragen zijn er geselecteerd?
    aantal_vragen = models.PositiveSmallIntegerField(default=0)

    # hoeveel antwoorden zijn er al ingevuld?
    aantal_antwoorden = models.PositiveSmallIntegerField(default=0)

    # de gekozen vragen (initieel met antwoord "?")
    # en de opgegeven antwoorden
    vraag_antwoord = models.ManyToManyField(ToetsAntwoord, blank=True)

    # actieve vraag
    huidige_vraag = models.ForeignKey(ToetsAntwoord, null=True, on_delete=models.SET_NULL, related_name='quiz_huidige')

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s [%s] %s/%s" % (localtime(self.opgestart).strftime('%Y-%m-%d %H:%M:%S'),
                                  self.sporter.pk,
                                  self.aantal_antwoorden, self.aantal_vragen)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzen"

    objects = models.Manager()      # for the editor only


class Uitdaging(models.Model):

    """ Uitdaging van de week/maand """

    # tonen vanaf datum
    tonen_vanaf = models.DateField(default='2000-01-01')

    # de geselecteerde vraag
    vraag = models.ForeignKey(Vraag, on_delete=models.CASCADE)

    # TODO: bijhouden wie de vraag al goed beantwoord hebben?

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "[%s] vanaf %s" % (self.pk, self.tonen_vanaf)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Uitdaging"
        verbose_name_plural = "Uitdagingen"

    objects = models.Manager()      # for the editor only


# end of file
