# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.urls import reverse
from Account.models import Account, get_account
from Account.operations.wachtwoord import account_test_wachtwoord_sterkte
from Account.operations.otp import otp_zet_controle_niet_gelukt
from Account.plugin_manager import account_plugins_login_gate, account_plugins_ww_vergeten
from Functie.rol import rol_eval_rechten_simpel
from Logboek.models import schrijf_in_logboek
from Mailer.operations import render_email_template, mailer_queue_email, mailer_email_is_valide
from Overig.helpers import get_safe_from_ip
from TijdelijkeCodes.definities import RECEIVER_WACHTWOORD_VERGETEN
from TijdelijkeCodes.operations import set_tijdelijke_codes_receiver, maak_tijdelijke_code_wachtwoord_vergeten
import logging


TEMPLATE_WW_VERGETEN = 'account/wachtwoord-vergeten.dtl'
TEMPLATE_WW_VERGETEN_EMAIL = 'account/wachtwoord-vergeten-email.dtl'
TEMPLATE_WW_WIJZIGEN = 'account/wachtwoord-wijzigen.dtl'

EMAIL_TEMPLATE_WACHTWOORD_VERGETEN = 'email_account/wachtwoord-vergeten.dtl'

my_logger = logging.getLogger('MH.Account')


def account_stuur_email_wachtwoord_vergeten(account, email, **kwargs):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    context = {
        'url': maak_tijdelijke_code_wachtwoord_vergeten(account, email=email, **kwargs),
        'naam_site': settings.NAAM_SITE,
        'contact_email': settings.EMAIL_BONDSBUREAU,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_WACHTWOORD_VERGETEN)

    mailer_queue_email(email,
                       'Wachtwoord vergeten',
                       mail_body,
                       enforce_whitelist=False)         # deze mails altijd doorlaten


class WachtwoordVergetenView(TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker een e-mailadres op
        kan geven waar een wachtwoord-reset url heen gestuurd wordt.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WW_VERGETEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['kruimels'] = (
            (reverse('Account:login'), 'Inloggen'),
            (None, 'Wachtwoord vergeten')
        )

        return context

    def post(self, request, *args, **kwargs):

        # FUTURE: is er iets af te leiden uit de timing? (e-mail bekend / niet bekend)?
        # FUTURE: rate limiter (op IP) - zie view_registreer_gast

        from_ip = get_safe_from_ip(request)
        context = super().get_context_data(**kwargs)
        context['foutmelding'] = ''

        email = request.POST.get('email', '')[:150]   # afkappen voor extra veiligheid
        email = str(email).lower()
        if not mailer_email_is_valide(email):       # vangt ook te korte / lege invoer af
            context['foutmelding'] = 'Voer een valide e-mailadres in van een bestaand account'

        account = None
        if not context['foutmelding']:
            username = request.POST.get('lid_nr', '')[:10]  # afkappen voor extra veiligheid

            # zoek een account met deze email
            try:
                account = Account.objects.get(username=username)
            except Account.DoesNotExist:
                # email is niet bekend en past niet bij de inlog naam
                context['foutmelding'] = 'Voer het e-mailadres en bondsnummer in van een bestaand account'
                # (niet te veel wijzer maken over de combi bondsnummer en e-mailadres)
            else:
                # loop de plugins af om een eventueel nieuw e-mailadres uit de CRM te krijgen
                for _, func in account_plugins_ww_vergeten:
                    func(request, from_ip, account)
                # for

                if account.bevestigde_email.lower() != email and account.nieuwe_email.lower() != email:
                    # geen match
                    context['foutmelding'] = 'Voer het e-mailadres en bondsnummer in van een bestaand account'
                    # (niet te veel wijzer maken over de combi bondsnummer en e-mailadres)

        if account and not context['foutmelding']:
            # success: stuur nu een e-mail naar het account

            schrijf_in_logboek(account=None,
                               gebruikte_functie="Wachtwoord",
                               activiteit="Stuur e-mail naar adres %s voor account %s, verzocht vanaf IP %s." % (
                                           repr(email),                 # kan bevestigde of nieuwe email zijn
                                           repr(account.get_account_full_name()),
                                           from_ip))

            account_stuur_email_wachtwoord_vergeten(account,
                                                    wachtwoord='vergeten',
                                                    email=email)        # kan bevestigde of nieuwe email zijn

            http_resp = render(request, TEMPLATE_WW_VERGETEN_EMAIL, context)
        else:
            # toon foutmelding
            http_resp = render(request, self.template_name, context)

        return http_resp


def receive_wachtwoord_vergeten(request, account):
    """ deze functie wordt vanuit een POST context aangeroepen als een tijdelijke url gevolgd wordt
        voor een vergeten wachtwoord.
            account is een Account object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.

        We loggen automatisch in op het account waar de link bij hoort
        en sturen dan door naar de wijzig-wachtwoord pagina
    """
    # integratie met de authenticatie laag van Django
    login(request, account)

    from_ip = get_safe_from_ip(request)
    my_logger.info('%s LOGIN automatische inlog voor wachtwoord-vergeten met account %s' % (
                        from_ip, repr(account.username)))

    # FUTURE: als WW vergeten via Account.nieuwe_email ging, dan kunnen we die als bevestigd markeren

    for _, func, skip in account_plugins_login_gate:
        if not skip:
            httpresp = func(request, from_ip, account)
            if httpresp:
                # plugin has decided that the user may not login
                # and has generated/rendered an HttpResponse that we cannot handle here
                return httpresp

    otp_zet_controle_niet_gelukt(request)

    # gebruiker mag NIET aangemeld blijven
    # zorg dat de session-cookie snel verloopt
    request.session.set_expiry(0)

    request.session['moet_oude_ww_weten'] = False

    # track het session_id in de log zodat we deze kunnen koppelen aan de webserver logs
    session_id = request.session.session_key
    my_logger.info('Account %s has SESSION %s' % (repr(account.username), repr(session_id)))

    # schrijf in het logboek
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Inloggen (code)",
                       activiteit="Automatische inlog op account %s vanaf IP %s" % (
                                        repr(account.get_account_full_name()), from_ip))

    # controleer of deze gebruiker rollen heeft en dus van rol mag wisselen
    rol_eval_rechten_simpel(request, account)

    return reverse('Account:nieuw-wachtwoord')


