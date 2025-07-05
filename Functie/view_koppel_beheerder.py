# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat, Cast
from django.views.generic import ListView, View
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account, get_account
from Functie.definities import Rol
from Functie.forms import ZoekBeheerdersForm, WijzigBeheerdersForm, WijzigEmailForm
from Functie.models import Functie
from Functie.operations import functie_vraag_email_bevestiging, functie_wijziging_stuur_email_notificatie
from Functie.rol import (rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving,
                         rol_zet_mag_wisselen_voor_account)
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Sporter.models import Sporter
from TijdelijkeCodes.definities import RECEIVER_BEVESTIG_EMAIL_FUNCTIE
from TijdelijkeCodes.operations import set_tijdelijke_codes_receiver


TEMPLATE_KOPPEL_BEHEERDERS = 'functie/koppel-beheerders.dtl'
TEMPLATE_WIJZIG_EMAIL = 'functie/email-wijzigen.dtl'
TEMPLATE_BEVESTIG_EMAIL = 'functie/email-bevestig.dtl'
TEMPLATE_EMAIL_BEVESTIGD = 'functie/email-bevestigd.dtl'


def mag_beheerder_wijzigen_of_403(request, functie):
    """ Stuur gebruiker weg als illegaal van de aanroepende view gebruik gemaakt wordt

        Wordt gebruikt door:
            WijzigView (koppelen van leden aan 1 functie) - tijdens get_queryset()
            OntvangWijzigingenView - vroeg in afhandelen POST verzoek
    """

    # test_func van WijzigView laat alleen BB, BKO, RKO of HWL door
    # OntvangWijzigingenView heeft niet zo'n filter

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if rol_nu == Rol.ROL_BB:
        # BB mag BKO koppelen + alle globale functies
        if functie.rol not in ('BKO', 'CS', 'MWW', 'MO', 'MWZ', 'MLA', 'SUP'):
            raise PermissionDenied('Niet de beheerder')
        return

    if rol_nu == Rol.ROL_SEC:
        if functie.vereniging != functie_nu.vereniging:
            # verkeerde vereniging
            raise PermissionDenied('Verkeerde vereniging')

        if functie.rol != 'HWL':
            # niet een rol die de SEC mag wijzigen
            raise PermissionDenied('Niet de beheerder')

        # SEC
        return

    if rol_nu == Rol.ROL_HWL:
        if functie.vereniging != functie_nu.vereniging:
            # verkeerde vereniging
            raise PermissionDenied('Verkeerde vereniging')

        if functie.rol not in ('HWL', 'WL'):
            # niet een rol die de HWL mag wijzigen
            raise PermissionDenied('Niet de beheerder')

        # HWL
        return

    # RCL mag HWL en WL koppelen van vereniging binnen regio RCL
    if rol_nu == Rol.ROL_RCL and functie.rol in ('HWL', 'WL'):
        if functie_nu.regio != functie.vereniging.regio:
            raise PermissionDenied('Verkeerde regio')
        return

    # BKO, RKO, RCL

    # controleer dat deze wijziging voor de juiste competitie is
    # (voorkomt BKO 25m 1pijl probeert RKO Indoor te koppelen)
    if not functie_nu or functie_nu.comp_type != functie.comp_type:
        # SEC/HWL/WL verdwijnt hier ook
        raise PermissionDenied('Verkeerde competitie')

    if rol_nu == Rol.ROL_BKO:
        if functie.rol != 'RKO':
            raise PermissionDenied('Niet de beheerder')
        return

    elif rol_nu == Rol.ROL_RKO:
        if functie.rol != 'RCL':
            raise PermissionDenied('Niet de beheerder')

        # controleer of deze regio gewijzigd mag worden
        if functie.regio.rayon != functie_nu.rayon:
            raise PermissionDenied('Verkeerde rayon')
        return

    # niets hier te zoeken (RCL en andere rollen)
    raise PermissionDenied('Niet de beheerder')


