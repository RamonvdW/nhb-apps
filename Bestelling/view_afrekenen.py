# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestelling.definities import (BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_NIEUW,
                                   BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_MISLUKT)
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE, TRANSACTIE_TYPE_HANDMATIG
from Betaal.format import format_bedrag_euro
from Betaal.mutaties import betaal_mutatieverzoek_start_ontvangst
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from decimal import Decimal
from time import sleep

TEMPLATE_BESTELLING_AFREKENEN = 'bestelling/bestelling-afrekenen.dtl'
TEMPLATE_BESTELLING_AFGEROND = 'bestelling/bestelling-afgerond.dtl'


class BestellingAfrekenenView(UserPassesTestMixin, TemplateView):

    """ Deze functie wordt gebruikt om een betaling op te starten.
        Als de betaling nog niet bestaat, dan wordt deze opgestart via de POST.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTELLING_AFREKENEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None      # wordt gezet door dispatch()
        self.bestelling = None  # wordt gezet door dispatch()

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.rol_nu not in (Rol.ROL_NONE, None)

    def dispatch(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen voor get_queryset/get_context_data
            hier is het mogelijk om een redirect te doen.

            Let op: test_func is nog niet aangeroepen
        """
        self.rol_nu = rol_get_huidige(self.request)

        if self.rol_nu != Rol.ROL_NONE:

            account = get_account(self.request)

            try:
                bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
                bestel_nr = int(bestel_nr)
                bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
            except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
                raise Http404('Niet gevonden')

            if bestelling.status == BESTELLING_STATUS_AFGEROND:
                # betaling is al klaar
                url = reverse('Bestelling:na-de-betaling', kwargs={'bestel_nr': bestelling.bestel_nr})
                return HttpResponseRedirect(url)

            self.bestelling = bestelling

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # de details worden via DynamicBestellingCheckStatus opgehaald
        context['bestelling'] = bestelling = self.bestelling

        context['url_status_check'] = reverse('Bestelling:dynamic-check-status',
                                              kwargs={'bestel_nr': bestelling.bestel_nr})

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (reverse('Bestelling:toon-bestellingen'), 'Bestellingen'),
            (reverse('Bestelling:toon-bestelling-details', kwargs={'bestel_nr': bestelling.bestel_nr}), 'Bestelling'),
            (None, 'Afrekenen')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de gebruiker op de knop BETALEN drukt in de bestelling
            de enige taak van deze functie is een bestelling met status MISLUKT terug zetten naar NIEUW.
        """
        if self.bestelling.status == BESTELLING_STATUS_MISLUKT:
            self.bestelling.status = BESTELLING_STATUS_NIEUW
            self.bestelling.save(update_fields=['status'])

        # doorsturen naar de GET
        url = reverse('Bestelling:bestelling-afrekenen',
                      kwargs={'bestel_nr': self.bestelling.bestel_nr})
        return HttpResponseRedirect(url)


class DynamicBestellingCheckStatus(UserPassesTestMixin, View):

    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu != Rol.ROL_NONE

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen vanuit de template om te kijken wat de status van de bestelling/betaling is.

            Dit is een POST by-design, om caching te voorkomen.
        """
        account = get_account(request)

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        # print('bestelling.status=%s' % bestelling.status)
        out = dict()
        out['status'] = 'error'  # fallback

        if bestelling.status == BESTELLING_STATUS_NIEUW:
            # de betaling is nog niet actief
            out['status'] = 'nieuw'

            # start een nieuwe transactie op
            # LET OP: deze tekst moeten we kort houden, want Mollie + iDEAL kapt af op 36 tekens
            #         dus MijnHandboogsport bestelling MH-1234567 verliest de laatste 4 cijfers
            beschrijving = "%s %s" % (bestelling.mh_bestel_nr(), settings.AFSCHRIFT_SITE_NAAM)

            te_betalen_euro = bestelling.totaal_euro

            site_url = settings.SITE_URL
            if 'localhost:8000' in site_url:
                # insert actual port number during LiveServerTestCase
                site_url = site_url.replace('localhost:8000', request.get_host())

            url_na_de_betaling = site_url + reverse('Bestelling:na-de-betaling',
                                                    kwargs={'bestel_nr': bestelling.bestel_nr})

            # start de bestelling via de achtergrond taak
            # deze slaat de referentie naar de mutatie op in de bestelling
            betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        beschrijving,
                        te_betalen_euro,
                        url_na_de_betaling,
                        # snel == '1',
                        snel=True)          # niet wachten op reactie

        elif bestelling.status == BESTELLING_STATUS_BETALING_ACTIEF:
            if bestelling.betaal_mutatie:
                url = bestelling.betaal_mutatie.url_checkout
                if url:
                    # de checkout url is beschikbaar
                    # stuur de bezoeker daar heen
                    out['status'] = 'betaal'
                    out['checkout_url'] = url

        elif bestelling.status == BESTELLING_STATUS_AFGEROND:
            # we zouden hier niet moeten komen
            # TODO: automatisch doorsturen
            out['status'] = 'afgerond'

        elif bestelling.status == BESTELLING_STATUS_MISLUKT:
            out['status'] = 'mislukt'

        else:
            # geannuleerd komt hier
            raise Http404('Onbekende status')

        # niet gebruiken: raise Http404('Onbekende status')
        # want een 404 leidt tot een foutmelding pagina met status 200 ("OK")

        return JsonResponse(out)


