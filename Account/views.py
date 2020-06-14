# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, resolve, Resolver404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView, ListView
from django.db.models import F, Q, Value
from django.db.models.functions import Concat
from django.utils import timezone
from .forms import LoginForm, ZoekAccountForm, KiesAccountForm
from .models import (Account, AccountEmail,
                     account_email_bevestiging_ontvangen, account_check_gewijzigde_email)
from .rechten import account_rechten_otp_controle_gelukt, account_rechten_login_gelukt
from Overig.tijdelijke_url import (set_tijdelijke_url_receiver,
                                   RECEIVER_BEVESTIG_ACCOUNT_EMAIL, RECEIVER_ACCOUNT_WISSEL,
                                   maak_tijdelijke_url_accountwissel, maak_tijdelijke_url_account_email)
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Mailer.models import mailer_queue_email, mailer_obfuscate_email
from datetime import timedelta
import logging


TEMPLATE_LOGIN = 'account/login.dtl'
TEMPLATE_VERGETEN = 'account/wachtwoord-vergeten.dtl'
TEMPLATE_UITLOGGEN = 'account/uitloggen.dtl'
TEMPLATE_BEVESTIGD = 'account/bevestigd.dtl'
TEMPLATE_AANGEMAAKT = 'account/aangemaakt.dtl'
TEMPLATE_ACTIVITEIT = 'account/activiteit.dtl'
TEMPLATE_GEBLOKKEERD = 'account/geblokkeerd.dtl'
TEMPLATE_NIEUWEEMAIL = 'account/nieuwe-email.dtl'
TEMPLATE_BEVESTIG_EMAIL = 'account/bevestig-email.dtl'
TEMPLATE_LOGINAS_ZOEK = 'account/login-as-zoek.dtl'
TEMPLATE_LOGINAS_GO = 'account/login-as-go.dtl'


my_logger = logging.getLogger('NHBApps.Account')


# login plugins zijn functies die kijken of een account in mag loggen
# dit kan gebruikt worden door andere applicaties om mee te beslissen in het login process
# zonder dat er een dependencies ontstaat vanuit Account naar die applicatie
account_plugins_login = list()

# declaratie van de login plugin functie:
#       def plugin(request, from_ip, account):
#           return None (mag inloggen) of HttpResponse object (mag niet inloggen)
# de plugin wordt aangeroepen na succesvolle authenticatie van username+password
# de functie render (uit django.shortcuts) produceert een HttpResponse object

# plugins are sorted on prio, lowest first
# the following blocks are defined
# 10-19: Account block 1 checks (is blocked)
# 20-29: other   block 1 checks (pass on new email from CRM)
# 30-39: Account block 2 checks (email not accepted check)
# 40-49: other   block 2 checks (leeftijdsklassen check)
def account_add_plugin_login(prio, func):
    account_plugins_login.append( (prio, func) )
    account_plugins_login.sort(key=lambda x: x[0])


def account_check_nieuwe_email(request, from_ip, account):
    """ detecteer wissel van email in CRM; stuur bevestig verzoek mail """

    # kijk of een nieuw emailadres bevestigd moet worden
    ack_url, mailadres = account_check_gewijzigde_email(account)
    if ack_url:
        # schrijf in het logboek
        schrijf_in_logboek(account=None,
                           gebruikte_functie="Inloggen",
                           activiteit="Bevestiging van nieuwe email gevraagd voor account %s" % repr(
                               account.username))

        text_body = ("Hallo!\n\n"
                     + "Dit is een verzoek vanuit de website van de NHB om toegang tot je email te bevestigen.\n"
                     + "Klik op onderstaande link om dit te bevestigen.\n\n"
                     + ack_url + "\n\n"
                     + "Als je dit verzoek onverwacht ontvangen hebt, neem dan contact met ons op via info@handboogsport.nl\n\n"
                     + "Veel plezier met de site!\n"
                     + "Het bondsburo\n")

        mailer_queue_email(mailadres, 'Email adres bevestigen', text_body)

        context = {'partial_email': mailer_obfuscate_email(mailadres)}
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_NIEUWEEMAIL, context)

    # geen wijziging van emailadres - gewoon doorgaan
    return None

account_add_plugin_login(30, account_check_nieuwe_email)


def account_check_geblokkeerd(request, from_ip, account):
    """ voorkom login op een account totdat het email adres bevestigd is """

    if account.accountemail_set.count() < 1:
        # onverwacht geen email bij dit account
        return None     # inloggen mag gewoon

    email = account.accountemail_set.all()[0]

    if not email.email_is_bevestigd:
        schrijf_in_logboek(account, 'Inloggen',
                           'Mislukte inlog vanaf IP %s voor account %s met onbevestigde email' % (
                               from_ip, repr(account.username)))

        my_logger.info('%s LOGIN Mislukte inlog voor account %s met onbevestigde email' % (
                               from_ip, repr(account.username)))

        # TODO: knop maken om na X uur een nieuwe mail te kunnen krijgen
        context = {'partial_email': mailer_obfuscate_email(email.nieuwe_email)}
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_BEVESTIG_EMAIL, context)

    # we wachten niet op bevestiging email - ga gewoon door
    return None

