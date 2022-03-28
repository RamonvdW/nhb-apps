# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Mandje.models import MandjeInhoud
from Plein.menu import menu_dynamics
from decimal import Decimal


TEMPLATE_MANDJE_TOON_INHOUD = 'mandje/toon-inhoud.dtl'


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

        inhoud = (MandjeInhoud
                  .objects
                  .filter(account=account)
                  .select_related('inschrijving',
                                  'inschrijving__wedstrijd',
                                  'inschrijving__sessie',
                                  'inschrijving__sporterboog',
                                  'inschrijving__sporterboog__boogtype',
                                  'inschrijving__sporterboog__sporter'))

        context['inhoud'] = inhoud

        context['mandje_is_leeg'] = True

        totaal_euro = Decimal(0)
        for regel in inhoud:
            # maak een beschrijving van deze regel
            regel.beschrijving = beschrijving = list()

            if regel.inschrijving:
                inschrijving = regel.inschrijving

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

                if regel.korting_euro:
                    regel.gebruikte_code_str = "Onbekende code"
                    if inschrijving.gebruikte_code:
                        code = inschrijving.gebruikte_code
                        regel.gebruikte_code_str = "code %s (korting: %d%%)" % (code.code, code.percentage)

                totaal_euro += regel.prijs_euro
                totaal_euro += regel.korting_euro
            else:
                beschrijving.append('Onbekend product')

            # maak een knop om deze bestelling te verwijderen uit het mandje
            regel.url_verwijder = "??"

            context['mandje_is_leeg'] = False
        # for

        totaal_euro += 1
        context['totaal_euro'] = totaal_euro
        context['moet_afrekenen'] = (totaal_euro > 0)

        context['kruimels'] = (
            (None, 'Mandje'),
        )

        menu_dynamics(self.request, context)
        return context

# end of file
