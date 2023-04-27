# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from Account.otp import account_otp_controleer, account_otp_loskoppelen
from Functie.definities import Rollen
from Functie.forms import OTPControleForm
from Functie.rol import rol_get_huidige
from Mailer.operations import mailer_queue_email, render_email_template
from Plein.menu import menu_dynamics


TEMPLATE_OTP_CONTROLE = 'functie/otp-controle.dtl'
EMAIL_TEMPLATE_OTP_IS_LOSGEKOPPELD = 'email_functie/otp-is-losgekoppeld.dtl'


def functie_stuur_email_otp_losgekoppeld(account):

    """ Stuur een e-mail naar 'account' om te melden dat de OTP losgekoppeld is """

    context = {
        'voornaam': account.get_first_name(),
        'contact_email': settings.EMAIL_BONDSBUREAU,
        'url_handleiding_beheerders': settings.URL_PDF_HANDLEIDING_BEHEERDERS
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_OTP_IS_LOSGEKOPPELD)

    mailer_queue_email(account.bevestigde_email,
                       'Tweede factor losgekoppeld op ' + settings.NAAM_SITE,
                       mail_body)


class OTPLoskoppelenView(UserPassesTestMixin, View):

    """ Deze view levert een POST-functie om de tweede factor los te kunnen koppelen
        voor een gekozen gebruiken. Dit kan alleen de BB.
    """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    @staticmethod
    def post(request, *args, **kwargs):
        url = reverse('Overig:activiteit')

        if request.POST.get("reset_tweede_factor", None):
            inlog_naam = request.POST.get("inlog_naam", '')[:6]     # afkappen voor de veiligheid

            try:
                account = Account.objects.get(username=inlog_naam)
            except Account.DoesNotExist:
                raise Http404('Niet gevonden')

            url += '?zoekterm=%s' % account.username

            # doe het feitelijke loskoppelen + in logboek schrijven
            is_losgekoppeld = account_otp_loskoppelen(request, account)

            if is_losgekoppeld:
                functie_stuur_email_otp_losgekoppeld(account)

        return HttpResponseRedirect(url)


class OTPControleView(TemplateView):
    """ Met deze view kan de OTP-controle doorlopen worden
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
            # gebruiker heeft geen OTP-koppeling
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = OTPControleForm(request.POST)
        context = {'form': form}

        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            if account_otp_controleer(request, account, otp_code):
                # controle is gelukt (is ook al gelogd)
                next_url = form.cleaned_data.get('next_url')
                if not next_url:
                    next_url = reverse('Functie:wissel-van-rol')
                if next_url[-1] != '/':
                    next_url += '/'
                return HttpResponseRedirect(next_url)

            # controle is mislukt (is al gelogd en in het logboek geschreven)
            form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
            context['toon_hulp'] = True
            context['email_support'] = settings.EMAIL_SUPPORT

            now = timezone.localtime(timezone.now())
            context['tijdstip'] = now.strftime('%H:%M')
            # de code verandert sneller dan een brute-force aan kan, dus niet nodig om te blokkeren

        # still here --> re-render with error message
        menu_dynamics(request, context)
        return render(request, TEMPLATE_OTP_CONTROLE, context)


# end of file
