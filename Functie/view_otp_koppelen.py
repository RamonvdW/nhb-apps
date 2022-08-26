# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.otp import account_otp_prepare_koppelen, account_otp_koppel, account_otp_is_gekoppeld
from Functie.rol import rol_evalueer_opnieuw, rol_get_huidige_functie, rol_mag_wisselen
from Plein.menu import menu_dynamics
from .forms import OTPControleForm
from .maak_qrcode import qrcode_get


TEMPLATE_OTP_GEKOPPELD = 'functie/otp-koppelen-gelukt.dtl'
TEMPLATE_OTP_KOPPELEN = 'functie/otp-koppelen-stap2-scan-qr-code.dtl'
TEMPLATE_OTP_KOPPELEN_STAP1 = 'functie/otp-koppelen-stap1-uitleg.dtl'
TEMPLATE_OTP_KOPPELEN_STAP2 = 'functie/otp-koppelen-stap2-scan-qr-code.dtl'
TEMPLATE_OTP_KOPPELEN_STAP3 = 'functie/otp-koppelen-stap3-code-invoeren.dtl'


class OTPKoppelenStapView(UserPassesTestMixin, TemplateView):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        # evalueer opnieuw welke rechten de gebruiker heeft
        rol_evalueer_opnieuw(self.request)

        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)

        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als de tweede factor niet meer gekoppeld hoeft te worden """

        if not request.user.is_authenticated:
            return redirect('Plein:plein')

        if account_otp_is_gekoppeld(request.user):
            return redirect('Plein:plein')

        return super().dispatch(request, *args, **kwargs)


class OTPKoppelenStap1View(OTPKoppelenStapView):

    template_name = TEMPLATE_OTP_KOPPELEN_STAP1

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_stap_2'] = reverse('Functie:otp-koppelen-stap2')

        menu_dynamics(self.request, context)
        return context


class OTPKoppelenStap2View(OTPKoppelenStapView):

    template_name = TEMPLATE_OTP_KOPPELEN_STAP2

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_stap_1'] = reverse('Functie:otp-koppelen-stap1')
        context['url_stap_3'] = reverse('Functie:otp-koppelen-stap3')

        account = self.request.user

        # haal de QR code op (en alles wat daar voor nodig is)
        account_otp_prepare_koppelen(account)
        context['qrcode'] = qrcode_get(account)

        tmp = account.otp_code.lower()
        context['otp_secret'] = " ".join([tmp[i:i+4] for i in range(0, len(tmp), 4)])

        menu_dynamics(self.request, context)
        return context


class OTPKoppelenStap3View(OTPKoppelenStapView):

    template_name = TEMPLATE_OTP_KOPPELEN_STAP3

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_stap_2'] = reverse('Functie:otp-koppelen-stap2')
        context['url_controleer'] = reverse('Functie:otp-koppelen-stap3')

        context['form'] = OTPControleForm()
        context['now'] = timezone.now()

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """

        account = request.user

        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            if account_otp_koppel(request, account, otp_code):
                # geef de succes pagina
                context = dict()
                menu_dynamics(request, context)
                return render(request, TEMPLATE_OTP_GEKOPPELD, context)

            # controle is mislukt - is al gelogd
            form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
            # FUTURE: blokkeer na X pogingen

        # still here --> re-render with error message
        context = dict()

        context['url_stap_2'] = reverse('Functie:otp-koppelen-stap2')
        context['url_controleer'] = reverse('Functie:otp-koppelen-stap3')

        context['form'] = form
        context['now'] = timezone.now()

        menu_dynamics(request, context)
        return render(request, self.template_name, context)

# end of file