set_tijdelijke_codes_receiver(RECEIVER_WACHTWOORD_VERGETEN, receive_wachtwoord_vergeten)


class NieuwWachtwoordView(UserPassesTestMixin, TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WW_WIJZIGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn
        if self.request.user.is_authenticated:
            self.account = get_account(self.request)
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            context['moet_oude_ww_weten'] = self.request.session['moet_oude_ww_weten']
        except KeyError:
            context['moet_oude_ww_weten'] = True

        context['account'] = self.account

        context['kruimels'] = (
            (None, 'Wachtwoord wijzigen'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de OPSLAAN knop gebruikt wordt op het formulier
            om een nieuw wachtwoord op te geven.
        """
        context = super().get_context_data(**kwargs)

        huidige_ww = request.POST.get('huidige', '')[:50]   # afkappen voor extra veiligheid
        nieuw_ww = request.POST.get('nieuwe', '')[:50]      # afkappen voor extra veiligheid
        from_ip = get_safe_from_ip(self.request)

        try:
            moet_oude_ww_weten = self.request.session['moet_oude_ww_weten']
        except KeyError:
            moet_oude_ww_weten = True

        # controleer het nieuwe wachtwoord
        valid, errmsg = account_test_wachtwoord_sterkte(nieuw_ww, self.account.username)

        # controleer het huidige wachtwoord
        if moet_oude_ww_weten and valid:
            if not authenticate(username=self.account.username, password=huidige_ww):
                valid = False
                errmsg = "Huidige wachtwoord komt niet overeen"

                schrijf_in_logboek(account=self.account,
                                   gebruikte_functie="Wachtwoord",
                                   activiteit='Verkeerd huidige wachtwoord vanaf IP %s voor account %s' % (
                                                    from_ip, repr(self.account.username)))
                my_logger.info('%s LOGIN Verkeerd huidige wachtwoord voor account %s' % (
                                    from_ip, repr(self.account.username)))

        if not valid:
            context['foutmelding'] = errmsg
            context['toon_tip'] = True
            context['account'] = self.account

            try:
                context['moet_oude_ww_weten'] = self.request.session['moet_oude_ww_weten']
            except KeyError:
                context['moet_oude_ww_weten'] = True

            return render(request, self.template_name, context)

        # wijzigen van het wachtwoord zorgt er ook voor dat alle sessies van deze gebruiker vervallen
        # hierdoor blijft de gebruiker niet ingelogd op andere sessies
        self.account.set_password(nieuw_ww)      # does not save the account
        self.account.save()

        # houd de gebruiker ingelogd in deze sessie
        update_session_auth_hash(request, self.account)

        try:
            del request.session['moet_oude_ww_weten']
        except KeyError:
            pass

        # schrijf in het logboek
        schrijf_in_logboek(account=self.account,
                           gebruikte_functie="Wachtwoord",
                           activiteit="Nieuw wachtwoord voor account %s" % repr(self.account.get_account_full_name()))

        return HttpResponseRedirect(reverse('Plein:plein'))

# end of file
