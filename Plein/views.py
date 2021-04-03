# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404
from django.urls import Resolver404
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from Functie.rol import Rollen, rol_get_huidige, rol_get_beschrijving
from Handleiding.views import reverse_handleiding
from Mailer.models import mailer_notify_internal_error
from Taken.taken import eval_open_taken
from .menu import menu_dynamics
import traceback
import logging
import sys


TEMPLATE_PLEIN_BEZOEKER = 'plein/plein-bezoeker.dtl'    # niet ingelogd
TEMPLATE_PLEIN_SCHUTTER = 'plein/plein-schutter.dtl'    # schutter (ROL_SCHUTTER)
TEMPLATE_PLEIN_BEHEERDER = 'plein/plein-beheerder.dtl'  # beheerder (ROL_BB/BKO/RKO/RCL/SEC/HWL/WL)
TEMPLATE_PRIVACY = 'plein/privacy.dtl'
TEMPLATE_NIET_ONDERSTEUND = 'plein/niet-ondersteund.dtl'
TEMPLATE_HANDLER_403 = 'plein/fout_403.dtl'
TEMPLATE_HANDLER_404 = 'plein/fout_404.dtl'
TEMPLATE_HANDLER_500 = 'plein/fout_500.dtl'

ROL2HANDLEIDING_PAGINA = {
    Rollen.ROL_BB: settings.HANDLEIDING_BB,
    Rollen.ROL_BKO: settings.HANDLEIDING_BKO,
    Rollen.ROL_RKO: settings.HANDLEIDING_RKO,
    Rollen.ROL_RCL: settings.HANDLEIDING_RCL,
    Rollen.ROL_HWL: settings.HANDLEIDING_HWL,
    Rollen.ROL_WL:  settings.HANDLEIDING_WL,
    Rollen.ROL_SEC: settings.HANDLEIDING_SEC,
}

my_logger = logging.getLogger('NHBApps.Plein')
in_500_handler = False


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

        if request.user.is_authenticated:
            rol_nu = rol_get_huidige(request)

            if rol_nu == Rollen.ROL_SCHUTTER:
                template = TEMPLATE_PLEIN_SCHUTTER

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

                context['handleiding_url'] = reverse_handleiding(handleiding_pagina)

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
        context['email_bondsburo'] = settings.EMAIL_BONDSBURO
        menu_dynamics(self.request, context)
        return context


class NietOndersteundView(View):

    """ Django class-based om te rapporteren dat de browser niet ondersteund wordt """

    def get(self, request, *args, **kwargs):
        context = dict()
        return render(request, TEMPLATE_NIET_ONDERSTEUND, context)


def site_handler403_permission_denied(request, exception=None):

    """ Django view om code-403 fouten af te handelen.
        403 is "permission denied"

        Deze functie wordt aangeroepen voor de volgende excepties:
            PermissionDenied from django.core.exceptions
    """
    # print('site_handler403: exception=%s; info=%s' % (repr(exception), str(exception)))
    context = dict()
    info = str(exception)
    if len(info):
        context['info'] = info
    return render(request, TEMPLATE_HANDLER_403, context)


def site_handler404_page_not_found(request, exception=None):

    """ Django view om code-404 fouten af te handelen.
        404 is "page not found"
        404 wordt ook nog gebruikt in heel veel foutsituaties

        Deze function wordt aangeroepen bij de volgende excepties:
            Http404 from django.http
            Resolver404 from django.urls
    """
    # print('site_handler404: exception=%s; info=%s' % (repr(exception), str(exception)))
    context = dict()
    if repr(exception).startswith('Resolver404('):
        # voorkom dat we een hele urlconf dumpen naar de gebruiker
        info = "Pagina bestaat niet"
    else:
        info = str(exception)
    if len(info):
        context['info'] = info
    return render(request, TEMPLATE_HANDLER_404, context)


def site_handler500_internal_server_error(request, exception=None):

    """ Django view om code-500 fouten af te handelen.
        500 is "server internal error"

        Deze function wordt aangeroepen bij runtime errors met de view code.
    """
    #print('site_handler500: exception=%s; info=%s' % (repr(exception), str(exception)))
    global in_500_handler

    # vang de fout en schrijf deze in de syslog
    tups = sys.exc_info()
    tb = traceback.format_exception(*tups)
    tb_msg = '\n'.join(tb)
    my_logger.error('Internal server error:\n' + tb_msg)

    # voorkom fout op fout
    if not in_500_handler:              # pragma: no branch
        in_500_handler = True

        # stuur een mail naar de ontwikkelaars
        # reduceer tot de nuttige regels
        tb = [line for line in tb if '/site-packages/' not in line]
        tb_msg = '\n'.join(tb)

        # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
        mailer_notify_internal_error(tb_msg)

        in_500_handler = False

    context = dict()
    return render(request, TEMPLATE_HANDLER_500, context)


class TestSpecialePagina(View):

    """ deze view wordt gebruikt om de site_handlers hier boven te raken tijdens autotest """
    @staticmethod
    def get(request, *args, **kwargs):
        code = kwargs['code']
        if code == '403a':
            raise PermissionDenied('test')

        if code == '403b':
            raise PermissionDenied()

        if code == '404a':
            raise Http404('test')

        if code == '404b':
            raise Http404()

        if code == '404c':
            raise Resolver404()

        if code == '500':       # pragma: no branch
            # nog geen exceptie gevonden die hiervoor gebruikt kan worden
            return site_handler500_internal_server_error(request, None)


# end of file
