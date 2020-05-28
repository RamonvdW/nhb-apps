# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.utils import timezone
from django.shortcuts import redirect, render
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat, Cast
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account, HanterenPersoonsgegevens
from Account.otp import account_otp_prepare_koppelen, account_otp_koppel, account_otp_is_gekoppeld, account_otp_controleer
from Account.rechten import account_rechten_eval_now, account_rechten_is_otp_verified
from NhbStructuur.models import ADMINISTRATIEVE_REGIO, NhbLid
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Overig.tijdelijke_url import maak_tijdelijke_url_functie_email
from Mailer.models import mailer_queue_email
from Overig.tijdelijke_url import set_tijdelijke_url_receiver, RECEIVER_BEVESTIG_FUNCTIE_EMAIL
from Overig.helpers import get_safe_from_ip
from .rol import Rollen, rol_mag_wisselen, rol_enum_pallet, rol2url,\
                 rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving, \
                 rol_activeer_rol, rol_activeer_functie, rol_evalueer_opnieuw
from .models import Functie, account_needs_vhpg, account_needs_otp
from .forms import ZoekBeheerdersForm, WijzigBeheerdersForm, OTPControleForm, AccepteerVHPGForm, WijzigEmailForm
from .qrcode import qrcode_get
import logging


TEMPLATE_OVERZICHT = 'functie/overzicht.dtl'
TEMPLATE_OVERZICHT_VERENIGING = 'functie/overzicht-vereniging.dtl'
TEMPLATE_WIJZIG = 'functie/wijzig.dtl'
TEMPLATE_WIJZIG_EMAIL = 'functie/wijzig-email.dtl'
TEMPLATE_BEVESTIG_EMAIL = 'functie/bevestig.dtl'
TEMPLATE_EMAIL_BEVESTIGD = 'functie/bevestigd.dtl'
TEMPLATE_WISSELVANROL = 'functie/wissel-van-rol.dtl'
TEMPLATE_VHPG_ACCEPTATIE = 'functie/vhpg-acceptatie.dtl'
TEMPLATE_VHPG_AFSPRAKEN = 'functie/vhpg-afspraken.dtl'
TEMPLATE_VHPG_OVERZICHT = 'functie/vhpg-overzicht.dtl'
TEMPLATE_OTP_CONTROLE = 'functie/otp-controle.dtl'
TEMPLATE_OTP_KOPPELEN = 'functie/otp-koppelen.dtl'
TEMPLATE_OTP_GEKOPPELD = 'functie/otp-koppelen-gelukt.dtl'

my_logger = logging.getLogger('NHBApps.Functie')


def mag_beheerder_wijzigen_of_404(request, functie):
    """ Stuur gebruiker weg als illegaal van de aanroepende view gebruik gemaakt wordt

        Wordt gebruikt door:
            WijzigView (koppelen van leden aan 1 functie) - tijdens get_queryset()
            OntvangWijzigingenView - vroeg in afhandelen POST verzoek
    """

    # test_func van WijzigView laat alleen BB, BKO, RKO of CWZ door
    # OntvangWijzigingenView heeft niet zo'n filter

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if rol_nu == Rollen.ROL_BB:
        # BB mag BKO koppelen
        if functie.rol != 'BKO':
            raise Resolver404()
        return

    if rol_nu == Rollen.ROL_CWZ:
        if functie.nhb_ver != functie_nu.nhb_ver:
            # verkeerde vereniging
            raise Resolver404()

        # CWZ or WL
        return

    # BKO, RKO, RCL

    # controleer dat deze wijziging voor de juiste competitie is
    # (voorkomt BKO 25m 1pijl probeert RKO Indoor te koppelen)
    if not functie_nu or functie_nu.comp_type != functie.comp_type:
        # CWZ verdwijnt hier ook
        raise Resolver404()

    if rol_nu == Rollen.ROL_BKO:
        if functie.rol != 'RKO':
            raise Resolver404()
        return

    elif rol_nu == Rollen.ROL_RKO:
        if functie.rol != 'RCL':
            raise Resolver404()

        # controleer of deze regio gewijzigd mag worden
        if functie.nhb_regio.rayon != functie_nu.nhb_rayon:
            raise Resolver404()
        return

    # niets hier te zoeken (RCL en andere rollen)
    raise Resolver404()


