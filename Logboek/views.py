# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.urls import reverse
from Functie.rol import Rollen, rol_get_huidige
from Plein.menu import menu_dynamics
from .models import LogboekRegel
from urllib.parse import quote_plus


TEMPLATE_LOGBOEK_REST = 'logboek/rest.dtl'
TEMPLATE_LOGBOEK_ROLLEN = 'logboek/rollen.dtl'
TEMPLATE_LOGBOEK_UITROL = 'logboek/uitrol.dtl'
TEMPLATE_LOGBOEK_RECORDS = 'logboek/records.dtl'
TEMPLATE_LOGBOEK_ACCOUNTS = 'logboek/accounts.dtl'
TEMPLATE_LOGBOEK_CLUSTERS = 'logboek/clusters.dtl'
TEMPLATE_LOGBOEK_COMPETITIE = 'logboek/competitie.dtl'
TEMPLATE_LOGBOEK_NHBSTRUCTUUR = 'logboek/nhbstructuur.dtl'
TEMPLATE_LOGBOEK_ACCOMMODATIES = 'logboek/accommodaties.dtl'

RESULTS_PER_PAGE = 50


class LogboekBasisView(UserPassesTestMixin, ListView):

    """ Deze view toont het logboek """

    # class variables shared by all instances
    template_name = ""              # must override
    base_url = ""                   # must override
    paginate_by = RESULTS_PER_PAGE  # enable Paginator built into ListView
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) in (Rollen.ROL_IT, Rollen.ROL_BB)

    def _make_link_urls(self, context):
        # voorbereidingen voor een regel met volgende/vorige links
        # en rechtstreekse links naar een 10 pagina's
        links = list()

        num_pages = context['paginator'].num_pages
        page_nr = context['page_obj'].number

        # previous
        if page_nr > 1:
            tup = ('vorige', self.base_url + '?page=%s' % (page_nr - 1))
            links.append(tup)
        else:
            tup = ('vorige_disable', '')
            links.append(tup)

        # block van 10 pagina's; huidige pagina in het midden
        range_start = page_nr - 5
        range_end = range_start + 9
        if range_start < 1:
            range_end += (1 - range_start)  # 1-0=1, 1--1=2, 1--2=3, etc.
            range_start = 1
        if range_end > num_pages:
            range_end = num_pages
        for pgnr in range(range_start, range_end+1):
            tup = ('%s' % pgnr, self.base_url + '?page=%s' % pgnr)
            links.append(tup)
        # for

        # next
        if page_nr < num_pages:
            tup = ('volgende', self.base_url + '?page=%s' % (page_nr + 1))
            links.append(tup)
        else:
            tup = ('volgende_disable', '')
            links.append(tup)

        return links

    def get_queryset(self):
        # haal de queryset met focus op en filter deze op een eventuele zoekterm
        qset = self.get_focused_queryset()

        zoekterm = self.request.GET.get('zoekterm', '')
        if zoekterm:
            qset = (qset
                    .annotate(hele_naam=Concat('actie_door_account__first_name',
                                               Value(' '),
                                               'actie_door_account__last_name'))
                    .filter(Q(gebruikte_functie__icontains=zoekterm) |
                            Q(actie_door_account__hele_naam__icontains=zoekterm) |
                            Q(activiteit__icontains=zoekterm)))
        return qset

    def get_focused_queryset(self):
        # must be implemented by sub-class
        raise NotImplementedError()     # pragma: no cover

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['filter'] = self.filter

        if context['is_paginated']:
            context['page_links'] = self._make_link_urls(context)
            context['active'] = str(context['page_obj'].number)

        # extra informatie vaststellen, maar alleen voor de actieve pagina
        for obj in context['object_list']:
            obj.door = obj.bepaal_door()
        # for

        context['url_rest'] = reverse('Logboek:rest')
        context['url_rollen'] = reverse('Logboek:rollen')
        context['url_uitrol'] = reverse('Logboek:uitrol')
        context['url_records'] = reverse('Logboek:records')
        context['url_accounts'] = reverse('Logboek:accounts')
        context['url_clusters'] = reverse('Logboek:clusters')
        context['url_competitie'] = reverse('Logboek:competitie')
        context['url_nhbstructuur'] = reverse('Logboek:nhbstructuur')
        context['url_accommodaties'] = reverse('Logboek:accommodaties')

        context['filter_url'] = self.base_url

        # extra knop tonen om zoekterm te wissen
        zoekterm = self.request.GET.get('zoekterm', '')
        if zoekterm:
            context['zoekterm'] = zoekterm
            context['unfiltered_url'] = reverse('Logboek:%s' % self.filter)

            zoekterm = "?zoekterm=%s" % quote_plus(zoekterm)
            context['url_rest'] += zoekterm
            context['url_rollen'] += zoekterm
            context['url_uitrol'] += zoekterm
            context['url_records'] += zoekterm
            context['url_accounts'] += zoekterm
            context['url_clusters'] += zoekterm
            context['url_competitie'] += zoekterm
            context['url_nhbstructuur'] += zoekterm
            context['url_accommodaties'] += zoekterm

        menu_dynamics(self.request, context, actief='hetplein')
        return context


