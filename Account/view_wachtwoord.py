# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.urls import reverse
from Account.models import AccountEmail
from Account.operations import account_test_wachtwoord_sterkte
from Account.rechten import account_rechten_login_gelukt
from Account.view_login import account_plugins_login
from Logboek.models import schrijf_in_logboek
from Mailer.operations import render_email_template, mailer_queue_email, mailer_email_is_valide
from Overig.helpers import get_safe_from_ip
from Overig.tijdelijke_url import (set_tijdelijke_url_receiver,
                                   RECEIVER_WACHTWOORD_VERGETEN,
                                   maak_tijdelijke_url_wachtwoord_vergeten)
from Plein.menu import menu_dynamics
import logging


TEMPLATE_VERGETEN = 'account/wachtwoord-vergeten.dtl'
TEMPLATE_EMAIL = 'account/email_wachtwoord-vergeten.dtl'
TEMPLATE_NIEUW_WACHTWOORD = 'account/nieuw-wachtwoord.dtl'
EMAIL_TEMPLATE_WACHTWOORD_VERGETEN = 'email_account/wachtwoord-vergeten.dtl'

my_logger = logging.getLogger('NHBApps.Account')


def account_stuur_email_wachtwoord_vergeten(accountemail, **kwargs):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    context = {
        'url': maak_tijdelijke_url_wachtwoord_vergeten(accountemail, **kwargs),
        'naam_site': settings.NAAM_SITE,
        'contact_email': settings.EMAIL_BONDSBUREAU,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_WACHTWOORD_VERGETEN)

    mailer_queue_email(accountemail.bevestigde_email,
                       'Wachtwoord vergeten',
                       mail_body,
                       enforce_whitelist=False)


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

        context['kruimels'] = (
            (reverse('Account:login'), 'Inloggen'),
            (None, 'Wachtwoord vergeten')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):

        from_ip = get_safe_from_ip(request)
        account_email = None
        context = super().get_context_data(**kwargs)
        context['foutmelding'] = ''

        email = request.POST.get('email', '')[:150]   # afkappen voor extra veiligheid
        if not mailer_email_is_valide(email):
            context['foutmelding'] = 'Voer een valide e-mailadres in van een bestaand account'

        if not context['foutmelding']:
            username = request.POST.get('lid_nr', '')[:10]  # afkappen voor extra veiligheid

            # zoek een account met deze email
            try:
                account_email = (AccountEmail
                                 .objects
                                 .get(bevestigde_email__iexact=email,  # iexact = case insensitive volledige match
                                      account__username=username))

            except AccountEmail.DoesNotExist:
                # email is niet bekend en past niet bij de inlog naam
                context['foutmelding'] = 'Voer het e-mailadres en NHB nummer in van een bestaand account'
                # (niet te veel wijzer maken over de combi NHB nummer en e-mailadres)

        # we controleren hier niet of het account inactief is, dat doet login wel weer

        menu_dynamics(self.request, context)

        if not context['foutmelding'] and account_email is not None:
            # we hebben nu het account waar we een de e-mail voor moeten sturen

            schrijf_in_logboek(account=None,
                               gebruikte_functie="Wachtwoord",
                               activiteit="Stuur e-mail naar adres %s voor account %s, verzocht vanaf IP %s." % (
                                           repr(account_email.bevestigde_email),
                                           repr(account_email.account.get_account_full_name()),
                                           from_ip))

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

    for _, func, _ in account_plugins_login:
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
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn
        return self.request.user.is_authenticated

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            context['moet_oude_ww_weten'] = self.request.session['moet_oude_ww_weten']
        except KeyError:
            context['moet_oude_ww_weten'] = True

        account = self.request.user
        if account.sporter_set.count() > 0:      # FUTURE: ongewenste kennis over op Sporter.account
            context['kruimels'] = (
                (reverse('Sporter:profiel'), 'Mijn pagina'),
                (None, 'Wachtwoord wijzigen')
            )
        else:
            context['kruimels'] = (
                (None, 'Wachtwoord wijzigen'),
            )

        menu_dynamics(self.request, context)
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

            menu_dynamics(self.request, context)
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