def mag_email_wijzigen_of_404(request, functie):
    """ Stuur gebruiker weg als illegaal van de aanroepende view gebruik gemaakt wordt

        Wordt gebruikt door:
            WijzigEmailView - tijdens GET en POST
    """

    # test_func van WijzigEmailView laat alleen BB, BKO, RKO, RCL of CWZ door

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    # rol mag direct onderliggende functie aanpassen:
    #   BB --> alle BKO
    #   BKO (comp_type) --> alle RKO (comp_type)
    #   RKO (comp_type) --> alle RCL (comp_type) in zijn rayon

    if rol_nu == Rollen.ROL_BB:
        # BB mag BKO email aanpassen
        if functie.rol != 'BKO':
            raise Resolver404()
        return

    # de rest is gekoppeld aan een functie
    if not functie_nu:
        raise Resolver404()     # pragma: no cover

    # rol mag zijn eigen e-mailadres aanpassen
    if functie_nu == functie:
        return

    # BKO, RKO, RCL

    # controleer dat deze wijziging voor de juiste competitie is
    # (voorkomt BKO 25m 1pijl probeert RKO Indoor te koppelen)
    if functie_nu.comp_type != functie.comp_type:
        # CWZ verdwijnt hier ook
        raise Resolver404()

    if rol_nu == Rollen.ROL_BKO:
        if functie.rol != 'RKO':
            raise Resolver404()
        return

    elif rol_nu == Rollen.ROL_RKO:
        if functie.rol != 'RCL':
            raise Resolver404()

        # controleer of deze regio gewijzigd mag worden
        if functie.nhb_regio.rayon != functie_nu.nhb_rayon:
            raise Resolver404()
        return

    # niets hier te zoeken
    raise Resolver404()


def receive_bevestiging_functie_email(request, functie):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgd wordt
        om een nieuw email adres te bevestigen voor een functie.

        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.
    """

    # het is mogelijk om meerdere keren hetzelfde e-mailadres te koppelen
    # je hebt dan meerdere mails met tijdelijke urls om te volgen
    # bij gebruik van de 1e worden alle tijdelijke urls geconsumeerd
    # maar dan wordt deze functie ook meerdere keren aangeroepen
    # na de eerste keer is nieuwe_email leeg en zou het mis gaan
    # we moeten wel steeds dezelfde template invullen en terug geven
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


set_tijdelijke_url_receiver(RECEIVER_BEVESTIG_FUNCTIE_EMAIL, receive_bevestiging_functie_email)


def functie_vraag_email_bevestiging(functie):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_url_functie_email(functie)

    text_body = "Hallo!\n\n" + \
                "Een beheerder heeft dit e-mailadres gekoppeld op de website van de NHB.\n" + \
                "Klik op onderstaande link om dit te bevestigen.\n\n" + \
                url + "\n\n" + \
                "Als je dit niet herkent, neem dan contact met ons op via info@handboogsport.nl\n\n" + \
                "Het bondsburo\n"

    mailer_queue_email(functie.nieuwe_email, 'Bevestig gebruik e-mail voor rol', text_body)


class WijzigEmailView(UserPassesTestMixin, View):

    """ Via deze view kan het e-mailadres van een functie aangepast worden """

    # class variables shared by all instances

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def _get_functie_or_404(self):
        functie_pk = self.kwargs['functie_pk']
        try:
            functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Resolver404()
        return functie

    def _render_form(self, form, functie):
        context = dict()
        context['functie'] = functie

        rol = rol_get_huidige(self.request)
        if rol == Rollen.ROL_CWZ:
            context['is_rol_cwz'] = True
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
            menu_dynamics(self.request, context, actief='vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')
            menu_dynamics(self.request, context, actief='competitie')

        context['form'] = form
        context['form_submit_url'] = reverse('Functie:wijzig-email', kwargs={'functie_pk': functie.pk})

        return render(self.request, TEMPLATE_WIJZIG_EMAIL, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        functie = self._get_functie_or_404()

        # TODO: functie.nieuwe_email opruimen als SiteTijdelijkeUrl verlopen is (of opgeruimd is)

        # BKO, RKO, RCL, CWZ mogen hun eigen contactgegevens wijzigen
        # als ze de rol aangenomen hebben
        # verder mogen ze altijd de onderliggende laag aanpassen (net als beheerders koppelen)
        mag_email_wijzigen_of_404(self.request, functie)
        form = WijzigEmailForm()
        return self._render_form(form, functie)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de OPSLAAN knop van het formulier.
        """
        functie = self._get_functie_or_404()
        mag_email_wijzigen_of_404(self.request, functie)

        form = WijzigEmailForm(self.request.POST)
        if not form.is_valid():
            # geeft het invulformulier terug voor de foutmelding + nieuwe poging
            form.add_error(None, 'E-mailadres niet geaccepteerd')
            return self._render_form(form, functie)

        # sla het nieuwe e-mailadres op
        functie.nieuwe_email = form.cleaned_data['email']
        functie.save()

        account = self.request.user
        schrijf_in_logboek(account, 'Rollen', 'Nieuw e-mailadres ingevoerd voor rol %s' % functie.beschrijving)

        # stuur email
        # (extra args zijn input voor hash, om unieke url te krijgen)
        functie_vraag_email_bevestiging(functie)

        context = dict()
        context['functie'] = functie

        # stuur terug naar het overzicht
        rol = rol_get_huidige(self.request)
        if rol == Rollen.ROL_CWZ:
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')

        return render(request, TEMPLATE_BEVESTIG_EMAIL, context)


