# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF, OPLEIDING_INSCHRIJVING_STATUS_TO_SHORT_STR,
                                  OPLEIDING_AFMELDING_STATUS_TO_SHORT_STR)
from Opleiding.models import Opleiding, OpleidingInschrijving, OpleidingAfgemeld
from Sporter.models import Sporter
from decimal import Decimal
from codecs import BOM_UTF8
import csv


TEMPLATE_OPLEIDING_AANMELDINGEN = 'opleiding/aanmeldingen.dtl'
TEMPLATE_OPLEIDING_AFMELDING_DETAILS = 'opleiding/afmelding-details.dtl'
TEMPLATE_OPLEIDING_AANMELDING_DETAILS = 'opleiding/aanmelding-details.dtl'

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


def get_inschrijving_mh_bestel_nr(inschrijving):
    bestel_product = inschrijving.bestellingproduct_set.first()
    if bestel_product:
        bestelling = bestel_product.bestelling_set.first()
        if bestelling:
            return bestelling.mh_bestel_nr()

    return "?"


def get_email_telefoon(deelnemer: OpleidingInschrijving | OpleidingAfgemeld, sporter: Sporter) -> (str, str):
    if deelnemer.aanpassing_email:
        email = deelnemer.aanpassing_email
    else:
        email = sporter.email

    if deelnemer.aanpassing_telefoon:
        telefoon = deelnemer.aanpassing_telefoon
    else:
        telefoon = sporter.telefoon

    if telefoon == '':
        telefoon = '?'

    return email, telefoon


class OpleidingAanmeldingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de inschrijvingen voor een opleiding inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_AANMELDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        if self.rol_nu not in (Rol.ROL_MO, Rol.ROL_HWL, Rol.ROL_SEC):
            return False
        if self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC):
            if self.functie_nu.vereniging.ver_nr not in settings.OPLEIDINGEN_VERKOPER_VER_NRS:
                return False
        return True

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            opleiding_pk = str(kwargs['opleiding_pk'])[:6]     # afkappen voor de veiligheid
            opleiding = (Opleiding
                         .objects
                         .get(pk=opleiding_pk))
        except (ValueError, TypeError, Opleiding.DoesNotExist):
            raise Http404('Opleiding niet gevonden')

        context['opleiding'] = opleiding

        inschrijvingen = (OpleidingInschrijving
                          .objects
                          .filter(opleiding=opleiding)
                          .select_related('sporter')
                          .order_by('nummer'))

        context['inschrijvingen'] = inschrijvingen

        totaal_ontvangen_euro = Decimal('000.00')
        totaal_retour_euro = Decimal('000.00')

        aantal_aanmeldingen = 0
        for inschrijving in inschrijvingen:

            sporter = inschrijving.sporter

            aantal_aanmeldingen += 1
            inschrijving.volg_nr = aantal_aanmeldingen
            inschrijving.reserveringsnummer = inschrijving.nummer + settings.TICKET_NUMMER_START__OPLEIDING
            inschrijving.is_definitief = (inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF)

            inschrijving.status_str = OPLEIDING_INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

            inschrijving.sporter_str = sporter.lid_nr_en_volledige_naam()

            inschrijving.url_details = reverse('Opleiding:details-aanmelding',
                                               kwargs={'inschrijving_pk': inschrijving.pk})

            totaal_ontvangen_euro += inschrijving.bedrag_ontvangen
        # for

        afmeldingen = (OpleidingAfgemeld
                       .objects
                       .filter(opleiding=opleiding)
                       .select_related('sporter')
                       .order_by('nummer'))

        context['afmeldingen'] = afmeldingen

        for afmelding in afmeldingen:
            sporter = afmelding.sporter

            aantal_aanmeldingen += 1
            afmelding.volg_nr = aantal_aanmeldingen
            afmelding.reserveringsnummer = afmelding.nummer + settings.TICKET_NUMMER_START__OPLEIDING

            afmelding.status_str = OPLEIDING_AFMELDING_STATUS_TO_SHORT_STR[afmelding.status]

            afmelding.sporter_str = sporter.lid_nr_en_volledige_naam()

            afmelding.url_details = reverse('Opleiding:details-afmelding',
                                            kwargs={'afmelding_pk': afmelding.pk})

            totaal_ontvangen_euro += afmelding.bedrag_ontvangen
            totaal_retour_euro += afmelding.bedrag_retour
        # for

        # context['totaal_euro'] = totaal_ontvangen_euro - totaal_retour_euro
        context['totaal_ontvangen_euro'] = totaal_ontvangen_euro
        context['totaal_retour_euro'] = totaal_retour_euro
        context['aantal_aanmeldingen'] = aantal_aanmeldingen

        if self.rol_nu != Rol.ROL_SEC:
            context['url_download_csv'] = reverse('Opleiding:download-aanmeldingen-csv',
                                                  kwargs={'opleiding_pk': opleiding.pk})

        if self.rol_nu == Rol.ROL_MO:
            context['kruimels'] = (
                (reverse('Opleiding:manager'), 'Opleidingen'),
                (None, 'Aanmeldingen'),
            )
        else:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Opleiding:vereniging'), 'Opleidingen'),
                (None, 'Aanmeldingen'),
            )

        return context


