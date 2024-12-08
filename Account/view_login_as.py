# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from Account.forms import ZoekAccountForm, KiesAccountForm
from Account.models import Account, get_account
from Account.operations.otp import otp_zet_controle_gelukt, otp_zet_controle_niet_gelukt
from Account.operations.session_vars import zet_sessionvar_if_changed
from Account.view_login import account_plugins_login_gate
from Account.middleware import SESSIONVAR_ACCOUNT_LOGIN_AS_DATE
from Functie.rol import rol_bepaal_beschikbare_rollen
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from TijdelijkeCodes.definities import RECEIVER_ACCOUNT_WISSEL
from TijdelijkeCodes.operations import set_tijdelijke_codes_receiver, maak_tijdelijke_code_accountwissel
import logging


TEMPLATE_LOGIN_AS_ZOEK = 'account/login-as-zoek.dtl'
TEMPLATE_LOGIN_AS_GO = 'account/login-as-go.dtl'

my_logger = logging.getLogger('MH.Account')


def receiver_account_wissel(request, account):
    """ Met deze functie kan een geautoriseerd persoon inloggen op de site als een andere gebruiker.
            obj is een Account object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.
    """
    old_last_login = account.last_login
    old_otp_controle = account.otp_controle_gelukt_op

    # integratie met de authenticatie laag van Django
    logout(request)             # einde oude sessie (if any)
    login(request, account)     # maakt nieuwe sessie

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog met account %s' % (from_ip, repr(account.username)))

    for _, func, skip in account_plugins_login_gate:
        if not skip:
            http_resp = func(request, from_ip, account)
            if http_resp:
                # plugin has decided that the user may not login
                # and has generated/rendered an HttpResponse that we cannot handle here

                # integratie met de authenticatie laag van Django
                # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                logout(request)

                return http_resp
    # for

    # track het session_id in de log zodat we deze kunnen koppelen aan de webserver logs
    session_id = request.session.session_key
    my_logger.info('Account %s has SESSION %s' % (repr(account.username), repr(session_id)))

    if account.otp_is_actief:
        # fake de OTP passage
        otp_zet_controle_gelukt(request)
    else:
        otp_zet_controle_niet_gelukt(request)

    # herstel de last_login van de echte gebruiker
    account.last_login = old_last_login
    account.otp_controle_gelukt_op = old_otp_controle
    account.save(update_fields=['last_login', 'otp_controle_gelukt_op'])

    date_str = timezone.now().strftime('%Y-%m-%d')
    zet_sessionvar_if_changed(request, SESSIONVAR_ACCOUNT_LOGIN_AS_DATE, date_str)

    # zorg dat de session-cookie snel verloopt --> nergens voor nodig
    # login-as sessie is maar 1 dag bruikbaar
    # request.session.set_expiry(0)

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Inloggen (code)",
                       activiteit="Automatische inlog als gebruiker %s vanaf IP %s" % (repr(account.username),
                                                                                       repr(from_ip)))

    # zorg dat de rollen meteen beschikbaar zijn
    rol_bepaal_beschikbare_rollen(request, account)

    return reverse('Plein:plein')


set_tijdelijke_codes_receiver(RECEIVER_ACCOUNT_WISSEL, receiver_account_wissel)


class LoginAsZoekView(UserPassesTestMixin, ListView):

    """ Deze view laat Wissel van Rol toe naar een gekozen gebruiker
        zodat de website 'door de ogen van' deze gebruiker bekeken kan worden
    """

    # class variables shared by all instances
    template_name = TEMPLATE_LOGIN_AS_ZOEK
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = None
        self.zoekterm = ""

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # deze functie wordt gebruikt voordat de GET of de POST afgehandeld wordt (getest bewezen)
        account = get_account(self.request)
        if account.is_authenticated:
            return account.is_staff
        return False

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        self.form = form = ZoekAccountForm(self.request.GET)
        form.full_clean()  # vult cleaned_data

        try:
            zoekterm = form.cleaned_data['zoekterm']
            if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
                self.zoekterm = zoekterm
                qset = (Account
                        .objects
                        .exclude(is_staff=True)
                        .filter(Q(username__icontains=zoekterm) |           # dekt zoeken op bondsnummer
                                Q(unaccented_naam__icontains=zoekterm) |
                                Q(first_name__icontains=zoekterm) |         # dekt zoeken mét accenten
                                Q(last_name__icontains=zoekterm))           # dekt zoeken mét accenten
                        .order_by('username'))
                return qset[:50]
        except KeyError:
            # hier komen we als het form field bijvoorbeeld te lang was
            pass

        self.zoekterm = ""
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['url'] = reverse('Account:account-wissel')
        context['zoekterm'] = self.zoekterm
        context['form'] = self.form

        if context['object_list']:
            context['aantal_gevonden'] = context['object_list'].count()
        else:
            context['aantal_gevonden'] = 0

        context['kruimels'] = (
            (reverse('Functie:wissel-van-rol'), 'Wissel van rol'),
            (None, 'Account wissel'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Selecteer knop.
        """
        form = KiesAccountForm(request.POST)
        form.full_clean()  # vult cleaned_data
        account_pk = form.cleaned_data.get('selecteer')

        try:
            account = Account.objects.get(pk=account_pk)
        except Account.DoesNotExist:
            raise Http404('Account heeft geen e-mail')

        # prevent upgrade
        if account.is_staff:
            raise PermissionDenied()

        context = {'account': account}

        # schrijf de intentie in het logboek
        schrijf_in_logboek(account=self.request.user,
                           gebruikte_functie="Inloggen",
                           activiteit="Wissel naar account %s" % repr(account.username))

        # maak een tijdelijke URL aan waarmee de inlog gedaan kan worden
        url = maak_tijdelijke_code_accountwissel(account, naar_account=account.username)
        context['login_as_url'] = url

        context['kruimels'] = (
            (reverse('Functie:wissel-van-rol'), 'Wissel van rol'),
            (reverse('Account:account-wissel'), 'Account wissel'),
            (None, 'Activeer'),
        )

        return render(self.request, TEMPLATE_LOGIN_AS_GO, context)


# end of file
