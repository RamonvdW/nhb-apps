# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import transaction
from django.conf import settings
from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import GESLACHT2STR
from Bestel.definities import BESTELLING_STATUS2STR
from Bestel.models import BestelMandje, Bestelling
from Functie.rol import rol_get_huidige_functie
from Mailer.operations import render_email_template, mailer_queue_email
from Overig.helpers import get_safe_from_ip
from Registreer.definities import REGISTRATIE_FASE_AFGEWEZEN
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from Wedstrijden.definities import INSCHRIJVING_STATUS_DEFINITIEF, INSCHRIJVING_STATUS_TO_STR
from Wedstrijden.models import WedstrijdInschrijving
import logging

TEMPLATE_GAST_ACCOUNTS = 'registreer/beheer-gast-accounts.dtl'
TEMPLATE_GAST_ACCOUNT_DETAILS = 'registreer/beheer-gast-account-details.dtl'
EMAIL_TEMPLATE_GAST_AFGEWEZEN = 'email_registreer/gast-afgewezen.dtl'

my_logger = logging.getLogger('MH.Registreer')


class GastAccountsView(UserPassesTestMixin, TemplateView):
    """ Deze view laat de SEC van vereniging 8000 de gast-accounts lijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_GAST_ACCOUNTS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        context['gasten'] = gasten = list()
        context['afgewezen'] = afgewezen = list()

        for gast in (GastRegistratie
                     .objects
                     .select_related('sporter',
                                     'account')
                     .order_by('-aangemaakt')):  # nieuwste eerst

            # zoek de laatste-inlog bij elk lid
            # SEC mag de voorkeuren van de sporters aanpassen
            if gast.lid_nr > 0:
                gast.url_details = reverse('Registreer:beheer-gast-account-details',
                                           kwargs={'lid_nr': gast.lid_nr})

            gast.geen_inlog = 0
            if gast.account:
                if gast.account.last_login:
                    gast.laatste_inlog = gast.account.last_login
                else:
                    gast.geen_inlog = 2
            else:
                # onvoltooid account
                gast.geen_inlog = 1

            if gast.fase == REGISTRATIE_FASE_AFGEWEZEN:
                afgewezen.append(gast)
            else:
                gasten.append(gast)
        # for

        context['heeft_afgewezen'] = len(afgewezen) > 0

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, "Gast accounts")
        )

        return context


class GastAccountDetailsView(UserPassesTestMixin, TemplateView):
    """ Deze view laat de SEC van vereniging 8000 de details van een gast-accounts zien """

    # class variables shared by all instances
    template_name = TEMPLATE_GAST_ACCOUNT_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    @staticmethod
    def _zoek_matches(gast, context):
        # zoek naar overeenkomst in CRM
        try:
            eigen_lid_nr = int(gast.eigen_lid_nummer)
        except ValueError:
            pks1 = list()
        else:
            pks1 = list(Sporter
                        .objects
                        .exclude(is_gast=True)
                        .filter(lid_nr=eigen_lid_nr)
                        .values_list('pk', flat=True))

        if gast.wa_id:
            pks2 = list(Sporter
                        .objects
                        .exclude(is_gast=True)
                        .filter(wa_id=gast.wa_id)
                        .values_list('pk', flat=True))
        else:
            pks2 = list()

        pks3 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(achternaam__iexact=gast.achternaam)
                    .values_list('pk', flat=True))

        pks4 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(voornaam__iexact=gast.voornaam)
                    .values_list('pk', flat=True))

        pks5 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(geboorte_datum=gast.geboorte_datum)
                    .values_list('pk', flat=True))

        pks6 = list(Sporter
                    .objects
                    .exclude(is_gast=True)
                    .filter(email__iexact=gast.email)
                    .values_list('pk', flat=True))

        match_count = dict()    # [pk] = count
        for pk in pks1 + pks2 + pks3 + pks4 + pks5 + pks6:
            try:
                match_count[pk] += 1
            except KeyError:
                match_count[pk] = 1
        # for

        best = list()
        for pk, count in match_count.items():
            tup = (count, pk)
            best.append(tup)
        # for
        best.sort(reverse=True)     # hoogste eerst

        beste_pks = [pk for count, pk in best[:10] if count > 1]

        context['heeft_matches'] = len(beste_pks) > 0
        context['overzetten_naar_lid_nr'] = None
        hoogste_ophef = 0

        matches = (Sporter
                   .objects
                   .select_related('account',
                                   'bij_vereniging')
                   .filter(pk__in=beste_pks))
        for match in matches:
            match.is_match_geboorte_datum = match.geboorte_datum == gast.geboorte_datum
            match.is_match_email = match.email.lower() == gast.email.lower()

            match.is_match_lid_nr = gast.eigen_lid_nummer == str(match.lid_nr)
            match.is_match_geslacht = gast.geslacht == match.geslacht
            match.is_match_voornaam = gast.voornaam.upper() in match.voornaam.upper()
            match.is_match_achternaam = gast.achternaam.upper() in match.achternaam.upper()

            if match.bij_vereniging:
                match.vereniging_str = match.bij_vereniging.ver_nr_en_naam()
                match.is_match_vereniging = gast.club.upper() in match.vereniging_str.upper()

                match.plaats_str = match.bij_vereniging.plaats
                match.is_match_plaats = (gast.club_plaats.upper().replace('-', ' ') in
                                         match.plaats_str.upper().replace('-', ' '))
            else:
                match.is_match_vereniging = False
                match.is_match_plaats = False

            match.heeft_account = (match.account is not None)

            match.ophef = 0

            if match.is_match_geboorte_datum:
                match.ophef += 1
            if match.is_match_email:
                match.ophef += 5
            if match.is_match_lid_nr:
                match.ophef += 5
            if match.is_match_voornaam:
                match.ophef += 1
            if match.is_match_achternaam:
                match.ophef += 1
            if match.is_match_geslacht:
                match.ophef += 1
            if match.is_match_vereniging:
                match.ophef += 1
            if match.is_match_plaats:
                match.ophef += 1
            if match.heeft_account:
                match.ophef += 5

            if match.ophef > hoogste_ophef:         # pragma: no branch
                context['overzetten_naar_lid_nr'] = match.lid_nr
                hoogste_ophef = match.ophef

            gast.ophef += match.ophef
        # for

        context['sporter_matches'] = matches

        for sporter in context['sporter_matches']:
            sporter.geslacht_str = GESLACHT2STR[sporter.geslacht]
        # for

    @staticmethod
    def _zoek_gebruik(gast, context):
        # zoek naar gebruik van het gast-account

        # zoek bestellingen / aankopen
        context['gast_mandje'] = BestelMandje.objects.filter(account=gast.account).first()
        context['gast_bestellingen'] = (Bestelling
                                        .objects
                                        .filter(account=gast.account)
                                        .order_by('-aangemaakt')        # nieuwste eerst
                                        .select_related('account')
                                        [:10])

        for bestelling in context['gast_bestellingen']:
            bestelling.status_str = BESTELLING_STATUS2STR[bestelling.status]
        # for

        # zoek inschrijvingen (er is geen bestelling van indien betaald door iemand anders)
        context['gast_wedstrijden'] = (WedstrijdInschrijving
                                       .objects
                                       .filter(sporterboog__sporter=gast.sporter)
                                       .select_related('wedstrijd')
                                       [:10])

        for inschrijving in context['gast_wedstrijden']:
            inschrijving.status_str = INSCHRIJVING_STATUS_TO_STR[inschrijving.status]
            if inschrijving.status == INSCHRIJVING_STATUS_DEFINITIEF:
                gast.ophef = -100
        # for

        if gast.ophef < 0 and context['overzetten_naar_lid_nr']:
            context['overzetten_url'] = reverse('Registreer:bestellingen-overzetten',
                                                kwargs={'van_lid_nr': gast.sporter.lid_nr,
                                                        'naar_lid_nr': context['overzetten_naar_lid_nr']})

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        lid_nr = kwargs['lid_nr'][:6]       # afkappen voor extra veiligheid
        try:
            lid_nr = int(lid_nr)
            gast = GastRegistratie.objects.select_related('account', 'sporter').get(lid_nr=lid_nr)
        except (ValueError, GastRegistratie.DoesNotExist):
            raise Http404('Slechte parameter')

        gast.geslacht_str = GESLACHT2STR[gast.geslacht]
        context['gast'] = gast

        gast.ophef = 0
        self._zoek_matches(gast, context)
        self._zoek_gebruik(gast, context)

        if not gast.account:
            delta = timezone.now() - gast.aangemaakt
            gast.dagen_geleden = delta.days

        if gast.fase == REGISTRATIE_FASE_AFGEWEZEN:
            gast.is_afgewezen = True
        elif gast.ophef >= 4:
            gast.url_ophef = reverse('Registreer:opheffen')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Registreer:beheer-gast-accounts'), "Gast accounts"),
            (None, "Gast account details")
        )

        return context


class GastAccountOpheffenView(UserPassesTestMixin, View):

    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de SEC8000 op de Opheffen knop drukt + modaal bevestigd heeft """

        lid_nr = request.POST.get('lid_nr', '')[:6]  # afkappen voor extra veiligheid
        try:
            lid_nr = int(lid_nr)
            gast = GastRegistratie.objects.get(lid_nr=lid_nr)
        except (ValueError, GastRegistratie.DoesNotExist):
            raise Http404('Niet gevonden')

        if gast.fase != REGISTRATIE_FASE_AFGEWEZEN:
            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            account = get_account(request)
            beheerder_naam = account.get_account_full_name()

            with transaction.atomic():
                gast.fase = REGISTRATIE_FASE_AFGEWEZEN
                gast.logboek += '[%s] %s in de rol van %s heeft dit gast-account afgewezen\n' % (
                                        stamp_str, beheerder_naam, self.functie_nu.beschrijving)
                gast.save(update_fields=['fase', 'logboek'])

                if gast.account:
                    gast.account.is_active = False
                    gast.account.save(update_fields=['is_active'])

                if gast.sporter:
                    gast.sporter.is_actief_lid = False
                    gast.sporter.save(update_fields=['is_actief_lid'])

            # schrijf in syslog
            from_ip = get_safe_from_ip(request)
            my_logger.info('%s REGISTREER gast-account %s afgewezen door %s; stuur e-mail' % (
                                from_ip, gast.lid_nr, beheerder_naam))

            # stuur een e-mail over de afwijzing
            context = {
                'voornaam': gast.voornaam,
                'gast_lid_nr': gast.lid_nr,
                'naam_site': settings.NAAM_SITE,
                'contact_email': settings.EMAIL_BONDSBUREAU,
            }
            mail_body = render_email_template(context, EMAIL_TEMPLATE_GAST_AFGEWEZEN)

            # stuur de e-mail
            mailer_queue_email(gast.email,
                               'Gast-account afgewezen',
                               mail_body)

        return HttpResponseRedirect(reverse('Registreer:beheer-gast-accounts'))


