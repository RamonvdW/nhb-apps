# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.timezone import localtime
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Bestel.models import Bestelling
from Betaal.mutaties import betaal_start_ontvangst
from Plein.menu import menu_dynamics
from decimal import Decimal

TEMPLATE_BESTELLING_DETAILS = 'bestel/toon-bestelling-details.dtl'
TEMPLATE_BESTELLING_AFREKENEN = 'bestel/bestelling-afrekenen.dtl'


class ToonBestellingDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker de details van een bestelling inzien en een betaling opstarten """

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

    @staticmethod
    def _beschrijf_transacties(bestelling):

        transacties_euro = Decimal(0)

        transacties = (bestelling
                       .transacties
                       .all())

        for transactie in transacties:
            transactie.regels = regels = list()

            regel = localtime(transactie.when).strftime('%Y-%m-%d %H:%M')
            regels.append(regel)

            regels.append(transactie.beschrijving)

            if transactie.is_restitutie:
                regels.append('Restitutie')
                transacties_euro -= transactie.bedrag_euro
            else:
                regels.append('Ontvangen van %s' % transactie.klant_naam)
                transacties_euro += transactie.bedrag_euro
        # for

        return transacties, transacties_euro

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

        context['transacties'], transacties_euro = self._beschrijf_transacties(bestelling)

        rest_euro = bestelling.totaal_euro - transacties_euro
        context['rest_euro'] = rest_euro

        if rest_euro >= Decimal('0.01'):
            context['url_afrekenen'] = reverse('Bestel:bestelling-afrekenen',
                                               kwargs={'bestel_nr': bestelling.bestel_nr})

        context['producten'], context['bevat_fout'] = self._beschrijf_inhoud_bestelling(bestelling)

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Bestelling'),
        )

        menu_dynamics(self.request, context)
        return context


class BestellingAfrekenenView(UserPassesTestMixin, TemplateView):

    """ Deze functie wordt gebruikt om een betaling op te starten.
        Als de betaling nog niet bestaat, dan wordt deze opgestart via de POST.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTELLING_AFREKENEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):
        """ Voeg de code toe aan het mandje """

        account = request.user

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        snel = str(request.POST.get('snel', ''))[:1]

        # zoek de betaling erbij
        if bestelling.actief_transactie:
            # betaling is al opgestart; transactie is al actief, dus ga daar mee door
            print('POST: door gaan met actieve transactie nog niet gemaakt')

        elif bestelling.actief_mutatie:
            # betaling is al opgestart; we wachten op de achtergrond taak
            print('POST: door gaan met actieve mutatie is nog niet gemaakt')

        else:
            # start een nieuwe transactie op
            beschrijving = "MijnHandboogsport bestelling %s" % bestelling.bestel_nr

            rest_euro = bestelling.totaal_euro
            for transactie in bestelling.transacties:
                if transactie.is_restitutie:
                    rest_euro += transactie.bedrag_euro
                else:
                    rest_euro -= transactie.bedrag_euro
            # for

            mutatie = betaal_start_ontvangst(beschrijving, rest_euro, snel == '1')

            bestelling.actief_mutatie = mutatie
            bestelling.save(update_fields=['actief_mutatie'])

        # go to the "show progress" screen
        url = reverse('Bestel:bestelling-afrekenen',
                      kwargs={'bestel_nr': bestelling.bestel_nr})

        return HttpResponseRedirect(url)

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


        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (reverse('Bestel:toon-bestelling-details', kwargs={'bestel_nr': bestelling.bestel_nr}), 'Bestelling'),
            (None, 'Afrekenen')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
