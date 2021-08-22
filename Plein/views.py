# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from Functie.rol import Rollen, rol_get_huidige, rol_get_beschrijving
from Handleiding.views import reverse_handleiding
from Taken.taken import eval_open_taken
from .menu import menu_dynamics


TEMPLATE_PLEIN_BEZOEKER = 'plein/plein-bezoeker.dtl'    # niet ingelogd
TEMPLATE_PLEIN_SPORTER = 'plein/plein-sporter.dtl'      # sporter (ROL_SCHUTTER)
TEMPLATE_PLEIN_BEHEERDER = 'plein/plein-beheerder.dtl'  # beheerder (ROL_BB/BKO/RKO/RCL/SEC/HWL/WL)
TEMPLATE_PRIVACY = 'plein/privacy.dtl'
TEMPLATE_NIET_ONDERSTEUND = 'plein/niet-ondersteund.dtl'

ROL2HANDLEIDING_PAGINA = {
    Rollen.ROL_BB: settings.HANDLEIDING_BB,
    Rollen.ROL_BKO: settings.HANDLEIDING_BKO,
    Rollen.ROL_RKO: settings.HANDLEIDING_RKO,
    Rollen.ROL_RCL: settings.HANDLEIDING_RCL,
    Rollen.ROL_HWL: settings.HANDLEIDING_HWL,
    Rollen.ROL_WL:  settings.HANDLEIDING_WL,
    Rollen.ROL_SEC: settings.HANDLEIDING_SEC,
}


def is_browser_supported(request):
    """ analyseer de User Agent header
        geef True terug als de browser ondersteund wordt
    """

    # minimal requirement is ECMAScript 2015 (ES6)
    # since most browsers have supported this since 2016/2017, we don't need to check the version
    # only filter out Internet Explorer

    is_supported = True

    try:
        useragent = request.META['HTTP_USER_AGENT']
    except KeyError:
        # niet aanwezig, dus kan geen analyse doen
        pass
    else:
        if " MSIE " in useragent:
            # Internal Explorer versie tm IE10: worden niet ondersteund
            is_supported = False
        elif "Trident/7.0; rv:11" in useragent:
            # Internet Explorer versie 11
            is_supported = False

    # wel ondersteund
    return is_supported


def site_root_view(request):
    """ simpele Django view functie om vanaf de top-level site naar het Plein te gaan """

    if not is_browser_supported(request):
        return redirect('Plein:niet-ondersteund')

    return redirect('Plein:plein')


class PleinView(View):
    """ Django class-based view voor het Plein """

    # class variables shared by all instances

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        if not is_browser_supported(request):
            return redirect('Plein:niet-ondersteund')

        # zet alles goed voor bezoekers / geen rol
        template = TEMPLATE_PLEIN_BEZOEKER
        context = dict()

        # ga naar live server banner tonen?
        context['ga_naar_live_server'] = settings.IS_TEST_SERVER

        if request.user.is_authenticated:
            rol_nu = rol_get_huidige(request)

            if rol_nu == Rollen.ROL_SCHUTTER:
                template = TEMPLATE_PLEIN_SPORTER

            elif rol_nu == Rollen.ROL_NONE or rol_nu is None:
                # gebruik de bezoeker pagina
                pass

            else:
                # beheerder
                template = TEMPLATE_PLEIN_BEHEERDER

                try:
                    handleiding_pagina = ROL2HANDLEIDING_PAGINA[rol_nu]
                except KeyError:
                    handleiding_pagina = settings.HANDLEIDING_TOP

                context['handleiding_url'] = reverse_handleiding(request, handleiding_pagina)

                if rol_nu == Rollen.ROL_IT:
                    context['rol_is_it'] = True
                elif rol_nu == Rollen.ROL_BB:
                    context['rol_is_bb'] = True
                elif rol_nu == Rollen.ROL_BKO:
                    context['rol_is_bko'] = True
                elif rol_nu == Rollen.ROL_RKO:
                    context['rol_is_rko'] = True
                elif rol_nu == Rollen.ROL_RCL:
                    context['rol_is_rcl'] = True
                elif rol_nu == Rollen.ROL_HWL:
                    context['rol_is_hwl'] = True
                elif rol_nu == Rollen.ROL_WL:
                    context['rol_is_wl'] = True
                elif rol_nu == Rollen.ROL_SEC:
                    context['rol_is_sec'] = True
                else:                               # pragma: no cover
                    # vangnet voor nieuwe rollen
                    raise ValueError("PleinView: onbekende rol %s" % rol_nu)

                context['huidige_rol'] = rol_get_beschrijving(request)

                # kijk hoeveel taken er open staan
                eval_open_taken(request)

        context['naam_site'] = settings.NAAM_SITE
        context['email_support'] = settings.EMAIL_SUPPORT

        menu_dynamics(self.request, context)
        return render(request, template, context)


class PrivacyView(TemplateView):

    """ Django class-based view voor het Privacy bericht """

    # class variables shared by all instances
    template_name = TEMPLATE_PRIVACY

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['url_privacyverklaring'] = settings.PRIVACYVERKLARING_URL
        context['email_bondsbureau'] = settings.EMAIL_BONDSBUREAU
        menu_dynamics(self.request, context)
        return context


class NietOndersteundView(View):

    """ Django class-based om te rapporteren dat de browser niet ondersteund wordt """

    @staticmethod
    def get(request, *args, **kwargs):
        context = dict()
        context['email_support'] = settings.EMAIL_SUPPORT
        return render(request, TEMPLATE_NIET_ONDERSTEUND, context)


# end of file