class DownloadAanmeldingenBestandCSV(UserPassesTestMixin, View):

    """ Maak een bestand met alle inschrijvingen, geschikt voor import in een spreadsheet programma """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        if self.rol_nu not in (Rol.ROL_MO, Rol.ROL_HWL):
            return False
        if self.rol_nu == Rol.ROL_HWL:
            if self.functie_nu.vereniging.ver_nr not in settings.OPLEIDINGEN_VERKOPER_VER_NRS:
                return False
        return True

    @staticmethod
    def _output_aanmeldingen(writer, opleiding):
        aanmeldingen = (OpleidingInschrijving
                        .objects
                        .filter(opleiding=opleiding)
                        .select_related('sporter',
                                        'sporter__bij_vereniging')
                        .order_by('nummer'))

        writer.writerow(['Reserveringsnummer', 'Aangemeld op', 'Afgemeld op', 'Status',
                         'Bestelnummer', 'Prijs', 'Ontvangen', 'Retour',
                         'Lid nr', 'Sporter', 'E-mailadres', 'Telefoon', 'Ver nr', 'Vereniging'])

        for aanmelding in aanmeldingen:
            sporter = aanmelding.sporter
            reserveringsnummer = aanmelding.nummer + settings.TICKET_NUMMER_START__OPLEIDING

            bestelnummer_str = get_inschrijving_mh_bestel_nr(aanmelding)

            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                ver_str = sporter.bij_vereniging.naam
            else:
                ver_nr = 0
                ver_str = 'geen'

            qset = aanmelding.bestellingproduct_set.all()
            if qset.count() > 0:
                bestelproduct = qset[0]
                prijs_str = format_bedrag_euro(bestelproduct.prijs_euro)
            else:
                prijs_str = 'Geen (handmatige inschrijving)'

            email, telefoon = get_email_telefoon(aanmelding, sporter)

            row = [
                str(reserveringsnummer),
                timezone.localtime(aanmelding.wanneer_aangemeld).strftime('%Y-%m-%d %H:%M'),
                '',     # wanneer afgemeld
                OPLEIDING_INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status],
                bestelnummer_str,
                prijs_str,
                format_bedrag_euro(aanmelding.bedrag_ontvangen),
                '',     # bedrag retour
                str(sporter.lid_nr),
                sporter.volledige_naam(),
                email,
                telefoon,
                str(ver_nr),
                ver_str]

            writer.writerow(row)
        # for

    @staticmethod
    def _output_afmeldingen(writer, opleiding):
        afmeldingen = (OpleidingAfgemeld
                       .objects
                       .filter(opleiding=opleiding)
                       .select_related('sporter',
                                       'sporter__bij_vereniging')
                       .order_by('nummer'))

        writer.writerow(['Reserveringsnummer', 'Aangemeld op', 'Afgemeld op', 'Status',
                         'Bestelnummer', 'Prijs', 'Ontvangen', 'Retour',
                         'Lid nr', 'Sporter', 'E-mailadres', 'Telefoon', 'Ver nr', 'Vereniging'])

        for afmelding in afmeldingen:
            sporter = afmelding.sporter
            reserveringsnummer = afmelding.nummer + settings.TICKET_NUMMER_START__OPLEIDING

            bestelnummer_str = get_inschrijving_mh_bestel_nr(afmelding)

            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                ver_str = sporter.bij_vereniging.naam
            else:
                ver_nr = 0
                ver_str = 'geen'

            qset = afmelding.bestellingproduct_set.all()
            if qset.count() > 0:
                bestelproduct = qset[0]
                prijs_str = format_bedrag_euro(bestelproduct.prijs_euro)
            else:
                prijs_str = 'Geen (handmatige inschrijving)'

            email, telefoon = get_email_telefoon(afmelding, sporter)

            row = [
                str(reserveringsnummer),
                timezone.localtime(afmelding.wanneer_aangemeld).strftime('%Y-%m-%d %H:%M'),
                timezone.localtime(afmelding.wanneer_afgemeld).strftime('%Y-%m-%d %H:%M'),
                OPLEIDING_AFMELDING_STATUS_TO_SHORT_STR[afmelding.status],
                bestelnummer_str,
                prijs_str,
                format_bedrag_euro(afmelding.bedrag_ontvangen),
                format_bedrag_euro(afmelding.bedrag_retour),
                str(sporter.lid_nr),
                sporter.volledige_naam(),
                email,
                telefoon,
                str(ver_nr),
                ver_str]

            writer.writerow(row)
        # for

    def get(self, request, *args, **kwargs):

        try:
            opleiding_pk = str(kwargs['opleiding_pk'])[:6]     # afkappen voor de veiligheid
            opleiding = (Opleiding
                         .objects
                         .get(pk=opleiding_pk))
        except (ValueError, TypeError, Opleiding.DoesNotExist):
            raise Http404('Opleiding niet gevonden')

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen.csv"'

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings

        self._output_aanmeldingen(writer, opleiding)
        writer.writerow([])
        self._output_afmeldingen(writer, opleiding)

        return response


