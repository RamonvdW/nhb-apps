# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Betaal.format import format_bedrag_euro
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR,
                                  EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF, EVENEMENT_INSCHRIJVING_STATUS_AFGEMELD,
                                  EVENEMENT_AFMELDING_STATUS_TO_SHORT_STR,)
from Evenement.models import Evenement, EvenementInschrijving, EvenementAfgemeld
from Evenement.view_inschrijven import splits_evenement_workshop_keuzes
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Kalender.view_helpers import get_url_kalender_overzicht_met_datum
from decimal import Decimal
from codecs import BOM_UTF8
import csv


TEMPLATE_EVENEMENT_AANMELDINGEN = 'evenement/aanmeldingen.dtl'
TEMPLATE_EVENEMENT_AFMELDING_DETAILS = 'evenement/afmelding-details.dtl'
TEMPLATE_EVENEMENT_AANMELDING_DETAILS = 'evenement/aanmelding-details.dtl'
TEMPLATE_EVENEMENT_WORKSHOP_KEUZES = 'evenement/workshop-keuzes.dtl'

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


def get_inschrijving_mh_bestel_nr(inschrijving):
    regel = inschrijving.bestelling
    if regel:
        bestelling = regel.bestelling_set.first()
        if bestelling:
            return bestelling.mh_bestel_nr()

    return ""


class EvenementAanmeldingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de inschrijvingen voor een evenement inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_AANMELDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        ver = self.functie_nu.vereniging

        try:
            evenement_pk = str(kwargs['evenement_pk'])[:6]     # afkappen voor de veiligheid
            evenement = (Evenement
                         .objects
                         .filter(organiserende_vereniging=ver)
                         .select_related('organiserende_vereniging')
                         .get(pk=evenement_pk))
        except (ValueError, TypeError, Evenement.DoesNotExist):
            raise Http404('Evenement niet gevonden')

        context['evenement'] = evenement

        inschrijvingen = (EvenementInschrijving
                          .objects
                          .filter(evenement=evenement)
                          .exclude(status=EVENEMENT_INSCHRIJVING_STATUS_AFGEMELD)
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
            inschrijving.reserveringsnummer = inschrijving.nummer + settings.TICKET_NUMMER_START__EVENEMENT
            inschrijving.is_definitief = (inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF)

            inschrijving.status_str = EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

            inschrijving.sporter_str = sporter.lid_nr_en_volledige_naam()

            inschrijving.url_details = reverse('Evenement:details-aanmelding',
                                               kwargs={'inschrijving_pk': inschrijving.pk})

            totaal_ontvangen_euro += inschrijving.bedrag_ontvangen
        # for

        afmeldingen = (EvenementAfgemeld
                       .objects
                       .filter(evenement=evenement)
                       .select_related('sporter')
                       .order_by('nummer'))

        context['afmeldingen'] = afmeldingen

        for afmelding in afmeldingen:
            sporter = afmelding.sporter

            aantal_aanmeldingen += 1
            afmelding.volg_nr = aantal_aanmeldingen
            afmelding.reserveringsnummer = afmelding.nummer + settings.TICKET_NUMMER_START__EVENEMENT

            afmelding.status_str = EVENEMENT_AFMELDING_STATUS_TO_SHORT_STR[afmelding.status]

            afmelding.sporter_str = sporter.lid_nr_en_volledige_naam()

            afmelding.url_details = reverse('Evenement:details-afmelding',
                                            kwargs={'afmelding_pk': afmelding.pk})

            totaal_ontvangen_euro += afmelding.bedrag_ontvangen
            totaal_retour_euro += afmelding.bedrag_retour
        # for

        # context['totaal_euro'] = totaal_ontvangen_euro - totaal_retour_euro
        context['totaal_ontvangen_euro'] = totaal_ontvangen_euro
        context['totaal_retour_euro'] = totaal_retour_euro
        context['aantal_aanmeldingen'] = aantal_aanmeldingen

        context['url_download_csv'] = reverse('Evenement:download-aanmeldingen-csv',
                                              kwargs={'evenement_pk': evenement.pk})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Evenement:vereniging'), 'Evenementen'),
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
        return self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL)

    @staticmethod
    def _output_aanmeldingen(writer, evenement: Evenement):
        aanmeldingen = (EvenementInschrijving
                        .objects
                        .filter(evenement=evenement)
                        .exclude(status=EVENEMENT_INSCHRIJVING_STATUS_AFGEMELD)
                        .select_related('sporter',
                                        'sporter__bij_vereniging')
                        .order_by('nummer'))

        writer.writerow(['Reserveringsnummer', 'Aangemeld op', '', 'Status',
                         'Bestelnummer', 'Prijs', 'Ontvangen', '',
                         'Bondsnummer', 'Sporter', 'E-mailadres', 'Ver nr', 'Vereniging',
                         'Gekozen workshops'])

        ws_code2beschrijving = dict()
        if evenement.workshop_opties:
            for regel in evenement.workshop_opties.replace('\r', '\n').split('\n'):
                pos = regel.find(' ')
                code = regel[:pos]
                ws_code2beschrijving[code] = regel
            # for

        for aanmelding in aanmeldingen:
            sporter = aanmelding.sporter
            reserveringsnummer = aanmelding.nummer + settings.TICKET_NUMMER_START__EVENEMENT

            bestelnummer_str = get_inschrijving_mh_bestel_nr(aanmelding)

            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                ver_str = sporter.bij_vereniging.naam
            else:
                ver_nr = 0
                ver_str = 'geen'

            regel = aanmelding.bestelling
            if regel:
                prijs_str = format_bedrag_euro(regel.bedrag_euro)
            else:
                prijs_str = 'Geen (handmatige inschrijving)'

            ws_keuzes = list()
            for code in aanmelding.gekozen_workshops.split(' '):
                if code:
                    ws_keuzes.append(ws_code2beschrijving[code])
            # for

            row = [
                str(reserveringsnummer),
                timezone.localtime(aanmelding.wanneer).strftime('%Y-%m-%d %H:%M'),
                '',     # afgemeld op
                EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status],
                bestelnummer_str,
                prijs_str,
                format_bedrag_euro(aanmelding.bedrag_ontvangen),
                '',     # retour
                str(sporter.lid_nr),
                sporter.volledige_naam(),
                sporter.email,
                str(ver_nr),
                ver_str,
                "\n".join(ws_keuzes)]

            writer.writerow(row)
        # for

    @staticmethod
    def _output_afmeldingen(writer, evenement):
        afmeldingen = (EvenementAfgemeld
                       .objects
                       .filter(evenement=evenement)
                       .select_related('sporter',
                                       'sporter__bij_vereniging')
                       .order_by('nummer'))

        writer.writerow(['Reserveringsnummer', 'Aangemeld op', 'Afgemeld op', 'Status',
                         'Bestelnummer', 'Prijs', 'Ontvangen', 'Retour',
                         'Bondsnummer', 'Sporter', 'E-mailadres', 'Ver nr', 'Vereniging'])

        for afgemeld in afmeldingen:
            sporter = afgemeld.sporter
            reserveringsnummer = afgemeld.nummer + settings.TICKET_NUMMER_START__EVENEMENT

            bestelnummer_str = get_inschrijving_mh_bestel_nr(afgemeld)

            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                ver_str = sporter.bij_vereniging.naam
            else:
                ver_nr = 0
                ver_str = 'geen'

            regel = afgemeld.bestelling
            if regel:
                prijs_str = format_bedrag_euro(regel.bedrag_euro)
            else:
                prijs_str = 'Geen (handmatige inschrijving)'

            row = [
                str(reserveringsnummer),
                timezone.localtime(afgemeld.wanneer_inschrijving).strftime('%Y-%m-%d %H:%M'),
                timezone.localtime(afgemeld.wanneer_afgemeld).strftime('%Y-%m-%d %H:%M'),
                EVENEMENT_AFMELDING_STATUS_TO_SHORT_STR[afgemeld.status],
                bestelnummer_str,
                prijs_str,
                format_bedrag_euro(afgemeld.bedrag_ontvangen),
                format_bedrag_euro(afgemeld.bedrag_retour),
                str(sporter.lid_nr),
                sporter.volledige_naam(),
                sporter.email,
                str(ver_nr),
                ver_str]

            writer.writerow(row)
        # for

    def get(self, request, *args, **kwargs):

        ver = self.functie_nu.vereniging

        try:
            evenement_pk = str(kwargs['evenement_pk'])[:6]     # afkappen voor de veiligheid
            evenement = (Evenement
                         .objects
                         .filter(organiserende_vereniging=ver)
                         .select_related('organiserende_vereniging')
                         .get(pk=evenement_pk))
        except (ValueError, TypeError, Evenement.DoesNotExist):
            raise Http404('Evenement niet gevonden')

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen.csv"'

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings

        self._output_aanmeldingen(writer, evenement)
        writer.writerow([])
        self._output_afmeldingen(writer, evenement)

        return response


