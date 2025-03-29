# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_IFAA
from Bestelling.definities import BESTELLING_REGEL_CODE_WEDSTRIJD, BESTELLING_KORT_BREAK
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.models import BestellingRegel
from Betaal.format import format_bedrag_euro
from Mailer.operations import mailer_email_is_valide, mailer_queue_email, render_email_template
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
from Wedstrijden.models import WedstrijdInschrijving, WedstrijdKorting, beschrijf_korting
from decimal import Decimal
import datetime

EMAIL_TEMPLATE_INFO_INSCHRIJVING_WEDSTRIJD = 'email_wedstrijden/info-inschrijving-wedstrijd.dtl'


class WedstrijdBestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        # evenementen
        mandje_pks = list()

        # wedstrijden
        for inschrijving in (WedstrijdInschrijving
                             .objects
                             .filter(wanneer__lt=verval_datum,
                                     status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)
                             .select_related('bestelling',
                                             'koper')):

            regel = inschrijving.bestelling

            self.stdout.write('[INFO] Vervallen: BestellingRegel pk=%s inschrijving (%s) in mandje van %s' % (
                              regel.pk, inschrijving, inschrijving.koper))

            mandje = regel.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            self.annuleer(regel)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestellingRegel met pk=%s wordt verwijderd' % regel.pk)
            regel.delete()
        # for

        return mandje_pks

    def reserveer(self, inschrijving: WedstrijdInschrijving, mandje_van_str: str) -> BestellingRegel:
        """ Maak een reservering voor de wedstrijd sessie (zodat iemand anders deze niet kan reserveren)
            en geef een BestellingRegel terug.
        """

        # verhoog het aantal inschrijvingen op deze sessie
        # hiermee geven we een garantie op een plekje
        # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
        sessie = inschrijving.sessie
        sessie.aantal_inschrijvingen += 1
        sessie.save(update_fields=['aantal_inschrijvingen'])

        wedstrijd = inschrijving.wedstrijd
        sporter = inschrijving.sporterboog.sporter

        kort_lijst = ['Wedstrijd "%s"' % wedstrijd.titel,
                      'deelname door %s' % sporter.lid_nr_en_volledige_naam(),
                      'met boog %s' % inschrijving.sporterboog.boogtype.beschrijving]

        prijs_euro = wedstrijd.bepaal_prijs_voor_sporter(sporter)
        # btw en gewicht zijn niet van toepassing
        # kortingen worden niet hier bepaald

        regel = BestellingRegel(
                    korte_beschrijving=BESTELLING_KORT_BREAK.join(kort_lijst),
                    bedrag_euro=prijs_euro,
                    code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel.save()

        inschrijving.bestelling = regel

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, mandje_van_str)
        inschrijving.log += msg

        inschrijving.save(update_fields=['bestelling', 'log'])

        return regel

    def afmelden(self, inschrijving: WedstrijdInschrijving):
        """
            Verwerk het verzoek tot afmelden voor een wedstrijd.
        """
        if inschrijving.status not in (WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                       WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD):
            self.stdout.write('[INFO] WedstrijdInschrijving met pk=%s afmelden' % inschrijving.pk)

            # verlaag het aantal inschrijvingen op deze sessie
            sessie = inschrijving.sessie
            sessie.aantal_inschrijvingen -= 1
            sessie.save(update_fields=['aantal_inschrijvingen'])

            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            msg = "[%s] Afgemeld voor de wedstrijd\n" % stamp_str
            inschrijving.log += msg

            inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD

            # inschrijving.sessie en inschrijving.klasse kunnen niet op None gezet worden
            # inschrijving mag niet verwijderd worden, in verband met mogelijk verwijzing vanuit bestelling

            inschrijving.save(update_fields=['status', 'log'])

    def annuleer(self, regel: BestellingRegel):
        """
            Het product wordt uit het mandje gehaald of de bestelling wordt geannuleerd (voordat deze betaald is)
            Geef een eerder gemaakte reservering voor een wedstrijd weer vrij.
        """
        inschrijving = WedstrijdInschrijving.objects.filter(bestelling=regel).first()
        if not inschrijving:
            self.stdout.write(
                '[ERROR] Kan WedstrijdInschrijving voor regel met pk=%s niet vinden {annuleer}' % regel.pk)
            return

        self.afmelden(inschrijving)

        # # zet de inschrijving om in een afmelding
        # now = timezone.now()
        # stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        # msg = "[%s] Annuleer inschrijving voor deze opleiding\n" % stamp_str
        #
        # afmelding = WedstrijdAfgemeld(
        #                 wanneer_aangemeld=inschrijving.wanneer_aangemeld,
        #                 nummer=inschrijving.nummer,
        #                 wanneer_afgemeld=now,
        #                 status=OPLEIDING_AFMELDING_STATUS_AFGEMELD,
        #                 opleiding=inschrijving.opleiding,
        #                 bestelling=None,
        #                 sporter=inschrijving.sporter,
        #                 koper=inschrijving.koper,
        #                 bedrag_ontvangen=inschrijving.bedrag_ontvangen,
        #                 log=inschrijving.log + msg)
        #
        # if inschrijving.status != WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
        #     # nog niet betaald
        #     afmelding.status = WEDSTRIJD_AFMELDING_STATUS_GEANNULEERD
        #
        # afmelding.save()
        #
        # self.stdout.write('[INFO] Wedstrijd inschrijving pk=%s status %s --> afgemeld pk=%s status %s' % (
        #                     inschrijving.pk,
        #                     WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
        #                     afmelding.pk,
        #                     WEDSTRIJD_AFMELDING_STATUS_TO_STR[afmelding.status]))

        # verwijder de inschrijving
        self.stdout.write('[INFO] WedstrijdInschrijving pk=%s wordt verwijderd' % inschrijving.pk)
        inschrijving.delete()

    def is_besteld(self, regel: BestellingRegel):
        """
            Het gereserveerde product in het mandje is nu omgezet in een bestelling.
            Verander de status van het gevraagde product naar 'besteld maar nog niet betaald'
        """
        inschrijving = WedstrijdInschrijving.objects.filter(bestelling=regel).first()
        if not inschrijving:
            self.stdout.write(
                '[ERROR] Kan WedstrijdInschrijving voor regel met pk=%s niet vinden {is_besteld}' % regel.pk)
            return

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Omgezet in een bestelling\n" % stamp_str

        inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD
        inschrijving.log += msg
        inschrijving.save(update_fields=['status', 'log'])

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """
            Het product is betaald, dus de reservering moet definitief gemaakt worden.
            Wordt ook aangeroepen als een bestelling niet betaald hoeft te worden (totaal bedrag nul).
        """
        inschrijving = WedstrijdInschrijving.objects.filter(bestelling=regel).first()
        if not inschrijving:
            self.stdout.write(
                '[ERROR] Kan WedstrijdInschrijving voor regel met pk=%s niet vinden {is_betaald}' % regel.pk)
            return

        inschrijving.ontvangen_euro = bedrag_ontvangen
        inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        bedrag_str = format_bedrag_euro(bedrag_ontvangen)
        msg = "[%s] Betaling ontvangen (%s); status is nu definitief\n" % (stamp_str, bedrag_str)
        inschrijving.log += msg

        inschrijving.save(update_fields=['ontvangen_euro', 'status', 'log'])

        # stuur een e-mail naar de sporter, als dit niet de koper is
        sporter = inschrijving.sporterboog.sporter
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

                aanwezig = datetime.datetime.combine(inschrijving.sessie.datum, inschrijving.sessie.tijd_begin)
                aanwezig -= datetime.timedelta(minutes=inschrijving.wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn)

                context = {
                    'voornaam': sporter.voornaam,
                    'koper_volledige_naam': koper_account.volledige_naam(),
                    'reserveringsnummer': settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk,
                    'wed_titel': inschrijving.wedstrijd.titel,
                    'wed_adres': inschrijving.wedstrijd.locatie.adres_oneliner(),
                    'wed_datum': inschrijving.sessie.datum,
                    'wed_klasse': inschrijving.wedstrijdklasse.beschrijving,
                    'wed_org_ver': inschrijving.wedstrijd.organiserende_vereniging,
                    'aanwezig_tijd': aanwezig.strftime('%H:%M'),
                    'contact_email': inschrijving.wedstrijd.contact_email,
                    'contact_tel': inschrijving.wedstrijd.contact_telefoon,
                    'geen_account': sporter.account is None,
                    'naam_site': settings.NAAM_SITE,
                }

                if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
                    context['wed_klasse'] += ' [%s]' % inschrijving.wedstrijdklasse.afkorting

                mail_body = render_email_template(context, EMAIL_TEMPLATE_INFO_INSCHRIJVING_WEDSTRIJD)

                mailer_queue_email(email,
                                   'Inschrijving op wedstrijd',
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

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """
            Bepaal welke vereniging de verkopende partij is
            Geeft het verenigingsnummer terug, of -1 als dit niet te bepalen was
        """
        ver_nr = -1
        inschrijving = (WedstrijdInschrijving
                        .objects
                        .filter(bestelling=regel)
                        .select_related('wedstrijd',
                                        'wedstrijd__organiserende_vereniging')
                        .first())
        if inschrijving:
            ver_nr = inschrijving.wedstrijd.organiserende_vereniging.ver_nr
        else:
            self.stdout.write(
                '[ERROR] Kan WedstrijdInschrijving voor regel met pk=%s niet vinden {get_verkoper_ver_nr}' % regel.pk)
        return ver_nr


class WedstrijdKortingBestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        # nothing to do
        return []

    def annuleer(self, regel: BestellingRegel):
        """ niets te doen """
        pass

    def is_besteld(self, regel: BestellingRegel):
        """ niets te doen """
        pass

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """ niets te doen """
        pass

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """ korting hoort bij de wedstrijd waar deze voor is """
        return regel.korting_ver_nr


wedstrijd_bestel_plugin = WedstrijdBestelPlugin()
wedstrijd_korting_bestel_plugin = WedstrijdKortingBestelPlugin()

# end of file
