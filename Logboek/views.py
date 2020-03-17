# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from Functie.rol import Rollen, rol_get_huidige
from Plein.menu import menu_dynamics
from .models import LogboekRegel


TEMPLATE_LOGBOEK_ALLES = 'logboek/logboek.dtl'
TEMPLATE_LOGBOEK_ACCOUNTS = 'logboek/logboek-accounts.dtl'
TEMPLATE_LOGBOEK_NHBSTRUCTUUR = 'logboek/logboek-nhbstructuur.dtl'
TEMPLATE_LOGBOEK_RECORDS = 'logboek/logboek-records.dtl'
TEMPLATE_LOGBOEK_ROLLEN = 'logboek/logboek-rollen.dtl'


class LogboekBasisView(UserPassesTestMixin, ListView):

    """ Deze view toont het logboek """

    # class variables shared by all instances
    template_name = ""      # must override

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) in (Rollen.ROL_IT, Rollen.ROL_BB)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # must override
        return None         # pragma: no cover

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='logboek')
        return context


class LogboekAllesView(LogboekBasisView):
    """ Deze view toont de het hele logboek """
    template_name = TEMPLATE_LOGBOEK_ALLES

    def get_queryset(self):
        """ retourneer de data voor de template view """
        # 100 nieuwste logboek entries
        # TODO: pagination toevoegen
        objs = LogboekRegel.objects.all().order_by('-toegevoegd_op')[:100]
        for obj in objs:
            obj.door = obj.bepaal_door()
        # for
        return objs


class LogboekRecordsView(LogboekBasisView):
    """ Deze view toont de regels uit het logboek die met het importeren van de records te maken hebben """
    template_name = TEMPLATE_LOGBOEK_RECORDS

    def get_queryset(self):
        """ retourneer de data voor de template view """
        objs = LogboekRegel.objects.all().filter(gebruikte_functie='Records').order_by('-toegevoegd_op')[:100]
        for obj in objs:
            obj.door = obj.bepaal_door()
        # for
        return objs


class LogboekAccountsView(LogboekBasisView):
    """ Deze view toont de logboek regels die met Accounts te maken hebben: aanmaken, inloggen, OTP, etc. """
    template_name = TEMPLATE_LOGBOEK_ACCOUNTS

    def get_queryset(self):
        """ retourneer de data voor de template view """
        objs = LogboekRegel.objects.all().filter(Q(gebruikte_functie='maak_beheerder') |
                                                 Q(gebruikte_functie='Inloggen') |
                                                 Q(gebruikte_functie='OTP controle') |
                                                 Q(gebruikte_functie='Bevestig e-mail') |
                                                 Q(gebruikte_functie='Registreer met NHB nummer')).order_by('-toegevoegd_op')[:100]
        for obj in objs:
            obj.door = obj.bepaal_door()
        # for
        return objs


class LogboekRollenView(LogboekBasisView):
    """ Deze view toont de logboek regels die met het koppelen van rollen te maken hebben """
    template_name = TEMPLATE_LOGBOEK_ROLLEN

    def get_queryset(self):
        """ retourneer de data voor de template view """
        objs = LogboekRegel.objects.all().filter(gebruikte_functie='Rollen').order_by('-toegevoegd_op')[:100]
        for obj in objs:
            obj.door = obj.bepaal_door()
        # for
        return objs


class LogboekNhbStructuurView(LogboekBasisView):
    """ Deze view toont de logboek regels die met het importeren van de CRM data te maken hebben """
    template_name = TEMPLATE_LOGBOEK_NHBSTRUCTUUR

    def get_queryset(self):
        """ retourneer de data voor de template view """
        objs = LogboekRegel.objects.all().filter(gebruikte_functie='NhbStructuur').order_by('-toegevoegd_op')[:100]
        for obj in objs:
            obj.door = obj.bepaal_door()
        # for
        return objs

# end of file
