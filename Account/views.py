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
from .models import account_create_nhb, AccountCreateError
from Plein.kruimels import make_context_broodkruimels


TEMPLATE_LOGIN = 'account/login.dtl'
TEMPLATE_UITGELOGD = 'account/uitgelogd.dtl'
TEMPLATE_REGISTREER = 'account/registreer.dtl'
TEMPLATE_AANGEMAAKT = 'account/aangemaakt.dtl'
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
            login_naam = request.POST.get("login_naam", None)
            wachtwoord = request.POST.get("wachtwoord", None)
            user = authenticate(username=login_naam, password=wachtwoord)
            if user:
                login(request, user)
                return HttpResponseRedirect(reverse('Plein:plein'))
            form.add_error(None, 'De combinatie van inlog naam en wachtwoord worden niet herkend. Probeer het nog eens.')

        # still here --> re-render with error message
        context = { 'form': form }
        make_context_broodkruimels(context, 'Plein:plein', 'Account:login')
        return render(request, TEMPLATE_LOGIN, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
            we geven een lege form aan de template
        """
        form = LoginForm()
        context = { 'form': form }
        make_context_broodkruimels(context, 'Plein:plein', 'Account:login')
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
        make_context_broodkruimels(context, 'Plein:plein')
        return context


class WachtwoordVergetenView(TemplateView):
    """
        Deze view geeft de pagina waarmee de gebruiker zijn wachtwoord kan wijzigen
    """

    template_name = TEMPLATE_VERGETEN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        make_context_broodkruimels(context, 'Plein:plein', 'Account:login', 'Account:wachtwoord-vergeten')
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


class RegistreerView(TemplateView):
    """
        Deze view wordt gebruikt om een nieuw account aan te maken.
    """

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op een van de knoppen.
        """
        form = RegistreerForm(request.POST)
        if form.is_valid():
            nhb_nummer = request.POST.get('nhb_nummer', None)
            nieuw_wachtwoord = request.POST.get('nieuw_wachtwoord', None)
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
        make_context_broodkruimels(context, 'Plein:plein', 'Account:login', 'Account:registreer')
        return render(request, TEMPLATE_REGISTREER, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # GET operation --> create empty form
        form = RegistreerForm()
        context = { 'form': form }
        make_context_broodkruimels(context, 'Plein:plein', 'Account:login', 'Account:registreer')
        return render(request, TEMPLATE_REGISTREER, context)


def aangemaakt(request):
    try:
        login_naam = request.session['login_naam']
        partial_email = request.session['partial_email']
    except KeyError:
        return HttpResponseRedirect(reverse('Plein:plein'))

    context = {'login_naam': login_naam,
               'partial_email': partial_email }

    make_context_broodkruimels(context, 'Plein:plein', 'Account:registreer', 'Account:aangemaakt')

    return render(request, TEMPLATE_AANGEMAAKT, context)

# end of file
