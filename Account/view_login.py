# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
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
from Account.operations import account_email_bevestiging_ontvangen, account_check_gewijzigde_email
from Account.otp import otp_zet_control_niet_gelukt
from Account.plugin_manager import account_plugins_login_gate, account_plugins_post_login, account_add_plugin_login_gate
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_queue_email, mailer_obfuscate_email, render_email_template
from Overig.helpers import get_safe_from_ip
from TijdelijkeCodes.definities import RECEIVER_BEVESTIG_ACCOUNT_EMAIL
from TijdelijkeCodes.operations import set_tijdelijke_codes_receiver
from Plein.menu import menu_dynamics
from datetime import timedelta
import logging


TEMPLATE_LOGIN = 'account/login.dtl'
TEMPLATE_EMAIL_BEVESTIGD = 'account/email-bevestigd.dtl'
TEMPLATE_AANGEMAAKT = 'account/email_aangemaakt.dtl'
TEMPLATE_GEBLOKKEERD = 'account/login-geblokkeerd.dtl'
TEMPLATE_EMAIL_BEVESTIG_NIEUWE = 'account/email-bevestig-nieuwe.dtl'
TEMPLATE_EMAIL_BEVESTIG_HUIDIGE = 'account/email-bevestig-huidige.dtl'

EMAIL_TEMPLATE_BEVESTIG_TOEGANG_EMAIL = 'email_account/bevestig-toegang-email.dtl'

my_logger = logging.getLogger('NHBApps.Account')


def account_stuur_email_bevestig_nieuwe_email(mailadres, ack_url):
    """ Stuur een mail om toegang tot het (gewijzigde) e-mailadres te bevestigen """

    context = {
        'naam_site': settings.NAAM_SITE,
        'url': ack_url,
        'contact_email': settings.EMAIL_BONDSBUREAU
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_TOEGANG_EMAIL)

    mailer_queue_email(mailadres,
                       'Email adres bevestigen',
                       mail_body,
                       enforce_whitelist=False)


def account_check_nieuwe_email(request, from_ip, account):
    """ detecteer wissel van e-mail in CRM; stuur bevestig verzoek mail """

    # kijk of een nieuw e-mailadres bevestigd moet worden
    ack_url, mailadres = account_check_gewijzigde_email(account)
    if ack_url:
        # schrijf in het logboek
        schrijf_in_logboek(account=None,
                           gebruikte_functie="Inloggen",
                           activiteit="Bevestiging van nieuwe email gevraagd voor account %s" % repr(
                               account.username))

        account_stuur_email_bevestig_nieuwe_email(mailadres, ack_url)

        context = {'partial_email': mailer_obfuscate_email(mailadres)}
        menu_dynamics(request, context)
        return render(request, TEMPLATE_EMAIL_BEVESTIG_NIEUWE, context)

    # geen wijziging van e-mailadres - gewoon doorgaan
    return None


# skip_for_login_as=True om te voorkomen dat we een e-mail sturen door de login-as
account_add_plugin_login_gate(30, account_check_nieuwe_email, True)


def account_check_email_is_bevestigd(request, from_ip, account):
    """ voorkom login op een account totdat het e-mailadres bevestigd is """

    if not account.email_is_bevestigd:
        schrijf_in_logboek(account, 'Inloggen',
                           'Mislukte inlog vanaf IP %s voor account %s met onbevestigde email' % (
                               from_ip, repr(account.username)))

        my_logger.info('%s LOGIN Mislukte inlog voor account %s met onbevestigde email' % (
                               from_ip, repr(account.username)))

        # FUTURE: knop maken om na X uur een nieuwe mail te kunnen krijgen
        context = {'partial_email': mailer_obfuscate_email(account.nieuwe_email)}
        menu_dynamics(request, context)
        return render(request, TEMPLATE_EMAIL_BEVESTIG_HUIDIGE, context)

    # we wachten niet op bevestiging email - ga gewoon door
    return None


# skip_for_login_as=True om te voorkomen dat gaan blokkeren op een onbevestigde e-mail
account_add_plugin_login_gate(40, account_check_email_is_bevestigd, True)


