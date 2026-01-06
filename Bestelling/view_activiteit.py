# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db.models.query_utils import Q
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.urls import reverse
from Account.models import get_account
from Bestelling.definities import (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS2STR, BESTELLING_REGEL_CODE2STR,
                                   BESTELLING_KORT_BREAK,
                                   BESTELLING_REGEL_CODE_WEBWINKEL, BESTELLING_REGEL_CODE_WEDSTRIJD,
                                   BESTELLING_REGEL_CODE_OPLEIDING, BESTELLING_REGEL_CODE_EVENEMENT)
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
            self.is_staff = get_account(self.request).is_staff
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWW, Rol.ROL_MO, Rol.ROL_MWZ)

    @staticmethod
    def _selecteer_bestellingen(context, form, zoekterm):
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
                                .prefetch_related('transacties',
                                                  'regels')
                                .filter(Q(bestel_nr=nr) |
                                        Q(account__username=nr) |
                                        Q(ontvanger__vereniging__ver_nr=nr) |
                                        Q(regels__korte_beschrijving__icontains=str(nr)))
                                .order_by('-aangemaakt',                # recent aangemaakt eerst
                                          'pk')
                                .distinct('aangemaakt', 'pk'))          # voorkom dupes
            except ValueError:
                if zoekterm == "**":
                    bestellingen = (Bestelling
                                    .objects
                                    .select_related('account',
                                                    'ontvanger',
                                                    'ontvanger__vereniging')
                                    .prefetch_related('transacties',
                                                      'regels')
                                    .filter(status__in=(BESTELLING_STATUS_NIEUW,
                                                        BESTELLING_STATUS_BETALING_ACTIEF,
                                                        BESTELLING_STATUS_MISLUKT))
                                    .order_by('-bestel_nr'))        # nieuwste eerst
                    context['zoekt_status'] = True
                else:
                    bestellingen = (Bestelling
                                    .objects
                                    .select_related('account',
                                                    'ontvanger',
                                                    'ontvanger__vereniging')
                                    .prefetch_related('transacties',
                                                      'regels')
                                    .filter(Q(account__unaccented_naam__icontains=zoekterm) |
                                            Q(ontvanger__vereniging__naam__icontains=zoekterm) |
                                            Q(regels__korte_beschrijving__icontains=zoekterm) |
                                            Q(transacties__payment_id=zoekterm))
                                    .order_by('-bestel_nr')         # nieuwste eerst
                                    .distinct('bestel_nr'))         # voorkom dupes
        else:
            # toon de nieuwste bestellingen
            context['nieuwste'] = True
            bestellingen = (Bestelling
                            .objects
                            .select_related('account',
                                            'ontvanger',
                                            'ontvanger__vereniging')
                            .prefetch_related('regels')
                            .order_by('-bestel_nr'))        # nieuwste eerst

        if form.is_bound:
            if not form.cleaned_data['webwinkel']:
                # vinkje is niet gezet, dus webwinkel producten zijn niet gewenst --> behoud waar deze None is
                bestellingen = bestellingen.exclude(regels__code=BESTELLING_REGEL_CODE_WEBWINKEL)

            if not form.cleaned_data['wedstrijden']:
                # vinkje is niet gezet, dus wedstrijd bestellingen zijn niet gewenst --> behoud waar deze None is
                bestellingen = bestellingen.exclude(regels__code=BESTELLING_REGEL_CODE_WEDSTRIJD)

            if not form.cleaned_data['evenementen']:
                # vinkje is niet gezet, dus evenement bestellingen zijn niet gewenst --> behoud waar deze None is
                bestellingen = bestellingen.exclude(regels__code=BESTELLING_REGEL_CODE_EVENEMENT)

            if not form.cleaned_data['opleidingen']:
                # vinkje is niet gezet, dus opleidingen bestellingen zijn niet gewenst --> behoud waar deze None is
                bestellingen = bestellingen.exclude(regels__code=BESTELLING_REGEL_CODE_OPLEIDING)

            if not form.cleaned_data['gratis']:
                # vinkje is niet gezet, dus gratis bestellingen zijn niet gewenst
                bestellingen = bestellingen.exclude(totaal_euro__lt=0.001)

        return bestellingen

    @staticmethod
    def _bestellingen_aankleden(bestellingen):
        for bestelling in bestellingen:
            bestelling.bestel_nr_str = bestelling.mh_bestel_nr()
            bestelling.ver_nr_str = str(bestelling.ontvanger.vereniging.ver_nr)
            bestelling.ver_naam = bestelling.ontvanger.vereniging.naam
            bestelling.status_str = BESTELLING_STATUS2STR[bestelling.status]

            bestelling.regels_list = bestelling.regels.all()

            aantal_wedstrijd = 0
            aantal_webwinkel = 0
            aantal_evenement = 0
            aantal_opleiding = 0
            laatste_wedstrijd_beschrijving = ''
            laatste_evenement_beschrijving = ''
            laatste_opleiding_beschrijving = ''

            for regel in bestelling.regels_list:

                regel.korte_beschrijving_lst = regel.korte_beschrijving.split(BESTELLING_KORT_BREAK)

                if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD:
                    aantal_wedstrijd += 1
                    laatste_wedstrijd_beschrijving = regel.korte_beschrijving_lst[0]

                elif regel.code == BESTELLING_REGEL_CODE_WEBWINKEL:
                    aantal_webwinkel += 1

                elif regel.code == BESTELLING_REGEL_CODE_EVENEMENT:
                    aantal_evenement += 1
                    laatste_evenement_beschrijving = regel.korte_beschrijving_lst[0]

                elif regel.code == BESTELLING_REGEL_CODE_OPLEIDING:
                    aantal_opleiding += 1
                    laatste_opleiding_beschrijving = regel.korte_beschrijving_lst[0]

                else:
                    regel.geen_beschrijving = True
            # for

            beschrijvingen = list()
            if aantal_webwinkel:
                beschrijvingen.append('%sx webwinkel' % aantal_webwinkel)
            if aantal_wedstrijd:
                beschrijvingen.append('%sx %s' % (aantal_wedstrijd, laatste_wedstrijd_beschrijving))
            if aantal_evenement:
                beschrijvingen.append('%sx %s' % (aantal_evenement, laatste_evenement_beschrijving))
            if aantal_opleiding:
                beschrijvingen.append('%sx %s' % (aantal_opleiding, laatste_opleiding_beschrijving))

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

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoekformulier
        context['zoek_url'] = reverse('Bestelling:activiteit')
        if len(self.request.GET.keys()) == 0:
            # no query parameters
            form = ZoekBestellingForm(initial={'webwinkel': True,
                                               'wedstrijden': True,
                                               'evenementen': True,
                                               'opleidingen': True,
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

        # bepaal het aantal bestellingen sinds het begin van de maand
        bestelling = Bestelling.objects.order_by('-aangemaakt').first()
        if bestelling:
            now = bestelling.aangemaakt
        else:
            now = timezone.now()
        context['begin_maand'] = datetime.date(day=1, month=now.month, year=now.year)
        begin_maand = datetime.datetime(day=1, month=now.month, year=now.year)
        begin_maand = timezone.make_aware(begin_maand)

        bestellingen = self._selecteer_bestellingen(context, form, zoekterm)
        qset = bestellingen.filter(aangemaakt__gte=begin_maand)
        context['aantal_bestellingen'] = qset.count()

        pks = qset.values_list('pk', flat=True)
        verkopers = Bestelling.objects.filter(pk__in=pks).order_by('ontvanger').distinct('ontvanger')
        context['aantal_verkopers'] = verkopers.count()
        # for verkoper in verkopers:
        #     print(verkoper.ontvanger)

        # details toevoegen voor de eerste 50 bestellingen deze maand
        bestellingen = list(bestellingen[:50])
        context['bestellingen'] = bestellingen

        self._bestellingen_aankleden(bestellingen)

        if self.is_staff:
            context['url_omzet'] = reverse('Bestelling:omzet')

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
    exclude_ver_nr = ()
    limited = False

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
                        .prefetch_related('regels')
                        .select_related('ontvanger__vereniging'))

        if len(self.exclude_ver_nr):
            bestellingen = bestellingen.exclude(ontvanger__vereniging__in=self.exclude_ver_nr)

        aantal = dict()         # [jaar] = integer     (aantal verkopen)
        omzet = dict()          # [jaar] = Decimal
        vers = dict()           # [jaar] = [ver_nr, ..]
        jaar_aantal = dict()    # [jaar] = integer (aantal verkopen)
        jaar_omzet = dict()     # [jaar] = Decimal
        jaar_vers = dict()      # [jaar] = [ver_nr, ..]
        jaar_code = dict()      # [(jaar, code)] = integer
        jaar_maanden = dict()   # [jaar] = [maand nr, ..]

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

                jaar = bestelling.aangemaakt.year
                try:
                    jaar_aantal[jaar] += 1
                    jaar_omzet[jaar] += bestelling.totaal_euro
                    if ver_nr not in jaar_vers[jaar]:
                        jaar_vers[jaar].append(ver_nr)
                except KeyError:
                    jaar_aantal[jaar] = 1
                    jaar_omzet[jaar] = bestelling.totaal_euro
                    jaar_vers[jaar] = [ver_nr]

                for regel in bestelling.regels.all():
                    tup = (jaar, regel.code)
                    try:
                        jaar_code[tup] += 1
                    except KeyError:
                        jaar_code[tup] = 1
                # for

                maand = bestelling.aangemaakt.month
                try:
                    if maand not in jaar_maanden[jaar]:
                        jaar_maanden[jaar].append(maand)
                except KeyError:
                    jaar_maanden[jaar] = [maand]
        # for

        lijst = [(datetime.date(tup[0], tup[1], 1), aantal[tup], omzet[tup], len(vers[tup])) for tup in aantal.keys()]
        lijst.sort(reverse=True)        # nieuwste bovenaan
        context['lijst'] = lijst

        codes = list(set([code for _, code in jaar_code.keys()]))
        codes.sort()
        context['codes'] = [BESTELLING_REGEL_CODE2STR[code]
                            for code in codes]

        per_jaar = list()
        jaren = set(list(jaar_aantal.keys()) + list(jaar_omzet.keys()))
        for jaar in jaren:
            aantallen = list()
            for code in codes:
                try:
                    code_aantal = jaar_code[(jaar, code)]
                except KeyError:
                    code_aantal = '-'
                aantallen.append(code_aantal)
            # for
            tup = (jaar, len(jaar_maanden[jaar]), jaar_aantal[jaar], jaar_omzet[jaar], len(jaar_vers[jaar]), aantallen)
            per_jaar.append(tup)
        # for
        per_jaar.sort(reverse=True)        # nieuwste bovenaan
        context['per_jaar'] = per_jaar

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

        context['limited'] = self.limited
        if self.limited:
            context['url_limited'] = reverse('Bestelling:omzet')
        else:
            context['url_limited'] = reverse('Bestelling:omzet-leden')

        context['kruimels'] = (
            (reverse('Bestelling:activiteit'), 'Bestellingen en Betalingen'),
            (None, 'Omzet')
        )

        return context


class BestelOmzetAllesView(BestelOmzetView):
    exclude_ver_nr = ()
    limited = False


class BestelOmzetLedenView(BestelOmzetView):
    exclude_ver_nr = (settings.WEBWINKEL_VERKOPER_VER_NR,)
    limited = True


# end of file
