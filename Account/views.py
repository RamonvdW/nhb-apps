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
from .forms import LoginForm, RegistreerForm
from .models import account_create_nhb, account_email_is_bevestigd, AccountCreateError
from Overig.tijdelijke_url import set_tijdelijke_url_receiver, RECEIVER_ACCOUNTEMAIL
from Plein.menu import menu_dynamics


TEMPLATE_LOGIN = 'account/login.dtl'
TEMPLATE_UITGELOGD = 'account/uitgelogd.dtl'
TEMPLATE_REGISTREER = 'account/registreer.dtl'
TEMPLATE_AANGEMAAKT = 'account/aangemaakt.dtl'
TEMPLATE_BEVESTIGD = 'account/bevestigd.dtl'
TEMPLATE_VERGETEN = 'account/wachtwoord-vergeten.dtl'


class LoginView(TemplateView):
    """
        Deze view het startpunt om in te loggen
        De login dialoog bevat drie knoppen:
            Log in --> inloggen met ingevoerd username/password
            Wachtwoord vergeten --> wachtwoord reset email krijgen
            Registreer --> nieuw account aanmaken
    """

    form_class = LoginForm

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de LOG IN knop.
        """
        form = LoginForm(request.POST)
        if form.is_valid():
            login_naam = form.cleaned_data.get("login_naam")
            wachtwoord = form.cleaned_data.get("wachtwoord")
            user = authenticate(username=login_naam, password=wachtwoord)
            if user:
                # integratie met de authenticatie laag van Django
                login(request, user)
                # TODO: redirect NHB schutters naar schutter start-pagina
                return HttpResponseRedirect(reverse('Plein:plein'))
            form.add_error(None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

        # still here --> re-render with error message
        context = { 'form': form }
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_LOGIN, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
            we geven een lege form aan de template
        """
        form = LoginForm()
        context = { 'form': form }
        menu_dynamics(request, context, actief='inloggen')
        return render(request, TEMPLATE_LOGIN, context)


class LogoutView(View):
    """
        Deze view zorgt voor het uitloggen
        Knoppen / links om uit te loggen moeten hier naartoe wijzen
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
            we zorgen voor het uitloggen en sturen door naar een andere pagina
        """

        # integratie met de authenticatie laag van Django
        logout(request)

        # redirect to success page
        return HttpResponseRedirect(reverse('Account:uitgelogd'))


class UitgelogdView(TemplateView):
    """
        Deze view geeft de pagina die de gebruiker vertelt dat uitloggen gelukt is
    """

    # class variables shared by all instances
    template_name = TEMPLATE_UITGELOGD

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context)
        return context


class WachtwoordVergetenView(TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    template_name = TEMPLATE_VERGETEN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def obfuscate_email(email):
    """ Helper functie om een email adres te maskeren
        voorbeeld: nhb.ramonvdw@gmail.com --> nh####w@gmail.com
    """
    user, domein = email.rsplit("@", 1)
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
    print("obfuscate_email: %s --> %s" % (repr(email), repr(new_email)))
    return new_email


class RegistreerNhbNummerView(TemplateView):
    """
        Deze view wordt gebruikt om het NHB nummer in te voeren voor een nieuw account.
    """

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        print("RegistreerNhbNummerView.post")
        form = RegistreerForm(request.POST)
        if form.is_valid():
            print("RegistreerNhbNummerView: form is valid")
            nhb_nummer = form.cleaned_data.get('nhb_nummer')
            email = form.cleaned_data.get('email')
            nieuw_wachtwoord = form.cleaned_data.get('nieuw_wachtwoord')
            error = False
            try:
                ack_url = account_create_nhb(nhb_nummer, email, nieuw_wachtwoord)
            except AccountCreateError as exc:
                print("Exception: AccountCreateError: %s" % str(exc))
                form.add_error(None, str(exc))
            else:
                print("RegistreerView: email=%s, ack_url=%s" % (repr(email), repr(ack_url)))
                # TODO: send email
                request.session['login_naam'] = nhb_nummer
                request.session['partial_email'] = obfuscate_email(email)
                request.session['TEMP_ACK_URL'] = ack_url
                return HttpResponseRedirect(reverse('Account:aangemaakt'))

        # still here --> re-render with error message
        context = { 'form': form }
        # TODO: menu_dynamics?
        return render(request, TEMPLATE_REGISTREER, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # GET operation --> create empty form
        form = RegistreerForm()
        context = { 'form': form }
        # TODO: menu_dynamics?
        return render(request, TEMPLATE_REGISTREER, context)


class RegistreerWachtwoordView(TemplateView):
    """
        Deze view wordt gebruikt om een het wachtwoord in te voeren voor een nieuw account.
    """

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op een van de knoppen.
        """
        form = RegistreerForm(request.POST)
        if form.is_valid():
            nhb_nummer = form.cleaned_data.get('nhb_nummer')
            email = form.cleaned_data.get('nhb_nummer')
            nieuw_wachtwoord = form.cleaned_data.get('nieuw_wachtwoord')
            error = False
            try:
                email, ack_url = account_create_nhb(nhb_nummer, nieuw_wachtwoord)
            except AccountCreateError as exc:
                form.add_error(None, str(exc))
            else:
                print("RegistreerView: email=%s, ack_url=%s" % (repr(email), repr(ack_url)))
                request.session['login_naam'] = nhb_nummer
                request.session['partial_email'] = obfuscate_email(email)
                request.session['TEMP_ACK_URL'] = ack_url
                # TODO: send email
                return HttpResponseRedirect(reverse('Account:aangemaakt'))

        # still here --> re-render with error message
        context = { 'form': form }
        # TODO: menu_dynamics?
        return render(request, TEMPLATE_REGISTREER, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # GET operation --> create empty form
        form = RegistreerForm()
        context = { 'form': form }
        # TODO: menu_dynamics?
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

    def get(selfself, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # informatie doorgifte van de registratie view naar deze view
        # gaat via server-side sessie-variabelen
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

        # TODO: menu_dynamic?
        return render(request, TEMPLATE_AANGEMAAKT, context)


def receive_bevestiging_accountemail(request, obj):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgt wordt
        om een email adres te bevestigen.
            obj is een AccountEmail object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden.
    """
    print("receive_bevestiging_accountemail: obj=%s" % repr(obj))
    account_email_is_bevestigd(obj)
    # TODO: implement verdere reactie.
    # TODO: Iets opslaan in de sessie voor de pagina waar we naar redirecten?
    request.session['XXX'] = 123
    return reverse('Account:bevestigd')


set_tijdelijke_url_receiver(RECEIVER_ACCOUNTEMAIL, receive_bevestiging_accountemail)

# end of file