def mag_email_wijzigen_of_403(request, functie):
    """ Stuur gebruiker weg als illegaal van de aanroepende view gebruik gemaakt wordt

        Wordt gebruikt door:
            WijzigEmailView - tijdens GET en POST
    """

    # test_func van WijzigEmailView laat alleen BB, BKO, RKO, RCL, SEC en HWL door

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    # rol mag direct onderliggende functie aanpassen:
    #   BB --> alle BKO
    #   BKO (comp_type) --> alle RKO (comp_type)
    #   RKO (comp_type) --> alle RCL (comp_type) in zijn rayon

    # special voor BB, want dat is geen functie
    if rol_nu == Rol.ROL_BB:
        # BB mag BKO email aanpassen + alle globale rollen
        if functie.rol not in ('BKO', 'CS', 'MWW', 'MO', 'MWZ', 'MLA', 'SUP'):
            raise PermissionDenied('Niet de beheerder')
        return

    # voor de rest moet de gebruiker een functie bezitten
    if not functie_nu:
        raise PermissionDenied('Niet de beheerder')     # pragma: no cover

    # SEC, HWL en WL mogen email van HWL en WL aanpassen
    if rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_WL):
        # alleen binnen eigen vereniging
        if functie_nu.vereniging != functie.vereniging:
            raise PermissionDenied('Verkeerde vereniging')

        if functie.rol not in ('HWL', 'WL'):
            # hier verdwijnt SEC in het putje
            # secretaris email is alleen aan te passen via Onze Relaties
            raise PermissionDenied('Niet de beheerder')

        if rol_nu == Rol.ROL_WL and functie.rol != 'WL':
            # WL mag alleen zijn eigen e-mailadres aanpassen
            raise PermissionDenied('Niet de beheerder')

        return

    # alle rollen mogen hun eigen e-mailadres aanpassen
    if functie_nu == functie:
        return

    # RCL mag email van HWL en WL aanpassen van vereniging binnen regio RCL
    if rol_nu == Rol.ROL_RCL and functie.rol in ('HWL', 'WL'):
        if functie_nu.regio != functie.vereniging.regio:
            raise PermissionDenied('Verkeerde regio')
        return

    # BKO, RKO, RCL

    # controleer dat deze wijziging voor de juiste competitie is
    # (voorkomt BKO 25m 1pijl probeert RKO Indoor te koppelen)
    if functie_nu.comp_type != functie.comp_type:
        raise PermissionDenied('Verkeerde competitie')

    if rol_nu == Rol.ROL_BKO:
        if functie.rol != 'RKO':
            raise PermissionDenied('Niet de beheerder')
        return

    elif rol_nu == Rol.ROL_RKO:
        if functie.rol != 'RCL':
            raise PermissionDenied('Niet de beheerder')

        # controleer of deze regio gewijzigd mag worden
        if functie.regio.rayon != functie_nu.rayon:
            raise PermissionDenied('Verkeerde rayon')
        return

    # niets hier te zoeken
    raise PermissionDenied('Niet de beheerder')


def receive_bevestiging_functie_email(request, functie):
    """ deze functie wordt vanuit een POST context aangeroepen als een tijdelijke url gevolgd wordt
        om een nieuw email adres te bevestigen voor een functie.

        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.
    """

    # het is mogelijk om meerdere keren hetzelfde e-mailadres te koppelen
    # je hebt dan meerdere mails met tijdelijke urls om te volgen
    # deze functie wordt voor elke gevolgde url aangeroepen
    # na de eerste keer is nieuwe_email leeg en gebeurt er niets
    # we geven wel steeds het succes verhaal terug
    if functie.nieuwe_email:
        # schrijf in het logboek
        from_ip = get_safe_from_ip(request)
        msg = "Bevestigd vanaf IP %s voor functie %s" % (from_ip, functie.beschrijving)
        schrijf_in_logboek(account=None,
                           gebruikte_functie="Bevestig e-mail",
                           activiteit=msg)

        # zet het e-mailadres door
        functie.bevestigde_email = functie.nieuwe_email
        functie.nieuwe_email = ''
        functie.save()

    context = {'functie': functie}
    return render(request, TEMPLATE_EMAIL_BEVESTIGD, context)


set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_EMAIL_FUNCTIE, receive_bevestiging_functie_email)