def receive_bevestiging_account_email(request, account):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgd wordt
        om een email adres te bevestigen, zowel de eerste keer als wijziging van email.
            account is een Account object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden.
    """
    account_email_bevestiging_ontvangen(account)

    # schrijf in het logboek
    from_ip = get_safe_from_ip(request)

    msg = "Bevestigd vanaf IP %s voor account %s" % (from_ip, account.get_account_full_name())
    schrijf_in_logboek(account=account,
                       gebruikte_functie="Bevestig e-mail",
                       activiteit=msg)

    context = dict()
    if not request.user.is_authenticated:
        context['show_login'] = True

    context['verberg_login_knop'] = True

    menu_dynamics(request, context)
    return render(request, TEMPLATE_EMAIL_BEVESTIGD, context)


set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_ACCOUNT_EMAIL, receive_bevestiging_account_email)


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
                account = Account.objects.get(bevestigde_email__iexact=login_naam)   # iexact = case insensitive volledige match
            except Account.DoesNotExist:
                # email is ook niet bekend
                # LET OP! dit kan heel snel heel veel data worden! - voorkom storage overflow!!
                # my_logger.info('%s LOGIN Mislukte inlog voor onbekend inlog naam %s' % (from_ip, repr(login_naam)))
                # schrijf_in_logboek(None, 'Inloggen', 'Mislukte inlog vanaf IP %s: onbekende inlog naam %s' % (from_ip, repr(login_naam)))
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
                                           from_ip, repr(login_naam)))
                    my_logger.info(
                        '%s LOGIN Mislukte inlog voor geblokkeerd account %s' % (from_ip, repr(login_naam)))
                    context = {'account': account}
                    menu_dynamics(self.request, context)
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
        account2 = authenticate(username=account.username, password=wachtwoord)
        if not account2:
            # authenticatie is niet gelukt
            # reden kan zijn: verkeerd wachtwoord
            #  (of: is_active=False, maar: gebruiken we niet)

            # onthoudt precies wanneer dit was
            account.laatste_inlog_poging = timezone.now()
            schrijf_in_logboek(account, 'Inloggen',
                               'Mislukte inlog vanaf IP %s voor account %s' % (from_ip, repr(login_naam)))
            my_logger.info('%s LOGIN Mislukte inlog voor account %s' % (from_ip, repr(login_naam)))

            # onthoudt hoe vaak dit verkeerd gegaan is
            account.verkeerd_wachtwoord_teller += 1
            account.save(update_fields=['laatste_inlog_poging', 'verkeerd_wachtwoord_teller'])

            # bij te veel pogingen, blokkeer het account
            if account.verkeerd_wachtwoord_teller >= settings.AUTH_BAD_PASSWORD_LIMIT:
                account.is_geblokkeerd_tot = (timezone.now()
                                              + timedelta(minutes=settings.AUTH_BAD_PASSWORD_LOCKOUT_MINS))
                account.verkeerd_wachtwoord_teller = 0  # daarna weer volle mogelijkheden
                account.save(update_fields=['is_geblokkeerd_tot', 'verkeerd_wachtwoord_teller'])

                schrijf_in_logboek(account, 'Inlog geblokkeerd',
                                   'Account %s wordt geblokkeerd tot %s' % (
                                       repr(login_naam),
                                       account.is_geblokkeerd_tot.strftime('%Y-%m-%d %H:%M:%S')))

                context = {'account': account}
                menu_dynamics(self.request, context)
                httpresp = render(self.request, TEMPLATE_GEBLOKKEERD, context)
                return False, httpresp

            # wachtwoord klopt niet, doe opnieuw
            return False, None

        # wachtwoord is goed
        account = account2

        # kijk of er een reden is om gebruik van het account te weren
        for _, func, _ in account_plugins_login_gate:
            httpresp = func(self.request, from_ip, account)
            if httpresp:
                # plugin has decided that the user may not login
                # and has generated/rendered an HttpResponse

                # integratie met de authenticatie laag van Django
                # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
                logout(self.request)

                return False, httpresp
        # for

        # integratie met de authenticatie laag van Django
        login(self.request, account)

        my_logger.info('%s LOGIN op account %s' % (from_ip, repr(account.username)))

        if account.verkeerd_wachtwoord_teller > 0:
            account.verkeerd_wachtwoord_teller = 0
            account.save(update_fields=['verkeerd_wachtwoord_teller'])

        # aangemeld blijven checkbox
        if not form.cleaned_data.get('aangemeld_blijven', False):
            # gebruiker wil NIET aangemeld blijven
            # zorg dat de session-cookie snel verloopt
            self.request.session.set_expiry(0)

        # de OTP control is nog niet uitgevoerd
        otp_zet_control_niet_gelukt(self.request)

        return True, None

    def _get_redirect(self, form, account):
        # voer de automatische redirect uit, indien gevraagd
        next_url = form.cleaned_data.get('next')
        if next_url:
            # validation is gedaan in forms.py
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

            httpresp, account = self._zoek_account(form)
            if httpresp:
                # account is geblokkeerd
                return httpresp

            if account:
                # account bestaat
                login_success, httpresp = self._probeer_login(form, account)

                if login_success:
                    # login gelukt
                    url = self._get_redirect(form, account)
                    return HttpResponseRedirect(url)

                if httpresp:
                    # geknikkerd met foutmelding
                    return httpresp

            # gebruiker mag het nog een keer proberen
            if len(form.errors) == 0:
                form.add_error(None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

        # still here --> re-render with error message
        context = {
            'form': form,
            'verberg_login_knop': True,
        }

        if account and account.verkeerd_wachtwoord_teller > 0:
            context['show_wachtwoord_vergeten'] = True

        menu_dynamics(request, context)
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
                    pass
                else:
                    # is valide url
                    return HttpResponseRedirect(next_url)

            return HttpResponseRedirect(reverse('Plein:plein'))

        form = LoginForm(initial={'next': next_url})

        context = dict()
        context['form'] = form
        context['verberg_login_knop'] = True

        context['kruimels'] = (
            (None, 'Inloggen'),
        )

        menu_dynamics(request, context)
        return render(request, TEMPLATE_LOGIN, context)


# end of file
