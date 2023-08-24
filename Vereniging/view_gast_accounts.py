# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import GESLACHT2STR
from Bestel.definities import BESTELLING_STATUS2STR
from Bestel.models import BestelMandje, Bestelling
from Functie.rol import rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from Wedstrijden.definities import INSCHRIJVING_STATUS_TO_STR
from Wedstrijden.models import WedstrijdInschrijving

TEMPLATE_GAST_ACCOUNTS = 'vereniging/gast-accounts.dtl'
TEMPLATE_GAST_ACCOUNT_DETAILS = 'vereniging/gast-account-details.dtl'


class GastAccountsView(UserPassesTestMixin, ListView):
    """ Deze view laat de SEC van vereniging 8000 de gast-accounts lijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_GAST_ACCOUNTS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        objs = (GastRegistratie
                .objects
                .select_related('sporter',
                                'account')
                .order_by('-aangemaakt'))       # nieuwste eerst

        for gast in objs:
            sporter = gast.sporter
            account = gast.account

            # zoek de laatste-inlog bij elk lid
            # SEC mag de voorkeuren van de sporters aanpassen
            gast.url_details = reverse('Vereniging:gast-account-details',
                                       kwargs={'lid_nr': gast.lid_nr})

            gast.geen_inlog = 0
            if account:
                if account.last_login:
                    gast.laatste_inlog = gast.account.last_login
                else:
                    gast.geen_inlog = 2
            else:
                # onvoltooid account
                gast.geen_inlog = 1
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, "Gast accounts")
        )

        menu_dynamics(self.request, context)
        return context


class GastAccountDetailsView(UserPassesTestMixin, TemplateView):
    """ Deze view laat de SEC van vereniging 8000 de details van een gast-accounts zien """

    # class variables shared by all instances
    template_name = TEMPLATE_GAST_ACCOUNT_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    @staticmethod
    def _zoek_matches(gast, context):
        # zoek naar overeenkomst in CRM
        try:
            eigen_lid_nr = int(gast.eigen_lid_nummer)
        except ValueError:
            pks1 = list()
        else:
            pks1 = list(Sporter
                        .objects
                        .exclude(is_gast=True)
                        .filter(lid_nr=eigen_lid_nr)
                        .values_list('pk', flat=True))

        if gast.wa_id:
            pks2 = list(Sporter
                        .objects
                        .exclude(is_gast=True)
                        .filter(wa_id=gast.wa_id)
                        .values_list('pk', flat=True))
        else:
            pks2 = list()

        pks3 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(achternaam__iexact=gast.achternaam)
                    .values_list('pk', flat=True))

        pks4 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(voornaam__iexact=gast.voornaam)
                    .values_list('pk', flat=True))

        pks5 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(geboorte_datum=gast.geboorte_datum)
                    .values_list('pk', flat=True))

        pks6 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(email__iexact=gast.email)
                    .values_list('pk', flat=True))

        match_count = dict()    # [pk] = count
        for pk in pks1 + pks2 + pks3 + pks4 + pks5 + pks6:
            try:
                match_count[pk] += 1
            except KeyError:
                match_count[pk] = 1
        # for

        best = list()
        for pk, count in match_count.items():
            tup = (count, pk)
            best.append(tup)
        # for
        best.sort(reverse=True)     # hoogste eerst

        beste_pks = [pk for count, pk in best[:10] if count > 1]

        context['heeft_matches'] = len(beste_pks) > 0
        context['sporter_matches'] = Sporter.objects.select_related('account', 'bij_vereniging').filter(pk__in=beste_pks)

        for sporter in context['sporter_matches']:
            sporter.geslacht_str = GESLACHT2STR[sporter.geslacht]
        # for

    @staticmethod
    def _zoek_gebruik(gast, context):
        # zoek naar gebruik van het gast-account

        # zoek bestellingen / aankopen
        context['gast_mandje'] = BestelMandje.objects.filter(account=gast.account).first()
        context['gast_bestellingen'] = (Bestelling
                                        .objects
                                        .filter(account=gast.account)
                                        .order_by('-aangemaakt')        # nieuwste eerst
                                        .select_related('account')
                                        [:10])

        for bestelling in context['gast_bestellingen']:
            bestelling.status_str = BESTELLING_STATUS2STR[bestelling.status]
        # for

        # zoek inschrijvingen (er is geen bestelling van indien betaald door iemand anders)
        context['gast_wedstrijden'] = (WedstrijdInschrijving
                                       .objects
                                       .filter(sporterboog__sporter=gast.sporter)
                                       .select_related('wedstrijd')
                                       [:10])

        for inschrijving in context['gast_wedstrijden']:
            inschrijving.status_str = INSCHRIJVING_STATUS_TO_STR[inschrijving.status]
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        lid_nr = kwargs['lid_nr'][:6]       # afkappen voor extra veiligheid
        try:
            lid_nr = int(lid_nr)
            gast = GastRegistratie.objects.select_related('account', 'sporter').get(lid_nr=lid_nr)
        except (ValueError, GastRegistratie.DoesNotExist):
            raise Http404('Slechte parameter')

        gast.geslacht_str = GESLACHT2STR[gast.geslacht]
        context['gast'] = gast

        self._zoek_matches(gast, context)
        self._zoek_gebruik(gast, context)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, "Gast account details")
        )

        menu_dynamics(self.request, context)
        return context


# end of file
