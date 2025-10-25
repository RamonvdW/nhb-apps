# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404, JsonResponse
from django.utils import timezone
from django.shortcuts import redirect, render, reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Account.operations.session_vars import zet_sessionvar_if_changed
from Bestelling.operations import eval_mandje_inhoud
from Functie.definities import Rol
from Functie.rol import (rol_get_huidige, rol_get_beschrijving, rol_mag_wisselen, rol_eval_rechten_simpel,
                         gebruiker_is_scheids)
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Taken.operations import eval_open_taken


TEMPLATE_PLEIN_SPORTER = 'plein/plein-sporter.dtl'       # sporter (ROL_SPORTER)
TEMPLATE_PLEIN_BEZOEKER = 'plein/plein-bezoeker.dtl'     # niet ingelogd
TEMPLATE_PLEIN_BEHEERDER = 'plein/plein-beheerder.dtl'   # beheerder (ROL_BB/BKO/RKO/RCL/SEC/HWL/WL)
TEMPLATE_PLEIN_HANDLEIDINGEN = 'plein/handleidingen.dtl'
TEMPLATE_NIET_ONDERSTEUND = 'plein/niet-ondersteund.dtl'
TEMPLATE_PRIVACY = 'plein/privacy.dtl'
TEMPLATE_TEST_UI = 'plein/test-ui.dtl'

SESSIONVAR_VORIGE_POST = 'plein_vorige_post'


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


def plein_datetime_stamp_str():
    """ geeft een string terug die de huidige datum en tijd bevat tot uren en minuten
        wordt gebruikt om een nieuwe minuut te ontdekken
    """
    now = timezone.now()
    return now.strftime('%Y-%m-%d %H:%M')


def site_root_view(request):
    """ simpele Django view functie om vanaf de top-level site naar het Plein te gaan """

    if not is_browser_supported(request):
        return redirect('Plein:niet-ondersteund')

    return redirect('Plein:plein')


