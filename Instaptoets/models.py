# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils.timezone import localtime
from Sporter.models import Sporter
import datetime


class Vraag(models.Model):
    """ een vraag die bruikbaar is voor de instaptoets en de quiz """

    # mag de vraag getoond worden?
    is_actief = models.BooleanField(default=True)

    # selectief gebruik van de vragen
    gebruik_voor_toets = models.BooleanField(default=True)
    gebruik_voor_quiz = models.BooleanField(default=False)

    # de tekst van de vraag
    vraag_tekst = models.TextField(blank=True)

    # de vier mogelijke antwoorden
    antwoord_a = models.CharField(default='', max_length=200, blank=True)
    antwoord_b = models.CharField(default='', max_length=200, blank=True)
    antwoord_c = models.CharField(default='', max_length=200, blank=True)
    antwoord_d = models.CharField(default='', max_length=200, blank=True)

    # welk van de antwoorden is de juiste?
    juiste_antwoord = models.CharField(default='a', max_length=1)

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
        verbose_name = "Antwoord"
        verbose_name_plural = "Antwoorden"

    objects = models.Manager()      # for the editor only


class Instaptoets(models.Model):

    # wanneer opgestart
    opgestart = models.DateTimeField(auto_now_add=True)
    afgerond = models.DateTimeField(default=datetime.datetime(year=9999, month=12, day=31).replace(tzinfo=datetime.timezone.utc))

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
    huidige_vraag = models.ForeignKey(ToetsAntwoord, null=True, on_delete=models.SET_NULL, related_name='toets_huidige')

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "%s [%s] %s/%s" % (localtime(self.opgestart).strftime('%Y-%m-%d %H:%M:%S'),
                                  self.sporter.pk,
                                  self.aantal_antwoorden, self.aantal_vragen)

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


class VoorstelVraag(models.Model):
    """ Ingediend voorstel voor een nieuwe vraag """

    # wanneer is dit voorstel aangemaakt
    aangemaakt = models.DateTimeField(auto_now_add=True)

    # wie heeft de vraag ingediend?
    ingediend_door = models.ForeignKey(Sporter, on_delete=models.CASCADE)

    # de tekst van de vraag
    vraag_tekst = models.TextField(blank=True)

    # de vier mogelijke antwoorden
    antwoord_a = models.CharField(default='', max_length=200)
    antwoord_b = models.CharField(default='', max_length=200)
    antwoord_c = models.CharField(default='', max_length=200)
    antwoord_d = models.CharField(default='', max_length=200)

    # welk van de antwoorden is de juiste?
    juiste_antwoord = models.CharField(default='a', max_length=1)

    # geschiedenis
    logboek = models.TextField(blank=True)

    # TODO: status afhandelen aanvraag

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        return "[%s] %s.." % (self.pk, self.vraag_tekst[:60])

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "VoorstelVraag"
        verbose_name_plural = "VoorstelVragen"

    objects = models.Manager()      # for the editor only


# end of file
