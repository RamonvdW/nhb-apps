# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import GESLACHT2STR
from Bestel.mutaties import bestel_mutatieverzoek_afmelden_wedstrijd, bestel_mutatieverzoek_verwijder_product_uit_mandje
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Sporter.models import Sporter, SporterVoorkeuren, get_sporter_voorkeuren
from Wedstrijden.models import (Wedstrijd, WedstrijdInschrijving, INSCHRIJVING_STATUS_TO_SHORT_STR,
                                INSCHRIJVING_STATUS_AFGEMELD, INSCHRIJVING_STATUS_RESERVERING_MANDJE)
from decimal import Decimal
from codecs import BOM_UTF8
import csv


TEMPLATE_WEDSTRIJDEN_AANMELDINGEN = 'wedstrijden/aanmeldingen.dtl'
TEMPLATE_WEDSTRIJDEN_AANMELDING_DETAILS = 'wedstrijden/aanmelding-details.dtl'


# TODO: HWL moet sporter kunnen verplaatsen naar een andere sessie

class KalenderAanmeldingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de inschrijvingen voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_AANMELDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_BB)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=wedstrijd_pk))
        except (ValueError, TypeError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        aanmeldingen = (WedstrijdInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .select_related('sessie',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'korting')
                        .order_by('sessie',
                                  'status'))
        context['aanmeldingen'] = aanmeldingen

        totaal_ontvangen_euro = Decimal('000.00')
        totaal_retour_euro = Decimal('000.00')

        aantal_aanmeldingen = 0
        aantal_afmeldingen = 0
        for aanmelding in aanmeldingen:

            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter

            if aanmelding.status != INSCHRIJVING_STATUS_AFGEMELD:
                aantal_aanmeldingen += 1
                aanmelding.volg_nr = aantal_aanmeldingen

                aanmelding.reserveringsnummer = aanmelding.pk + settings.TICKET_NUMMER_START__WEDSTRIJD
            else:
                aantal_afmeldingen += 1
                aanmelding.is_afgemeld = True

            aanmelding.status_str = INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status]

            aanmelding.sporter_str = sporter.lid_nr_en_volledige_naam()
            aanmelding.boog_str = sporterboog.boogtype.beschrijving

            aanmelding.korting_str = 'geen'
            if aanmelding.korting:
                aanmelding.korting_str = '%s%%' % aanmelding.korting.percentage

            aanmelding.url_details = reverse('Wedstrijden:details-aanmelding',
                                             kwargs={'inschrijving_pk': aanmelding.pk})

            totaal_ontvangen_euro += aanmelding.ontvangen_euro
            totaal_retour_euro += aanmelding.retour_euro
        # for

        # context['totaal_euro'] = totaal_ontvangen_euro - totaal_retour_euro
        context['totaal_ontvangen_euro'] = totaal_ontvangen_euro
        context['totaal_retour_euro'] = totaal_retour_euro
        context['aantal_aanmeldingen'] = aantal_aanmeldingen
        context['aantal_afmeldingen'] = aantal_afmeldingen

        if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_BB):
            context['url_download_tsv'] = reverse('Wedstrijden:download-aanmeldingen-tsv',
                                                  kwargs={'wedstrijd_pk': wedstrijd.pk})
            context['url_download_csv'] = reverse('Wedstrijden:download-aanmeldingen-csv',
                                                  kwargs={'wedstrijd_pk': wedstrijd.pk})

        if self.rol_nu == Rollen.ROL_HWL:
            context['url_toevoegen'] = reverse('Wedstrijden:inschrijven-handmatig',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})

        if self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_SEC):
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )
        else:
            # BB
            context['kruimels'] = (
                (reverse('Wedstrijden:manager'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )

        menu_dynamics(self.request, context)
        return context


class DownloadAanmeldingenBestandTSV(UserPassesTestMixin, View):

    """ Maak een simpel bestand met alle aanmeldingen met tab-gescheiden velden (TSV = tab separated values).
        geschikt voor importeren in een scoreverwerkingsprogramma
    """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_BB)

    def get(self, request, *args, **kwargs):
        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .prefetch_related('sessies')
                         .get(pk=wedstrijd_pk))
        except (ValueError, TypeError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL:
            if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.nhb_ver.ver_nr:
                raise Http404('Wedstrijd is niet bij jullie vereniging')

        lid_nr2geslacht = dict()     # [lid_nr] = wedstrijd geslacht (M/V/X)
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            sporter = voorkeuren.sporter

            if voorkeuren.wedstrijd_geslacht_gekozen:
                lid_nr2geslacht[sporter.lid_nr] = voorkeuren.wedstrijd_geslacht
        # for

        aanmeldingen = (WedstrijdInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)
                        .select_related('sessie',
                                        'wedstrijdklasse',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'korting')
                        .order_by('sessie',
                                  'wanneer',
                                  'status'))

        response = HttpResponse(content_type='text/tab-separated-values; charset=UTF-8')
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen.txt"'

        # Ianseo supports a tab-separate file with specific column order, without headers
        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter="\t")       # tab separated fields

        # maak een mapping van sessie naar nummers 1..n
        sessie_pk2nr = dict()       # [pk] = nr
        nr = 0
        for sessie in wedstrijd.sessies.order_by('pk'):
            nr += 1
            sessie_pk2nr[sessie.pk] = nr
        # for

        for aanmelding in aanmeldingen:
            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter
            sessie_nr = sessie_pk2nr[aanmelding.sessie.pk]
            klasse_afkorting = aanmelding.wedstrijdklasse.afkorting
            ver = sporter.bij_vereniging
            if ver:
                ver_nr = ver.ver_nr
                ver_naam = ver.naam
            else:
                ver_nr = 0
                ver_naam = '?'

            try:
                wedstrijd_geslacht = lid_nr2geslacht[sporter.lid_nr]
            except KeyError:
                # wedstrijdgeslacht is niet bekend
                # neem het geslacht van de sporter zelf
                wedstrijd_geslacht = sporter.geslacht

            writer.writerow([sporter.lid_nr,        # TODO: sporter met meerdere bogen niet ondersteund
                             sessie_nr,
                             sporterboog.boogtype.afkorting,
                             klasse_afkorting,      # wedstrijdklasse zoals gedefinieerd voor de wedstrijd
                             '',                    # baan
                             1,                     # indiv qualification
                             0,                     # team qualification
                             0,                     # indiv finals
                             0,                     # team finals
                             0,                     # mixed finals
                             sporter.achternaam,    # achternaam (wordt oms omgezet in hoofdletters)
                             sporter.voornaam,      # voornaam
                             wedstrijd_geslacht,    # M/0 is man, de rest vrouw
                             ver_nr,
                             ver_naam,
                             sporter.geboorte_datum.strftime('%Y-%m-%d')])
        # for

        return response


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
        return self.rol_nu in (Rollen.ROL_HWL, Rollen.ROL_BB)

    def get(self, request, *args, **kwargs):
        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=wedstrijd_pk))
        except (ValueError, TypeError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL:
            if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.nhb_ver.ver_nr:
                raise Http404('Wedstrijd is niet bij jullie vereniging')

        lid_nr2voorkeuren = dict()   # [lid_nr] = SporterVoorkeuren
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            sporter = voorkeuren.sporter

            lid_nr2voorkeuren[sporter.lid_nr] = voorkeuren
        # for

        aanmeldingen = (WedstrijdInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .exclude(status=INSCHRIJVING_STATUS_AFGEMELD)
                        .select_related('sessie',
                                        'wedstrijdklasse',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'korting')
                        .order_by('sessie',
                                  'wanneer',
                                  'status'))

        response = HttpResponse(content_type='text/csv; charset=UTF-8')
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen.csv"'

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings
        writer.writerow(['Reserveringsnummer', 'Aangemeld op', 'Status',
                         'Prijs', 'Korting', 'Ontvangen', 'Retour',
                         'Sessie', 'Code', 'Wedstrijdklasse',
                         'Lid nr', 'Sporter', 'Geslacht', 'Boog', 'Vereniging',
                         'Para classificatie', 'Voorwerpen op schietlijn', 'Para opmerking'])

        for aanmelding in aanmeldingen:
            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter
            reserveringsnummer = aanmelding.pk + settings.TICKET_NUMMER_START__WEDSTRIJD

            if sporter.bij_vereniging:
                ver_str = sporter.bij_vereniging.ver_nr_en_naam()
            else:
                ver_str = '[0000] Geen vereniging'

            # ga uit van het geslacht van de sporter zelf
            wedstrijd_geslacht = sporter.geslacht
            para_materiaal = para_notitie = ''

            try:
                voorkeuren = lid_nr2voorkeuren[sporter.lid_nr]
            except KeyError:
                pass
            else:
                if voorkeuren.para_met_rolstoel:
                    para_materiaal = 'Ja'
                para_notitie = voorkeuren.opmerking_para_sporter

                if voorkeuren.wedstrijd_geslacht_gekozen:
                    wedstrijd_geslacht = voorkeuren.wedstrijd_geslacht

            qset = aanmelding.bestelproduct_set.all()
            if qset.count() > 0:
                bestelproduct = qset[0]
                prijs_str = '€ %s' % bestelproduct.prijs_euro
            else:
                prijs_str = 'Geen (handmatige inschrijving)'

            if aanmelding.korting:
                korting_str = '%s%%' % aanmelding.korting.percentage
            else:
                korting_str = 'Geen'

            writer.writerow([
                reserveringsnummer,
                aanmelding.wanneer.strftime('%Y-%m-%d %H:%M'),
                INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status],
                prijs_str,
                korting_str,
                '€ %s' % aanmelding.ontvangen_euro,
                '€ %s' % aanmelding.retour_euro,
                aanmelding.sessie.beschrijving,
                aanmelding.wedstrijdklasse.afkorting,
                aanmelding.wedstrijdklasse.beschrijving,
                sporter.lid_nr,
                sporter.volledige_naam(),
                GESLACHT2STR[wedstrijd_geslacht],
                sporterboog.boogtype.beschrijving,
                ver_str,
                sporter.para_classificatie,
                para_materiaal,
                para_notitie])
        # for

        return response


