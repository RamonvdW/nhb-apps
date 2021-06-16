# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.functions import Concat
from django.utils.timezone import make_aware
from django.views.generic import TemplateView
from django.utils.formats import localize
from django.db.models import F, Q, Value, Count
from django.utils import timezone
from django.urls import reverse
from Functie.models import Functie
from Functie.rol import SESSIONVAR_ROL_HUIDIGE, SESSIONVAR_ROL_MAG_WISSELEN, rol2url, rol_get_huidige, Rollen
from NhbStructuur.models import NhbLid
from Plein.menu import menu_dynamics
from .models import Account, AccountEmail, AccountSessions
from .forms import ZoekAccountForm
import datetime
import logging


TEMPLATE_ACTIVITEIT = 'account/activiteit.dtl'

my_logger = logging.getLogger('NHBApps.Account')


class ActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de activiteiten van de gebruikers """

    # class variables shared by all instances
    template_name = TEMPLATE_ACTIVITEIT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = Rollen.ROL_NONE
        self.sort_level = {'BKO': 10000, 'RKO': 500, 'RCL': 40, 'SEC': 3, 'HWL': 2, 'WL': 1}

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        account = self.request.user
        if account.is_authenticated:
            self.rol_nu = rol_get_huidige(self.request)
            if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_IT):
                return True

        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['nieuwe_accounts'] = (AccountEmail
                                      .objects
                                      .select_related('account')
                                      .all()
                                      .order_by('-account__date_joined')[:50])

        nieuwste = context['nieuwe_accounts'][0].account    # kost losse database access
        jaar = nieuwste.date_joined.year
        maand = nieuwste.date_joined.month
        deze_maand = make_aware(datetime.datetime(year=jaar, month=maand, day=1))

        context['deze_maand_count'] = (Account
                                       .objects
                                       .order_by('-date_joined')
                                       .filter(date_joined__gte=deze_maand)
                                       .count())
        context['deze_maand'] = deze_maand

        context['totaal'] = Account.objects.count()

        context['recente_activiteit'] = (AccountEmail
                                         .objects
                                         .filter(account__last_login__isnull=False)
                                         .select_related('account')
                                         .order_by('-account__last_login')[:50])

        context['inlog_pogingen'] = (AccountEmail
                                     .objects
                                     .select_related('account')
                                     .filter(account__laatste_inlog_poging__isnull=False)
                                     .filter(account__last_login__lt=F('account__laatste_inlog_poging'))
                                     .order_by('-account__laatste_inlog_poging')[:50])

        # hulp nodig
        account_pks = list()
        for functie in (Functie
                        .objects
                        .prefetch_related('accounts',
                                          'accounts__vhpg',
                                          'accounts__accountemail_set')
                        .annotate(aantal=Count('accounts'))
                        .filter(aantal__gt=0)):
            for account in functie.accounts.all():
                add = False

                if account.vhpg.count() > 0:
                    vhpg = account.vhpg.all()[0]
                    # elke 11 maanden moet de verklaring afgelegd worden
                    # dit is ongeveer (11/12)*365 == 365-31 = 334 dagen
                    opnieuw = vhpg.acceptatie_datum + datetime.timedelta(days=334)
                    now = timezone.now()
                    if opnieuw < now:
                        add = True
                else:
                    add = True

                if not account.otp_is_actief:
                    add = True

                if add:
                    if account.pk not in account_pks:
                        account_pks.append(account.pk)
            # for
        # for

        hulp = list()
        for account in (Account
                        .objects
                        .prefetch_related('vhpg',
                                          'functie_set')
                        .filter(pk__in=account_pks)
                        .order_by('last_login',
                                  'unaccented_naam')):

            if account.vhpg.count() > 0:
                vhpg = account.vhpg.all()[0]

                # elke 11 maanden moet de verklaring afgelegd worden
                # dit is ongeveer (11/12)*365 == 365-31 = 334 dagen
                opnieuw = vhpg.acceptatie_datum + datetime.timedelta(days=334)
                now = timezone.now()
                if opnieuw < now:
                    account.vhpg_str = 'Verlopen'
                else:
                    account.vhpg_str = 'Ja'
            else:
                account.vhpg_str = 'Nee'

            if account.otp_is_actief:
                account.tweede_factor_str = 'Ja'
            else:
                account.tweede_factor_str = 'Nee'

            totaal_level = 0
            functies = list()
            for functie in account.functie_set.all():
                level = self.sort_level[functie.rol]
                tup = (level, functie.rol)
                functies.append(tup)
                totaal_level += level
            # for
            functies.sort(reverse=True)
            account.functies_str = ", ".join([tup[1] for tup in functies])

            tup = (totaal_level, account.pk, account)
            hulp.append(tup)
        # for

        hulp.sort(reverse=True)
        context['hulp'] = [tup[2] for tup in hulp]

        # zoekformulier
        context['zoek_url'] = reverse('Account:activiteit')
        context['zoekform'] = form = ZoekAccountForm(self.request.GET)
        form.full_clean()   # vult form.cleaned_data

        try:
            zoekterm = form.cleaned_data['zoekterm']
        except KeyError:
            # hier komen we als het form field niet valide was, bijvoorbeeld veel te lang
            zoekterm = ""
        context['zoekterm'] = zoekterm

        leden = list()
        if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
            try:
                nhb_nr = int(zoekterm[:6])
                lid = (NhbLid
                       .objects
                       .select_related('account')
                       .prefetch_related('account__functie_set',
                                         'account__vhpg')
                       .get(nhb_nr=nhb_nr))
                leden.append(lid)
            except (ValueError, NhbLid.DoesNotExist):
                leden = (NhbLid
                         .objects
                         .annotate(volledige_naam=Concat('voornaam', Value(' '), 'achternaam'))
                         .select_related('account')
                         .prefetch_related('account__functie_set',
                                           'account__vhpg')
                         .filter(Q(volledige_naam__icontains=zoekterm) |
                                 Q(account__unaccented_naam__icontains=zoekterm))
                         .order_by('account__unaccented_naam', 'achternaam', 'voornaam'))[:50]

        context['zoek_leden'] = list(leden)
        for lid in leden:
            lid.nhb_nr_str = str(lid.nhb_nr)
            lid.inlog_naam_str = 'Nog geen account aangemaakt'
            lid.email_is_bevestigd_str = '-'
            lid.tweede_factor_str = '-'
            lid.vhpg_str = '-'

            if lid.account:
                account = lid.account
                lid.inlog_naam_str = account.username

                email = account.accountemail_set.all()[0]
                if email.email_is_bevestigd:
                    lid.email_is_bevestigd_str = 'Ja'
                else:
                    lid.email_is_bevestigd_str = 'Nee'

                do_vhpg = True
                if account.otp_is_actief:
                    lid.tweede_factor_str = 'Ja'
                elif account.functie_set.count() == 0:
                    lid.tweede_factor_str = 'n.v.t.'
                    do_vhpg = False
                else:
                    lid.tweede_factor_str = 'Nee'

                if do_vhpg:
                    lid.vhpg_str = 'Nee'
                    if account.vhpg.count() > 0:
                        vhpg = account.vhpg.all()[0]

                        # elke 11 maanden moet de verklaring afgelegd worden
                        # dit is ongeveer (11/12)*365 == 365-31 = 334 dagen
                        opnieuw = vhpg.acceptatie_datum + datetime.timedelta(days=334)
                        now = timezone.now()
                        if opnieuw < now:
                            lid.vhpg_str = 'Verlopen (geaccepteerd op %s)' % localize(vhpg.acceptatie_datum)
                        else:
                            lid.vhpg_str = 'Ja (op %s)' % localize(vhpg.acceptatie_datum)
                else:
                    lid.vhpg_str = 'n.v.t.'

                lid.functies = account.functie_set.order_by('beschrijving')
        # for

        # toon sessies
        if self.rol_nu == Rollen.ROL_IT:
            accses = (AccountSessions
                      .objects
                      .select_related('account', 'session')
                      .order_by('account', 'session__expire_date'))
            for obj in accses:
                # TODO: onderstaande zorgt voor losse database hits voor elke sessie
                session = SessionStore(session_key=obj.session.session_key)

                try:
                    obj.mag_wisselen_str = session[SESSIONVAR_ROL_MAG_WISSELEN]
                except KeyError:        # pragma: no cover
                    obj.mag_wisselen_str = '?'

                try:
                    obj.laatste_rol_str = rol2url[session[SESSIONVAR_ROL_HUIDIGE]]
                except KeyError:        # pragma: no cover
                    obj.laatste_rol_str = '?'
            # for
            context['accses'] = accses

        menu_dynamics(self.request, context)
        return context


# end of file
