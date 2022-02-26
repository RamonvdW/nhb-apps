# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import rol_mag_wisselen


def reverse_handleiding(request, pagina):
    """ geeft de URL terug voor een handleiding pagina """
    return reverse('Handleiding:' + pagina)


class HandleidingView(UserPassesTestMixin, View):

    """ Deze view biedt alle handleiding pagina's aan """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_mag_wisselen(self.request)

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        # print("resolver_match: %s" % repr(request.resolver_match))

        context = {}
        if request.resolver_match.url_name == 'begin':
            page = settings.HANDLEIDING_TOP
        else:
            page = request.resolver_match.url_name

        template = 'handleiding/%s.dtl' % page

        context['kruimels'] = (
            (None, 'Handleiding'),
        )

        menu_dynamics(self.request, context)
        return render(request, template, context)


# end of file
