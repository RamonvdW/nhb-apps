# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestelling.definities import BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD
from Bestelling.models import Bestelling
from Bestelling.operations.mutaties import bestel_overboeking_ontvangen
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie
from decimal import Decimal, InvalidOperation

TEMPLATE_OVERBOEKING_ONTVANGEN = 'bestelling/overboeking-ontvangen.dtl'


class OverboekingOntvangenView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERBOEKING_ONTVANGEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_MWW)

    def _zoek_overboekingen(self):
        overboekingen = list()
        for bestelling in (Bestelling
                           .objects
                           .filter(ontvanger__vereniging__ver_nr=self.functie_nu.vereniging.ver_nr)
                           .prefetch_related('transacties')
                           .order_by('-aangemaakt'))[:250]:         # nieuwste eerst

            # handmatige overboekingen zoeken
            for transactie in bestelling.transacties.filter(is_handmatig=True):
                transactie.bestelling = bestelling
                overboekingen.append(transactie)
            # for

            if len(overboekingen) >= 100:       # pragma: no cover
                break
        # for

        return overboekingen

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.vereniging

        context['overboekingen'] = self._zoek_overboekingen()
        context['kenmerk'] = context['bedrag'] = ''

        context['url_opslaan'] = reverse('Bestel:overboeking-ontvangen')

        if self.rol_nu == Rollen.ROL_MWW:
            context['kruimels'] = (
                (reverse('Webwinkel:manager'), 'Webwinkel'),
                (None, 'Overboekingen'),
            )
        else:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (None, 'Overboekingen'),
            )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruiken op Opslaan drukt. """

        context = dict()

        context['ver'] = self.functie_nu.vereniging
        context['url_opslaan'] = reverse('Bestel:overboeking-ontvangen')

        actie = request.POST.get('actie', '')[:5]
        bedrag = request.POST.get('bedrag', '')[:20].strip()
        kenmerk = request.POST.get('kenmerk', '')[:10].strip()

        # controleer het kenmerk
        bestelling = None
        try:
            bestel_nr = int(kenmerk)
            bestelling = Bestelling.objects.select_related('ontvanger__vereniging').get(bestel_nr=bestel_nr)
        except (ValueError, Bestelling.DoesNotExist):
            context['kenmerk'] = ''
            context['fout_kenmerk'] = 'Bestelnummer wordt niet herkend'
        else:
            context['kenmerk'] = '%07d' % bestelling.bestel_nr      # %07d restores to 7 digits with prefix zeros

        # controleer het bedrag
        try:
            bedrag = bedrag.replace(',', '.')       # regional --> system
            bedrag_euro = Decimal(bedrag)
        except InvalidOperation:
            context['bedrag'] = ''
            if bestelling:
                context['fout_bedrag'] = ('Verwacht bedrag: € %.2f' % bestelling.totaal_euro).replace('.', ',')
            else:
                context['fout_bedrag'] = 'Voer het ontvangen bedrag in'
        else:
            context['bedrag'] = ("%.2f" % bedrag_euro).replace('.', ',')    # system --> regional

            if bestelling:
                if bestelling.ontvanger.vereniging.ver_nr != self.functie_nu.vereniging.ver_nr:
                    context['fout_kenmerk'] = 'Bestelnummer is niet voor jullie vereniging'

                elif bestelling.status == BESTELLING_STATUS_AFGEROND:
                    context['fout_kenmerk'] = 'Betaling is al geregistreerd'

                elif bestelling.status == BESTELLING_STATUS_GEANNULEERD:
                    context['fout_kenmerk'] = 'Bestelling is geannuleerd'

                else:
                    verschil_euro = abs(bestelling.totaal_euro - bedrag_euro)
                    mag_afwijken = request.POST.get('accept_bedrag', False)
                    if verschil_euro < Decimal('0.01') or mag_afwijken:
                        if actie == 'regis':  # afgekapte 'registreer'
                            # gebruiker heeft gevraagd om op te slaan
                            snel = str(request.POST.get('snel', ''))[:1]
                            bestel_overboeking_ontvangen(bestelling, bedrag_euro, snel == '1')

                            # geef weer een lege invoer
                            context['bedrag'] = ''
                            context['kenmerk'] = ''
                        else:
                            context['was_foutvrij'] = True
                            context['akkoord_afwijking'] = mag_afwijken

                    else:
                        context['fout_bedrag'] = ('Verwacht bedrag: € %.2f' % bestelling.totaal_euro).replace('.', ',')

        context['overboekingen'] = self._zoek_overboekingen()

        if self.rol_nu == Rollen.ROL_MWW:
            context['kruimels'] = (
                (reverse('Webwinkel:manager'), 'Webwinkel'),
                (None, 'Overboekingen'),
            )
        else:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (None, 'Overboekingen'),
            )

        return render(request, TEMPLATE_OVERBOEKING_ONTVANGEN, context)


# end of file
