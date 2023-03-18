# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db.models.query_utils import Q
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.urls import reverse
from Bestel.definities import (BESTELLING_STATUS2STR, BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_WACHT_OP_BETALING,
                               BESTELLING_STATUS_MISLUKT)
from Bestel.forms import ZoekAccountForm
from Bestel.models import Bestelling
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Plein.menu import menu_dynamics
import datetime

TEMPLATE_BESTEL_ACTIVITEIT = 'bestel/activiteit.dtl'


class BestelActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de activiteiten van de gebruikers """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTEL_ACTIVITEIT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_MWW)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoekformulier
        context['zoek_url'] = reverse('Bestel:activiteit')
        context['zoekform'] = form = ZoekAccountForm(self.request.GET)
        form.full_clean()   # vult form.cleaned_data

        try:
            zoekterm = form.cleaned_data['zoekterm']
        except KeyError:
            # hier komen we als het form field niet valide was, bijvoorbeeld veel te lang
            zoekterm = ""
        context['zoekterm'] = zoekterm

        bestellingen = list()
        if len(zoekterm) >= 2:  # minimaal twee cijfers/tekens van de naam/nummer
            try:
                # strip "MH-"
                zoekterm = zoekterm.strip()
                if zoekterm[:3].upper() == 'MH-':
                    zoekterm = zoekterm[3:]

                nr = int(zoekterm[:7])      # afkappen voor de veiligheid (bestel_nr = 7 pos)
                bestellingen = (Bestelling
                                .objects
                                .select_related('account',
                                                'ontvanger',
                                                'ontvanger__vereniging')
                                .filter(Q(bestel_nr=nr) |
                                        Q(account__username=nr) |
                                        Q(ontvanger__vereniging__ver_nr=nr) |
                                        Q(producten__wedstrijd_inschrijving__sporterboog__sporter__lid_nr=nr))
                                .order_by('-bestel_nr'))            # nieuwste eerst
            except ValueError:
                if zoekterm == "**":
                    bestellingen = (Bestelling
                                    .objects
                                    .select_related('account',
                                                    'ontvanger',
                                                    'ontvanger__vereniging')
                                    .filter(status__in=(BESTELLING_STATUS_NIEUW,
                                                        BESTELLING_STATUS_WACHT_OP_BETALING,
                                                        BESTELLING_STATUS_MISLUKT))
                                    .order_by('-bestel_nr'))            # nieuwste eerst
                    context['zoekt_status'] = True
                else:
                    bestellingen = (Bestelling
                                    .objects
                                    .select_related('account',
                                                    'ontvanger',
                                                    'ontvanger__vereniging')
                                    .filter(Q(account__unaccented_naam__icontains=zoekterm) |
                                            Q(ontvanger__vereniging__naam__icontains=zoekterm) |
                                            Q(producten__wedstrijd_inschrijving__sporterboog__sporter__unaccented_naam__icontains=zoekterm) |
                                            Q(producten__webwinkel_keuze__product__omslag_titel__icontains=zoekterm))
                                    .order_by('-bestel_nr'))            # nieuwste eerst
        else:
            # toon de 50 nieuwste bestellingen
            context['nieuwste'] = True
            bestellingen = (Bestelling
                            .objects
                            .select_related('account',
                                            'ontvanger',
                                            'ontvanger__vereniging')
                            .order_by('-bestel_nr'))                # nieuwste eerst

        bestellingen = bestellingen.distinct('bestel_nr')       # verwijder dupes

        context['bestellingen'] = list(bestellingen[:50])
        for bestelling in context['bestellingen']:
            bestelling.bestel_nr_str = bestelling.mh_bestel_nr()
            bestelling.ver_nr_str = str(bestelling.ontvanger.vereniging.ver_nr)
            bestelling.ver_naam = bestelling.ontvanger.vereniging.naam
            bestelling.status_str = BESTELLING_STATUS2STR[bestelling.status]

            bestelling.prods_list = list(bestelling
                                         .producten
                                         .select_related('wedstrijd_inschrijving',
                                                         'wedstrijd_inschrijving__wedstrijd',
                                                         'wedstrijd_inschrijving__wedstrijd__organiserende_vereniging',
                                                         'wedstrijd_inschrijving__sporterboog__sporter',
                                                         'wedstrijd_inschrijving__sporterboog__boogtype',
                                                         'webwinkel_keuze',
                                                         'webwinkel_keuze__product',
                                                         'webwinkel_keuze__koper')
                                         .all())

            aantal_wedstrijd = 0
            aantal_webwinkel = 0
            laatste_wedstrijd_beschrijving = ''

            for product in bestelling.prods_list:

                if product.wedstrijd_inschrijving:
                    aantal_wedstrijd += 1
                    inschrijving = product.wedstrijd_inschrijving
                    product.beschrijving_str1 = 'Wedstrijd bij %s' % inschrijving.wedstrijd.organiserende_vereniging.ver_nr_en_naam()
                    product.beschrijving_str2 = 'voor %s (%s)' % (
                        inschrijving.sporterboog.sporter.lid_nr_en_volledige_naam(),
                        inschrijving.sporterboog.boogtype.beschrijving)
                    product.beschrijving_str3 = inschrijving.wedstrijd.titel
                    laatste_wedstrijd_beschrijving = product.beschrijving_str1

                elif product.webwinkel_keuze:
                    aantal_webwinkel += 1
                    keuze = product.webwinkel_keuze
                    product.beschrijving_str2 = keuze.product.omslag_titel

                else:
                    product.geen_beschrijving = True
            # for

            beschrijvingen = list()
            if aantal_webwinkel:
                beschrijvingen.append('%sx webwinkel' % aantal_webwinkel)
            if aantal_wedstrijd:
                beschrijvingen.append('%sx %s' % (aantal_wedstrijd, laatste_wedstrijd_beschrijving))

            if len(beschrijvingen):
                bestelling.beschrijving_kort = " + ".join(beschrijvingen)
            else:
                bestelling.beschrijving_kort = '?'

            bestelling.trans_list = list(bestelling
                                         .transacties
                                         .all())

            # for transactie in bestelling.trans_list:
            #     pass
            # # for

        # for

        if self.rol_nu == Rollen.ROL_MWW:
            context['kruimels'] = (
                (reverse('Webwinkel:manager'), 'Webwinkel'),
                (None, 'Bestellingen en Betalingen'),
            )
        else:
            context['kruimels'] = (
                (None, 'Bestellingen en Betalingen'),
            )

        now = timezone.now()

        context['begin_maand'] = datetime.date(day=1, month=now.month, year=now.year)

        begin_maand = datetime.datetime(day=1, month=now.month, year=now.year)
        begin_maand = timezone.make_aware(begin_maand)

        qset = Bestelling.objects.filter(aangemaakt__gte=begin_maand)

        context['aantal_bestellingen'] = qset.count()
        context['aantal_verkopers'] = qset.distinct('ontvanger').count()

        menu_dynamics(self.request, context)
        return context


# end of file
