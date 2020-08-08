# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.views.generic import TemplateView
from Account.otp import account_otp_prepare_koppelen, account_otp_koppel, account_otp_controleer
from Plein.menu import menu_dynamics
from .models import account_needs_otp
from .forms import OTPControleForm
from .qrcode import qrcode_get
import logging


TEMPLATE_OTP_CONTROLE = 'functie/otp-controle.dtl'
TEMPLATE_OTP_KOPPELEN = 'functie/otp-koppelen.dtl'
TEMPLATE_OTP_GEKOPPELD = 'functie/otp-koppelen-gelukt.dtl'


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

        account = request.user
        if not account.otp_is_actief:
            # gebruiker heeft geen OTP koppeling
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = OTPControleForm()
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_CONTROLE, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus stuur terug naar af
            return HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user
        if not account.otp_is_actief:
            # gebruiker heeft geen OTP koppeling
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            if account_otp_controleer(request, account, otp_code):
                # controle is gelukt (is ook al gelogd)
                # terug naar de Wissel-van-rol pagina
                return HttpResponseRedirect(reverse('Functie:wissel-van-rol'))
            else:
                # controle is mislukt (is al gelogd en in het logboek geschreven)
                form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
                # FUTURE: blokkeer na X pogingen

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_CONTROLE, context)


class OTPKoppelenView(TemplateView):
    """ Met deze view kan de OTP koppeling tot stand gebracht worden
    """

    @staticmethod
    def _account_needs_otp_or_redirect(request):
        """ Controleer dat het account OTP nodig heeft, of wegsturen """

        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus zou hier niet moeten komen
            return None, HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user

        if not account_needs_otp(account):
            # gebruiker heeft geen OTP nodig
            return account, HttpResponseRedirect(reverse('Plein:plein'))

        if account.otp_is_actief:
            # gebruiker is al gekoppeld, dus niet zomaar toestaan om een ander apparaat ook te koppelen!!
            return account, HttpResponseRedirect(reverse('Plein:plein'))

        return account, None

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        account, response = self._account_needs_otp_or_redirect(request)
        if response:
            return response

        # haal de QR code op (en alles wat daar voor nodig is)
        account_otp_prepare_koppelen(account)
        qrcode = qrcode_get(account)

        tmp = account.otp_code.lower()
        secret = " ".join([tmp[i:i+4] for i in range(0, 16, 4)])

        form = OTPControleForm()
        context = {'form': form,
                   'qrcode': qrcode,
                   'otp_secret': secret }
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_KOPPELEN, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """
        account, response = self._account_needs_otp_or_redirect(request)
        if response:
            return response

        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            if account_otp_koppel(request, account, otp_code):
                # geef de succes pagina
                context = dict()
                menu_dynamics(request, context, actief="inloggen")
                return render(request, TEMPLATE_OTP_GEKOPPELD, context)

            # controle is mislukt - is al gelogd
            form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
            # FUTURE: blokkeer na X pogingen

        # still here --> re-render with error message
        qrcode = qrcode_get(account)
        tmp = account.otp_code.lower()
        secret = " ".join([tmp[i:i+4] for i in range(0, 16, 4)])
        context = {'form': form,
                   'qrcode': qrcode,
                   'otp_secret': secret}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_KOPPELEN, context)


# end of file
