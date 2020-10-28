# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import AccountEmail, account_test_wachtwoord_sterkte
from .rechten import account_rechten_login_gelukt
from .view_login import account_plugins_login
from Overig.tijdelijke_url import (set_tijdelijke_url_receiver,
                                   RECEIVER_WACHTWOORD_VERGETEN,
                                   maak_tijdelijke_url_wachtwoord_vergeten)
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Mailer.models import mailer_queue_email, mailer_email_is_valide
import logging


TEMPLATE_VERGETEN = 'account/wachtwoord-vergeten.dtl'
TEMPLATE_EMAIL = 'account/email_wachtwoord-vergeten.dtl'
TEMPLATE_NIEUW_WACHTWOORD = 'account/nieuw-wachtwoord.dtl'

my_logger = logging.getLogger('NHBApps.Account')


def account_stuur_email_wachtwoord_vergeten(accountemail, **kwargs):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_url_wachtwoord_vergeten(accountemail, **kwargs)

    text_body = ("Hallo!\n\n"
                 + "Je hebt aangegeven je wachtwoord vergeten te zijn voor de website van de NHB.\n"
                 + "Klik op onderstaande link om een nieuw wachtwoord in te stellen.\n\n"
                 + url + "\n\n"
                 + "Als jij dit niet was, neem dan contact met ons op via info@handboogsport.nl\n\n"
                 + "Veel plezier met de site!\n"
                 + "Het bondsburo\n")

    mailer_queue_email(accountemail.bevestigde_email, 'Wachtwoord vergeten', text_body)


class WachtwoordVergetenView(TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker een e-mailadres op
        kan geven waar een wachtwoord-reset url heen gestuurd wordt.

    """

    # class variables shared by all instances
    template_name = TEMPLATE_VERGETEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief="inloggen")
        return context

    def post(self, request, *args, **kwargs):

        from_ip = get_safe_from_ip(request)
        context = super().get_context_data(**kwargs)
        context['foutmelding'] = ''

        email = request.POST.get('email', '')[:150]   # afkappen voor extra veiligheid
        if not mailer_email_is_valide(email):
            context['foutmelding'] = 'Voer het e-mailadres in van een bestaand account'

        if not context['foutmelding']:
            # zoek een account met deze email
            try:
                account_email = (AccountEmail
                                 .objects
                                 .get(bevestigde_email__iexact=email))  # iexact = case insensitive volledige match

            except AccountEmail.DoesNotExist:
                # email is ook niet bekend
                context['foutmelding'] = 'Voer het e-mailadres in van een bestaand account'

            except AccountEmail.MultipleObjectsReturned:
                # kan niet kiezen tussen verschillende accounts
                # werkt dus niet als het email hergebruikt is voor meerdere accounts
                context['foutmelding'] = 'Er is een probleem met dit e-mailadres. Neem contact op met het bondsburo!'

                # schrijf de intentie in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Wachtwoord",
                                   activiteit="E-mail adres %s wordt gebruikt voor meer dan een account. Dit wordt niet ondersteund." % repr(email))

        # we controleren hier niet of het account inactief is, dat doet login wel weer

        menu_dynamics(self.request, context, actief="inloggen")

        if not context['foutmelding']:
            # we hebben nu het account waar we een de e-mail voor moeten sturen

            schrijf_in_logboek(account=None,
                               gebruikte_functie="Wachtwoord",
                               activiteit="Stuur e-mail naar adres %s voor account %s, verzocht vanaf IP %s." % (
                                   repr(account_email.bevestigde_email), repr(account_email.account.get_account_full_name()), from_ip))

            account_stuur_email_wachtwoord_vergeten(account_email,
                                                    wachtwoord='vergeten',
                                                    email=account_email.bevestigde_email)
            httpresp = render(request, TEMPLATE_EMAIL, context)
        else:
            httpresp = render(request, self.template_name, context)

        return httpresp


def receive_wachtwoord_vergeten(request, obj):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgd wordt
        voor een vergeten wachtwoord.
            obj is een AccountEmail object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden.

        We loggen automatisch in op het account waar de link bij hoort
        en sturen dan door naar de wijzig-wachtwoord pagina
    """
    account = obj.account

    # integratie met de authenticatie laag van Django
    login(request, account)

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog voor wachtwoord-vergeten met account %s' % (from_ip, repr(account.username)))

    for _, func in account_plugins_login:
        httpresp = func(request, from_ip, account)
        if httpresp:
            # plugin has decided that the user may not login
            # and has generated/rendered an HttpResponse that we cannot handle here
            return httpresp

    account_rechten_login_gelukt(request)

    # gebruiker mag NIET aangemeld blijven
    # zorg dat de session-cookie snel verloopt
    request.session.set_expiry(0)

    request.session['moet_oude_ww_weten'] = False

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Wachtwoord",
                       activiteit="Automatische inlog op account %s vanaf IP %s" % (repr(account.get_account_full_name()), from_ip))

    return reverse('Account:nieuw-wachtwoord')


