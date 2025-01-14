# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db.models.query_utils import Q
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.urls import reverse
from Account.models import get_account
from Bestelling.definities import (BESTELLING_STATUS2STR, BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_MISLUKT)
from Bestelling.forms import ZoekBestellingForm
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_PAYMENT
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
import datetime

TEMPLATE_BESTEL_ACTIVITEIT = 'bestelling/activiteit.dtl'
TEMPLATE_BESTEL_OMZET = 'bestelling/omzet.dtl'


class BestelActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de activiteiten van de gebruikers """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTEL_ACTIVITEIT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.is_staff = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        if self.rol_nu == Rol.ROL_BB:
            account = get_account(self.request)
            self.is_staff = account.is_staff
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWW)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoekformulier
        context['zoek_url'] = reverse('Bestel:activiteit')
        if len(self.request.GET.keys()) == 0:
            # no query parameters
            form = ZoekBestellingForm(initial={'webwinkel': True,
                                               'wedstrijden': True,
                                               'evenementen': True,
                                               'gratis': True})
        else:
            form = ZoekBestellingForm(self.request.GET)
            form.full_clean()   # vult form.cleaned_data
        context['zoekform'] = form

        if form.is_bound:
            try:
                zoekterm = form.cleaned_data['zoekterm']
            except KeyError:
                # hier komen we als het form field niet valide was, bijvoorbeeld veel te lang
                zoekterm = ""
        else:
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
                                .prefetch_related('transacties')
                                .filter(Q(bestel_nr=nr) |
                                        Q(account__username=nr) |
                                        Q(ontvanger__vereniging__ver_nr=nr) |
                                        Q(producten__wedstrijd_inschrijving__sporterboog__sporter__lid_nr=nr))
                                .order_by('-aangemaakt'))             # nieuwste eerst (werkt beter op test server)
                                # .order_by('-bestel_nr'))            # nieuwste eerst
            except ValueError:
                if zoekterm == "**":
                    bestellingen = (Bestelling
                                    .objects
                                    .select_related('account',
                                                    'ontvanger',
                                                    'ontvanger__vereniging')
                                    .prefetch_related('transacties')
                                    .filter(status__in=(BESTELLING_STATUS_NIEUW,
                                                        BESTELLING_STATUS_BETALING_ACTIEF,
                                                        BESTELLING_STATUS_MISLUKT))
                                    .order_by('-bestel_nr'))            # nieuwste eerst
                    context['zoekt_status'] = True
                else:
                    bestellingen = (Bestelling
                                    .objects
                                    .select_related('account',
                                                    'ontvanger',
                                                    'ontvanger__vereniging')
                                    .prefetch_related('transacties')
                                    .filter(Q(account__unaccented_naam__icontains=zoekterm) |
                                            Q(ontvanger__vereniging__naam__icontains=zoekterm) |
                                            Q(producten__wedstrijd_inschrijving__sporterboog__sporter__unaccented_naam__icontains=zoekterm) |
                                            Q(producten__webwinkel_keuze__product__omslag_titel__icontains=zoekterm) |
                                            Q(transacties__payment_id=zoekterm))
                                    .order_by('-bestel_nr'))            # nieuwste eerst
        else:
            # toon de nieuwste bestellingen
            context['nieuwste'] = True
            bestellingen = (Bestelling
                            .objects
                            .select_related('account',
                                            'ontvanger',
                                            'ontvanger__vereniging')
                            .order_by('-bestel_nr'))     # nieuwste eerst

        bestellingen = bestellingen.distinct('bestel_nr')       # verwijder dupes

        if form.is_bound:
            if not form.cleaned_data['webwinkel']:
                # vinkje is niet gezet, dus webwinkel producten zijn niet gewenst --> behoud waar deze None is
                bestellingen = bestellingen.filter(producten__webwinkel_keuze=None)

            if not form.cleaned_data['wedstrijden']:
                # vinkje is niet gezet, dus wedstrijd bestellingen zijn niet gewenst --> behoud waar deze None is
                bestellingen = bestellingen.filter(producten__wedstrijd_inschrijving=None)

            if not form.cleaned_data['evenementen']:
                # vinkje is niet gezet, dus evenement bestellingen zijn niet gewenst --> behoud waar deze None is
                bestellingen = bestellingen.filter(producten__evenement_inschrijving=None,
                                                   producten__evenement_afgemeld=None)

            if not form.cleaned_data['gratis']:
                # vinkje is niet gezet, dus gratis bestellingen zijn niet gewenst
                bestellingen = bestellingen.exclude(totaal_euro__lt=0.001)

        # bepaal het aantal bestellingen sinds het begin van de maand
        now = timezone.now()
        context['begin_maand'] = datetime.date(day=1, month=now.month, year=now.year)
        begin_maand = datetime.datetime(day=1, month=now.month, year=now.year)
        begin_maand = timezone.make_aware(begin_maand)

        qset = bestellingen.filter(aangemaakt__gte=begin_maand)
        context['aantal_bestellingen'] = qset.count()

        pks = qset.values_list('pk', flat=True)
        verkopers = Bestelling.objects.filter(pk__in=pks).order_by('ontvanger').distinct('ontvanger')
        context['aantal_verkopers'] = verkopers.count()

        # details toevoegen voor de eerste 50 bestellingen deze maand
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
                                                         'webwinkel_keuze__koper',
                                                         'evenement_inschrijving__evenement',
                                                         'evenement_inschrijving__evenement__organiserende_vereniging',
                                                         'evenement_inschrijving__sporter',
                                                         'evenement_afgemeld__evenement',
                                                         'evenement_afgemeld__evenement__organiserende_vereniging',
                                                         'evenement_afgemeld__sporter')
                                         .all())

            aantal_wedstrijd = 0
            aantal_webwinkel = 0
            aantal_evenement = 0
            laatste_wedstrijd_beschrijving = ''
            laatste_evenement_beschrijving = ''

            for product in bestelling.prods_list:

                if product.wedstrijd_inschrijving:
                    aantal_wedstrijd += 1
                    inschrijving = product.wedstrijd_inschrijving
                    product.beschrijving_str1 = 'Wedstrijd bij %s' % inschrijving.wedstrijd.organiserende_vereniging.ver_nr_en_naam()
                    product.beschrijving_str2 = 'voor %s (%s)' % (
                        inschrijving.sporterboog.sporter.lid_nr_en_volledige_naam(),
                        inschrijving.sporterboog.boogtype.beschrijving)
                    product.beschrijving_str3 = inschrijving.wedstrijd.titel

                    laatste_wedstrijd_beschrijving = product.beschrijving_str3

                elif product.webwinkel_keuze:
                    aantal_webwinkel += 1
                    keuze = product.webwinkel_keuze
                    product.beschrijving_str2 = keuze.product.omslag_titel

                elif product.evenement_inschrijving:
                    aantal_evenement += 1

                    inschrijving = product.evenement_inschrijving
                    product.beschrijving_str1 = 'Evenement bij %s' % inschrijving.evenement.organiserende_vereniging.ver_nr_en_naam()
                    product.beschrijving_str2 = 'voor %s' % inschrijving.sporter.lid_nr_en_volledige_naam()
                    product.beschrijving_str3 = inschrijving.evenement.titel

                    laatste_evenement_beschrijving = product.beschrijving_str3

                elif product.evenement_afgemeld:
                    aantal_evenement += 1

                    inschrijving = product.evenement_afgemeld
                    product.beschrijving_str1 = 'Evenement bij %s' % inschrijving.evenement.organiserende_vereniging.ver_nr_en_naam()
                    product.beschrijving_str2 = 'voor %s' % inschrijving.sporter.lid_nr_en_volledige_naam()
                    product.beschrijving_str3 = inschrijving.evenement.titel

                    laatste_evenement_beschrijving = product.beschrijving_str3

                else:
                    product.geen_beschrijving = True
            # for

            beschrijvingen = list()
            if aantal_webwinkel:
                beschrijvingen.append('%sx webwinkel' % aantal_webwinkel)
            if aantal_wedstrijd:
                beschrijvingen.append('%sx %s' % (aantal_wedstrijd, laatste_wedstrijd_beschrijving))
            if aantal_evenement:
                beschrijvingen.append('%sx %s' % (aantal_evenement, laatste_evenement_beschrijving))

            bestelling.beschrijving_kort = " + ".join(beschrijvingen) if len(beschrijvingen) else "?"

            bestelling.trans_list = list()
            transactie_mollie = None
            for transactie in bestelling.transacties.order_by('when'):     # oudste eerst

                if transactie.transactie_type == TRANSACTIE_TYPE_MOLLIE_PAYMENT:
                    # alleen de laatste tonen
                    transactie_mollie = transactie
                else:
                    bestelling.trans_list.append(('Transactie', transactie))
            # for

            if transactie_mollie:
                bestelling.trans_list.append(('Mollie status', transactie_mollie))
        # for

        if self.is_staff:
            context['url_omzet'] = reverse('Bestel:omzet')

        if self.rol_nu == Rol.ROL_MWW:
            context['kruimels'] = (
                (reverse('Webwinkel:manager'), 'Webwinkel'),
                (None, 'Bestellingen en Betalingen'),
            )
        else:
            context['kruimels'] = (
                (None, 'Bestellingen en Betalingen'),
            )

        return context


class BestelOmzetView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor overzicht omzet over de afgelopen maanden """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTEL_OMZET
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rol.ROL_BB:
            account = get_account(self.request)
            return account.is_staff
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        bestellingen = (Bestelling
                        .objects
                        .select_related('ontvanger__vereniging'))

        aantal = dict()     # [(jaar, maand)] = integer     (aantal verkopen)
        omzet = dict()      # [(jaar, maand)] = Decimal
        vers = dict()       # [(jaar, maand)] = [ver_nr, ..]
        for bestelling in bestellingen:
            tup = (bestelling.aangemaakt.year, bestelling.aangemaakt.month)
            ver_nr = bestelling.ontvanger.vereniging.ver_nr

            if bestelling.totaal_euro > 0:
                try:
                    aantal[tup] += 1
                    omzet[tup] += bestelling.totaal_euro
                    if ver_nr not in vers[tup]:
                        vers[tup].append(ver_nr)
                except KeyError:
                    aantal[tup] = 1
                    omzet[tup] = bestelling.totaal_euro
                    vers[tup] = [ver_nr]
        # for

        lijst = [(datetime.date(tup[0], tup[1], 1), aantal[tup], omzet[tup], len(vers[tup])) for tup in aantal.keys()]
        lijst.sort(reverse=True)        # nieuwste bovenaan
        context['lijst'] = lijst

        context['totaal_aantal'] = sum(aantal.values())
        context['totaal_omzet'] = sum(omzet.values())

        uniek_vers = list()
        for ver_nrs in vers.values():
            for ver_nr in ver_nrs:
                if ver_nr not in uniek_vers:
                    uniek_vers.append(ver_nr)
            # for
        # for
        context['totaal_vers'] = len(uniek_vers)

        context['kruimels'] = (
            (reverse('Bestel:activiteit'), 'Bestellingen en Betalingen'),
            (None, 'Omzet')
        )

        return context


# end of file
