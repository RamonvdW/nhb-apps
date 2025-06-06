# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
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
from Account.models import get_account, Account
from BasisTypen.definities import GESLACHT2STR
from Bestelling.definities import BESTELLING_STATUS2STR
from Bestelling.models import BestellingMandje, Bestelling
from Evenement.models import EvenementInschrijving, EvenementAfgemeld
from Functie.rol import rol_get_huidige_functie
from Mailer.operations import render_email_template, mailer_queue_email
from Opleiding.models import OpleidingInschrijving, OpleidingAfgemeld
from Overig.helpers import get_safe_from_ip
from Registreer.definities import REGISTRATIE_FASE_AFGEWEZEN
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from Webwinkel.models import WebwinkelKeuze
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR
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
        context['count_afgewezen'] = len(afgewezen)
        context['count_gasten'] = len(gasten)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
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
    def _zoek_overeenkomsten(gast, context):
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
                match.is_match_vereniging = False
                for woord in gast.club.upper().split():
                    if woord in match.vereniging_str.upper():   # pragma: no branch
                        match.is_match_vereniging = True
                # for

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
            else:
                match.ophef = 0             # TODO: waarom?!
            if match.is_match_plaats:
                match.ophef += 1
            if match.heeft_account:
                match.ophef += 5

            if match.ophef > hoogste_ophef:         # pragma: no branch
                context['overzetten_naar_lid_nr'] = match.lid_nr
                context['overzetten_naar_sporter'] = match
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
        context['gast_mandje'] = BestellingMandje.objects.filter(account=gast.account).first()
        context['gast_bestellingen'] = (Bestelling
                                        .objects
                                        .filter(account=gast.account)
                                        .order_by('-aangemaakt')        # nieuwste eerst
                                        .select_related('account')
                                        [:10])

        for bestelling in context['gast_bestellingen']:
            bestelling.status_str = BESTELLING_STATUS2STR[bestelling.status]
        # for

        # zoek inschrijvingen (er is geen bestelling van als deze betaald door iemand anders)
        context['gast_wedstrijden'] = (WedstrijdInschrijving
                                       .objects
                                       .filter(sporterboog__sporter=gast.sporter)
                                       .select_related('wedstrijd')
                                       [:10])

        for inschrijving in context['gast_wedstrijden']:
            inschrijving.status_str = WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]
            if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
                # definitieve inschrijving op wedstrijd
                gast.ophef = -100
            else:
                # gereserveerd in mandje
                # of nog niet betaalde bestelling
                gast.ophef = -1
        # for

        # zoek koper van wedstrijd/evenement/opleiding
        context['gast_koper_1a'] = EvenementAfgemeld.objects.filter(koper=gast.account)[:10]
        context['gast_koper_1b'] = EvenementAfgemeld.objects.filter(koper=gast.account)[:10]
        context['gast_koper_2a'] = OpleidingInschrijving.objects.filter(koper=gast.account)[:10]
        context['gast_koper_2b'] = OpleidingAfgemeld.objects.filter(koper=gast.account)[:10]
        context['gast_koper_3a'] = WedstrijdInschrijving.objects.filter(koper=gast.account)[:10]

        koper_count = (len(context['gast_koper_1a']) + len(context['gast_koper_1b']) +
                       len(context['gast_koper_2a']) + len(context['gast_koper_2b']) +
                       len(context['gast_koper_3a']))
        if koper_count > 0:
            gast.ophef -= 100
        else:
            context['gast_koper_geen'] = True

        if gast.ophef < 0 and context['overzetten_naar_lid_nr']:
            if context['overzetten_naar_sporter'].account:
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
        self._zoek_overeenkomsten(gast, context)
        self._zoek_gebruik(gast, context)

        if not gast.account:
            delta = timezone.now() - gast.aangemaakt
            gast.dagen_geleden = delta.days

        if gast.fase == REGISTRATIE_FASE_AFGEWEZEN:
            gast.is_afgewezen = True
        elif gast.ophef >= 4:
            gast.url_ophef = reverse('Registreer:opheffen')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
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
        self.afk2sb = dict()
        self.account_old = None
        self.account_new = None
        self.sporter_old = None
        self.sporter_new = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol == 'SEC' and self.functie_nu.vereniging.is_extern

    def _bestellingen_overzetten(self):
        for bestelling in (Bestelling
                           .objects
                           .filter(account=self.account_old)
                           .prefetch_related('regels')
                           .select_related('account')):

            bestelling.account = self.account_new
            regel_pks = list(bestelling.regels.values_list('pk', flat=True))

            for inschrijving in WedstrijdInschrijving.objects.filter(bestelling__pk__in=regel_pks):

                if self.sporter_old == inschrijving.sporterboog.sporter:
                    afk = inschrijving.sporterboog.boogtype.afkorting
                    try:
                        sb = self.afk2sb[afk]
                    except KeyError:
                        raise Http404('SporterBoog ontbreekt voor boog %s' % afk)
                    else:
                        inschrijving.sporterboog = sb

                if inschrijving.koper == self.account_old:
                    inschrijving.koper = self.account_new

                inschrijving.save(update_fields=['koper', 'sporterboog'])
            # for

            for keuze in WebwinkelKeuze.objects.filter(bestelling__pk__in=regel_pks):
                if keuze.koper == self.account_old:
                    keuze.koper = self.account_new
                    keuze.save(update_fields=['koper'])
            # for

            # TODO: nodig voor evenementen?
            # niet nodig voor opleidingen

            bestelling.save(update_fields=['account'])
        # for

    def _inschrijvingen_overzetten(self):
        # zoek inschrijvingen (er is geen bestelling van als deze betaald door iemand anders)
        for obj in (WedstrijdInschrijving
                    .objects
                    .filter(sporterboog__sporter=self.sporter_old)
                    .select_related('sporterboog__boogtype')):
            afk = obj.sporterboog.boogtype.afkorting
            try:
                sb = self.afk2sb[afk]
            except KeyError:
                raise Http404('SporterBoog ontbreekt voor boog %s' % afk)
            else:
                obj.sporterboog = sb
                obj.save(update_fields=['sporterboog'])
        # for

    def _koper_overzetten(self):
        # koper van wedstrijd/evenement/opleiding overzetten
        EvenementAfgemeld.objects.filter(koper=self.account_old).update(koper=self.account_new)
        EvenementAfgemeld.objects.filter(koper=self.account_old).update(koper=self.account_new)
        OpleidingInschrijving.objects.filter(koper=self.account_old).update(koper=self.account_new)
        OpleidingAfgemeld.objects.filter(koper=self.account_old).update(koper=self.account_new)
        WedstrijdInschrijving.objects.filter(koper=self.account_old).update(koper=self.account_new)

    def post(self, request, *args, **kwargs):
        van_lid_nr = kwargs['van_lid_nr']
        naar_lid_nr = kwargs['naar_lid_nr']

        try:
            gast = GastRegistratie.objects.select_related('account', 'sporter').get(lid_nr=van_lid_nr)
        except (ValueError, GastRegistratie.DoesNotExist):
            raise Http404('Gast-account niet gevonden')

        self.account_old = gast.account
        self.sporter_old = gast.sporter

        try:
            sporter_new = Sporter.objects.select_related('account').get(lid_nr=naar_lid_nr)
        except (ValueError, Sporter.DoesNotExist):
            raise Http404('Sporter niet gevonden')

        if not sporter_new.account:
            raise Http404('Sporter heeft nog geen account')

        self.sporter_new = sporter_new
        self.account_new = sporter_new.account

        # maak een SporterBoog vertaling
        self.afk2sb = dict()
        for sb in sporter_new.sporterboog_set.all():
            self.afk2sb[sb.boogtype.afkorting] = sb
        # for

        self._bestellingen_overzetten()         # eigen bestellingen
        self._inschrijvingen_overzetten()       # door iemand anders gekocht
        self._koper_overzetten()                # koper voor iemand anders

        url = reverse('Registreer:beheer-gast-account-details', kwargs={'lid_nr': gast.lid_nr})
        return HttpResponseRedirect(url)

# end of file