class OntvangBeheerderWijzigingenView(View):

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        raise Resolver404()

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        functie_pk = self.kwargs['functie_pk']
        try:
            functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Resolver404()

        mag_beheerder_wijzigen_of_404(request, functie)

        form = WijzigBeheerdersForm(request.POST)
        form.full_clean()  # vult cleaned_data
        add = form.cleaned_data.get('add')
        drop = form.cleaned_data.get('drop')

        if add:
            account_pk = add
        elif drop:
            account_pk = drop
        else:
            raise Resolver404()

        try:
            account = Account.objects.get(pk=account_pk)
        except Account.DoesNotExist:
            raise Resolver404()

        if account.nhblid_set.count() > 0:
            nhblid = account.nhblid_set.all()[0]
            wie = "NHB lid %s (%s)" % (nhblid.nhb_nr, nhblid.volledige_naam())
        else:
            nhblid = None
            wie = "Account %s" % account.get_account_full_name()

        if add:
            rol_nu, functie_nu = rol_get_huidige_functie(request)
            if rol_nu == Rollen.ROL_CWZ:
                # stel zeker dat nhblid lid is bij de vereniging van functie
                if not nhblid or nhblid.bij_vereniging != functie.nhb_ver:
                    raise Resolver404()

            functie.accounts.add(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "%s is beheerder gemaakt voor functie %s" % (wie, functie.beschrijving))
        else:
            functie.accounts.remove(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "%s losgekoppeld van functie %s" % (wie, functie.beschrijving))

        return HttpResponseRedirect(reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': functie.pk}))


class WijzigBeheerdersView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders voor een functie gekozen worden """

    # class variables shared by all instances
    template_name = TEMPLATE_WIJZIG

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._form = None
        self._functie = None
        self._zoekterm = None
        self._huidige_beheerders = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        functie_pk = self.kwargs['functie_pk']
        try:
            self._functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Resolver404()

        mag_beheerder_wijzigen_of_404(self.request, self._functie)

        self._form = ZoekBeheerdersForm(self.request.GET)
        self._form.full_clean()  # vult cleaned_data

        # huidige beheerders willen we niet opnieuw vinden
        beheerder_accounts = self._functie.accounts.all()
        for account in beheerder_accounts:
            account.geo_beschrijving = ''
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                regio = nhblid.bij_vereniging.regio
                if regio.regio_nr != ADMINISTRATIEVE_REGIO:
                    account.geo_beschrijving = "regio %s / rayon %s" % (regio.regio_nr, regio.rayon.rayon_nr)
        self._huidige_beheerders = beheerder_accounts

        zoekterm = self._form.cleaned_data['zoekterm']
        if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
            self._zoekterm = zoekterm

            # let op: we koppelen een account, maar zoeken een NHB lid,
            #         om te kunnen filteren op vereniging
            #         accounts die geen NhbLid zijn worden hier niet gevonden
            qset = NhbLid.objects.\
                exclude(account=None).\
                exclude(is_actief_lid=False).\
                exclude(account__in=beheerder_accounts).\
                annotate(hele_reeks=Concat('voornaam', Value(' '), 'achternaam')).\
                annotate(nhb_nr_str=Cast('nhb_nr', CharField())).\
                filter(
                    Q(nhb_nr_str__contains=zoekterm) |
                    Q(voornaam__icontains=zoekterm) |
                    Q(achternaam__icontains=zoekterm) |
                    Q(hele_reeks__icontains=zoekterm)). \
                order_by('nhb_nr')

            rol_nu, functie_nu = rol_get_huidige_functie(self.request)
            if rol_nu == Rollen.ROL_CWZ:
                # CWZ en WL alleen uit de eigen gelederen laten kiezen
                qset = qset.filter(bij_vereniging=functie_nu.nhb_ver)

            objs = list()
            for nhblid in qset[:50]:
                account = nhblid.account
                account.geo_beschrijving = ''
                account.nhb_nr_str = str(nhblid.nhb_nr)

                if rol_nu == Rollen.ROL_CWZ:
                    account.vereniging_naam = nhblid.bij_vereniging.naam
                else:
                    regio = nhblid.bij_vereniging.regio
                    if regio.regio_nr != ADMINISTRATIEVE_REGIO:
                        account.geo_beschrijving = "regio %s / rayon %s" % (regio.regio_nr, regio.rayon.rayon_nr)

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

        if self._functie.rol == "CWZ":
            context['is_rol_cwz'] = True
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
            menu_dynamics(self.request, context, actief='vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')
            menu_dynamics(self.request, context, actief='competitie')
        return context


class OverzichtVerenigingView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders binnen een vereniging getoond en gewijzigd worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_VERENIGING

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_CWZ     # TODO: voeg ondersteuning toe voor WL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # de huidige rol bepaalt welke functies gewijzigd mogen worden
        # en de huidige functie selecteert de vereniging
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # zoek alle rollen binnen deze vereniging
        objs = Functie.objects.filter(nhb_ver=functie_nu.nhb_ver)

        # zet beheerders en wijzig_url
        for obj in objs:
            obj.beheerders = [account.volledige_naam() for account in
                              obj.accounts.only('username', 'first_name', 'last_name').all()]

            obj.wijzig_url = None
            obj.email_url = None

            # alleen CWZ mag wijzigingen doen; WL niet
            if rol_nu == Rollen.ROL_CWZ:
                obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})
                obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # als er geen wijzig knop in beeld hoeft te komen, dan kan de tabel wat smaller
        context['show_wijzig_kolom'] = False
        for obj in context['object_list']:
            if obj.wijzig_url:
                context['show_wijzig_kolom'] = True
                break   # from the for
        # for

        context['terug_url'] = reverse('Vereniging:overzicht')

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class OverzichtView(UserPassesTestMixin, ListView):

    """ Via deze view worden de huidige beheerders getoond
        met Wijzig knoppen waar de gebruiker dit mag, aan de hand van de huidige rol

        Wordt ook gebruikt om de CWZ relevante bestuurders te tonen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        # alle competitie beheerders + CWZ
        return rol in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _sorteer_functies(objs):
        """ Sorteer de functies zodat:
            18 < 25
            BKO < RKO < RCL
            op volgorde van rayon- of regionummer (oplopend)
        """
        SORT_LEVEL = {'BKO': 1,  'RKO': 2, 'RCL': 3}
        tup2obj = dict()
        sort_me = list()
        for obj in objs:
            if obj.rol == 'RKO':
                deel = obj.nhb_rayon.rayon_nr
            elif obj.rol == 'RCL':
                deel = obj.nhb_regio.regio_nr
            else:
                deel = 0

            tup = (obj.comp_type, SORT_LEVEL[obj.rol], deel)
            sort_me.append(tup)
            tup2obj[tup] = obj
        # for
        sort_me.sort()
        objs = [tup2obj[tup] for tup in sort_me]
        return objs

    def _zet_wijzig_urls(self, objs):
        """ Voeg een wijzig_url veld toe aan elk Functie object
        """
        # de huidige rol bepaalt welke functies gewijzigd mogen worden
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if rol_nu == Rollen.ROL_BB:
            wijzigbare_functie_rol = 'BKO'
        elif rol_nu == Rollen.ROL_BKO:
            wijzigbare_functie_rol = 'RKO'
        elif rol_nu == Rollen.ROL_RKO:
            wijzigbare_functie_rol = 'RCL'
            rko_rayon_nr = functie_nu.nhb_rayon.rayon_nr
        else:
            # beheerder kan niets wijzigen, maar inzien mag wel
            wijzigbare_functie_rol = "niets"

        for obj in objs:
            obj.wijzig_url = None
            if obj.rol == wijzigbare_functie_rol:
                # als BB mag je beide BKO's wijzigen
                # overige rollen alleen van hun eigen competitie type (Indoor / 25m1pijl)
                if rol_nu == Rollen.ROL_BB or obj.comp_type == functie_nu.comp_type:
                    obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})

                    # verdere begrenzing RKO: alleen 'zijn' Regio's
                    if rol_nu == Rollen.ROL_RKO and obj.rol == "RCL" and obj.nhb_regio.rayon.rayon_nr != rko_rayon_nr:
                        obj.wijzig_url = None
        # for

        wijzigbare_functie = functie_nu
        if rol_nu == Rollen.ROL_BB:
            wijzigbare_email_rol = 'BKO'
        elif rol_nu == Rollen.ROL_BKO:
            wijzigbare_email_rol = 'RKO'
        elif rol_nu == Rollen.ROL_RKO:
            wijzigbare_email_rol = 'RCL'
            rko_rayon_nr = functie_nu.nhb_rayon.rayon_nr
        else:
            # beheerder kan niets wijzigen, maar inzien mag wel
            wijzigbare_email_rol = 'niets'

        for obj in objs:
            obj.email_url = None

            if obj == wijzigbare_functie:
                obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})
            elif obj.rol == wijzigbare_email_rol:
                # als BB mag je beide BKO's wijzigen
                # overige rollen alleen van hun eigen competitie type (Indoor / 25m1pijl)
                if rol_nu == Rollen.ROL_BB or obj.comp_type == functie_nu.comp_type:
                    obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})

                    # verdere begrenzing RKO: alleen 'zijn' Regio's
                    if rol_nu == Rollen.ROL_RKO and obj.rol == "RCL" and obj.nhb_regio.rayon.rayon_nr != rko_rayon_nr:
                        obj.email_url = None
        # for

    def _zet_accounts(self, objs):
        """ als we de template door functie.accounts.all() laten lopen dan resulteert
            elke lookup in een database query voor het volledige account record.
            Hier doen we het iets efficienter.
        """
        for obj in objs:
            obj.beheerders = [account.volledige_naam() for account in obj.accounts.only('username', 'first_name', 'last_name').all()]
        # for

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # maak een lijst van de functies
        if rol_nu == Rollen.ROL_CWZ:
            # toon alleen de hierarchy vanuit deze vereniging omhoog
            functie_cwz = functie_nu
            objs = Functie.objects.select_related('nhb_rayon', 'nhb_regio').\
                                   filter(Q(rol='RCL', nhb_regio=functie_cwz.nhb_ver.regio) |
                                          Q(rol='RKO', nhb_rayon=functie_cwz.nhb_ver.regio.rayon) |
                                          Q(rol='BKO'))
        else:
            objs = Functie.objects.select_related('nhb_rayon', 'nhb_regio').\
                                   exclude(rol='CWZ')       # TODO: verander in filter(rol__in [BKO, RKO, RCL]")

        objs = self._sorteer_functies(objs)

        # zet de wijzig urls, waar toegestaan
        self._zet_wijzig_urls(objs)
        self._zet_accounts(objs)
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_CWZ:
            context['rol_is_cwz'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context


class WisselVanRolView(UserPassesTestMixin, ListView):

    """ Django class-based view om van rol te wisselen """

    # TODO: zou next parameter kunnen ondersteunen, net als login view

    # class variables shared by all instances
    template_name = TEMPLATE_WISSELVANROL

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        # evalueer opnieuw welke rechten de gebruiker heeft
        rol_evalueer_opnieuw(self.request)

        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _functie_volgorde(functie):
        if functie.rol == "BKO":
            volgorde = 10  # 10
        elif functie.rol == "RKO":
            volgorde = 20 + functie.nhb_rayon.rayon_nr  # 21-24
        elif functie.rol == "RCL":
            volgorde = functie.nhb_regio.regio_nr  # 101-116
        elif functie.rol == "CWZ":
            volgorde = functie.nhb_ver.nhb_nr  # 1000-9999
        else:
            volgorde = 0  # valt meteen op dat 'ie bovenaan komt
        return volgorde

    def _get_functies_eigen(self):
        objs = list()

        hierarchy2 = dict()      # [parent_tup] = list of child_tup
        for child_tup, parent_tup in rol_enum_pallet(self.request):
            rol, functie_pk = child_tup

            # rollen die je altijd aan moet kunnen nemen als je ze hebt
            if rol == Rollen.ROL_IT:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'IT beheerder', 'url': url, 'volgorde': 1})

            elif rol == Rollen.ROL_BB:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'Manager competitiezaken', 'url': url, 'volgorde': 2})

            elif rol == Rollen.ROL_SCHUTTER:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'Schutter', 'url': url, 'volgorde': 10000})

            elif rol == Rollen.ROL_NONE:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'Gebruiker', 'url': url, 'volgorde': 10001})

            elif parent_tup == (None, None):
                # top-level rol voor deze gebruiker - deze altijd tonen
                url = reverse('Functie:activeer-functie', kwargs={'functie_pk': functie_pk})
                functie = Functie.objects.\
                            select_related('nhb_ver').\
                            only('beschrijving', 'nhb_ver__naam').\
                            get(pk=functie_pk)
                title = functie.beschrijving
                ver_naam = ''
                if functie.nhb_ver:
                    ver_naam = functie.nhb_ver.naam
                volgorde = self._functie_volgorde(functie)
                objs.append({'titel': title, 'ver_naam': ver_naam, 'url': url, 'volgorde': volgorde})
            else:
                try:
                    hierarchy2[parent_tup].append(child_tup)
                except KeyError:
                    hierarchy2[parent_tup] = [child_tup,]
        # for

        objs.sort(key=lambda x: x['volgorde'])
        return objs, hierarchy2

    def _get_functies_help_anderen(self, hierarchy2):
        objs = list()

        # nu nog uitzoeken welke ge-erfde functies we willen tonen
        # deze staan in hierarchy
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if functie_nu:
            nu_tup = (rol_nu, functie_nu.pk)
        else:
            nu_tup = (rol_nu, None)

        try:
            child_tups = hierarchy2[nu_tup]
        except KeyError:
            # geen ge-erfde functies
            pass
        else:
            for rol, functie_pk in child_tups:
                url = reverse('Functie:activeer-functie', kwargs={'functie_pk': functie_pk})
                if rol == Rollen.ROL_CWZ:
                    functie = Functie.objects.select_related('nhb_ver').only('beschrijving', 'nhb_ver__naam').get(pk=functie_pk)
                    volgorde = self._functie_volgorde(functie)
                    objs.append({'titel': functie.beschrijving, 'ver_naam': functie.nhb_ver.naam, 'url': url, 'volgorde': volgorde})
                else:
                    functie = Functie.objects.only('beschrijving').get(pk=functie_pk)
                    volgorde = self._functie_volgorde(functie)
                    objs.append({'titel': functie.beschrijving, 'ver_naam': "", 'url': url, 'volgorde': volgorde})
            # for

        objs.sort(key=lambda x: x['volgorde'])
        return objs

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        objs, hierarchy = self._get_functies_eigen()
        objs2 = self._get_functies_help_anderen(hierarchy)

        if len(objs2):
            objs.append({'separator': True})
            objs.extend(objs2)

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['show_vhpg'], context['vhpg'] = account_needs_vhpg(self.request.user)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if account_rechten_is_otp_verified(self.request):
            context['show_otp_controle'] = False
            context['show_otp_koppelen'] = False
        else:
            if account_otp_is_gekoppeld(self.request.user):
                context['show_otp_koppelen'] = False
                context['show_otp_controle'] = True
            else:
                context['show_otp_koppelen'] = True
                context['show_otp_controle'] = False

        context['wiki_2fa_url'] = settings.WIKI_URL_2FA
        context['wiki_2fa_titel'] = 'Tweede-factor authenticatie'

        context['wiki_rollen'] = settings.WIKI_URL_ROLLEN

        # login-as functie voor IT beheerder
        if rol_get_huidige(self.request) == Rollen.ROL_IT:
            context['url_login_as'] = reverse('Account:account-wissel')

        # TODO: volgende code is alleen voor de testsuite - willen we dit live terug zien?
        context['insert_meta'] = True
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['meta_rol'] = rol2url[rol_nu]
        if functie_nu:
            context['meta_functie'] = functie_nu.beschrijving       # template doet html escaping
        else:
            context['meta_functie'] = ""

        menu_dynamics(self.request, context, actief='wissel-van-rol')
        return context