account_add_plugin_login(10, account_check_geblokkeerd)


class LoginView(TemplateView):
    """
        Deze view het startpunt om in te loggen
        Het inloggen zelf gebeurt met een POST omdat de invoervelden dan in
        de http body meegestuurd worden
    """

    # class variables shared by all instances
    form_class = LoginForm

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de LOG IN knop.
        """
        # https://stackoverflow.com/questions/5868786/what-method-should-i-use-for-a-login-authentication-request
        form = LoginForm(request.POST)
        if form.is_valid():
            from_ip = get_safe_from_ip(request)
            login_naam = form.cleaned_data.get('login_naam')
            wachtwoord = form.cleaned_data.get('wachtwoord')
            next = form.cleaned_data.get('next')

            # we doen hier alvast een stukje voorwerk dat normaal door het backend gedaan wordt
            # ondersteunen inlog met Account.username en Account.bevestigde_email

            # zoek een bestaand account
            account = None
            try:
                account = Account.objects.get(username=login_naam)
            except Account.DoesNotExist:
                # account met deze username bestaat niet
                # sta ook toe dat met het email adres ingelogd wordt
                try:
                    email = AccountEmail.objects.get(bevestigde_email=login_naam)
                except AccountEmail.DoesNotExist:
                    # email is ook niet bekend
                    # LET OP! dit kan heel snel heel veel data worden! - voorkom storage overflow!!
                    #my_logger.info('%s LOGIN Mislukte inlog voor onbekend inlog naam %s' % (from_ip, repr(login_naam)))
                    #schrijf_in_logboek(None, 'Inloggen', 'Mislukte inlog vanaf IP %s: onbekende inlog naam %s' % (from_ip, repr(login_naam)))
                    pass
                except AccountEmail.MultipleObjectsReturned:
                    # kan niet kiezen tussen verschillende accounts
                    # werkt dus niet als het email hergebruikt is voor meerdere accounts
                    form.add_error(None,
                                   'Inloggen met e-mail is niet mogelijk. Probeer het nog eens.')
                    account = None
                else:
                    # email gevonden
                    # pak het account erbij
                    account = email.account

            if account:
                # account bestaat wel

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
                        menu_dynamics(request, context, actief='inloggen')
                        return render(request, TEMPLATE_GEBLOKKEERD, context)

                # controleer het wachtwoord
                if authenticate(username=account.username, password=wachtwoord):
                    # wachtwoord is goed

                    # kijk of er een reden is om gebruik van het account te weren
                    for _, func in account_plugins_login:
                        httpresp = func(request, from_ip, account)
                        if httpresp:
                            # plugin has decided that the user may not login
                            # and has generated/rendered an HttpResponse
                            return httpresp

                    # integratie met de authenticatie laag van Django
                    login(request, account)

                    my_logger.info('%s LOGIN op account %s' % (from_ip, repr(account.username)))

                    if account.verkeerd_wachtwoord_teller > 0:
                        account.verkeerd_wachtwoord_teller = 0
                        account.save()

                    # Aangemeld blijven checkbox
                    if not form.cleaned_data.get('aangemeld_blijven', False):
                        # gebruiker wil NIET aangemeld blijven
                        # zorg dat de session-cookie snel verloopt
                        request.session.set_expiry(0)

                    account_rechten_login_gelukt(request)

                    # voer de automatische redirect uit, indien gevraagd
                    if next:
                        # reject niet bestaande urls
                        # resolve zoekt de view die de url af kan handelen
                        if next[-1] != '/':
                            next += '/'
                        try:
                            resolve(next)
                        except Resolver404:
                            pass
                        else:
                            # is valide url
                            return HttpResponseRedirect(next)

                    return HttpResponseRedirect(reverse('Plein:plein'))
                else:
                    # authenticatie is niet gelukt
                    # reden kan zijn: verkeerd wachtwoord of is_active=False

                    # onthoudt precies wanneer dit was
                    account.laatste_inlog_poging = timezone.now()
                    schrijf_in_logboek(account, 'Inloggen', 'Mislukte inlog vanaf IP %s voor account %s' % (from_ip, repr(login_naam)))
                    my_logger.info('%s LOGIN Mislukte inlog voor account %s' % (from_ip, repr(login_naam)))

                    # onthoudt hoe vaak dit verkeerd gegaan is
                    account.verkeerd_wachtwoord_teller += 1
                    account.save()

                    # bij te veel pogingen, blokkeer het account
                    if account.verkeerd_wachtwoord_teller >= settings.AUTH_BAD_PASSWORD_LIMIT:
                        account.is_geblokkeerd_tot = timezone.now() + timedelta(minutes=settings.AUTH_BAD_PASSWORD_LOCKOUT_MINS)
                        account.verkeerd_wachtwoord_teller = 0      # daarna weer volle mogelijkheden
                        account.save()
                        schrijf_in_logboek(account, 'Inlog geblokkeerd',
                                           'Account %s wordt geblokkeerd tot %s' % (repr(login_naam), account.is_geblokkeerd_tot.strftime('%Y-%m-%d %H:%M:%S')))
                        context = {'account': account}
                        menu_dynamics(request, context, actief='inloggen')
                        return render(request, TEMPLATE_GEBLOKKEERD, context)

            # gebruiker mag het nog een keer proberen
            if len(form.errors) == 0:
                form.add_error(None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_LOGIN, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
            we geven een lege form aan de template
        """
        next = request.GET.get('next', '')      # waar eventueel naartoe na de login?
        if request.user.is_authenticated:
            # gebruiker is al ingelogd --> stuur meteen door

            # voer de automatische redirect uit, indien gevraagd
            if next:
                # reject niet bestaande urls
                # resolve zoekt de view die de url af kan handelen
                if next[-1] != '/':
                    next += '/'
                try:
                    resolve(next)
                except Resolver404:
                    pass
                else:
                    # is valide url
                    return HttpResponseRedirect(next)

            return HttpResponseRedirect(reverse('Plein:plein'))

        form = LoginForm(initial={'next': next})
        context = {'form': form}
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_LOGIN, context)


