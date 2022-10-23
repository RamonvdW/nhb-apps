# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models


BONDSPAS_STATUS_NIEUW = 'N'         # nieuw verzoek nog niet helemaal ingevuld
BONDSPAS_STATUS_OPHALEN = 'O'       # nog niet opgepikt door achtergrondtaak
BONDSPAS_STATUS_BEZIG = 'B'         # bezig met downloaden
BONDSPAS_STATUS_AANWEZIG = 'A'      # pas is aanwezig
BONDSPAS_STATUS_FAIL = 'F'          # downloaden is mislukt
BONDSPAS_STATUS_VERWIJDERD = 'V'    # om ruimte te besparen is de pas verwijderd

BONDSPAS_STATUS = [
    (BONDSPAS_STATUS_NIEUW, 'Nieuw verzoek'),
    (BONDSPAS_STATUS_OPHALEN, 'Ophaal verzoek'),
    (BONDSPAS_STATUS_BEZIG, 'In behandeling'),
    (BONDSPAS_STATUS_AANWEZIG, 'Aanwezig'),
    (BONDSPAS_STATUS_FAIL, 'Mislukt'),
    (BONDSPAS_STATUS_VERWIJDERD, 'Verwijderd')
]


# TODO: deze tabel is niet meer nodig
class Bondspas(models.Model):

    """ administratie van de Bondspas bestanden """

    # lid nummer waar deze pas bij hoort
    lid_nr = models.PositiveIntegerField(primary_key=True)

    # status van deze pas
    status = models.CharField(max_length=1, choices=BONDSPAS_STATUS, default=BONDSPAS_STATUS_NIEUW)

    # wanneer is de bondspas opgehaald (helpt bij het verwijderen van de oudste passen)
    # alleen geldig als status == BONDSPAS_STATUS_AANWEZIG
    aanwezig_sinds = models.DateTimeField(null=True, blank=True)

    # in geval van download problemen blokkeren we opnieuw downloaden tot dit tijdstip
    # alleen geldig als status = BONDSPAS_STATUS_FAIL
    opnieuw_proberen_na = models.DateTimeField(null=True, blank=True)

    # naam van het bestand op disk voor deze bondspas
    filename = models.CharField(max_length=50, blank=True)

    # hoe vaak heeft de gebruiker de pas bekeken?
    aantal_keer_bekeken = models.PositiveIntegerField(default=0)

    # hoe vaak is de pas (opnieuw) opgehaald door de achtergrondtaak?
    aantal_keer_opgehaald = models.PositiveIntegerField(default=0)

    # geschiedenis van het downloaden en verwijderen (maximaal 30 regels)
    log = models.TextField(blank=True)

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "%s (%s)" % (self.lid_nr, self.status)
        if self.aanwezig_sinds:
            msg += self.aanwezig_sinds.strftime(' %Y-%m-%d %H:%M utc')
        msg += " opgehaald:%s bekeken:%s" % (self.aantal_keer_opgehaald, self.aantal_keer_bekeken)
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "Bondspas"
        verbose_name_plural = "Bondspassen"

    objects = models.Manager()      # for the editor only


# end of file