class ActiveerRolView(UserPassesTestMixin, View):
    """ Django class-based view om een andere rol aan te nemen """

    # class variables shared by all instances

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def post(self, request, *args, **kwargs):
        from_ip = get_safe_from_ip(self.request)

        if 'rol' in kwargs:
            # activeer rol
            my_logger.info('%s ROL account %s wissel naar rol %s' % (from_ip, self.request.user.username, repr(kwargs['rol'])))
            rol_activeer_rol(request, kwargs['rol'])
        else:
            # activeer functie
            my_logger.info('%s ROL account %s wissel naar functie %s' % (from_ip, self.request.user.username, repr(kwargs['functie_pk'])))
            rol_activeer_functie(request, kwargs['functie_pk'])

        rol_beschrijving = rol_get_beschrijving(request)
        my_logger.info('%s ROL account %s is nu %s' % (from_ip, self.request.user.username, rol_beschrijving))

        # stuur een aantal rollen door naar een functionele pagina
        # de rest blijft in Wissel van Rol
        rol = rol_get_huidige(request)
        if rol == Rollen.ROL_BB:
            return redirect('Competitie:overzicht')

        if rol == Rollen.ROL_CWZ:
            return redirect('Vereniging:overzicht')

        return redirect('Functie:wissel-van-rol')


