# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Bestel.models import Bestelling
from Plein.menu import menu_dynamics
from decimal import Decimal

TEMPLATE_BESTELLING_DETAILS = 'bestel/toon-bestelling-details.dtl'


class ToonBestellingDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker de inhoud van zijn mandje zien """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTELLING_DETAILS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    @staticmethod
    def _beschrijf_inhoud_bestelling(bestelling):
        """ beschrijf de inhoud van een bestelling """

        bevat_fout = False

        controleer_euro = Decimal(0)

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
                    korting = inschrijving.gebruikte_code
                    product.gebruikte_code_str = "code %s (korting: %d%%)" % (korting.code, korting.percentage)
                    if korting.combi_basis_wedstrijd:
                        product.is_combi_korting = True
                        product.combi_reden = [wedstrijd.titel for wedstrijd in korting.voor_wedstrijden.all()]
                elif product.korting_euro:
                    product.gebruikte_code_str = "Onbekende code"
                    bevat_fout = True

                controleer_euro += product.prijs_euro
                controleer_euro -= product.korting_euro
            else:
                tup = ('Fout', 'Onbekend product')
                beschrijving.append(tup)
                bevat_fout = True
        # for

        # nooit een negatief totaalbedrag tonen want we geven geen geld weg
        if controleer_euro < 0.0:
            controleer_euro = 0.0

        if controleer_euro != bestelling.totaal_euro:
            bevat_fout = True

        return producten, bevat_fout

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        context['bestelling'] = bestelling

        context['producten'], context['bevat_fout'] = self._beschrijf_inhoud_bestelling(bestelling)

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Bestelling'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