class LogoutView(TemplateView):
    """
        Deze view zorgt voor het uitloggen met een POST
        Knoppen / links om uit te loggen moeten hier naartoe wijzen
    """

    # https://stackoverflow.com/questions/3521290/logout-get-or-post

    # class variables shared by all instances
    template_name = TEMPLATE_UITLOGGEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='uitloggen')
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is
            we zorgen voor het uitloggen en sturen door naar een andere pagina
        """
        from_ip = get_safe_from_ip(request)
        my_logger.info('%s LOGOUT voor account %s' % (from_ip, repr(request.user.username)))

        # integratie met de authenticatie laag van Django
        # dit wist ook de session data gekoppeld aan het cookie van de gebruiker
        logout(request)

        # redirect naar het plein
        return HttpResponseRedirect(reverse('Plein:plein'))


class WachtwoordVergetenView(TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_VERGETEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief="inloggen")
        return context


class AangemaaktView(TemplateView):
    """ Deze view geeft de laatste feedback naar de gebruiker
        nadat het account volledig aangemaakt is.
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # informatie doorgifte van de registratie view naar deze view
        # gaat via server-side session-variabelen
        try:
            login_naam = request.session['login_naam']
            partial_email = request.session['partial_email']
        except KeyError:
            # url moet direct gebruikt zijn
            return HttpResponseRedirect(reverse('Plein:plein'))

        # geef de data door aan de template
        context = {'login_naam': login_naam,
                   'partial_email': partial_email}
        menu_dynamics(request, context)

        return render(request, TEMPLATE_AANGEMAAKT, context)


class ActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de activiteiten van de gebruikers """

    # class variables shared by all instances
    template_name = TEMPLATE_ACTIVITEIT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        account = self.request.user
        if account.is_authenticated:
            if account.is_BB or account.is_staff:
                return True
        return False

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['nieuwe_accounts'] = AccountEmail.objects.all().order_by('-account__date_joined')[:50]
        context['recente_activiteit'] = AccountEmail.objects.filter(account__last_login__isnull=False).order_by('-account__last_login')[:50]
        context['inlog_pogingen'] = AccountEmail.objects.filter(account__laatste_inlog_poging__isnull=False).filter(account__last_login__lt=F('account__laatste_inlog_poging')).order_by('-account__laatste_inlog_poging')[:50]
        menu_dynamics(self.request, context, actief="hetplein")
        return context


class LoginAsZoekView(UserPassesTestMixin, ListView):

    """ Deze view laat Wissel van Rol toe naar een gekozen schutter
        zodat de website 'door de ogen van' deze schutter bekeken kan worden
    """

    template_name = TEMPLATE_LOGINAS_ZOEK

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # deze functie wordt gebruikt voordat de GET of de POST afgehandeld wordt (getest bewezen)
        account = self.request.user
        if account.is_authenticated:
            return account.is_staff
        return False

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> doe alsof dit niet bestaat """
        raise Resolver404()

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        self.form = ZoekAccountForm(self.request.GET)
        self.form.full_clean()  # vult cleaned_data

        zoekterm = self.form.cleaned_data['zoekterm']
        if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
            self.zoekterm = zoekterm
            qset = (Account
                    .objects
                    .exclude(is_staff=True)
                    .annotate(hele_naam=Concat('first_name', Value(' '), 'last_name'))
                    .filter(Q(username__icontains=zoekterm) |  # dekt nhb_nr
                            Q(first_name__icontains=zoekterm) |
                            Q(last_name__icontains=zoekterm) |
                            Q(hele_naam__icontains=zoekterm))
                    .order_by('username'))
            return qset[:50]

        self.zoekterm = ""
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['url'] = reverse('Account:account-wissel')
        context['zoekterm'] = self.zoekterm
        context['form'] = self.form

        menu_dynamics(self.request, context, actief='wissel-van-rol')
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Selecteer knop.
        """
        form = KiesAccountForm(request.POST)
        form.full_clean()  # vult cleaned_data
        account_pk = form.cleaned_data.get('selecteer')

        try:
            accountemail = AccountEmail.objects.get(account__pk=account_pk)
        except AccountEmail.DoesNotExist:
            raise Resolver404()

        # prevent upgrade
        if accountemail.account.is_staff:
            raise Resolver404()

        context = dict()
        context['account'] = accountemail.account

        # schrijf de intentie in het logboek
        schrijf_in_logboek(account=self.request.user,
                           gebruikte_functie="Inloggen",
                           activiteit="Wissel naar account %s" % repr(accountemail.account.username))

        # maak een tijdelijke URL aan waarmee de inlog gedaan kan worden
        url = maak_tijdelijke_url_accountwissel(accountemail, naar_account=accountemail.account.username)
        context['login_as_url'] = url

        menu_dynamics(self.request, context, actief='wissel-van-rol')
        return render(self.request, TEMPLATE_LOGINAS_GO, context)


def account_vraag_email_bevestiging(accountmail, **kwargs):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_url_account_email(accountmail, **kwargs)

    text_body = ("Hallo!\n\n"
                 + "Je hebt een account aangemaakt op de website van de NHB.\n"
                 + "Klik op onderstaande link om dit te bevestigen.\n\n"
                 + url + "\n\n"
                 + "Als jij dit niet was, neem dan contact met ons op via info@handboogsport.nl\n\n"
                 + "Veel plezier met de site!\n"
                 + "Het bondsburo\n")

    mailer_queue_email(accountmail.nieuwe_email, 'Aanmaken account voltooien', text_body)


def receive_bevestiging_accountemail(request, obj):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgd wordt
        om een email adres te bevestigen, zowel de eerste keer als wijziging van email.
            obj is een AccountEmail object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden.
    """
    account_email_bevestiging_ontvangen(obj)

    # schrijf in het logboek
    from_ip = get_safe_from_ip(request)
    account = obj.account

    msg = "Bevestigd vanaf IP %s voor account %s" % (from_ip, account.get_account_full_name())
    schrijf_in_logboek(account=account,
                       gebruikte_functie="Bevestig e-mail",
                       activiteit=msg)

    context = dict()
    if not request.user.is_authenticated:
        context['show_login'] = True
    menu_dynamics(request, context)
    return render(request, TEMPLATE_BEVESTIGD, context)


set_tijdelijke_url_receiver(RECEIVER_BEVESTIG_ACCOUNT_EMAIL, receive_bevestiging_accountemail)


def receiver_account_wissel(request, obj):
    """ Met deze functie kan een geauthoriseerd persoon tijdelijk inlogen op de site
        als een andere gebruiker.
            obj is een AccountEmail object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden.
    """
    account = obj.account

    old_last_login = account.last_login

    # integratie met de authenticatie laag van Django
    login(request, account)

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog als schutter %s' % (from_ip, repr(account.username)))

    for _, func in account_plugins_login:
        httpresp = func(request, from_ip, account)
        if httpresp:
            # plugin has decided that the user may not login
            # and has generated/rendered an HttpResponse that we cannot handle here
            return httpresp

    if account.otp_is_actief:
        # fake de OTP passage
        account_rechten_otp_controle_gelukt(request)
    else:
        account_rechten_login_gelukt(request)

    # herstel de last_login van de echte gebruiker
    account.last_login = old_last_login
    account.save(update_fields=['last_login'])

    # gebruiker mag NIET aangemeld blijven
    # zorg dat de session-cookie snel verloopt
    request.session.set_expiry(0)

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Inloggen",
                       activiteit="Automatische inlog als schutter %s vanaf IP %s" % (repr(account.username), from_ip))

    return reverse('Plein:plein')


set_tijdelijke_url_receiver(RECEIVER_ACCOUNT_WISSEL, receiver_account_wissel)


# TODO: een deel van de registratie code hier naartoe verplaatsen ivm alignment Aangemaakt en Email bevestigen


# end of file