class OpleidingDetailsAanmeldingView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de details van een inschrijving voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_AANMELDING_DETAILS
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        if self.rol_nu not in (Rol.ROL_MO, Rol.ROL_HWL, Rol.ROL_SEC):
            return False
        if self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC):
            if self.functie_nu.vereniging.ver_nr not in settings.OPLEIDINGEN_VERKOPER_VER_NRS:
                return False
        return True

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:7]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
        except (TypeError, ValueError):
            raise Http404('Geen valide parameter')

        try:
            inschrijving = (OpleidingInschrijving
                            .objects
                            .select_related('opleiding',
                                            'sporter')
                            .get(pk=inschrijving_pk))
        except OpleidingInschrijving.DoesNotExist:
            raise Http404('Aanmelding niet gevonden')

        context['inschrijving'] = inschrijving

        context['sporter'] = sporter = inschrijving.sporter
        context['ver'] = sporter.bij_vereniging

        context['toon_contactgegevens'] = True

        inschrijving.email, inschrijving.telefoon = get_email_telefoon(inschrijving, sporter)

        inschrijving.reserveringsnummer = inschrijving.pk + settings.TICKET_NUMMER_START__OPLEIDING

        inschrijving.status_str = OPLEIDING_INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

        inschrijving.bestelnummer_str = get_inschrijving_mh_bestel_nr(inschrijving)

        if self.rol_nu != Rol.ROL_SEC:
            inschrijving.url_afmelden = reverse('Opleiding:afmelden',
                                                kwargs={'inschrijving_pk': inschrijving.pk})

        qset = inschrijving.bestellingproduct_set.all()
        if qset.count() > 0:
            inschrijving.bestelproduct = qset[0]
        else:
            inschrijving.bestelproduct = None

        url_aanmeldingen = reverse('Opleiding:aanmeldingen',
                                   kwargs={'opleiding_pk': inschrijving.opleiding.pk})

        if self.rol_nu == Rol.ROL_MO:
            context['kruimels'] = (
                (reverse('Opleiding:manager'), 'Opleidingen'),
                (url_aanmeldingen, 'Aanmeldingen'),
                (None, 'Details aanmelding')
            )
        else:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Opleiding:vereniging'), 'Opleidingen'),
                (url_aanmeldingen, 'Aanmeldingen'),
                (None, 'Details aanmelding')
            )

        return context


class OpleidingDetailsAfmeldingView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de details van een afmelding voor een opleiding inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_AFMELDING_DETAILS
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        if self.rol_nu not in (Rol.ROL_MO, Rol.ROL_HWL, Rol.ROL_SEC):
            return False
        if self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC):
            if self.functie_nu.vereniging.ver_nr not in settings.OPLEIDINGEN_VERKOPER_VER_NRS:
                return False
        return True

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            afmelding_pk = str(kwargs['afmelding_pk'])[:7]     # afkappen voor de veiligheid
            afmelding_pk = int(afmelding_pk)
        except (TypeError, ValueError):
            raise Http404('Geen valide parameter')

        try:
            afmelding = (OpleidingAfgemeld
                         .objects
                         .select_related('opleiding',
                                         'sporter')
                         .get(pk=afmelding_pk))
        except OpleidingAfgemeld.DoesNotExist:
            raise Http404('Afmelding niet gevonden')

        context['afmelding'] = afmelding

        context['sporter'] = sporter = afmelding.sporter
        context['ver'] = sporter.bij_vereniging

        context['toon_contactgegevens'] = True

        afmelding.email, afmelding.telefoon = get_email_telefoon(afmelding, sporter)

        afmelding.reserveringsnummer = afmelding.pk + settings.TICKET_NUMMER_START__OPLEIDING

        afmelding.status_str = OPLEIDING_AFMELDING_STATUS_TO_SHORT_STR[afmelding.status]

        afmelding.bestelnummer_str = get_inschrijving_mh_bestel_nr(afmelding)

        url_aanmeldingen = reverse('Opleiding:aanmeldingen',
                                   kwargs={'opleiding_pk': afmelding.opleiding.pk})

        if self.rol_nu == Rol.ROL_MO:
            context['kruimels'] = (
                (reverse('Opleiding:manager'), 'Opleidingen'),
                (url_aanmeldingen, 'Aanmeldingen'),
                (None, 'Details afmelding')
            )
        else:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Opleiding:vereniging'), 'Opleidingen'),
                (url_aanmeldingen, 'Aanmeldingen'),
                (None, 'Details afmelding')
            )

        return context

# end of file
