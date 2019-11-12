# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from Plein.menu import menu_dynamics
from .models import LogboekRegel

TEMPLATE_LOGBOEK = 'logboek/logboek.dtl'


class LogboekView(LoginRequiredMixin, ListView):
    """ Deze view toont het logboek """

    # class variables shared by all instances
    template_name = TEMPLATE_LOGBOEK
    login_url = '/account/login/'       # no reverse call

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # 50 nieuwste logboek entries
        # TODO: pagination toevoegen
        objs = LogboekRegel.objects.all().order_by('-toegevoegd_op')[:50]
        for obj in objs:
            obj.door = obj.bepaal_door()
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='logboek')
        return context


# end of file