class VhpgAfsprakenView(UserPassesTestMixin, TemplateView):

    """ Django class-based view om van rol te wisselen """

    # class variables shared by all instances
    template_name = TEMPLATE_VHPG_AFSPRAKEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if self.request.user.is_authenticated:
            needs_vhpg, _ = account_needs_vhpg(self.request.user, show_only=True)
            return needs_vhpg
        return False

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='wissel-van-rol')
        return context


def account_vhpg_is_geaccepteerd(account):
    """ onthoud dat de vhpg net geaccepteerd is door de gebruiker
    """
    try:
        vhpg = HanterenPersoonsgegevens.objects.get(account=account)
    except HanterenPersoonsgegevens.DoesNotExist:
        vhpg = HanterenPersoonsgegevens()
        vhpg.account = account

    vhpg.acceptatie_datum = timezone.now()
    vhpg.save()


class VhpgAcceptatieView(TemplateView):
    """ Met deze view kan de gebruiker de verklaring hanteren persoonsgegevens accepteren
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus zou hier niet moeten komen
            return HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user
        needs_vhpg, _ = account_needs_vhpg(account)
        if not needs_vhpg:
            # gebruiker heeft geen VHPG nodig
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = AccepteerVHPGForm()
        context = {'form': form}
        menu_dynamics(request, context, actief="wissel-van-rol")
        return render(request, TEMPLATE_VHPG_ACCEPTATIE, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de knop van het formulier.
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus stuur terug naar af
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = AccepteerVHPGForm(request.POST)
        if form.is_valid():
            # hier komen we alleen als de checkbox gezet is
            account = request.user
            account_vhpg_is_geaccepteerd(account)
            schrijf_in_logboek(account, 'Rollen', 'VHPG geaccepteerd')
            account_rechten_eval_now(request, account)
            return HttpResponseRedirect(reverse('Functie:wissel-van-rol'))

        # checkbox is verplicht --> nog een keer
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_VHPG_ACCEPTATIE, context)


class VhpgOverzichtView(UserPassesTestMixin, ListView):

    """ Met deze view kan de Manager Competitiezaken een overzicht krijgen van alle beheerders
        die de VHPG geaccepteerd hebben en wanneer dit voor het laatste was.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_VHPG_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if self.request.user.is_authenticated:
            rol_nu = rol_get_huidige(self.request)
            return rol_nu == Rollen.ROL_BB
        return False

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        # er zijn ongeveer 30 beheerders
        # voorlopig geen probleem als een beheerder vaker voorkomt
        return HanterenPersoonsgegevens.objects.order_by('-acceptatie_datum')[:100]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        menu_dynamics(self.request, context, actief='competitie')
        return context


