# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import (BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING,
                                   BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD,
                                   BESTELLING_KORT_BREAK)
from Bestelling.models import BestellingRegel
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_TO_STR,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  EVENEMENT_INSCHRIJVING_STATUS_BESTELD,
                                  EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                  EVENEMENT_INSCHRIJVING_STATUS_AFGEMELD,
                                  EVENEMENT_AFMELDING_STATUS_TO_STR,
                                  EVENEMENT_AFMELDING_STATUS_GEANNULEERD,
                                  EVENEMENT_AFMELDING_STATUS_AFGEMELD)
from Evenement.models import EvenementInschrijving, EvenementAfgemeld
from Mailer.operations import mailer_queue_email, mailer_email_is_valide, render_email_template
from decimal import Decimal

EMAIL_TEMPLATE_INFO_INSCHRIJVING_EVENEMENT = 'email_evenement/info-inschrijving-evenement.dtl'


class EvenementBestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        # evenementen
        mandje_pks = list()
        for inschrijving in (EvenementInschrijving
                             .objects
                             .filter(status=EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                     wanneer__lt=verval_datum)
                             .select_related('bestelling',
                                             'koper')):

            regel = inschrijving.bestelling

            self.stdout.write('[INFO] Vervallen: BestellingRegel pk=%s inschrijving (%s) in mandje van %s' % (
                              regel.pk, inschrijving, inschrijving.koper))

            # onthoud in welk mandje deze lag
            mandje = regel.bestellingmandje_set.first()
            mandje_pks.append(mandje)

            self._verwijder_reservering(inschrijving)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestellingRegel met pk=%s wordt verwijderd' % regel.pk)
            regel.delete()
        # for

        return mandje_pks

    def reserveer(self, inschrijving: EvenementInschrijving, mandje_van_str: str) -> BestellingRegel:
        """ Maak een reservering voor het evenement (zodat iemand anders deze niet kan reserveren)
            en geef een BestellingRegel terug.
        """
        evenement = inschrijving.evenement
        sporter = inschrijving.sporter

        # (nog) geen aantallen om bij te werken
        kort_lijst = ['Evenement "%s"' % evenement.titel,
                      'voor %s' % sporter.lid_nr_en_volledige_naam()]
        prijs_euro = evenement.bepaal_prijs_voor_sporter(sporter)
        # btw, korting em gewicht zijn niet van toepassing

        # maak een product regel aan voor de bestelling
        regel = BestellingRegel(
                        korte_beschrijving=BESTELLING_KORT_BREAK.join(kort_lijst),
                        bedrag_euro=prijs_euro,
                        code=BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING)
        regel.save()

        inschrijving.bestelling = regel

        inschrijving.status = EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, mandje_van_str)
        inschrijving.log += msg

        inschrijving.save(update_fields=['bestelling', 'status', 'log'])

        return regel

    def verwijder_reservering(self, regel: BestellingRegel) -> BestellingRegel | None:
        """
            Het product wordt uit het mandje gehaald
            of de bestelling wordt geannuleerd (voordat deze betaald is)
        """
        nieuwe_regel = None

        inschrijving = regel.evenementinschrijving_set.first()
        if inschrijving:
            if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
                # verwijdering uit mandje
                self.stdout.write('[INFO] Evenement inschrijving pk=%s status %s --> verwijderd uit mandje' % (
                                    inschrijving.pk,
                                    EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))
            else:
                # zet de inschrijving om in een afmelding
                nieuwe_regel = BestellingRegel(
                                    korte_beschrijving="[GEANNULEERD] " + regel.korte_beschrijving,
                                    code=BESTELLING_REGEL_CODE_EVENEMENT_AFGEMELD)
                nieuwe_regel.save()

                now = timezone.now()
                stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
                msg = "[%s] Annuleer inschrijving voor dit evenement\n" % stamp_str

                afmelding = EvenementAfgemeld(
                                    wanneer_inschrijving=inschrijving.wanneer,
                                    nummer=inschrijving.nummer,
                                    wanneer_afgemeld=now,
                                    status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                                    bestelling=nieuwe_regel,
                                    evenement=inschrijving.evenement,
                                    sporter=inschrijving.sporter,
                                    koper=inschrijving.koper,
                                    bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                                    log=inschrijving.log + msg)

                if inschrijving.status != EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
                    # nog niet betaald
                    afmelding.status = EVENEMENT_AFMELDING_STATUS_GEANNULEERD

                afmelding.save()

                self.stdout.write('[INFO] Evenement inschrijving pk=%s status %s --> afgemeld pk=%s status %s' % (
                                    inschrijving.pk,
                                    EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
                                    afmelding.pk,
                                    EVENEMENT_AFMELDING_STATUS_TO_STR[afmelding.status]))

            # verwijder de inschrijving
            inschrijving.delete()

        return nieuwe_regel

    def _verwijder_reservering(self, inschrijving: EvenementInschrijving) -> EvenementAfgemeld | None:
        # wordt gebruikt bij:
        # - inschrijving uit het mandje
        # - annuleren van een bestelling

        afmelding = None

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Verwijder reservering voor dit evenement\n" % stamp_str

        if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            # verwijdering uit mandje
            self.stdout.write('[INFO] Inschrijving evenement pk=%s status %s --> verwijderd uit mandje' % (
                              inschrijving.pk,
                              EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))
        else:
            # zet de inschrijving om in een afmelding
            afmelding = EvenementAfgemeld(
                            wanneer_inschrijving=inschrijving.wanneer,
                            nummer=inschrijving.nummer,
                            wanneer_afgemeld=now,
                            status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                            evenement=inschrijving.evenement,
                            sporter=inschrijving.sporter,
                            koper=inschrijving.koper,
                            bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                            log=inschrijving.log + msg)

            if inschrijving.status != EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
                # nog niet betaald
                afmelding.status = EVENEMENT_AFMELDING_STATUS_GEANNULEERD

            afmelding.save()

            self.stdout.write('[INFO] Inschrijving evenement pk=%s status %s --> afgemeld pk=%s status %s' % (
                                inschrijving.pk,
                                EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
                                afmelding.pk,
                                EVENEMENT_AFMELDING_STATUS_TO_STR[afmelding.status]))

        # verwijder de inschrijving
        inschrijving.delete()

        return afmelding

    def is_besteld(self, regel: BestellingRegel):
        """
            Het gereserveerde product in het mandje is nu omgezet in een bestelling.
            Verander de status van het gevraagde product naar 'besteld maar nog niet betaald'
        """
        inschrijving = EvenementInschrijving.objects.filter(regel=regel).first()
        if not inschrijving:
            self.stdout.write('[ERROR] Kan EvenementInschrijving voor regel met pk=%s niet vinden' % regel.pk)
            return

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Omgezet in een bestelling\n" % stamp_str

        inschrijving.status = EVENEMENT_INSCHRIJVING_STATUS_BESTELD
        inschrijving.log += msg
        inschrijving.save(update_fields=['status', 'log'])

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """
            Het product is betaald, dus de reservering moet definitief gemaakt worden.
            Wordt ook aangeroepen als een bestelling niet betaald hoeft te worden (totaal bedrag nul).
        """

        inschrijving = EvenementInschrijving.objects.filter(regel=regel).first()
        if not inschrijving:
            self.stdout.write('[ERROR] Kan EvenementInschrijving voor regel met pk=%s niet vinden' % regel.pk)
            return

        inschrijving.bedrag_ontvangen = bedrag_ontvangen
        inschrijving.status = EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Betaling ontvangen (euro %s); status is nu definitief\n" % (stamp_str,
                                                                                inschrijving.bedrag_ontvangen)

        inschrijving.log += msg
        inschrijving.save(update_fields=['bedrag_ontvangen', 'status', 'log'])

        evenement = inschrijving.evenement

        # stuur een e-mail naar de sporter, als dit niet de koper is
        sporter = inschrijving.sporter
        sporter_account = sporter.account
        koper_account = inschrijving.koper
        if sporter_account != koper_account:
            email = None
            if sporter_account and sporter_account.email_is_bevestigd:
                email = sporter_account.bevestigde_email
            else:
                if mailer_email_is_valide(sporter.email):
                    email = sporter.email

            if email:
                # maak de e-mail en stuur deze naar sporter.

                context = {
                    'voornaam': sporter.voornaam,
                    'koper_volledige_naam': koper_account.volledige_naam(),
                    'reserveringsnummer': settings.TICKET_NUMMER_START__EVENEMENT + inschrijving.nummer,
                    'evenement_titel': evenement.titel,
                    'evenement_adres': evenement.locatie.adres_oneliner(),
                    'evenement_datum': evenement.datum,
                    'evenement_org_ver': evenement.organiserende_vereniging,
                    'begin_tijd': evenement.aanvang.strftime('%H:%M'),
                    'contact_email': evenement.contact_email,
                    'contact_tel': evenement.contact_telefoon,
                    'geen_account': sporter.account is None,
                    'naam_site': settings.NAAM_SITE,
                }

                mail_body = render_email_template(context, EMAIL_TEMPLATE_INFO_INSCHRIJVING_EVENEMENT)

                mailer_queue_email(email,
                                   'Inschrijving voor evenement',
                                   mail_body)

                stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
                msg = "[%s] Informatieve e-mail is gestuurd naar sporter %s\n" % (stamp_str, sporter.lid_nr)
                inschrijving.log += msg
                inschrijving.save(update_fields=['log'])

                self.stdout.write('[INFO] Informatieve e-mail is gestuurd naar sporter %s' % sporter.lid_nr)
            else:
                msg = "[%s] Kan geen informatieve e-mail sturen naar sporter %s (geen e-mail beschikbaar)\n" % (
                    sporter.lid_nr, stamp_str)
                inschrijving.log += msg
                inschrijving.save(update_fields=['log'])

                self.stdout.write(
                    '[INFO] Kan geen informatieve e-mail sturen naar sporter %s (geen e-mail beschikbaar)' %
                    sporter.lid_nr)

    def afmelden(self, inschrijving: EvenementInschrijving):
        """
            Verwerk het verzoek tot afmelden voor een evenement.
        """
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Afgemeld voor dit evenement\n" % stamp_str

        # (nog) geen aantallen om bij te werken

        # zet de inschrijving om in een afmelding
        afmelding = EvenementAfgemeld(
                            wanneer_inschrijving=inschrijving.wanneer,
                            wanneer_afgemeld=now,
                            nummer=inschrijving.nummer,
                            status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                            evenement=inschrijving.evenement,
                            sporter=inschrijving.sporter,
                            koper=inschrijving.koper,
                            bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                            log=inschrijving.log + msg)
        afmelding.save()

        # inschrijving kan niet verwijderd worden in verband met verwijzing vanuit de bestelling
        # zet de originele inschrijving daarom op 'afgemeld'
        inschrijving.status = EVENEMENT_INSCHRIJVING_STATUS_AFGEMELD
        inschrijving.log += msg
        inschrijving.save(update_fields=['status', 'log'])

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """
            Bepaal welke vereniging de verkopende partij is
            Geeft het verenigingsnummer terug, of -1 als dit niet te bepalen was
        """
        ver_nr = -1
        inschrijving = EvenementInschrijving.objects.filter(regel=regel).select_related('evenement').first()
        if inschrijving:
            ver_nr = inschrijving.evenement.organiserende_vereniging.ver_nr
        else:
            self.stdout.write(
                '[ERROR] Kan EvenementInschrijving voor regel met pk=%s niet vinden (get_verkoper_ver_nr)' % regel.pk)

        return ver_nr


evenement_bestel_plugin = EvenementBestelPlugin()

# end of file