class BestellingOverzettenView(UserPassesTestMixin, View):
    """ deze view wordt gebruikt door de SEC 8000 om de bestellingen van een gast-account over te zetten naar
        een normaal account. Dit maakt het gast-account "vrij" zodat het kan worden opgeheven.
    """

    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    @staticmethod
    def post(request, *args, **kwargs):
        van_lid_nr = kwargs['van_lid_nr']
        naar_lid_nr = kwargs['naar_lid_nr']

        try:
            gast = GastRegistratie.objects.select_related('account', 'sporter').get(lid_nr=van_lid_nr)
        except (ValueError, GastRegistratie.DoesNotExist):
            raise Http404('Gast-account niet gevonden')

        try:
            sporter = Sporter.objects.select_related('account').get(lid_nr=naar_lid_nr)
        except (ValueError, Sporter.DoesNotExist):
            raise Http404('Sporter niet gevonden')

        if not sporter.account:
            raise Http404('Sporter heeft nog geen account')

        # maak een SporterBoog vertaling
        afk2sb = dict()
        for sb in sporter.sporterboog_set.all():
            afk2sb[sb.boogtype.afkorting] = sb
        # for

        for bestelling in (Bestelling
                           .objects
                           .filter(account=gast.account)
                           .prefetch_related('producten')
                           .select_related('account')):

            bestelling.account = sporter.account

            for product in (bestelling.
                            producten.
                            select_related('wedstrijd_inschrijving',
                                           'wedstrijd_inschrijving__sporterboog__sporter',
                                           'wedstrijd_inschrijving__sporterboog__boogtype',
                                           'webwinkel_keuze')
                            .all()):

                inschrijving = product.wedstrijd_inschrijving
                if inschrijving:
                    if gast.sporter == inschrijving.sporterboog.sporter:
                        afk = inschrijving.sporterboog.boogtype.afkorting
                        try:
                            sb = afk2sb[afk]
                        except KeyError:
                            raise Http404('SporterBoog ontbreekt voor boog %s' % afk)
                        else:
                            inschrijving.sporterboog = sb

                    if inschrijving.koper == gast.account:
                        inschrijving.koper = sporter.account

                    inschrijving.save(update_fields=['koper', 'sporterboog'])

                keuze = product.webwinkel_keuze
                if keuze:
                    if keuze.koper == gast.account:
                        keuze.koper = sporter.account
                        keuze.save(update_fields=['koper'])
            # for

            bestelling.save(update_fields=['account'])
        # for

        url = reverse('Registreer:beheer-gast-account-details', kwargs={'lid_nr': gast.lid_nr})
        return HttpResponseRedirect(url)

# end of file
