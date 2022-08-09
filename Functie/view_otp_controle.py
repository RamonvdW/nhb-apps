# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from Account.otp import account_otp_controleer
from Plein.menu import menu_dynamics
from .forms import OTPControleForm


TEMPLATE_OTP_CONTROLE = 'functie/otp-controle.dtl'


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

        # waar eventueel naartoe na de controle?
        next_url = request.GET.get('next', '')

        form = OTPControleForm(initial={'next_url': next_url})

        context = dict()
        context['form'] = form

        context['kruimels'] = (
            (reverse('Functie:wissel-van-rol'), 'Wissel van rol'),
            (None, 'Controle tweede factor')
        )

        menu_dynamics(request, context)
        return render(request, TEMPLATE_OTP_CONTROLE, context)

    @staticmethod
    def post(request, *args, **kwargs):
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
                next_url = form.cleaned_data.get('next_url')
                if not next_url:
                    next_url = reverse('Functie:wissel-van-rol')
                return HttpResponseRedirect(next_url)
            else:
                # controle is mislukt (is al gelogd en in het logboek geschreven)
                form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
                # de code verandert sneller dan een brute-force aan kan, dus niet nodig om te blokkeren

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context)
        return render(request, TEMPLATE_OTP_CONTROLE, context)


# end of file