class PleinView(View):
    """ Django class-based view voor het Plein """

    # class variables shared by all instances
    # (geen)

    def dispatch(self, request, *args, **kwargs):
        """ checks + gebruiker doorsturen naar andere pagina's """

        # controleer of de browser niet ondersteund is
        if not is_browser_supported(request):
            return redirect('Plein:niet-ondersteund')

        # onvolledig gast-account registratie doorsturen naar de volgende vraag
        if request.user.is_authenticated:
            account = get_account(request)
            if account.is_gast:
                gast = account.gastregistratie_set.first()
                if gast and gast.fase != REGISTRATIE_FASE_COMPLEET:
                    # registratie is nog niet voltooid
                    # dwing terug naar de lijst met vragen
                    return redirect('Registreer:gast-meer-vragen')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        # zet alles goed voor bezoekers / geen rol
        template = TEMPLATE_PLEIN_BEZOEKER
        context = dict()

        context['naam_site'] = settings.NAAM_SITE

        # banner "ga naar live server" tonen?
        context['ga_naar_live_server'] = settings.IS_TEST_SERVER

        # site-specifieke default voor deze kaartjes
        context['toon_opleidingen'] = settings.TOON_OPLEIDINGEN

        allow_ping = False

        if request.user.is_authenticated:
            rol_nu = rol_get_huidige(request)

            if rol_nu == Rol.ROL_SPORTER:
                # ingelogd en huidige rol is sporter
                template = TEMPLATE_PLEIN_SPORTER

                context['url_profiel'] = reverse('Sporter:profiel')
                context['url_handleiding_leden'] = settings.URL_PDF_HANDLEIDING_LEDEN
                allow_ping = True

                if gebruiker_is_scheids(self.request):
                    context['url_scheids'] = reverse('Scheidsrechter:overzicht')

                if settings.TOON_LEDENVOORDEEL:
                    account = get_account(request)
                    if not account.is_gast:
                        context['url_voordeel'] = reverse('Ledenvoordeel:overzicht')

            elif rol_nu == Rol.ROL_NONE or rol_nu is None:
                # gebruik de bezoeker pagina
                pass

            else:
                # een van de vele beheerder rollen
                template = TEMPLATE_PLEIN_BEHEERDER

                context['huidige_rol'] = rol_get_beschrijving(request)

                if rol_nu == Rol.ROL_BB:
                    context['rol_is_bb'] = True
                    context['url_scheids'] = reverse('Scheidsrechter:overzicht')

                elif rol_nu == Rol.ROL_MO:
                    context['rol_is_mo'] = True
                elif rol_nu == Rol.ROL_MWZ:
                    context['rol_is_mwz'] = True
                elif rol_nu == Rol.ROL_MWW:
                    context['rol_is_mww'] = True
                elif rol_nu == Rol.ROL_BKO:
                    context['rol_is_bko'] = True
                elif rol_nu == Rol.ROL_RKO:
                    context['rol_is_rko'] = True
                elif rol_nu == Rol.ROL_RCL:
                    context['rol_is_rcl'] = True
                elif rol_nu == Rol.ROL_HWL:
                    context['rol_is_hwl'] = True
                elif rol_nu == Rol.ROL_WL:
                    context['rol_is_wl'] = True
                elif rol_nu == Rol.ROL_SEC:
                    context['rol_is_sec'] = True
                elif rol_nu == Rol.ROL_LA:
                    context['rol_is_la'] = True
                elif rol_nu == Rol.ROL_SUP:
                    context['rol_is_sup'] = True
                elif rol_nu == Rol.ROL_CS:
                    context['rol_is_cs'] = True
                elif rol_nu == Rol.ROL_MLA:
                    context['rol_is_mla'] = True
                else:                               # pragma: no cover
                    # vangnet voor nieuwe rollen
                    raise Http404("Onbekende rol %s (interne fout)" % rol_nu)

                if rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_MO, Rol.ROL_SUP, Rol.ROL_MLA):
                    # feedback, logboek, activiteit, etc.
                    context['toon_manager_sectie'] = True

                if rol_nu in (Rol.ROL_BB,
                              Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                              Rol.ROL_HWL, Rol.ROL_WL):
                    context['toon_bondscompetities'] = True

                allow_ping = True

        context['email_support'] = settings.EMAIL_SUPPORT
        context['url_email_support'] = 'mailto:' + settings.EMAIL_SUPPORT

        context['canonical'] = reverse('Plein:plein')

        if allow_ping:
            # laat een POST doen naar onszelf, maar maximaal 1x per minuut
            # (stamp bevat geen seconden)
            prev_stamp = request.session.get(SESSIONVAR_VORIGE_POST, '')
            do_ping = prev_stamp != plein_datetime_stamp_str()
            if do_ping:
                context['url_ping'] = reverse('Plein:plein')        # geen opvallende url

        return render(request, template, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze methode wordt aangeroepen als de javascript van de plein pagina een POST doet.
            Hier kunnen we zaken checken en mogen we een database wijziging doen (GET mag geen wijzigingen doen).

            We doen een nieuwe evaluatie van de rechten van de gebruiker en het aantal open taken.
            Als deze van geen-rechten naar wel-rechten gaat, dan komt Wissel van rol beschikbaar (en OTP, VHPG, etc.)
        """

        # CSRF token is al gecontroleerd

        if request.user.is_authenticated:
            account = get_account(request)

            # evalueer opnieuw of deze gebruiker van rol mag wisselen
            # dit wordt in de sessie opgeslagen en gebruikt om het Wissel van rol menu te tonen
            rol_eval_rechten_simpel(request, account)

            # kijk hoeveel taken er open staan
            eval_open_taken(request)

            # kijk of we iets in het mandje zit, zodat we het knopje kunnen tonen
            eval_mandje_inhoud(request)

            # onthoud wanneer deze post was
            # wordt gebruikt om de frequentie te beperken
            stamp = plein_datetime_stamp_str()
            zet_sessionvar_if_changed(request, SESSIONVAR_VORIGE_POST, stamp)

            out = {'ok': 'j'}
        else:
            out = {'ok': 'n'}

        return JsonResponse(out)


class PrivacyView(TemplateView):

    """ Django class-based view voor het Privacy bericht """

    # class variables shared by all instances
    template_name = TEMPLATE_PRIVACY

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['url_privacyverklaring'] = settings.PRIVACYVERKLARING_URL
        context['email_bb'] = settings.EMAIL_BONDSBUREAU
        context['url_email_bb'] = 'mailto:' + settings.EMAIL_BONDSBUREAU

        context['kruimels'] = (
            (None, 'Privacy'),
        )

        return context


class HandleidingenView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor toegang tot de Handleidingen """

    # class variables shared by all instances
    template_name = TEMPLATE_PLEIN_HANDLEIDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if self.request.user.is_authenticated:
            return rol_mag_wisselen(self.request)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_handleiding_leden'] = settings.URL_PDF_HANDLEIDING_LEDEN
        context['url_handleiding_beheerders'] = settings.URL_PDF_HANDLEIDING_BEHEERDERS
        context['url_handleiding_vereniging'] = settings.URL_PDF_HANDLEIDING_VERENIGINGEN

        context['kruimels'] = (
            (None, 'Handleidingen'),
        )

        return context


class NietOndersteundView(View):

    """ Django class-based om te rapporteren dat de browser niet ondersteund wordt """

    @staticmethod
    def get(request, *args, **kwargs):
        context = dict()
        context['email_support'] = settings.EMAIL_SUPPORT
        return render(request, TEMPLATE_NIET_ONDERSTEUND, context)


class TestUIView(View):

    @staticmethod
    def get(request, *args, **kwargs):
        context = {
            'icon': 'sluiten',
        }
        return render(request, TEMPLATE_TEST_UI, context)


# end of file
