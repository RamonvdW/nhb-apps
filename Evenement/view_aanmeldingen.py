# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestel.operations.mutaties import (#bestel_mutatieverzoek_afmelden_evenement,
                                        bestel_mutatieverzoek_verwijder_product_uit_mandje)
from Evenement.definities import EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR, EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF
from Evenement.models import Evenement, EvenementInschrijving
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from decimal import Decimal
from codecs import BOM_UTF8
import csv


TEMPLATE_EVENEMENT_AANMELDINGEN = 'evenement/aanmeldingen.dtl'
TEMPLATE_EVENEMENT_AANMELDING_DETAILS = 'evenement/aanmelding-details.dtl'

CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


def get_inschrijving_mh_bestel_nr(inschrijving):
    bestel_product = inschrijving.bestelproduct_set.first()
    if bestel_product:
        bestelling = bestel_product.bestelling_set.first()
        if bestelling:
            return bestelling.mh_bestel_nr()

    return ""


class EvenementAanmeldingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de inschrijvingen voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_AANMELDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_MWZ, Rollen.ROL_BB)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            evenement_pk = str(kwargs['evenement_pk'])[:6]     # afkappen voor de veiligheid
            evenement = (Evenement
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=evenement_pk))
        except (ValueError, TypeError, Evenement.DoesNotExist):
            raise Http404('Evenement niet gevonden')

        context['evenement'] = evenement

        inschrijvingen = (EvenementInschrijving
                        .objects
                        .filter(wedstrijd=evenement)
                        .select_related('sessie',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'korting')
                        .order_by('sessie',
                                  'pk'))        # = reserveringsnummer
        context['inschrijvingen'] = inschrijvingen

        totaal_ontvangen_euro = Decimal('000.00')
        totaal_retour_euro = Decimal('000.00')

        aantal_aanmeldingen = 0
        for inschrijving in inschrijvingen:

            sporterboog = inschrijving.sporterboog
            sporter = sporterboog.sporter

            aantal_aanmeldingen += 1
            inschrijving.volg_nr = aantal_aanmeldingen
            inschrijving.reserveringsnummer = inschrijving.pk + settings.TICKET_NUMMER_START__WEDSTRIJD
            inschrijving.is_definitief = (inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF)

            inschrijving.status_str = EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

            inschrijving.sporter_str = sporter.lid_nr_en_volledige_naam()
            inschrijving.boog_str = sporterboog.boogtype.beschrijving

            inschrijving.url_details = reverse('Evenement:details-aanmelding',
                                             kwargs={'inschrijving_pk': inschrijving.pk})

            totaal_ontvangen_euro += inschrijving.ontvangen_euro
            totaal_retour_euro += inschrijving.retour_euro
        # for

        # context['totaal_euro'] = totaal_ontvangen_euro - totaal_retour_euro
        context['totaal_ontvangen_euro'] = totaal_ontvangen_euro
        context['totaal_retour_euro'] = totaal_retour_euro
        context['aantal_aanmeldingen'] = aantal_aanmeldingen

        context['url_download_csv'] = reverse('Wedstrijden:download-aanmeldingen-csv',
                                              kwargs={'wedstrijd_pk': evenement.pk})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
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
        return self.rol_nu == Rollen.ROL_HWL

    def get(self, request, *args, **kwargs):
        try:
            evenement_pk = str(kwargs['evenement_pk'])[:6]     # afkappen voor de veiligheid
            evenement = (Evenement
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=evenement_pk))
        except (ValueError, TypeError, Evenement.DoesNotExist):
            raise Http404('Evenement niet gevonden')

        if evenement.organiserende_vereniging.ver_nr != self.functie_nu.vereniging.ver_nr:
            raise Http404('Evenement is niet bij jullie vereniging')

        aanmeldingen = (EvenementInschrijving
                        .objects
                        .filter(evenement=evenement)
                        .select_related('sporter')
                        .order_by('sporter',
                                  'wanneer',
                                  'status'))

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen.csv"'

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings

        writer.writerow(['Reserveringsnummer', 'Aangemeld op', 'Status',
                         'Bestelnummer', 'Prijs', 'Ontvangen', 'Retour',
                         'Lid nr', 'Sporter', 'E-mailadres', 'Ver nr', 'Vereniging'])

        output = list()
        for aanmelding in aanmeldingen:
            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter
            reserveringsnummer = aanmelding.pk + settings.TICKET_NUMMER_START__WEDSTRIJD

            bestelnummer_str = get_inschrijving_mh_bestel_nr(aanmelding)

            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                ver_str = sporter.bij_vereniging.naam
            else:
                ver_nr = 0
                ver_str = 'geen'

            qset = aanmelding.bestelproduct_set.all()
            if qset.count() > 0:
                bestelproduct = qset[0]
                prijs_str = '€ %s' % bestelproduct.prijs_euro
            else:
                prijs_str = 'Geen (handmatige inschrijving)'

            row = [
                str(reserveringsnummer),
                timezone.localtime(aanmelding.wanneer).strftime('%Y-%m-%d %H:%M'),
                EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status],
                bestelnummer_str,
                prijs_str,
                '€ %s' % aanmelding.ontvangen_euro,
                '€ %s' % aanmelding.retour_euro,
                str(sporter.lid_nr),
                sporter.volledige_naam(),
                sporter.email,
                str(ver_nr),
                ver_str]

            tup = (aanmelding.sessie.datum, aanmelding.sessie.tijd_begin, aanmelding.wedstrijdklasse.afkorting,
                   0, aanmelding.wanneer, aanmelding.pk, row)

            output.append(tup)
        # for

        output.sort()
        for tup in output:
            row = tup[-1]
            writer.writerow(row)
        # for

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
        return self.rol_nu == Rollen.ROL_HWL

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
                            .get(pk=inschrijving_pk))
        except EvenementInschrijving.DoesNotExist:
            raise Http404('Aanmelding niet gevonden')

        context['evenement'] = evenement = inschrijving.evenement

        # alleen van de eigen vereniging laten zien
        if evenement.organiserende_vereniging != self.functie_nu.vereniging:
            raise Http404('Verkeerde vereniging')

        context['sporter'] = sporter = inschrijving.sporter
        context['ver'] = sporter.bij_vereniging

        context['toon_contactgegevens'] = True

        inschrijving.reserveringsnummer = inschrijving.pk + settings.TICKET_NUMMER_START__WEDSTRIJD

        inschrijving.status_str = EVENEMENT_INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

        inschrijving.bestelnummer_str = get_inschrijving_mh_bestel_nr(inschrijving)

        inschrijving.url_afmelden = reverse('Evenement:afmelden',
                                            kwargs={'inschrijving_pk': inschrijving.pk})

        qset = inschrijving.bestelproduct_set.all()
        if qset.count() > 0:
            inschrijving.bestelproduct = qset[0]
        else:
            inschrijving.bestelproduct = None

        url_aanmeldingen = reverse('Evenement:aanmeldingen',
                                   kwargs={'evenement_pk': evenement.pk})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Evenement:vereniging'), 'Evenementen'),
            (url_aanmeldingen, 'Aanmeldingen'),
            (None, 'Details aanmelding')
        )

        return context


class AfmeldenView(UserPassesTestMixin, View):

    """ Via deze view kunnen beheerders een sporter afmelden voor een wedstrijd """

    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_MWZ, Rollen.ROL_BB)

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving_pk)
        except (TypeError, ValueError, WedstrijdInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        if self.rol_nu not in (Rollen.ROL_BB, Rollen.ROL_MWZ):
            # controleer dat dit een inschrijving is op een wedstrijd van de vereniging
            ver = self.functie_nu.vereniging
            if inschrijving.wedstrijd.organiserende_vereniging != ver:
                raise Http404('Verkeerde vereniging')

        snel = str(request.POST.get('snel', ''))[:1]

        if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            if inschrijving.bestelproduct_set.count() > 0:
                product = inschrijving.bestelproduct_set.first()
                bestel_mutatieverzoek_verwijder_product_uit_mandje(inschrijving.koper, product, snel == '1')
        else:
            bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel == '1')

        url = reverse('Wedstrijden:details-aanmelding', kwargs={'inschrijving_pk': inschrijving.pk})

        return HttpResponseRedirect(url)

# end of file
