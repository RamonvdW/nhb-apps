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
from Plein.menu import menu_dynamics
from .models import KalenderWedstrijd, KalenderInschrijving, INSCHRIJVING_STATUS_TO_STR, INSCHRIJVING_STATUS_AFGEMELD
from decimal import Decimal


TEMPLATE_KALENDER_AANMELDINGEN = 'kalender/aanmeldingen.dtl'


class KalenderAanmeldingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf inschrijven voor een wedstrijd """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_AANMELDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_BB)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=wedstrijd_pk))
        except KalenderWedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        aanmeldingen = (KalenderInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .select_related('sessie',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'gebruikte_code')
                        .order_by('sessie',
                                  'status'))
        context['aanmeldingen'] = aanmeldingen

        totaal_ontvangen_euro = Decimal('0')
        totaal_retour_euro = Decimal('0')

        aantal_aanmeldingen = 0
        aantal_afmeldingen = 0
        for aanmelding in aanmeldingen:

            if aanmelding.status != INSCHRIJVING_STATUS_AFGEMELD:
                aantal_aanmeldingen += 1
                aanmelding.volg_nr = aantal_aanmeldingen

                aanmelding.bib = aanmelding.pk + settings.TICKET_NUMMER_START__WEDSTRIJD
            else:
                aantal_afmeldingen += 1

            aanmelding.status_str = INSCHRIJVING_STATUS_TO_STR[aanmelding.status]

            aanmelding.sporter_str = aanmelding.sporterboog.sporter.lid_nr_en_volledige_naam()

            aanmelding.boog_str = aanmelding.sporterboog.boogtype.beschrijving

            aanmelding.korting_str = 'geen'
            if aanmelding.gebruikte_code:
                aanmelding.korting_str = '%s%%' % aanmelding.gebruikte_code.percentage

            totaal_ontvangen_euro += aanmelding.ontvangen_euro
            totaal_retour_euro += aanmelding.retour_euro
        # for

        context['totaal_euro'] = totaal_ontvangen_euro - totaal_retour_euro
        context['totaal_ontvangen_euro'] = totaal_ontvangen_euro
        context['totaal_retour_euro'] = totaal_retour_euro
        context['aantal_aanmeldingen'] = aantal_aanmeldingen
        context['aantal_afmeldingen'] = aantal_afmeldingen

        if self.rol_nu == Rollen.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Kalender:vereniging'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )
        else:
            context['kruimels'] = (
                (reverse('Kalender:manager'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )

        menu_dynamics(self.request, context, 'kalender')
        return context


# end of file
