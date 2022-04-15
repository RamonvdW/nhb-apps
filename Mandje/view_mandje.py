# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Betalingen.mutaties import betaling_get_volgende_boekingsnummer
from Functie.rol import Rollen, rol_get_huidige
from Kalender.mutaties import kalender_kortingscode_toepassen, kalender_verwijder_reservering
from Mandje.models import MandjeProduct, MandjeBestelling, MINIMUM_CODE_LENGTH, MANDJE_NOG_GEEN_BESTELLING
from Mandje.mandje import mandje_is_gewijzigd, eval_mandje_inhoud
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
from decimal import Decimal


TEMPLATE_MANDJE_TOON_INHOUD = 'mandje/toon-inhoud.dtl'

kalender_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__KALENDER_MUTATIES)


class ToonInhoudMandje(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker de inhoud van zijn mandje zien """

    # class variables shared by all instances
    template_name = TEMPLATE_MANDJE_TOON_INHOUD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    @staticmethod
    def _beschrijf_inhoud_mandje(account, maak_urls=True):
        """ gezamenlijke code voor het tonen van de inhoud van het mandje en het afrekenen """

        mandje_is_leeg = True
        bevat_fout = False

        bestellingen = (MandjeBestelling
                        .objects
                        .filter(account=account,
                                boekingsnummer=MANDJE_NOG_GEEN_BESTELLING)
                        .prefetch_related('producten'))

        if bestellingen.count() > 0:
            bestelling = bestellingen[0]
            controleer_euro = Decimal()

            producten = (bestelling
                         .producten
                         .select_related('inschrijving',
                                         'inschrijving__wedstrijd',
                                         'inschrijving__sessie',
                                         'inschrijving__sporterboog',
                                         'inschrijving__sporterboog__boogtype',
                                         'inschrijving__sporterboog__sporter'))

            for product in producten:
                # maak een beschrijving van deze regel
                product.beschrijving = beschrijving = list()

                if product.inschrijving:
                    inschrijving = product.inschrijving

                    tup = ('Reserveringsnummer', settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk)
                    beschrijving.append(tup)

                    tup = ('Wedstrijd', inschrijving.wedstrijd.titel)
                    beschrijving.append(tup)

                    sessie = inschrijving.sessie
                    tup = ('Sessie', '%s om %s' % (sessie.datum, sessie.tijd_begin.strftime('%H:%M')))
                    beschrijving.append(tup)

                    sporterboog = inschrijving.sporterboog
                    tup = ('Sporter', '%s' % sporterboog.sporter.lid_nr_en_volledige_naam())
                    beschrijving.append(tup)

                    sporter_ver = sporterboog.sporter.bij_vereniging
                    if sporter_ver:
                        ver_naam = sporter_ver.ver_nr_en_naam()
                    else:
                        ver_naam = 'Onbekend'
                    tup = ('Van vereniging', ver_naam)
                    beschrijving.append(tup)

                    tup = ('Boog', '%s' % sporterboog.boogtype.beschrijving)
                    beschrijving.append(tup)

                    if inschrijving.gebruikte_code:
                        code = inschrijving.gebruikte_code
                        product.gebruikte_code_str = "code %s (korting: %d%%)" % (code.code, code.percentage)
                    elif product.korting_euro:
                        product.gebruikte_code_str = "Onbekende code"
                        bevat_fout = True

                    controleer_euro += product.prijs_euro
                    controleer_euro -= product.korting_euro
                else:
                    tup = ('Fout', 'Onbekend product')
                    beschrijving.append(tup)
                    bevat_fout = True

                if maak_urls:
                    # maak een knop om deze bestelling te verwijderen uit het mandje
                    product.url_verwijder = reverse('Mandje:verwijder-inschrijving',
                                                    kwargs={'inhoud_pk': product.pk})

                mandje_is_leeg = False
            # for

            # nooit een negatief totaalbedrag tonen want we geven geen geld weg
            if controleer_euro < 0.0:
                controleer_euro = 0.0

            if controleer_euro != bestelling.totaal_euro:
                bevat_fout = True
        else:
            bestelling = None
            producten = None

        return bestelling, producten, mandje_is_leeg, bevat_fout

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user

        eval_mandje_inhoud(self.request)

        bestelling, producten, mandje_is_leeg, bevat_fout = self._beschrijf_inhoud_mandje(account)

        context['mandje_is_leeg'] = mandje_is_leeg
        context['bestelling'] = bestelling
        context['producten'] = producten
        context['bevat_fout'] = bevat_fout

        context['url_code_toevoegen'] = reverse('Mandje:code-toevoegen')
        if not bevat_fout:
            if bestelling.totaal_euro > 0:
                context['url_afrekenen'] = reverse('Mandje:toon-inhoud')

        context['kruimels'] = (
            (None, 'Mandje'),
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):

        account = self.request.user
        mandje_inhoud, mandje_is_leeg, totaal_euro, bevat_fout = self._beschrijf_inhoud_mandje(account, maak_urls=False)
        if bevat_fout:
            raise Http404('Afrekenen is niet mogelijk')

        # neem een boekingsnummer uit
        boekeingsnummer = betaling_get_volgende_boekingsnummer()

        url = reverse('Mandje:toon-inhoud')
        return HttpResponseRedirect(url)


class CodeToevoegenView(UserPassesTestMixin, View):

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):
        """ Voeg de code toe aan het mandje """

        # TODO: rate limiter

        code = ''
        for char in request.POST.get('code', '')[:40]:        # afkappen voor de veiligheid:
            if char.isalnum():
                code += char
        # for

        if len(code) >= MINIMUM_CODE_LENGTH:
            account = request.user
            snel = str(request.POST.get('snel', ''))[:1]

            if kalender_kortingscode_toepassen(account, code, snel == '1'):
                # gelukt
                mandje_is_gewijzigd(self.request)

        # terug naar het mandje
        url = reverse('Mandje:toon-inhoud')

        return HttpResponseRedirect(url)


class VerwijderUitMandje(UserPassesTestMixin, View):

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):
        try:
            inhoud_pk = str(kwargs['inhoud_pk'])[:6]        # afkappen voor de veiligheid
            inhoud_pk = int(inhoud_pk)
        except (KeyError, ValueError, TypeError):
            raise Http404('Verkeerde parameter')

        # zoek de regel op in het mandje van de ingelogde gebruiker
        account = request.user
        try:
            inhoud = MandjeProduct.objects.get(pk=inhoud_pk,
                                               account=account)
        except MandjeProduct.DoesNotExist:
            raise Http404('Niet gevonden in mandje')

        snel = str(request.POST.get('snel', ''))[:1]
        kalender_verwijder_reservering(inhoud.inschrijving, snel == '1')

        mandje_is_gewijzigd(self.request)

        url = reverse('Mandje:toon-inhoud')
        return HttpResponseRedirect(url)


# end of file