set_tijdelijke_url_receiver(RECEIVER_WACHTWOORD_VERGETEN, receive_wachtwoord_vergeten)


class NieuwWachtwoordView(UserPassesTestMixin, TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_NIEUW_WACHTWOORD

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            context['moet_oude_ww_weten'] = self.request.session['moet_oude_ww_weten']
        except KeyError:
            context['moet_oude_ww_weten'] = True

        account = self.request.user
        if account.nhblid_set.count() > 0:      # TODO: ongewenste kennis over op NhbLid.account
            menu_dynamics(self.request, context, actief="schutter")
        else:
            menu_dynamics(self.request, context, actief="hetplein")
        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de OPSLAAN knop gebruikt wordt op het formulier
            om een nieuw wachtwoord op te geven.
        """
        context = super().get_context_data(**kwargs)

        account = request.user
        huidige_ww = request.POST.get('huidige', '')[:50]   # afkappen voor extra veiligheid
        nieuw_ww = request.POST.get('nieuwe', '')[:50]      # afkappen voor extra veiligheid
        from_ip = get_safe_from_ip(self.request)

        try:
            moet_oude_ww_weten = self.request.session['moet_oude_ww_weten']
        except KeyError:
            moet_oude_ww_weten = True

        # controleer het nieuwe wachtwoord
        valid, errmsg = account_test_wachtwoord_sterkte(nieuw_ww, account.username)

        # controleer het huidige wachtwoord
        if moet_oude_ww_weten and valid:
            if not authenticate(username=account.username, password=huidige_ww):
                valid = False
                errmsg = "Huidige wachtwoord komt niet overeen"

                schrijf_in_logboek(account=account,
                                   gebruikte_functie="Wachtwoord",
                                   activiteit='Verkeerd huidige wachtwoord vanaf IP %s voor account %s' % (from_ip, repr(account.username)))
                my_logger.info('%s LOGIN Verkeerd huidige wachtwoord voor account %s' % (from_ip, repr(account.username)))

        if not valid:
            context['foutmelding'] = errmsg

            try:
                context['moet_oude_ww_weten'] = self.request.session['moet_oude_ww_weten']
            except KeyError:
                context['moet_oude_ww_weten'] = True

            if account.nhblid_set.count() > 0:  # TODO: ongewenste kennis over NhbLid.account
                menu_dynamics(self.request, context, actief="schutter")
            else:
                menu_dynamics(self.request, context, actief="hetplein")
            return render(request, self.template_name, context)

        # wijzigen van het wachtwoord zorgt er ook voor dat alle sessies van deze gebruiker vervallen
        # hierdoor blijft de gebruiker niet ingelogd op andere sessies
        account.set_password(nieuw_ww)
        account.save()

        # houd de gebruiker ingelogd in deze sessie
        update_session_auth_hash(request, account)

        try:
            del request.session['moet_oude_ww_weten']
        except KeyError:
            pass

        # schrijf in het logboek
        schrijf_in_logboek(account=account,
                           gebruikte_functie="Wachtwoord",
                           activiteit="Nieuw wachtwoord voor account %s" % repr(account.get_account_full_name()))

        return HttpResponseRedirect(reverse('Plein:plein'))

# end of file