class WijzigEmailView(UserPassesTestMixin, View):

    """ Via deze view kan het e-mailadres van een functie aangepast worden """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MO, Rol.ROL_MWZ, Rol.ROL_SUP, Rol.ROL_MLA,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_WL)

    def _get_functie_or_404(self):
        functie_pk = self.kwargs['functie_pk']
        try:
            functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Http404('Foutieve functie')
        return functie

    def _render_form(self, form, functie):
        context = dict()
        context['functie'] = functie

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_WL):
            # komt van Beheer vereniging
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Functie:overzicht-vereniging'), 'Beheerders'),
                (None, 'Wijzig e-mail')
            )
        elif self.rol_nu in (Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
            # komt van Bondscompetities
            context['terug_url'] = reverse('Functie:lijst-beheerders')
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('Functie:lijst-beheerders'), 'Beheerders'),
                (None, 'Wijzig e-mail')
            )
        else:
            # komt van Het Plein
            context['terug_url'] = reverse('Functie:lijst-beheerders')
            context['kruimels'] = (
                (reverse('Functie:lijst-beheerders'), 'Beheerders'),
                (None, 'Wijzig e-mail')
            )

        context['form'] = form
        context['form_submit_url'] = reverse('Functie:wijzig-email', kwargs={'functie_pk': functie.pk})

        return render(self.request, TEMPLATE_WIJZIG_EMAIL, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        functie = self._get_functie_or_404()

        # FUTURE: functie.nieuwe_email opruimen als SiteTijdelijkeUrl verlopen is (of opgeruimd is)

        # BKO, RKO, RCL, HWL mogen hun eigen contactgegevens wijzigen
        # als ze de rol aangenomen hebben
        # verder mogen ze altijd de onderliggende laag aanpassen (net als beheerders koppelen)
        mag_email_wijzigen_of_403(self.request, functie)
        form = WijzigEmailForm()
        return self._render_form(form, functie)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de OPSLAAN knop van het formulier.
        """
        functie = self._get_functie_or_404()
        mag_email_wijzigen_of_403(self.request, functie)

        form = WijzigEmailForm(self.request.POST)
        if not form.is_valid():
            # geeft het invulformulier terug voor de foutmelding + nieuwe poging
            form.add_error(None, 'e-mailadres niet geaccepteerd')
            return self._render_form(form, functie)

        # sla het nieuwe e-mailadres op
        functie.nieuwe_email = form.cleaned_data['email']
        functie.save()

        account = get_account(self.request)
        schrijf_in_logboek(account, 'Rollen', 'Nieuw e-mailadres ingevoerd voor rol %s' % functie.beschrijving)

        # stuur email
        # (extra args zijn input voor hash, om unieke url te krijgen)
        functie_vraag_email_bevestiging(functie)

        context = dict()
        context['functie'] = functie

        # stuur terug naar het overzicht
        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_WL):
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
        else:
            context['terug_url'] = reverse('Functie:lijst-beheerders')

        return render(request, TEMPLATE_BEVESTIG_EMAIL, context)


class OntvangBeheerderWijzigingenView(View):

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de knop om een beheerder te koppelen
            (WijzigBeheerdersView)
        """
        functie_pk = self.kwargs['functie_pk']
        try:
            functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Http404('Verkeerde functie')

        mag_beheerder_wijzigen_of_403(request, functie)
        door_account = get_account(request)

        form = WijzigBeheerdersForm(request.POST)
        form.full_clean()  # vult cleaned_data
        add = form.cleaned_data.get('add')
        drop = form.cleaned_data.get('drop')

        if add:
            account_pk = add
        elif drop:
            account_pk = drop
        else:
            raise Http404('Verkeerd gebruik')

        try:
            account = Account.objects.get(pk=account_pk)
        except Account.DoesNotExist:
            raise Http404('Account niet gevonden')

        if account.sporter_set.count() > 0:     # pragma: no branch
            sporter = account.sporter_set.first()
            wie = "Sporter %s (%s)" % (sporter.lid_nr, sporter.volledige_naam())
        else:
            sporter = None
            wie = "Account %s" % account.get_account_full_name()

        if add:
            rol_nu, functie_nu = rol_get_huidige_functie(request)
            if rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL):
                # stel zeker dat sporter lid is bij de vereniging van functie
                if not sporter or sporter.bij_vereniging != functie.vereniging:
                    raise PermissionDenied('Geen lid van jouw vereniging')

            functie.accounts.add(account)
            schrijf_in_logboek(door_account, 'Rollen',
                               "%s is beheerder gemaakt voor functie %s" % (wie, functie.beschrijving))

            # TODO: functie_wijziging_stuur_email_notificatie geef False terug indien account geen e-mail kan ontvangen

            functie_wijziging_stuur_email_notificatie(account, wie, functie.beschrijving, add=True)

            if account.functie_set.count() == 1:
                rol_zet_mag_wisselen_voor_account(account)
        else:
            functie.accounts.remove(account)
            schrijf_in_logboek(door_account, 'Rollen',
                               "%s losgekoppeld van functie %s" % (wie, functie.beschrijving))

            functie_wijziging_stuur_email_notificatie(account, wie, functie.beschrijving, remove=True)

        return HttpResponseRedirect(reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': functie.pk}))


class WijzigBeheerdersView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders voor een functie gekozen worden """

    # class variables shared by all instances
    template_name = TEMPLATE_KOPPEL_BEHEERDERS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self._form = None
        self._functie = None
        self._zoekterm = None
        self._huidige_beheerders = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MO, Rol.ROL_MWZ, Rol.ROL_SUP,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_SEC, Rol.ROL_HWL)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        functie_pk = self.kwargs['functie_pk']
        try:
            self._functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Http404('Verkeerde functie')

        mag_beheerder_wijzigen_of_403(self.request, self._functie)

        self._form = ZoekBeheerdersForm(self.request.GET)
        self._form.full_clean()  # vult cleaned_data

        # huidige beheerders willen we niet opnieuw vinden
        beheerder_accounts = self._functie.accounts.all()
        for account in beheerder_accounts:
            account.geo_beschrijving = '-'
            account.let_op = ''
            if account.sporter_set.count() > 0:     # pragma: no branch
                sporter = account.sporter_set.first()
                if sporter.bij_vereniging:
                    regio = sporter.bij_vereniging.regio
                    account.geo_beschrijving = "Regio %s" % regio.regio_nr
                    if not regio.is_administratief:
                        account.geo_beschrijving += " / rayon %s" % regio.rayon_nr
                if not sporter.bij_vereniging:
                    # deze melding komt na 15 januari
                    account.let_op = 'LET OP: geen lid meer bij een vereniging'
                elif self._functie.vereniging and sporter.bij_vereniging != self._functie.vereniging:
                    # functie voor beheerder van een vereniging
                    # lid is overgestapt
                    account.let_op = 'LET OP: geen lid bij deze vereniging'
        # for

        self._huidige_beheerders = beheerder_accounts

        zoekterm = self._form.cleaned_data['zoekterm']
        if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
            self._zoekterm = zoekterm

            # let op: we koppelen een account, maar zoeken een lid,
            #         om te kunnen filteren op vereniging
            #         accounts die geen lid zijn worden hier niet gevonden
            qset = (Sporter
                    .objects
                    .exclude(account=None)
                    .exclude(is_actief_lid=False)
                    .exclude(account__in=beheerder_accounts)
                    .annotate(hele_reeks=Concat('voornaam', Value(' '), 'achternaam'))
                    .annotate(lid_nr_str=Cast('lid_nr', CharField()))
                    .filter(Q(lid_nr_str__contains=zoekterm) |
                            Q(voornaam__icontains=zoekterm) |
                            Q(achternaam__icontains=zoekterm) |
                            Q(hele_reeks__icontains=zoekterm))
                    .order_by('lid_nr'))

            is_vereniging_rol = (self._functie.rol in ('SEC', 'HWL', 'WL'))
            if is_vereniging_rol:
                # alleen leden van de vereniging laten kiezen
                qset = qset.filter(bij_vereniging=self._functie.vereniging)

            objs = list()
            for sporter in qset[:50]:
                account = sporter.account
                account.geo_beschrijving = ''
                account.lid_nr_str = str(sporter.lid_nr)

                if is_vereniging_rol:
                    account.vereniging_naam = str(sporter.bij_vereniging)    # [1234] Naam
                else:
                    regio = sporter.bij_vereniging.regio
                    account.geo_beschrijving = "Regio %s" % regio.regio_nr
                    if not regio.is_administratief:
                        account.geo_beschrijving += " / rayon %s" % regio.rayon_nr

                objs.append(account)
            # for

            return objs

        self._zoekterm = ""
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['functie'] = self._functie
        context['huidige_beheerders'] = self._huidige_beheerders
        context['rol_str'] = rol_get_beschrijving(self.request)
        context['wijzig_url'] = reverse('Functie:ontvang-wijzigingen', kwargs={'functie_pk': self._functie.pk})
        context['zoek_url'] = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': self._functie.pk})
        context['zoekterm'] = self._zoekterm
        context['form'] = self._form

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL):
            # komt van Beheer vereniging
            context['is_vereniging_rol'] = True

            # Je kan hier op twee manieren komen:
            # via Plein, Verenigingen, Details (=Vereniging:accommodaties/details/pk/pk/), Koppel beheerders
            # via Verenging, Beheerders (=Functie:overzicht-vereniging), Koppel beheerders

            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Functie:overzicht-vereniging'), 'Beheerders'),
                (None, 'Wijzig beheerder')
            )
        elif self.rol_nu in (Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
            # komt van Bondscompetities
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('Functie:lijst-beheerders'), 'Beheerders'),
                (None, 'Wijzig beheerder')
            )
        else:
            # komt van Het Plein
            context['kruimels'] = (
                (reverse('Functie:lijst-beheerders'), 'Beheerders'),
                (None, 'Wijzig beheerder')
            )

        return context


# end of file
