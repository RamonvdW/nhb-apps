# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, resolve, Resolver404
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.utils import timezone
from Account.forms import LoginForm
from Account.models import Account
from Account.operations.otp import otp_zet_control_niet_gelukt
from Account.plugin_manager import account_plugins_login_gate, account_plugins_post_login
from Functie.rol import rol_bepaal_beschikbare_rollen
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from datetime import timedelta
import logging


TEMPLATE_LOGIN = 'account/login.dtl'
TEMPLATE_GEBLOKKEERD = 'account/login-geblokkeerd-tot.dtl'

my_logger = logging.getLogger('MH.Account')


class LoginView(TemplateView):
    """
        Deze view het startpunt om in te loggen
        Het inloggen zelf gebeurt met een POST omdat de invoervelden dan in
        de http body meegestuurd worden
    """

    # class variables shared by all instances
    form_class = LoginForm

    def _zoek_account(self, form):
        # zoek een bestaand account

        # we doen hier alvast een stukje voorwerk dat normaal door het backend gedaan wordt
        # ondersteunen inlog met Account.username en Account.bevestigde_email

        from_ip = get_safe_from_ip(self.request)
        login_naam = form.cleaned_data.get('login_naam')

        account = None
        try:
            account = Account.objects.get(username=login_naam)
        except Account.DoesNotExist:
            # account met deze username bestaat niet
            # sta ook toe dat met het e-mailadres ingelogd wordt
            try:
                # iexact = case insensitive volledige match
                account = Account.objects.get(bevestigde_email__iexact=login_naam)
            except Account.DoesNotExist:
                # email is ook niet bekend
                # LET OP! dit kan heel snel heel veel data worden! - voorkom storage overflow!!
                # my_logger.info('%s LOGIN Mislukte inlog voor onbekend inlog naam %s' % (from_ip, repr(login_naam)))
                # schrijf_in_logboek(None, 'Inloggen',
                #       'Mislukte inlog vanaf IP %s: onbekende inlog naam %s' % (from_ip, repr(login_naam)))
                pass
            except Account.MultipleObjectsReturned:
                # kan niet kiezen tussen verschillende accounts
                # werkt dus niet als het email hergebruikt is voor meerdere accounts
                form.add_error(None,
                               'Inloggen met e-mail is niet mogelijk. Probeer het nog eens.')

        if account:
            # blokkeer inlog als het account geblokkeerd is door te veel wachtwoord pogingen
            now = timezone.now()
            if account.is_geblokkeerd_tot:
                if account.is_geblokkeerd_tot > now:
                    schrijf_in_logboek(account, 'Inloggen',
                                       'Mislukte inlog vanaf IP %s voor geblokkeerd account %s' % (
                                           repr(from_ip), repr(account.username)))
                    my_logger.info(
                        '%s LOGIN Mislukte inlog voor geblokkeerd account %s' % (from_ip, repr(account.username)))
                    context = {'account': account}
                    httpresp = render(self.request, TEMPLATE_GEBLOKKEERD, context)
                    return httpresp, None

        return None, account

    def _probeer_login(self, form, account):
        """ Kijk of het wachtwoord goed is en het account niet geblokkeerd is

            Returns:
                Login success: True ro False
                HttpResponse: pre-rendered page, or None
        """

        from_ip = get_safe_from_ip(self.request)
        login_naam = form.cleaned_data.get('login_naam')
        wachtwoord = form.cleaned_data.get('wachtwoord')

        # controleer het wachtwoord
        # hiervoor moeten we volledige credentials aanleveren (username + password)
        # in geval van inlog met e-mailadres gebruiken we hier de username
        account2 = authenticate(username=account.username, password=wachtwoord)
        if not account2:
            # authenticatie is niet gelukt
            # reden kan zijn: verkeerd wachtwoord
            #  (of: is_active=False, maar: gebruiken we niet)

            # onthoudt precies wanneer dit was
            account.laatste_inlog_poging = timezone.now()
            schrijf_in_logboek(account, 'Inloggen',
                               'Mislukte inlog vanaf IP %s voor account %s' % (repr(from_ip), repr(login_naam)))
            my_logger.info('%s LOGIN Mislukte inlog voor account %s' % (from_ip, repr(login_naam)))

            # onthoudt hoe vaak dit verkeerd gegaan is
            account.verkeerd_wachtwoord_teller += 1
            account.save(update_fields=['laatste_inlog_poging', 'verkeerd_wachtwoord_teller'])

            # bij te veel pogingen, blokkeer het account
            if account.verkeerd_wachtwoord_teller >= settings.AUTH_BAD_PASSWORD_LIMIT:
                blokkeer_tot = timezone.now() + timedelta(minutes=settings.AUTH_BAD_PASSWORD_LOCKOUT_MINS)
                account.is_geblokkeerd_tot = blokkeer_tot
                account.verkeerd_wachtwoord_teller = 0      # na blokkade weer volle mogelijkheden
                account.save(update_fields=['is_geblokkeerd_tot', 'verkeerd_wachtwoord_teller'])

                schrijf_in_logboek(account, 'Inlog geblokkeerd',
                                   'Account %s wordt geblokkeerd tot %s' % (repr(account.username),
                                                                            blokkeer_tot.strftime('%Y-%m-%d %H:%M:%S')))

                context = {'account': account}
                http_resp = render(self.request, TEMPLATE_GEBLOKKEERD, context)
                return False, http_resp

            # wachtwoord klopt niet, doe opnieuw
            return False, None

        # wachtwoord is goed
        account = account2

        # kijk of er een reden is om gebruik van het account te weren
        for _, func, _ in account_plugins_login_gate:
            http_resp = func(self.request, from_ip, account)
            if http_resp:
                # plugin has decided that the user may not login
                # and has generated/rendered an HttpResponse

                # integratie met de authenticatie laag van Django
                # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                logout(self.request)

                return False, http_resp
        # for

        # integratie met de authenticatie laag van Django
        login(self.request, account)

        my_logger.info('%s LOGIN op account %s (met %s)' % (
                        from_ip,
                        repr(account.username),
                        'e-mailadres' if '@' in login_naam else 'lidnummer'))

        if account.verkeerd_wachtwoord_teller > 0:
            account.verkeerd_wachtwoord_teller = 0
            account.save(update_fields=['verkeerd_wachtwoord_teller'])

        # aangemeld blijven checkbox
        if not form.cleaned_data.get('aangemeld_blijven', False):
            # gebruiker wil NIET aangemeld blijven
            # zorg dat de session-cookie snel verloopt
            self.request.session.set_expiry(0)

        # de OTP controle is nog niet uitgevoerd
        otp_zet_control_niet_gelukt(self.request)
        rol_bepaal_beschikbare_rollen(self.request, account)

        return True, None

    def _get_redirect(self, form, account):
        # voer de automatische redirect uit, indien gevraagd
        next_url = form.cleaned_data.get('next_url')
        if next_url:
            if next_url[-1] != '/':
                next_url += '/'
            try:
                resolve(next_url)
            except Resolver404:
                # niet goed --> dan fallback naar Plein
                next_url = ''

        if next_url:
            return next_url

        # roep de redirect plugins aan
        for _, func in account_plugins_post_login:
            url = func(self.request, account)
            if url:
                return url
        # for

        # default: ga naar het Plein
        url = reverse('Plein:plein')
        return url

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de LOG IN knop.
        """
        # https://stackoverflow.com/questions/5868786/what-method-should-i-use-for-a-login-authentication-request
        form = LoginForm(request.POST)
        account = None

        if form.is_valid():
            http_resp, account = self._zoek_account(form)
            if http_resp:
                # account is geblokkeerd
                return http_resp

            if account:
                # account bestaat
                login_success, http_resp = self._probeer_login(form, account)

                if login_success:
                    # login gelukt

                    # track het session_id in de log zodat we deze kunnen koppelen aan de webserver logs
                    session_id = request.session.session_key
                    my_logger.info('Account %s has SESSION %s' % (repr(account.username), repr(session_id)))

                    url = self._get_redirect(form, account)
                    return HttpResponseRedirect(url)

                if http_resp:
                    # eruit geknikkerd met foutmelding
                    return http_resp

            # gebruiker mag het nog een keer proberen
            if len(form.errors) == 0:
                form.add_error(None,
                               'de combinatie van inlog naam en wachtwoord wordt niet herkend. Probeer het nog eens.')

        # still here --> re-render with error message
        context = {
            'form': form,
            'verberg_login_knop': True,
        }

        if account and account.verkeerd_wachtwoord_teller > 0:
            context['show_wachtwoord_vergeten'] = True

        return render(request, TEMPLATE_LOGIN, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
            we geven een lege form aan de template
        """
        next_url = request.GET.get('next', '')      # waar eventueel naartoe na de login?
        if request.user.is_authenticated:
            # gebruiker is al ingelogd --> stuur meteen door

            # voer de automatische redirect uit, indien gevraagd
            if next_url:
                # reject niet bestaande urls
                # resolve zoekt de view die de url af kan handelen
                if next_url[-1] != '/':
                    next_url += '/'
                try:
                    resolve(next_url)
                except Resolver404:
                    # niet gevonden
                    pass
                else:
                    # is valide url
                    return HttpResponseRedirect(next_url)

            return HttpResponseRedirect(reverse('Plein:plein'))

        form = LoginForm(initial={'next_url': next_url})

        context = dict()
        context['form'] = form
        context['verberg_login_knop'] = True
        if next_url:
            context['canonical'] = reverse('Account:login')

        context['kruimels'] = (
            (None, 'Inloggen'),
        )

        return render(request, TEMPLATE_LOGIN, context)


# end of file