class EvenementDetailsAanmeldingView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de details van een inschrijving voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_AANMELDING_DETAILS
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:7]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
        except (TypeError, ValueError):
            raise Http404('Geen valide parameter')

        try:
            inschrijving = (EvenementInschrijving
                            .objects
                            .select_related('evenement',
                                            'evenement__organiserende_vereniging',
                                            'sporter')
                            .get(pk=inschrijving_pk,
                                 # alleen van de eigen vereniging laten zien
                                 evenement__organiserende_vereniging=self.functie_nu.vereniging))
        except EvenementInschrijving.DoesNotExist:
            raise Http404('Aanmelding niet gevonden')

        context['inschrijving'] = inschrijving
        evenement = inschrijving.evenement

        context['sporter'] = sporter = inschrijving.sporter
        context['ver'] = sporter.bij_vereniging

        context['toon_contactgegevens'] = True

        inschrijving.reserveringsnummer = inschrijving.pk + settings.TICKET_NUMMER_START__EVENEMENT

        inschrijving.status_str = EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

        inschrijving.bestelnummer_str = get_inschrijving_mh_bestel_nr(inschrijving)

        if evenement.workshop_opties:
            inschrijving.heeft_workshops = True
            inschrijving.workshops = list()
            regels = evenement.workshop_opties.replace('\r', '\n').split('\n')
            print(inschrijving.gekozen_workshops)
            for keuze in inschrijving.gekozen_workshops.split(' '):
                for regel in regels:
                    if regel.startswith(keuze + ' '):
                        inschrijving.workshops.append(regel)
                # for
            # for
        else:
            inschrijving.heeft_workshops = False

        inschrijving.url_afmelden = reverse('Evenement:afmelden',
                                            kwargs={'inschrijving_pk': inschrijving.pk})

        # toon de prijs die geselecteerd was voor dit lid (jeugd/volwassenen)
        regel = inschrijving.bestelling
        if regel:
            inschrijving.kosten_euro = format_bedrag_euro(regel.bedrag_euro)
        else:
            inschrijving.kosten_euro = None

        url_aanmeldingen = reverse('Evenement:aanmeldingen',
                                   kwargs={'evenement_pk': evenement.pk})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Evenement:vereniging'), 'Evenementen'),
            (url_aanmeldingen, 'Aanmeldingen'),
            (None, 'Details aanmelding')
        )

        return context


class EvenementDetailsAfmeldingView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de details van een afmelding voor een evenement inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_AFMELDING_DETAILS
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            afmelding_pk = str(kwargs['afmelding_pk'])[:7]     # afkappen voor de veiligheid
            afmelding_pk = int(afmelding_pk)
        except (TypeError, ValueError):
            raise Http404('Geen valide parameter')

        try:
            afmelding = (EvenementAfgemeld
                         .objects
                         .select_related('evenement',
                                         'evenement__organiserende_vereniging',
                                         'sporter')
                         .get(pk=afmelding_pk,
                              # alleen van de eigen vereniging laten zien
                              evenement__organiserende_vereniging=self.functie_nu.vereniging))
        except EvenementAfgemeld.DoesNotExist:
            raise Http404('Afmelding niet gevonden')

        context['afmelding'] = afmelding

        context['sporter'] = sporter = afmelding.sporter
        context['ver'] = sporter.bij_vereniging

        context['toon_contactgegevens'] = True

        afmelding.reserveringsnummer = afmelding.pk + settings.TICKET_NUMMER_START__EVENEMENT

        afmelding.status_str = EVENEMENT_AFMELDING_STATUS_TO_SHORT_STR[afmelding.status]

        afmelding.bestelnummer_str = get_inschrijving_mh_bestel_nr(afmelding)

        # toon de prijs die geselecteerd was voor dit lid (jeugd/volwassenen)
        regel = afmelding.bestelling
        if regel:
            afmelding.kosten_euro = format_bedrag_euro(regel.bedrag_euro)
        else:
            afmelding.kosten_euro = None

        url_aanmeldingen = reverse('Evenement:aanmeldingen',
                                   kwargs={'evenement_pk': afmelding.evenement.pk})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Evenement:vereniging'), 'Evenementen'),
            (url_aanmeldingen, 'Aanmeldingen'),
            (None, 'Details afmelding')
        )

        return context


class EvenementWorkshopKeuzesView(TemplateView):

    """ Via deze view kunnen beheerders zien welke workshops favoriet zijn """

    # LET OP: deze pagina is bewust openbaar zodat een externe medewerker organisatie evenement erbij kan

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_WORKSHOP_KEUZES

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            evenement_pk = str(kwargs['evenement_pk'])[:6]     # afkappen voor de veiligheid
            evenement = (Evenement
                         .objects
                         .exclude(workshop_opties='')
                         .get(pk=evenement_pk))
        except (ValueError, TypeError, Evenement.DoesNotExist):
            raise Http404('Evenement niet gevonden')

        context['evenement'] = evenement

        keuzes = (EvenementInschrijving
                  .objects
                  .filter(evenement=evenement)
                  .exclude(gekozen_workshops='')
                  .values_list('gekozen_workshops', flat=True))

        context['aantal_opgaven'] = len(keuzes)

        code_count = dict()
        for inschrijving_keuzes in keuzes:
            for code in inschrijving_keuzes.split(' '):
                try:
                    code_count[code] += 1
                except KeyError:
                    code_count[code] = 1
        # for

        context['workshops'] = workshops = list()
        for ronde_nr, ronde_ws in splits_evenement_workshop_keuzes(evenement, prefix=''):
            ronde_ws_2 = list()
            for code, titel in ronde_ws:
                count = code_count.get(code, 0)
                tup = (code, count, titel)
                ronde_ws_2.append(tup)
            # for
            tup = (ronde_nr, ronde_ws_2)
            workshops.append(tup)
        # for

        context['kruimels'] = (
            (get_url_kalender_overzicht_met_datum(evenement.datum), 'Kalender'),
            (reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk}), 'Evenement'),
            (None, 'Voorkeur workshops')
        )

        return context

# end of file