class BestellingAfgerondView(UserPassesTestMixin, TemplateView):

    """ De CPSP stuurt de gebruiker naar deze view als de betaling afgerond is.
        We checken de status en bedanken de gebruiker of geven instructies voor de vervolgstappen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTELLING_AFGEROND
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rol.ROL_NONE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = get_account(self.request)

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.prefetch_related('transacties').get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        # geef de achtergrondtaak een kans om een callback van de CPSP te verwerken
        max_loops = 6
        if self.request.GET.get('snel', None):
            max_loops = 1
        while max_loops > 0 and bestelling.status != BESTELLING_STATUS_AFGEROND:
            max_loops -= 1
            sleep(0.5)
            bestelling = Bestelling.objects.prefetch_related('transacties').get(pk=bestelling.pk)
        # while

        bestelling.totaal_euro_str = format_bedrag_euro(bestelling.totaal_euro)

        context['bestelling'] = bestelling

        # TODO: onderstaande moeten we herzien. Er is 1 record van de betaling met alle totalen (in/uit).
        transacties_euro = Decimal(0)
        for transactie in bestelling.transacties.exclude(transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE):
            if transactie.transactie_type == TRANSACTIE_TYPE_HANDMATIG:
                transacties_euro += transactie.bedrag_handmatig
            else:
                transacties_euro += transactie.bedrag_beschikbaar
        # for

        context['ontvangen_euro_str'] = format_bedrag_euro(transacties_euro)

        context['url_afschrift'] = reverse('Bestelling:toon-bestelling-details',
                                           kwargs={'bestel_nr': bestelling.bestel_nr})

        context['url_status_check'] = reverse('Bestelling:dynamic-check-status',
                                              kwargs={'bestel_nr': bestelling.bestel_nr})

        if bestelling.status == BESTELLING_STATUS_AFGEROND:
            context['is_afgerond'] = True

        elif bestelling.status == BESTELLING_STATUS_BETALING_ACTIEF:
            # hier komen we als de betaling uitgevoerd is, maar de payment-status-changed nog niet
            # binnen is of nog niet verwerkt door de achtergrondtaak.
            # blijf pollen
            context['wacht_op_betaling'] = True

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (reverse('Bestelling:toon-bestellingen'), 'Bestellingen'),
            (reverse('Bestelling:toon-bestelling-details', kwargs={'bestel_nr': bestelling.bestel_nr}), 'Bestelling'),
            (None, 'Status betaling')
        )

        return context


# end of file