class OTPControleView(TemplateView):
    """ Met deze view kan de OTP controle doorlopen worden
        Na deze controle is de gebruiker authenticated + verified
    """

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus stuur terug naar af
            return HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user
        if not account.otp_is_actief:
            # gebruiker heeft geen OTP koppeling
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = OTPControleForm()
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_CONTROLE, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """
        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus stuur terug naar af
            return HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user
        if not account.otp_is_actief:
            # gebruiker heeft geen OTP koppeling
            return HttpResponseRedirect(reverse('Plein:plein'))

        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            if account_otp_controleer(request, account, otp_code):
                # controle is gelukt (is ook al gelogd)
                # terug naar de Wissel-van-rol pagina
                return HttpResponseRedirect(reverse('Functie:wissel-van-rol'))
            else:
                # controle is mislukt (is al gelogd en in het logboek geschreven)
                form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
                # TODO: blokkeer na X pogingen

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_CONTROLE, context)


class OTPKoppelenView(TemplateView):
    """ Met deze view kan de OTP koppeling tot stand gebracht worden
    """

    @staticmethod
    def _account_needs_otp_or_redirect(request):
        """ Controleer dat het account OTP nodig heeft, of wegsturen """

        if not request.user.is_authenticated:
            # gebruiker is niet ingelogd, dus zou hier niet moeten komen
            return None, HttpResponseRedirect(reverse('Plein:plein'))

        account = request.user

        if not account_needs_otp(account):
            # gebruiker heeft geen OTP nodig
            return account, HttpResponseRedirect(reverse('Plein:plein'))

        if account.otp_is_actief:
            # gebruiker is al gekoppeld, dus niet zomaar toestaan om een ander apparaat ook te koppelen!!
            return account, HttpResponseRedirect(reverse('Plein:plein'))

        return account, None

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        account, response = self._account_needs_otp_or_redirect(request)
        if response:
            return response

        # haal de QR code op (en alles wat daar voor nodig is)
        account_otp_prepare_koppelen(account)
        qrcode = qrcode_get(account)

        tmp = account.otp_code.lower()
        secret = " ".join([tmp[i:i+4] for i in range(0, 16, 4)])

        form = OTPControleForm()
        context = {'form': form,
                   'qrcode': qrcode,
                   'otp_secret': secret }
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_KOPPELEN, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Controleer knop.
        """
        account, response = self._account_needs_otp_or_redirect(request)
        if response:
            return response

        form = OTPControleForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            if account_otp_koppel(request, account, otp_code):
                # geef de succes pagina
                context = dict()
                menu_dynamics(request, context, actief="inloggen")
                return render(request, TEMPLATE_OTP_GEKOPPELD, context)

            # controle is mislukt - is al gelogd
            form.add_error(None, 'Verkeerde code. Probeer het nog eens.')
            # TODO: blokkeer na X pogingen

        # still here --> re-render with error message
        qrcode = qrcode_get(account)
        tmp = account.otp_code.lower()
        secret = " ".join([tmp[i:i+4] for i in range(0, 16, 4)])
        context = {'form': form,
                   'qrcode': qrcode,
                   'otp_secret': secret }
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_OTP_KOPPELEN, context)


# end of file
