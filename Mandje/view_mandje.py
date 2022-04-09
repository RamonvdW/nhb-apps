# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Kalender.mutaties import kalender_kortingscode_toepassen, kalender_verwijder_reservering
from Mandje.models import MandjeInhoud, MINIMUM_CODE_LENGTH
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user

        eval_mandje_inhoud(self.request)

        mandje_inhoud = (MandjeInhoud
                         .objects
                         .filter(account=account)
                         .select_related('inschrijving',
                                         'inschrijving__wedstrijd',
                                         'inschrijving__sessie',
                                         'inschrijving__sporterboog',
                                         'inschrijving__sporterboog__boogtype',
                                         'inschrijving__sporterboog__sporter'))

        context['mandje_inhoud'] = mandje_inhoud
        context['mandje_is_leeg'] = True

        totaal_euro = Decimal()
        for inhoud in mandje_inhoud:
            # maak een beschrijving van deze regel
            inhoud.beschrijving = beschrijving = list()

            if inhoud.inschrijving:
                inschrijving = inhoud.inschrijving

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
                    inhoud.gebruikte_code_str = "code %s (korting: %d%%)" % (code.code, code.percentage)
                elif inhoud.korting_euro:
                    inhoud.gebruikte_code_str = "Onbekende code"

                totaal_euro += inhoud.prijs_euro
                totaal_euro -= inhoud.korting_euro
            else:
                tup = ('Fout', 'Onbekend product')
                beschrijving.append(tup)

            # maak een knop om deze bestelling te verwijderen uit het mandje
            inhoud.url_verwijder = reverse('Mandje:verwijder-inschrijving',
                                           kwargs={'inhoud_pk': inhoud.pk})

            context['mandje_is_leeg'] = False
        # for

        # nooit een negatief totaalbedrag tonen want we geven geen geld weg
        if totaal_euro < 0.0:
            totaal_euro = 0.0

        context['totaal_euro'] = totaal_euro
        context['moet_afrekenen'] = (totaal_euro > 0)

        context['url_code_toevoegen'] = reverse('Mandje:code-toevoegen')

        context['kruimels'] = (
            (None, 'Mandje'),
        )

        menu_dynamics(self.request, context)
        return context


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
            inhoud = MandjeInhoud.objects.get(pk=inhoud_pk,
                                              account=account)
        except MandjeInhoud.DoesNotExist:
            raise Http404('Niet gevonden in mandje')

        snel = str(request.POST.get('snel', ''))[:1]
        kalender_verwijder_reservering(inhoud.inschrijving, snel == '1')

        mandje_is_gewijzigd(self.request)

        url = reverse('Mandje:toon-inhoud')
        return HttpResponseRedirect(url)


# end of file
