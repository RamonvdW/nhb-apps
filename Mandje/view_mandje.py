# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Kalender.models import KalenderMutatie, KALENDER_MUTATIE_AFMELDEN
from Mandje.models import MandjeInhoud
from Mandje.mandje import mandje_is_gewijzigd
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
from decimal import Decimal
import time


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

        totaal_euro = Decimal(0)
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
                tup = ('Van vereniging', '%s' % sporterboog.sporter.bij_vereniging.ver_nr_en_naam())
                beschrijving.append(tup)
                tup = ('Boog', '%s' % sporterboog.boogtype.beschrijving)
                beschrijving.append(tup)

                if inhoud.korting_euro:
                    inhoud.gebruikte_code_str = "Onbekende code"
                    if inschrijving.gebruikte_code:
                        code = inschrijving.gebruikte_code
                        inhoud.gebruikte_code_str = "code %s (korting: %d%%)" % (code.code, code.percentage)

                totaal_euro += inhoud.prijs_euro
                totaal_euro += inhoud.korting_euro
            else:
                beschrijving.append('Onbekend product')

            # maak een knop om deze bestelling te verwijderen uit het mandje
            inhoud.url_verwijder = reverse('Mandje:verwijder-inschrijving',
                                           kwargs={'inhoud_pk': inhoud.pk})

            context['mandje_is_leeg'] = False
        # for

        context['totaal_euro'] = totaal_euro
        context['moet_afrekenen'] = (totaal_euro > 0)

        context['kruimels'] = (
            (None, 'Mandje'),
        )

        menu_dynamics(self.request, context)
        return context


class VerwijderInschrijving(UserPassesTestMixin, View):

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

        # zet dit verzoek door naar het mutaties process
        inschrijving = inhoud.inschrijving
        mutatie = KalenderMutatie(
                        code=KALENDER_MUTATIE_AFMELDEN,
                        inschrijving=inschrijving)
        mutatie.save()

        # ping het achtergrond process
        kalender_mutaties_ping.ping()

        snel = str(request.POST.get('snel', ''))[:1]
        if snel != '1':         # pragma: no cover
            # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
            interval = 0.2      # om steeds te verdubbelen
            total = 0.0         # om een limiet te stellen
            while not mutatie.is_verwerkt and total + interval <= 3.0:
                time.sleep(interval)
                total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
                interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                mutatie = KalenderMutatie.objects.get(pk=mutatie.pk)
            # while

        mandje_is_gewijzigd(self.request)

        url = reverse('Mandje:toon-inhoud')

        return HttpResponseRedirect(url)



# end of file
