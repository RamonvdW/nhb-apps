# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.timezone import make_aware, get_default_timezone
from django.views.generic import TemplateView, View
from django.utils.formats import date_format
from django.db.models import F, Count
from Account.models import Account, AccountSessions, get_account
from Account.operations.otp import otp_loskoppelen, otp_stuur_email_losgekoppeld
from Functie.definities import Rol
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Functie.rol import rol_get_huidige
from Overig.forms import ZoekAccountForm
from Sporter.models import Sporter
import datetime


TEMPLATE_ACTIVITEIT = 'overig/activiteit.dtl'


class ActiviteitView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de activiteiten van de gebruikers """

    # class variables shared by all instances
    template_name = TEMPLATE_ACTIVITEIT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = Rol.ROL_NONE
        self.sort_level = {'MO': 20000, 'CS': 20001, 'BKO': 10000, 'RKO': 500, 'RCL': 40, 'SEC': 3, 'HWL': 2, 'WL': 1}

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        account = get_account(self.request)
        if account.is_authenticated:
            self.rol_nu = rol_get_huidige(self.request)
            if self.rol_nu == Rol.ROL_BB:
                return True

        return False

    @staticmethod
    def tel_actieve_gebruikers():
        # tel alle gebruikers die de afgelopen maand ingelogd hebben
        een_maand_geleden = timezone.now() - datetime.timedelta(days=31)
        user_list1 = Account.objects.filter(last_login__gt=een_maand_geleden).values_list('username', flat=True)

        # sessies worden verwijderd als deze verlopen is; standaard 14 dagen (SESSION_COOKIE_AGE)
        user_list2 = AccountSessions.objects.distinct('account').values_list('account__username', flat=True)

        unique = set().union(user_list1, user_list2)
        return len(unique)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['nieuwe_accounts'] = (Account
                                      .objects
                                      .all()
                                      .order_by('-date_joined')[:50])

        nieuwste = context['nieuwe_accounts'][0]
        jaar = nieuwste.date_joined.year
        maand = nieuwste.date_joined.month
        deze_maand = make_aware(datetime.datetime(year=jaar, month=maand, day=1))

        context['deze_maand_count'] = (Account
                                       .objects
                                       .order_by('-date_joined')
                                       .filter(date_joined__gte=deze_maand)
                                       .count())
        context['deze_maand_count_gast'] = (Account
                                            .objects
                                            .order_by('-date_joined')
                                            .filter(date_joined__gte=deze_maand,
                                                    is_gast=True)
                                            .count())
        context['deze_maand'] = deze_maand

        context['totaal'] = Account.objects.count()
        context['totaal_gast'] = Account.objects.filter(is_gast=True).count()

        context['aantal_actieve_gebruikers'] = self.tel_actieve_gebruikers()

        context['recente_activiteit'] = (Account
                                         .objects
                                         .filter(last_login__isnull=False)
                                         .order_by('-last_login')[:50])

        context['inlog_pogingen'] = (Account
                                     .objects
                                     .filter(laatste_inlog_poging__isnull=False)
                                     .filter(last_login__lt=F('laatste_inlog_poging'))
                                     .order_by('-laatste_inlog_poging')[:50])

        # hulp nodig
        now = timezone.now()
        account_pks = list()
        for functie in (Functie
                        .objects
                        .prefetch_related('accounts',
                                          'accounts__vhpg')
                        .annotate(aantal=Count('accounts'))
                        .filter(aantal__gt=0)):

            for account in functie.accounts.all():
                add = not account.otp_is_actief

                if add:
                    if account.pk not in account_pks:
                        account_pks.append(account.pk)
            # for
        # for

        hulp = list()
        for account in (Account
                        .objects
                        .prefetch_related('functie_set')
                        .filter(pk__in=account_pks)
                        .order_by('last_login',
                                  'unaccented_naam')):

            totaal_level = 0
            functies = list()
            for functie in account.functie_set.all():
                try:
                    level = self.sort_level[functie.rol]
                except KeyError:        # pragma: no cover
                    level = 999999
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
        context['zoek_url'] = reverse('Overig:activiteit')
        context['zoekform'] = form = ZoekAccountForm(self.request.GET)
        form.full_clean()   # vult form.cleaned_data

        try:
            zoekterm = form.cleaned_data['zoekterm']
        except KeyError:
            # hier komen we als het form field niet valide was, bijvoorbeeld veel te lang
            zoekterm = ""
        context['zoekterm'] = zoekterm

        sporters = list()
        if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
            try:
                lid_nr = int(zoekterm[:6])
                sporter = (Sporter
                           .objects
                           .select_related('account',
                                           'bij_vereniging__regio')
                           .prefetch_related('account__functie_set',
                                             'account__vhpg')
                           .get(lid_nr=lid_nr))
                sporters.append(sporter)
            except (ValueError, Sporter.DoesNotExist):
                sporters = (Sporter
                            .objects
                            .select_related('account',
                                            'bij_vereniging__regio')
                            .prefetch_related('account__functie_set',
                                              'account__vhpg')
                            .filter(unaccented_naam__icontains=zoekterm)
                            .order_by('unaccented_naam'))[:50]

        to_tz = get_default_timezone()
        current_year_str = ' %s' % now.year

        now_date = now.date()

        context['zoek_leden'] = list(sporters)
        for sporter in sporters:
            sporter.lid_nr_str = str(sporter.lid_nr)
            sporter.inlog_naam_str = 'Nog geen account aangemaakt'
            sporter.email_is_bevestigd_str = '-'
            sporter.tweede_factor_str = '-'
            sporter.vhpg_str = '-'
            sporter.laatste_inlog_str = '-'
            sporter.kan_loskoppelen = False

            if sporter.bij_vereniging:
                sporter.ver_str = "%s (%s, regio %s)" % (str(sporter.bij_vereniging),
                                                         sporter.bij_vereniging.plaats,
                                                         sporter.bij_vereniging.regio.regio_nr)
            else:
                sporter.ver_str = 'Geen'

            if sporter.is_actief_lid:
                sporter.status_str = 'Actief voor heel %s' % sporter.lid_tot_einde_jaar
            else:
                if sporter.sinds_datum > now_date:
                    sporter.status_str = 'Actief vanaf %s' % sporter.sinds_datum
                else:
                    sporter.status_str = 'Verlopen'

            if sporter.account:                     # pragma: no branch
                account = sporter.account
                sporter.inlog_naam_str = account.username

                if account.email_is_bevestigd:
                    sporter.email_is_bevestigd_str = 'Ja'
                else:
                    sporter.email_is_bevestigd_str = 'Nee'

                if account.last_login:
                    if account.last_login.year == now.year:
                        sporter.laatste_inlog_str = date_format(account.last_login.astimezone(to_tz),
                                                                'j F Y H:i').replace(current_year_str, '')

                do_vhpg = True
                if account.otp_is_actief:
                    sporter.tweede_factor_str = 'Ja'
                    if account.otp_controle_gelukt_op:
                        sporter.tweede_factor_str += ' (check gelukt op %s)' % date_format(
                                                            account.otp_controle_gelukt_op.astimezone(to_tz),
                                                            'j F Y H:i').replace(current_year_str, '')
                    sporter.kan_loskoppelen = True
                elif account.functie_set.count() == 0:
                    sporter.tweede_factor_str = 'n.v.t.'
                    do_vhpg = False
                else:
                    sporter.tweede_factor_str = 'Nee'

                if do_vhpg:
                    sporter.vhpg_str = 'Nee'
                    try:
                        vhpg = account.vhpg
                    except VerklaringHanterenPersoonsgegevens.DoesNotExist:
                        # geen registratie
                        pass
                    else:
                        # elke 11 maanden moet de verklaring afgelegd worden
                        # dit is ongeveer (11/12)*365 == 365-31 = 334 dagen
                        opnieuw = vhpg.acceptatie_datum + datetime.timedelta(days=334)
                        opnieuw = opnieuw.astimezone(to_tz)
                        now = timezone.now()
                        if opnieuw < now:
                            sporter.vhpg_str = 'Verlopen (geaccepteerd op %s)' % date_format(
                                                    vhpg.acceptatie_datum,
                                                    'j F Y H:i').replace(current_year_str, '')
                        else:
                            sporter.vhpg_str = 'Ja (op %s)' % date_format(
                                                    vhpg.acceptatie_datum.astimezone(to_tz),
                                                    'j F Y H:i').replace(current_year_str, '')

                sporter.functies = account.functie_set.order_by('beschrijving')

            if not sporter.is_gast:
                sporter.url_toon_bondspas = reverse('Bondspas:toon-bondspas-van',
                                                    kwargs={'lid_nr': sporter.lid_nr})
        # for

        context['url_reset_tweede_factor'] = reverse('Overig:otp-loskoppelen')

        age_group_counts = dict()       # [groep] = aantal
        for group in (1, 10, 20, 30, 40, 50, 60, 70, 80):
            age_group_counts[int(group/10)] = 0
        # for

        afgelopen_maand = timezone.now() - datetime.timedelta(days=30)
        jaar = timezone.now().year
        total = 0
        for geboorte_datum in (Sporter
                               .objects
                               .exclude(account=None)
                               .filter(account__last_login__gte=afgelopen_maand)
                               .values_list('geboorte_datum', flat=True)):
            leeftijd = jaar - geboorte_datum.year
            leeftijd = min(leeftijd, 89)
            group = int(leeftijd / 10)
            age_group_counts[group] += 1
            total += 1
        # for

        if total > 0:       # pragma: no branch
            age_groups = [((age * 10), (age * 10)+9, count, int((count * 100) / total))
                          for age, count in age_group_counts.items()]
            age_groups.sort()
            context['age_groups'] = age_groups

        context['kruimels'] = (
            (None, 'Account activiteit'),
        )

        return context


class OTPLoskoppelenView(UserPassesTestMixin, View):

    """ Deze view levert een POST-functie om de tweede factor los te kunnen koppelen
        voor een gekozen gebruiken. Dit kan alleen de BB.
    """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    @staticmethod
    def post(request, *args, **kwargs):
        url = reverse('Overig:activiteit')

        if request.POST.get("reset_tweede_factor", None):
            inlog_naam = request.POST.get("inlog_naam", '')[:6]     # afkappen voor de veiligheid

            try:
                account = Account.objects.get(username=inlog_naam)
            except Account.DoesNotExist:
                raise Http404('Niet gevonden')

            url += '?zoekterm=%s' % account.username

            # doe het feitelijke loskoppelen + in logboek schrijven
            is_losgekoppeld = otp_loskoppelen(request, account)

            if is_losgekoppeld:
                otp_stuur_email_losgekoppeld(account)

        return HttpResponseRedirect(url)


# end of file
