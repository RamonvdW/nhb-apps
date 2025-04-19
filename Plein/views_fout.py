# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import Resolver404
from django.utils.http import urlencode
from django.shortcuts import render, reverse
from django.views.generic import View
from django.views.defaults import ERROR_PAGE_TEMPLATE
from django.core.exceptions import PermissionDenied
from Functie.rol import rol_get_huidige_functie
from Mailer.operations import mailer_notify_internal_error
from Site.core import urls
import traceback
import logging
import sys


TEMPLATE_HANDLER_403 = 'plein/fout_403.dtl'
TEMPLATE_HANDLER_404 = 'plein/fout_404.dtl'
TEMPLATE_HANDLER_500 = 'plein/fout_500.dtl'

my_logger = logging.getLogger('MH.Plein')
in_500_handler = False


def site_handler403_permission_denied(request, exception=None):

    """ Django view om code-403 fouten af te handelen.
        403 is "permission denied"

        Deze functie wordt aangeroepen voor de volgende excepties:
            PermissionDenied from django.core.exceptions
    """

    # typische authenticatie fouten zijn omdat de gebruiker niet (meer) ingelogd is
    if not request.user.is_authenticated:
        url = reverse('Account:login')

        # TODO: next_url voor URL naar beheerdersfunctie doorgeven aan 2FA controle

        # whitelist een aantal urls die we willen ondersteunen
        params = dict()

        if request.path.startswith('/bondspas/'):
            # vervang alle mogelijke urls naar een basale
            params['next'] = '/bondspas/toon/'

        elif request.path.startswith('/sporter/'):
            # sporter, geen dynamische url voor de bondspas
            params['next'] = request.path

        elif request.path.startswith('/scheidsrechter/'):
            # sommige sporters zijn ook scheidsrechter
            params['next'] = request.path

        if len(params) > 0:
            params_str = urlencode(params)
            params_str = params_str.replace('%2F', '/')     # re-beautify
            url = url + '?' + params_str

        return HttpResponseRedirect(url)

    # print('site_handler403: exception=%s; info=%s' % (repr(exception), str(exception)))
    context = dict()
    info = str(exception)
    if len(info):
        context['info'] = info

    context['robots'] = 'noindex'   # prevent indexing this error message page

    context['email_support'] = settings.EMAIL_SUPPORT
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
    if type(exception) == Resolver404:
        # behandel verzoeken op de root met een echte 404
        # dit zijn typisch verzoeken voor icons, robots.txt, etc.
        rauw = True
        try:
            path = exception.args[0]['path']
            pos = path.find('/')
            if pos > 0:
                sub = path[:pos+1]
                toplevel = [str(pat.pattern) for pat in urls.urlpatterns if str(pat.pattern) != '']
                if sub in toplevel:
                    rauw = False
        except (KeyError, IndexError, TypeError):
            # typical for an internally raised Resolver404()
            rauw = False
            path = ''

        if rauw:
            # geef een 'rauwe' 404 terug
            body = ERROR_PAGE_TEMPLATE % {
                'title': 'Not Found',
                'details': 'The requested resource was not found on this server.'}
            return HttpResponse(body, content_type='text/html', status=404)

        # voorkom dat we een hele urlconf dumpen naar de gebruiker
        info = "Pagina bestaat niet"
        if path:
            context['meta_path'] = path
    else:
        info = str(exception)
    if len(info):
        context['info'] = info

    context['robots'] = 'noindex'   # prevent indexing this error message page

    context['email_support'] = settings.EMAIL_SUPPORT
    return render(request, TEMPLATE_HANDLER_404, context)


def site_handler500_internal_server_error(request, exception=None):

    """ Django view om code-500 fouten af te handelen.
        500 is "server internal error"

        Deze function wordt aangeroepen bij runtime errors met de view code.
    """
    # print('site_handler500: exception=%s; info=%s' % (repr(exception), str(exception)))
    global in_500_handler

    # voorkom fout op fout
    if not in_500_handler:              # pragma: no branch
        in_500_handler = True

        _, functie_nu = rol_get_huidige_functie(request)

        tb_msg_start = 'Internal server error:\n\n%s %s\n' % (request.method, request.path)
        if functie_nu:
            tb_msg_start += 'Huidige functie: [%s] %s\n' % (functie_nu.pk, str(functie_nu))
        tb_msg_start += '\n'

        # vang de fout en schrijf deze in de syslog
        tups = sys.exc_info()
        tb = traceback.format_exception(*tups)

        # full traceback in the local log
        tb_msg = tb_msg_start + '\n'.join(tb)
        my_logger.error(tb_msg)

        # stuur een mail naar de ontwikkelaars
        # reduceer tot de nuttige regels
        tb = [line for line in tb if '/site-packages/' not in line]
        tb_msg = tb_msg_start + '\n'.join(tb)

        # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
        mailer_notify_internal_error(tb_msg)

        in_500_handler = False

    context = dict()
    context['email_support'] = settings.EMAIL_SUPPORT
    context['robots'] = 'noindex'   # prevent indexing this error message page

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

        return site_handler404_page_not_found(request, 'Niet ondersteunde code')


# end of file