class KalenderDetailsAanmeldingView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de details van een inschrijving voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_AANMELDING_DETAILS
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_BB, Rollen.ROL_SPORTER)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:7]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
        except (TypeError, ValueError):
            raise Http404('Geen valide parameter')

        try:
            inschrijving = (WedstrijdInschrijving
                            .objects
                            .select_related('wedstrijd',
                                            'wedstrijd__organiserende_vereniging',
                                            'sessie',
                                            'wedstrijdklasse',
                                            'sporterboog',
                                            'sporterboog__sporter',
                                            'korting')
                            .get(pk=inschrijving_pk))
        except WedstrijdInschrijving.DoesNotExist:
            raise Http404('Aanmelding niet gevonden')

        if self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL):
            # alleen van de eigen vereniging laten zien
            ver = self.functie_nu.nhb_ver
            if inschrijving.wedstrijd.organiserende_vereniging != self.functie_nu.nhb_ver:
                raise Http404('Verkeerde vereniging')

        if self.rol_nu == Rollen.ROL_SPORTER:
            # alleen eigen inschrijvingen laten zien
            account = self.request.user
            sporter = Sporter.objects.get(account=account)
            if inschrijving.sporterboog.sporter.lid_nr != sporter.lid_nr:
                raise Http404('Niet jouw inschrijving')

        context['inschrijving'] = inschrijving
        context['sporter'] = sporter = inschrijving.sporterboog.sporter
        context['ver'] = sporter.bij_vereniging

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_HWL):
            context['toon_contactgegevens'] = True

        context['voorkeuren'] = voorkeuren = get_sporter_voorkeuren(sporter)
        voorkeuren.wedstrijdgeslacht_str = GESLACHT2STR[voorkeuren.wedstrijd_geslacht]

        inschrijving.status_str = INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

        if inschrijving.status != INSCHRIJVING_STATUS_AFGEMELD:
            inschrijving.url_afmelden = reverse('Wedstrijden:afmelden',
                                                kwargs={'inschrijving_pk': inschrijving.pk})

        if inschrijving.korting:
            inschrijving.korting_str = '%s%%' % inschrijving.korting.percentage
        else:
            inschrijving.korting_str = None

        qset = inschrijving.bestelproduct_set.all()
        if qset.count() > 0:
            inschrijving.bestelproduct = qset[0]
        else:
            inschrijving.bestelproduct = None

        url_aanmeldingen = reverse('Wedstrijden:aanmeldingen',
                                   kwargs={'wedstrijd_pk': inschrijving.wedstrijd.pk})

        if self.rol_nu == Rollen.ROL_BB:
            context['kruimels'] = (
                (reverse('Wedstrijden:manager'), 'Wedstrijdkalender'),
                (url_aanmeldingen, 'Aanmeldingen'),
                (None, 'Details aanmelding')
            )
        else:
            if not url_aanmeldingen:
                # exacte wedstrijd weten we niet!
                url_aanmeldingen = reverse('Wedstrijden:vereniging')

            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (url_aanmeldingen, 'Aanmeldingen'),
                (None, 'Details aanmelding')
            )

        menu_dynamics(self.request, context)
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
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_BB)

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving_pk)
        except (TypeError, ValueError, WedstrijdInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        if self.rol_nu != Rollen.ROL_BB:
            # controleer dat dit een inschrijving is op een wedstrijd van de vereniging
            ver = self.functie_nu.nhb_ver
            if inschrijving.wedstrijd.organiserende_vereniging != ver:
                raise Http404('Verkeerde vereniging')

        snel = str(request.POST.get('snel', ''))[:1]

        if inschrijving.status == INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            if inschrijving.bestelproduct_set.count() > 0:
                product = inschrijving.bestelproduct_set.all()[0]
                bestel_mutatieverzoek_verwijder_product_uit_mandje(inschrijving.koper, product, snel == '1')
        else:
            bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel == '1')

        url = reverse('Wedstrijden:details-aanmelding', kwargs={'inschrijving_pk': inschrijving.pk})

        return HttpResponseRedirect(url)

# end of file
