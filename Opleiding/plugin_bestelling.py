# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import BESTELLING_REGEL_CODE_OPLEIDING, BESTELLING_KORT_BREAK
from Bestelling.models import BestellingRegel
from Betaal.format import format_bedrag_euro
from Functie.models import Functie
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_TO_STR, OPLEIDING_AFMELDING_STATUS_TO_STR,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  OPLEIDING_INSCHRIJVING_STATUS_BESTELD,
                                  OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                                  OPLEIDING_INSCHRIJVING_STATUS_AFGEMELD,
                                  OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                                  OPLEIDING_AFMELDING_STATUS_GEANNULEERD)
from Opleiding.models import OpleidingInschrijving, OpleidingAfgemeld
from Taken.operations import maak_taak, check_taak_bestaat
from decimal import Decimal
import datetime


class OpleidingBestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        mandje_pks = list()
        for inschrijving in (OpleidingInschrijving
                             .objects
                             .filter(status=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                     wanneer_aangemeld__lt=verval_datum)
                             .select_related('bestelling',
                                             'koper')):

            regel = inschrijving.bestelling

            self.stdout.write('[INFO] Vervallen: BestellingRegel pk=%s inschrijving (%s) in mandje van %s' % (
                              regel.pk, inschrijving, inschrijving.koper))

            # onthoud in welk mandje deze lag
            mandje = regel.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            self.annuleer(regel)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestellingRegel met pk=%s wordt verwijderd' % regel.pk)
            regel.delete()
        # for

        return mandje_pks

    def reserveer(self, product_pk: int, mandje_van_str: str) -> BestellingRegel | None:
        """ Maak een reservering voor de opleiding
            en geef een BestellingRegel terug.
        """
        inschrijving = (OpleidingInschrijving
                        .objects
                        .select_related('opleiding',
                                        'sporter')
                        .filter(pk=product_pk)
                        .first())

        if not inschrijving:
            self.stdout.write('[WARNING] {opleiding bestel plugin}.reserveer: ' +
                              'kan OpleidingInschrijving met pk=%s niet vinden' % product_pk)
            return None

        # handmatige inschrijving heeft meteen status definitief en hoeft dus niet betaald te worden
        if inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF:
            return None

        opleiding = inschrijving.opleiding
        sporter = inschrijving.sporter

        # (nog) geen aantallen om bij te werken
        kort_lijst = ['Opleiding "%s"' % opleiding.titel,
                      'voor %s' % sporter.lid_nr_en_volledige_naam()]
        # btw, korting en gewicht zijn niet van toepassing

        # maak een product regel aan voor de bestelling
        regel = BestellingRegel(
                        korte_beschrijving=BESTELLING_KORT_BREAK.join(kort_lijst),
                        bedrag_euro=opleiding.kosten_euro,
                        code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel.save()

        inschrijving.bestelling = regel
        inschrijving.status = OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE
        inschrijving.nummer = inschrijving.pk

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, mandje_van_str)
        inschrijving.log += msg

        inschrijving.save(update_fields=['bestelling', 'log', 'status', 'nummer'])

        self.stdout.write('[DEBUG] Opleiding inschrijving pk=%s heeft status %s (%s)' % (
                          inschrijving.pk, inschrijving.status,
                          OPLEIDING_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))

        return regel

    def afmelden(self, product_pk: int):
        """
            Verwerk het verzoek tot afmelden voor een opleiding.
        """
        inschrijving = (OpleidingInschrijving
                        .objects
                        .select_related('opleiding',
                                        'sporter',
                                        'koper')
                        .get(pk=product_pk))

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Afgemeld voor deze opleiding\n" % stamp_str

        # (nog) geen aantallen om bij te werken

        # zet de inschrijving om in een afmelding
        afmelding = OpleidingAfgemeld(
                        wanneer_aangemeld=inschrijving.wanneer_aangemeld,
                        wanneer_afgemeld=now,
                        nummer=inschrijving.nummer,
                        status=OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                        opleiding=inschrijving.opleiding,
                        sporter=inschrijving.sporter,
                        koper=inschrijving.koper,
                        bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                        log=inschrijving.log + msg)
        afmelding.save()

        # behoud de inschrijving, in verband met de verwijzing vanuit een bestelling
        # zet de status op afgemeld
        inschrijving.status = OPLEIDING_INSCHRIJVING_STATUS_AFGEMELD
        inschrijving.log += msg
        inschrijving.save(update_fields=['status', 'log'])

    def annuleer(self, regel: BestellingRegel):
        """
            Het product wordt uit het mandje gehaald of de bestelling wordt geannuleerd (voordat deze betaald is)

            Geef een eerder gemaakte reservering voor een opleiding weer vrij
            zodat deze door iemand anders te kiezen zijn.
        """
        inschrijving = OpleidingInschrijving.objects.filter(bestelling=regel).first()
        if not inschrijving:
            self.stdout.write('[ERROR] Kan OpleidingInschrijving voor regel met pk=%s niet vinden' % regel.pk)
            return

        if inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            # verwijdering uit mandje
            self.stdout.write('[INFO] Opleiding inschrijving pk=%s status %s --> verwijderd uit mandje' % (
                                inschrijving.pk,
                                OPLEIDING_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))
        else:
            # zet de inschrijving om in een afmelding
            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            msg = "[%s] Annuleer inschrijving voor deze opleiding\n" % stamp_str

            afmelding = OpleidingAfgemeld(
                            wanneer_aangemeld=inschrijving.wanneer_aangemeld,
                            nummer=inschrijving.nummer,
                            wanneer_afgemeld=now,
                            status=OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                            opleiding=inschrijving.opleiding,
                            bestelling=None,
                            sporter=inschrijving.sporter,
                            koper=inschrijving.koper,
                            bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                            log=inschrijving.log + msg)

            if inschrijving.status != OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF:
                # nog niet betaald
                afmelding.status = OPLEIDING_AFMELDING_STATUS_GEANNULEERD

            afmelding.save()

            self.stdout.write('[INFO] Opleiding inschrijving pk=%s status %s --> afgemeld pk=%s status %s' % (
                                inschrijving.pk,
                                OPLEIDING_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
                                afmelding.pk,
                                OPLEIDING_AFMELDING_STATUS_TO_STR[afmelding.status]))

        # verwijder de inschrijving
        self.stdout.write('[INFO] OpleidingInschrijving pk=%s wordt verwijderd' % inschrijving.pk)
        inschrijving.delete()

    def is_besteld(self, regel: BestellingRegel):
        """
            Het gereserveerde product in het mandje is nu omgezet in een bestelling.
            Verander de status van het gevraagde product naar 'besteld maar nog niet betaald'
        """
        inschrijving = OpleidingInschrijving.objects.filter(bestelling=regel).first()
        if not inschrijving:
            self.stdout.write('[ERROR] Kan OpleidingInschrijving voor regel met pk=%s niet vinden' % regel.pk)
            return

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Omgezet in een bestelling\n" % stamp_str

        inschrijving.status = OPLEIDING_INSCHRIJVING_STATUS_BESTELD
        inschrijving.log += msg
        inschrijving.save(update_fields=['status', 'log'])

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """
            Het product is betaald, dus de reservering moet definitief gemaakt worden.
            Wordt ook aangeroepen als een bestelling niet betaald hoeft te worden (totaal bedrag nul).
        """
        inschrijving = OpleidingInschrijving.objects.filter(bestelling=regel).first()
        if not inschrijving:
            self.stdout.write('[ERROR] Kan OpleidingInschrijving voor regel met pk=%s niet vinden' % regel.pk)
            return

        inschrijving.bedrag_ontvangen = bedrag_ontvangen
        inschrijving.status = OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        bedrag_str = format_bedrag_euro(bedrag_ontvangen)
        msg = "[%s] Betaling ontvangen (%s); status is nu definitief\n" % (stamp_str, bedrag_str)
        inschrijving.log += msg

        inschrijving.save(update_fields=['bedrag_ontvangen', 'status', 'log'])

        # sporter is altijd de koper, dus de juiste mails zijn al gestuurd door de Bestellingen applicatie

        # maak een taak voor het bondsbureau om ze te informeren over de nieuwe inschrijving
        functie = Functie.objects.get(rol='MO')        # manager opleidingen

        opleiding = inschrijving.opleiding

        # maak taken aan om door te geven dat er nieuwe feedback is
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        taak_log = "[%s] Taak aangemaakt" % stamp_str
        taak_deadline = now + datetime.timedelta(days=7)
        taak_tekst = "Er is een nieuwe betaalde inschrijving voor de opleiding '%s'" % opleiding.beschrijving

        if not check_taak_bestaat(toegekend_aan_functie=functie, beschrijving=taak_tekst):
            maak_taak(toegekend_aan_functie=functie,
                      deadline=taak_deadline,
                      aangemaakt_door=None,         # None = 'systeem'
                      onderwerp='Nieuwe inschrijving voor opleiding',
                      beschrijving=taak_tekst,
                      log=taak_log)

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """
            Bepaal welke vereniging de verkopende partij is
            Geeft het verenigingsnummer terug, of -1 als dit niet te bepalen was
        """

        # alle opleidingen worden verkocht door het bondsbureau
        # TODO: organiserende_vereniging toevoegen aan elke opleiding
        return settings.WEBWINKEL_VERKOPER_VER_NR


opleiding_bestel_plugin = OpleidingBestelPlugin()

# end of file