class LogboekRestView(LogboekBasisView):
    """ Deze view toont de het hele logboek """

    template_name = TEMPLATE_LOGBOEK_REST
    filter = 'rest'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:alles')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .exclude(Q(gebruikte_functie='Records') |           # Records
                         Q(gebruikte_functie='maak_beheerder') |    # Accounts
                         Q(gebruikte_functie='Wachtwoord') |        # Accounts
                         Q(gebruikte_functie='Inloggen') |
                         Q(gebruikte_functie='Inlog geblokkeerd') |
                         Q(gebruikte_functie='OTP controle') |
                         Q(gebruikte_functie='Bevestig e-mail') |
                         Q(gebruikte_functie='Registreer met NHB nummer') |
                         Q(gebruikte_functie='Rollen') |            # Rollen
                         Q(gebruikte_functie='NhbStructuur') |      # NhbStructuur
                         Q(gebruikte_functie='Competitie') |        # Competitie
                         Q(gebruikte_functie='Accommodaties') |     # Accommodatie
                         Q(gebruikte_functie='Clusters') |          # Clusters
                         Q(gebruikte_functie='Uitrol') |            # Uitrol
                         Q(gebruikte_functie='oude_site_overnemen (command line)'))     # Import
                .order_by('-toegevoegd_op'))


class LogboekRecordsView(LogboekBasisView):
    """ Deze view toont de regels uit het logboek die met het importeren van de records te maken hebben """

    template_name = TEMPLATE_LOGBOEK_RECORDS
    filter = 'records'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:records')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .filter(gebruikte_functie='Records')
                .order_by('-toegevoegd_op'))


class LogboekAccountsView(LogboekBasisView):
    """ Deze view toont de logboek regels die met Accounts te maken hebben: aanmaken, inloggen, OTP, etc. """

    template_name = TEMPLATE_LOGBOEK_ACCOUNTS
    filter = 'accounts'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:accounts')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .filter(Q(gebruikte_functie='maak_beheerder') |
                        Q(gebruikte_functie='Inloggen') |
                        Q(gebruikte_functie='Inlog geblokkeerd') |
                        Q(gebruikte_functie='OTP controle') |
                        Q(gebruikte_functie='Bevestig e-mail') |
                        Q(gebruikte_functie='Registreer met NHB nummer') |
                        Q(gebruikte_functie='Wachtwoord'))
                .order_by('-toegevoegd_op'))


class LogboekRollenView(LogboekBasisView):
    """ Deze view toont de logboek regels die met het koppelen van rollen te maken hebben """

    template_name = TEMPLATE_LOGBOEK_ROLLEN
    filter = 'rollen'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:rollen')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .filter(gebruikte_functie='Rollen')
                .order_by('-toegevoegd_op'))


class LogboekNhbStructuurView(LogboekBasisView):
    """ Deze view toont de logboek regels die met het importeren van de CRM data te maken hebben """

    template_name = TEMPLATE_LOGBOEK_NHBSTRUCTUUR
    filter = 'nhbstructuur'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:nhbstructuur')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .filter(gebruikte_functie='NhbStructuur')
                .order_by('-toegevoegd_op'))


class LogboekCompetitieView(LogboekBasisView):
    """ Deze view toont de logboek regels die met het beheer van de competitie te maken hebben """

    template_name = TEMPLATE_LOGBOEK_COMPETITIE
    filter = 'competitie'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:competitie')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .filter(gebruikte_functie='Competitie')
                .order_by('-toegevoegd_op'))


class LogboekAccommodatiesView(LogboekBasisView):
    """ Deze view toont de logboek regels die met het beheer van de accommodaties te maken hebben """

    template_name = TEMPLATE_LOGBOEK_ACCOMMODATIES
    filter = 'accommodaties'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:accommodaties')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .filter(gebruikte_functie='Accommodaties')
                .order_by('-toegevoegd_op'))


class LogboekClustersView(LogboekBasisView):
    """ Deze view toont de logboek regels die met het beheer van de clusters te maken hebben """

    template_name = TEMPLATE_LOGBOEK_CLUSTERS
    filter = 'clusters'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:clusters')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .filter(gebruikte_functie='Clusters')
                .order_by('-toegevoegd_op'))


class LogboekUitrolView(LogboekBasisView):
    """ Deze view toont de logboek regels die met de uitrol van software te maken hebben """

    template_name = TEMPLATE_LOGBOEK_UITROL
    filter = 'uitrol'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = reverse('Logboek:uitrol')

    def get_focused_queryset(self):
        """ retourneer de data voor de template view """
        return (LogboekRegel
                .objects
                .select_related('actie_door_account')
                .filter(gebruikte_functie='Uitrol')
                .order_by('-toegevoegd_op'))


# end of file
