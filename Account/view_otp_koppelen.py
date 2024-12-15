# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseNotAllowed
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.forms import OTPControleForm
from Account.models import get_account
from Account.operations.maak_qrcode import qrcode_get
from Account.operations.otp import otp_prepare_koppelen, otp_koppel_met_code
from Functie.rol import rol_mag_wisselen

TEMPLATE_OTP_KOPPELEN_STAP1 = 'account/otp-koppelen-stap1-uitleg.dtl'
TEMPLATE_OTP_KOPPELEN_STAP2 = 'account/otp-koppelen-stap2-scan-qr-code.dtl'
TEMPLATE_OTP_KOPPELEN_STAP3 = 'account/otp-koppelen-stap3-code-invoeren.dtl'
TEMPLATE_OTP_GEKOPPELD = 'account/otp-koppelen-gelukt.dtl'


class OTPKoppelenStapView(UserPassesTestMixin, TemplateView):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.rol_nu, self.functie_nu = None, None
        self.account = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        # dispatch garandeert self.request.user.is_authenticated == True
        #self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return rol_mag_wisselen(self.request)

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als de tweede factor niet meer gekoppeld hoeft te worden """

        if request.method not in ('GET', 'POST'):
            return HttpResponseNotAllowed(permitted_methods=('GET', 'POST'))

        if not request.user.is_authenticated:
            return redirect('Plein:plein')

        self.account = get_account(request)
        if self.account.otp_is_actief:
            # OTP is al actief, dus niet nodig om te koppelen
            return redirect('Plein:plein')

        return super().dispatch(request, *args, **kwargs)


class OTPKoppelenStap1View(OTPKoppelenStapView):

    template_name = TEMPLATE_OTP_KOPPELEN_STAP1

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_stap_2'] = reverse('Account:otp-koppelen-stap2')

        return context


class OTPKoppelenStap2View(OTPKoppelenStapView):

    template_name = TEMPLATE_OTP_KOPPELEN_STAP2

    def post(self, request, *args, **kwargs):
        """ overgang vanuit stap 1
            hier kunnen we database wijziging doen: de OTP code aanmaken voor het account.
        """
        otp_prepare_koppelen(self.account)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_stap_1'] = reverse('Account:otp-koppelen-stap1')
        context['url_stap_3'] = reverse('Account:otp-koppelen-stap3')

        # haal de QR code op (en alles wat daar voor nodig is)
        context['qrcode'] = qrcode_get(self.account)

        tmp = self.account.otp_code.lower()
        context['otp_secret'] = " ".join([tmp[i:i+4] for i in range(0, len(tmp), 4)])

        return context


class OTPKoppelenStap3View(OTPKoppelenStapView):

    template_name = TEMPLATE_OTP_KOPPELEN_STAP3

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['url_stap_2'] = reverse('Account:otp-koppelen-stap2')
        context['url_controleer'] = reverse('Account:otp-koppelen-stap3')
        context['site_name'] = settings.OTP_ISSUER_NAME

        context['form'] = OTPControleForm()
        context['now'] = timezone.now()

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """
        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            if otp_koppel_met_code(request, self.account, otp_code):
                # gelukt
                # geef de succes pagina
                return render(request, TEMPLATE_OTP_GEKOPPELD)

            # controle is mislukt - is al gelogd
            form.add_error(None, 'verkeerde code. Probeer het nog eens.')
            # FUTURE: blokkeer na X pogingen

        # still here --> re-render with error message
        context = dict()

        context['url_stap_2'] = reverse('Account:otp-koppelen-stap2')
        context['url_controleer'] = reverse('Account:otp-koppelen-stap3')
        context['site_name'] = settings.OTP_ISSUER_NAME

        context['form'] = form
        context['now'] = timezone.now()

        return render(request, self.template_name, context)

# end of file
