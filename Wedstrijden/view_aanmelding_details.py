# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import ObjectDoesNotExist
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import GESLACHT2STR
from Bestelling.operations import (bestel_mutatieverzoek_afmelden_wedstrijd,
                                   bestel_mutatieverzoek_verwijder_regel_uit_mandje,
                                   bestel_mutatieverzoek_wedstrijdinschrijving_aanpassen)
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Sporter.models import SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_TO_SHORT_STR,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
from Wedstrijden.models import WedstrijdInschrijving, KalenderWedstrijdklasse, WedstrijdSessie, Wedstrijd
from Wedstrijden.operations.kwalificatie_scores import get_kwalificatie_scores
from Wedstrijden.view_aanmeldingen import get_inschrijving_mh_bestel_nr
from WedstrijdInschrijven.operations import get_sessies
from types import SimpleNamespace

TEMPLATE_WEDSTRIJDEN_AANMELDING_DETAILS = 'wedstrijden/aanmelding-details.dtl'
TEMPLATE_WEDSTRIJDEN_AANMELDING_AANPASSEN = 'wedstrijden/aanmelding-aanpassen.dtl'


class WedstrijdAanmeldingDetailsView(UserPassesTestMixin, TemplateView):

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
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

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
            raise Http404('Inschrijving niet gevonden')

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL):
            # alleen van de eigen vereniging laten zien
            if inschrijving.wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
                raise Http404('Verkeerde vereniging')

        context['inschrijving'] = inschrijving
        context['toon_sessie'] = inschrijving.sessie is not None
        context['sporter'] = sporter = inschrijving.sporterboog.sporter
        context['ver'] = sporter.bij_vereniging

        context['voorkeuren'] = voorkeuren = get_sporter_voorkeuren(sporter)
        voorkeuren.wedstrijdgeslacht_str = GESLACHT2STR[voorkeuren.wedstrijd_geslacht]

        inschrijving.reserveringsnummer = inschrijving.pk + settings.TICKET_NUMMER_START__WEDSTRIJD

        inschrijving.status_str = WEDSTRIJD_INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

        inschrijving.bestelnummer_str = get_inschrijving_mh_bestel_nr(inschrijving)

        if inschrijving.status not in (WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                       WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD):
            inschrijving.url_afmelden = reverse('Wedstrijden:afmelden',
                                                kwargs={'inschrijving_pk': inschrijving.pk})

            inschrijving.url_aanpassen = reverse('Wedstrijden:aanpassen',
                                                 kwargs={'inschrijving_pk': inschrijving.pk})

        if inschrijving.korting:
            inschrijving.korting_str = '%s%%' % inschrijving.korting.percentage
        else:
            inschrijving.korting_str = None

        regel = inschrijving.bestelling
        if regel:
            inschrijving.bedrag_euro_str = format_bedrag_euro(regel.bedrag_euro)
        else:
            inschrijving.bedrag_euro_str = None

        wedstrijd = inschrijving.wedstrijd
        if wedstrijd.eis_kwalificatie_scores:
            inschrijving.scores = get_kwalificatie_scores(inschrijving)
        else:
            inschrijving.scores = list()

        if self.rol_nu == Rol.ROL_MWZ:
            context['kruimels'] = [
                (reverse('Wedstrijden:manager'), 'Wedstrijdkalender'),
            ]
        else:
            # HWL
            context['kruimels'] = [
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            ]

        context['kruimels'].append((reverse('Wedstrijden:aanmeldingen',
                                            kwargs={'wedstrijd_pk': inschrijving.wedstrijd.pk}), 'Aanmeldingen'))
        context['kruimels'].append((None, 'Details aanmelding'))

        return context


class AanpassenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders aanpassingen doen in een inschrijving """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_AANMELDING_AANPASSEN
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

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
                                            'sporterboog__sporter__bij_vereniging',
                                            'sporterboog__sporter__bij_vereniging__regio',
                                            'sporterboog__sporter__bij_vereniging__regio__rayon',
                                            'korting',
                                            'bestelling')
                            .filter(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                                WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD))
                            .get(pk=inschrijving_pk))
        except WedstrijdInschrijving.DoesNotExist:
            raise Http404('Inschrijving niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            # alleen van de eigen vereniging laten aanpassen
            if inschrijving.wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
                raise Http404('Verkeerde vereniging')

        context['inschrijving'] = inschrijving
        context['sporter'] = sporter = inschrijving.sporterboog.sporter
        context['ver'] = sporter.bij_vereniging

        inschrijving.reserveringsnummer = inschrijving.pk + settings.TICKET_NUMMER_START__WEDSTRIJD
        inschrijving.bestelnummer_str = get_inschrijving_mh_bestel_nr(inschrijving)

        context['voorkeuren'] = voorkeuren = get_sporter_voorkeuren(sporter)
        voorkeuren.wedstrijdgeslacht_str = GESLACHT2STR[voorkeuren.wedstrijd_geslacht]

        context['keuzes'] = keuzes = list()

        for sporterboog in SporterBoog.objects.filter(sporter=sporter, voor_wedstrijd=True).select_related('boogtype'):

            tups = get_sessies(inschrijving.wedstrijd, sporter, voorkeuren, sporterboog.boogtype.pk)
            sessies = tups[0]

            for sessie in sessies:
                for klasse in sessie.klassen:
                    if klasse.is_compat:
                        is_gekozen = (sessie == inschrijving.sessie and
                                      klasse == inschrijving.wedstrijdklasse)

                        keuze = SimpleNamespace(
                                        nr=len(keuzes)+1,
                                        sporterboog=sporterboog,
                                        sessie=sessie,
                                        klasse=klasse,
                                        is_gekozen=is_gekozen)
                        keuzes.append(keuze)
                # for
            # for
        # for

        context['url_selecteer'] = reverse('Wedstrijden:aanpassen',
                                           kwargs={'inschrijving_pk': inschrijving.pk})

        if self.rol_nu == Rol.ROL_MWZ:
            context['kruimels'] = [
                (reverse('Wedstrijden:manager'), 'Wedstrijdkalender'),
            ]
        else:
            # HWL
            context['kruimels'] = [
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            ]

        context['kruimels'].append((reverse('Wedstrijden:aanmeldingen',
                                            kwargs={'wedstrijd_pk': inschrijving.wedstrijd.pk}), 'Aanmeldingen'))
        context['kruimels'].append((reverse('Wedstrijden:details-aanmelding',
                                            kwargs={'inschrijving_pk': inschrijving.pk}), 'Details aanmelding'))
        context['kruimels'].append((None, 'Aanpassen'))

        return context

    @staticmethod
    def _check_compat(wedstrijd: Wedstrijd, sporterboog: SporterBoog,
                      sessie_in: WedstrijdSessie, klasse_in: KalenderWedstrijdklasse):

        sporter = sporterboog.sporter
        voorkeuren = get_sporter_voorkeuren(sporter)
        tups = get_sessies(wedstrijd, sporter, voorkeuren, sporterboog.boogtype.pk)
        sessies = tups[0]

        accepted = False
        for sessie in sessies:
            if sessie == sessie_in:
                for klasse in sessie.klassen:
                    if klasse == klasse_in:
                        if klasse.is_compat:
                            accepted = True
                # for
        # for

        return accepted

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = (WedstrijdInschrijving
                            .objects
                            .filter(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                                WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD))
                            .select_related('wedstrijd',
                                            'wedstrijd__organiserende_vereniging',
                                            'sporterboog__sporter',
                                            'sporterboog__sporter__bij_vereniging',
                                            'sporterboog__sporter__bij_vereniging__regio',
                                            'sporterboog__sporter__bij_vereniging__regio__rayon')
                            .get(pk=inschrijving_pk))
        except (TypeError, ValueError, WedstrijdInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            # controleer dat dit een inschrijving is op een wedstrijd van de vereniging
            ver = self.functie_nu.vereniging
            if inschrijving.wedstrijd.organiserende_vereniging != ver:
                raise Http404('Verkeerde vereniging')

        # oude inschrijving omzetten in een nieuwe inschrijving
        sporterboog_str = request.POST.get('sporterboog', '')[:6]   # afkappen voor de veiligheid
        sessie_str = request.POST.get('sessie', '')[:6]             # afkappen voor de veiligheid
        klasse_str = request.POST.get('klasse', '')[:6]             # afkappen voor de veiligheid

        try:
            sporterboog_pk = int(sporterboog_str)
            sessie_pk = int(sessie_str)
            klasse_pk = int(klasse_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek (1)')

        try:
            sessie = inschrijving.wedstrijd.sessies.get(pk=sessie_pk)
            klasse = sessie.wedstrijdklassen.get(pk=klasse_pk)
            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter',
                                           'boogtype')
                           .filter(sporter=inschrijving.sporterboog.sporter)
                           .get(pk=sporterboog_pk))
        except ObjectDoesNotExist:
            raise Http404('Slecht verzoek (2)')

        # controleer dat sessie, wedstrijdklasse en boog toegestaan zijn
        if not self._check_compat(inschrijving.wedstrijd, sporterboog, sessie, klasse):
            raise Http404('Slecht verzoek (3)')

        # zet het verzoek door aan de achtergrondtaak
        door_account = get_account(request)
        snel = str(request.POST.get('snel', ''))[:1]

        bestel_mutatieverzoek_wedstrijdinschrijving_aanpassen(inschrijving, sporterboog, sessie, klasse,
                                                              door_account, snel)

        url = reverse('Wedstrijden:details-aanmelding', kwargs={'inschrijving_pk': inschrijving.pk})
        return HttpResponseRedirect(url)


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
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving_pk)
        except (TypeError, ValueError, WedstrijdInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        if self.rol_nu != Rol.ROL_MWZ:
            # controleer dat dit een inschrijving is op een wedstrijd van de vereniging
            ver = self.functie_nu.vereniging
            if inschrijving.wedstrijd.organiserende_vereniging != ver:
                raise Http404('Verkeerde vereniging')

        snel = str(request.POST.get('snel', ''))[:1]

        if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            regel = inschrijving.bestelling
            bestel_mutatieverzoek_verwijder_regel_uit_mandje(inschrijving.koper, regel, snel == '1')
        else:
            bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel == '1')

        url = reverse('Wedstrijden:details-aanmelding', kwargs={'inschrijving_pk': inschrijving.pk})

        return HttpResponseRedirect(url)

# end of file
