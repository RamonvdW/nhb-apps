# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone
from django.conf import settings
from .forms import LoginForm, RegistreerForm, OTPControleForm
from .models import AccountCreateError, AccountCreateNhbGeenEmail, Account,\
                    account_create_nhb, account_email_is_bevestigd,\
                    account_needs_otp, account_prep_for_otp, account_controleer_otp_code,\
                    account_zet_sessionvars_na_login, account_zet_sessionvars_na_otp_controle
from .leeftijdsklassen import leeftijdsklassen_zet_sessionvars_na_login
from .rol import rol_zet_sessionvars_na_login, rol_zet_sessionvars_na_otp_controle
from .qrcode import qrcode_get
from Overig.tijdelijke_url import set_tijdelijke_url_receiver, RECEIVER_ACCOUNTEMAIL
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from datetime import timedelta


TEMPLATE_LOGIN = 'account/login.dtl'
TEMPLATE_UITLOGGEN = 'account/uitloggen.dtl'
TEMPLATE_REGISTREER = 'account/registreer.dtl'
TEMPLATE_AANGEMAAKT = 'account/aangemaakt.dtl'
TEMPLATE_BEVESTIGD = 'account/bevestigd.dtl'
TEMPLATE_GEBLOKKEERD = 'account/geblokkeerd.dtl'
TEMPLATE_VERGETEN = 'account/wachtwoord-vergeten.dtl'
TEMPLATE_OTPCONTROLE = 'account/otp-controle.dtl'
TEMPLATE_OTPKOPPELEN = 'account/otp-koppelen.dtl'
TEMPLATE_OTPGEKOPPELD = 'account/otp-koppelen-gelukt.dtl'


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
            from_ip = request.META['REMOTE_ADDR']
            login_naam = form.cleaned_data.get("login_naam")
            wachtwoord = form.cleaned_data.get("wachtwoord")

            # kijk of het account bestaat en geblokkeerd is
            try:
                account = Account.objects.get(username=login_naam)
            except Account.DoesNotExist:
                # account bestaat niet
                # schrijf de mislukte inlogpoging in het logboek
                schrijf_in_logboek(None, 'Inloggen', 'Mislukte inlog vanaf IP %s: onbekend account %s' % (repr(from_ip), repr(login_naam)))
            else:
                # account bestaat wel
                # kijk of het geblokkeerd is
                now = timezone.now()
                if account.is_geblokkeerd_tot:
                    if account.is_geblokkeerd_tot > now:
                        schrijf_in_logboek(account, 'Inloggen',
                                           'Mislukte inlog vanaf IP %s voor geblokkeerd account %s' % (repr(from_ip), repr(login_naam)))
                        context = {'account': account}
                        menu_dynamics(request, context, actief='inloggen')
                        return render(request, TEMPLATE_GEBLOKKEERD, context)

                # niet geblokkeerd
                account2 = authenticate(username=login_naam, password=wachtwoord)
                if account2:
                    # authenticatie is gelukt
                    # integratie met de authenticatie laag van Django
                    login(request, account2)
                    account_zet_sessionvars_na_login(request)
                    rol_zet_sessionvars_na_login(account2, request)
                    leeftijdsklassen_zet_sessionvars_na_login(account2, request)

                    if account2.verkeerd_wachtwoord_teller > 0:
                        account2.verkeerd_wachtwoord_teller = 0
                        account2.save()

                    # meteen de OTP verificatie laten doen als dit account het nodig heeft
                    # als de gebruiker dit over slaat, dan komt het bij elke view die het nodig heeft automatisch terug
                    #if account_needs_otp(account2):
                    #    return HttpResponseRedirect(reverse('Account:otp-controle'))

                    return HttpResponseRedirect(reverse('Plein:plein'))
                else:
                    # authenticatie is niet gelukt
                    # reden kan zijn: verkeerd wachtwoord of is_active=False

                    # onthoudt precies wanneer dit was
                    account.laatste_inlog_poging = timezone.now()
                    schrijf_in_logboek(account, 'Inloggen', 'Mislukte inlog vanaf IP %s voor account %s' % (repr(from_ip), repr(login_naam)))

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
            form.add_error(None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_LOGIN, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
            we geven een lege form aan de template
        """
        form = LoginForm()
        context = {'form': form}
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_LOGIN, context)


class LogoutView(TemplateView):
    """
        Deze view zorgt voor het uitloggen met een POST
        Knoppen / links om uit te loggen moeten hier naartoe wijzen
    """

    # https://stackoverflow.com/questions/3521290/logout-get-or-post
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

        # integratie met de authenticatie laag van Django
        # TODO: wist dit ook de session?
        logout(request)

        # redirect naar het plein
        return HttpResponseRedirect(reverse('Plein:plein'))


class WachtwoordVergetenView(TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    template_name = TEMPLATE_VERGETEN

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief="inloggen")
        return context


def obfuscate_email(email):
    """ Helper functie om een email adres te maskeren
        voorbeeld: nhb.ramonvdw@gmail.com --> nh####w@gmail.com
    """
    try:
        user, domein = email.rsplit("@", 1)
    except ValueError:
        return email
    voor = 2
    achter = 1
    if len(user) <= 4:
        voor = 1
        achter = 1
        if len(user) <= 2:
            achter = 0
    hekjes = (len(user) - voor - achter)*'#'
    new_email = user[0:voor] + hekjes
    if achter > 0:
        new_email += user[-achter:]
    new_email = new_email + '@' + domein
    return new_email


class RegistreerNhbNummerView(TemplateView):
    """
        Deze view wordt gebruikt om het NHB nummer in te voeren voor een nieuw account.
    """

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        form = RegistreerForm(request.POST)
        if form.is_valid():
            nhb_nummer = form.cleaned_data.get('nhb_nummer')
            email = form.cleaned_data.get('email')
            nieuw_wachtwoord = form.cleaned_data.get('nieuw_wachtwoord')
            from_ip = request.META['REMOTE_ADDR']
            error = False
            try:
                ack_url = account_create_nhb(nhb_nummer, email, nieuw_wachtwoord)
            except AccountCreateNhbGeenEmail:
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit='NHB lid %s heeft geen email adres.' % nhb_nummer)

                form.add_error(None, 'Geen email adres bekend. Neem contact op met de secretaris van je vereniging.')
                # TODO: redirect naar een pagina met een uitgebreider duidelijk bericht
            except AccountCreateError as exc:
                form.add_error(None, str(exc))

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Mislukt voor nhb nummer %s vanaf IP %s: %s" % (repr(nhb_nummer), repr(from_ip), str(exc)))
            else:
                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Account aangemaakt voor NHB nummer %s vanaf IP %s" % (repr(nhb_nummer), repr(from_ip)))

                # TODO: send email
                request.session['login_naam'] = nhb_nummer
                request.session['partial_email'] = obfuscate_email(email)
                request.session['TEMP_ACK_URL'] = ack_url
                return HttpResponseRedirect(reverse('Account:aangemaakt'))

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_REGISTREER, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # GET operation --> create empty form
        form = RegistreerForm()
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_REGISTREER, context)


class BevestigdView(TemplateView):
    """
        Deze view wordt gebruikt om een bericht te tonen als de gebruiker de link
        in de e-mail gevolgd heeft.
        Zie ook receive_bevestiging_accountemail
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is """
        context = dict()
        menu_dynamics(request, context)
        return render(request, TEMPLATE_BEVESTIGD, context)


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
            temp_ack_url = request.session['TEMP_ACK_URL']
        except KeyError:
            # url moet direct gebruikt zijn
            return HttpResponseRedirect(reverse('Plein:plein'))

        # geef de data door aan de template
        context = {'login_naam': login_naam,
                   'partial_email': partial_email,
                   'temp_ack_url': temp_ack_url}
        menu_dynamics(request, context)

        return render(request, TEMPLATE_AANGEMAAKT, context)


class OTPControleView(TemplateView):
    """ Met deze view kan de OTP controle doorlopen worden
        Na deze controle is de gebruiker authenticated + verified
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus stuur terug naar af
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = OTPControleForm()
        context = {'form': form}
        menu_dynamics(request, context)
        return render(request, TEMPLATE_OTPCONTROLE, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """
        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            from_ip = request.META['REMOTE_ADDR']
            error = False
            account = request.user
            if account_controleer_otp_code(account, otp_code):
                # controle is gelukt
                account_zet_sessionvars_na_otp_controle(request)
                rol_zet_sessionvars_na_otp_controle(account, request)
                return HttpResponseRedirect(reverse('Plein:plein'))
            else:
                # controle is mislukt - schrijf dit in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="OTP controle",
                                   activiteit='Gebruiker %s OTP controle mislukt vanaf IP %s' % (repr(account.username), repr(from_ip)))

                form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
                # TODO: blokkeer na X pogingen

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTPCONTROLE, context)


class OTPKoppelenView(TemplateView):
    """ Met deze view kan de OTP koppeling tot stand gebracht worden
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus zou hier niet moeten komen
            return HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user

        if not account_needs_otp(account):
            # gebruiker heeft geen OTP nodig
            return HttpResponseRedirect(reverse('Plein:plein'))

        if account.otp_is_actief:
            # gebruiker is al gekoppeld, dus niet zomaar toestaan om een ander apparaat ook te koppelen!!
            return HttpResponseRedirect(reverse('Plein:plein'))

        # haal de QR code op (en alles wat daar voor nodig is)
        account_prep_for_otp(account)
        qrcode = qrcode_get(account)

        tmp = account.otp_code.lower()
        secret = " ".join([tmp[i:i+4] for i in range(0, 16, 4)])

        form = OTPControleForm()
        context = {'form': form,
                   'qrcode': qrcode,
                   'otp_secret': secret }
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTPKOPPELEN, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus stuur terug naar af
            return HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user

        if account.otp_is_actief:
            # gebruiker is al gekoppeld, dus niet zomaar toestaan om een ander apparaat ook te koppelen!!
            return HttpResponseRedirect(reverse('Plein:plein'))

        if not account_needs_otp(account):
            # gebruiker heeft geen OTP nodig
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            from_ip = request.META['REMOTE_ADDR']
            error = False
            if account_controleer_otp_code(account, otp_code):
                # controle is gelukt
                account.otp_is_actief = True
                account.save()
                account_zet_sessionvars_na_otp_controle(request)
                rol_zet_sessionvars_na_otp_controle(account, request)
                # geef de succes pagina
                context = dict()
                menu_dynamics(request, context, actief="inloggen")
                return render(request, TEMPLATE_OTPGEKOPPELD, context)
            else:
                # controle is mislukt - schrijf dit in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="OTP controle",
                                   activiteit='Gebruiker %s OTP koppeling controle mislukt vanaf IP %s' % (repr(account.username), repr(from_ip)))

                form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
                # TODO: blokkeer na X pogingen

        # still here --> re-render with error message
        qrcode = qrcode_get(account)
        tmp = account.otp_code.lower()
        secret = " ".join([tmp[i:i+4] for i in range(0, 16, 4)])
        context = {'form': form,
                   'qrcode': qrcode,
                   'otp_secret': secret }
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTPKOPPELEN, context)


def receive_bevestiging_accountemail(request, obj):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgt wordt
        om een email adres te bevestigen.
            obj is een AccountEmail object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden.
    """
    account_email_is_bevestigd(obj)

    # schrijf in het logboek
    from_ip = request.META['REMOTE_ADDR']
    msg = "Bevestigd vanaf IP " + repr(from_ip)

    account = obj.account
    msg += " voor account " + repr(account.username)
    if account.nhblid:
        msg += " (NHB lid met nummer %s)" % account.nhblid.nhb_nr
    schrijf_in_logboek(account=account,
                       gebruikte_functie="Bevestig e-mail",
                       activiteit=msg)

    # TODO: implementeer verdere reactie.
    # TODO: Iets opslaan in de sessie voor de pagina waar we naar redirecten?
    request.session['XXX'] = 123
    return reverse('Account:bevestigd')


set_tijdelijke_url_receiver(RECEIVER_ACCOUNTEMAIL, receive_bevestiging_accountemail)

# end of file
