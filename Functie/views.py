# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.utils import timezone
from django.shortcuts import redirect, render
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account, HanterenPersoonsgegevens
from Account.otp import account_otp_prepare_koppelen, account_otp_koppel, account_otp_is_gekoppeld, account_otp_controleer
from Account.rechten import account_rechten_eval_now, account_rechten_is_otp_verified
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from .rol import Rollen, rol_mag_wisselen, rol_enum_pallet, rol2url,\
                 rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving, \
                 rol_activeer_rol, rol_activeer_functie, rol_evalueer_opnieuw
from .models import Functie, account_needs_vhpg, account_needs_otp
from .forms import ZoekBeheerdersForm, WijzigBeheerdersForm, OTPControleForm, AccepteerVHPGForm
from .qrcode import qrcode_get
import logging


TEMPLATE_OVERZICHT = 'functie/overzicht.dtl'
TEMPLATE_OVERZICHT_VERENIGING = 'functie/overzicht-vereniging.dtl'
TEMPLATE_WIJZIG = 'functie/wijzig.dtl'
TEMPLATE_WISSELVANROL = 'functie/wissel-van-rol.dtl'
TEMPLATE_VHPG_ACCEPTATIE = 'functie/vhpg-acceptatie.dtl'
TEMPLATE_VHPG_AFSPRAKEN = 'functie/vhpg-afspraken.dtl'
TEMPLATE_VHPG_OVERZICHT = 'functie/vhpg-overzicht.dtl'
TEMPLATE_OTP_CONTROLE = 'functie/otp-controle.dtl'
TEMPLATE_OTP_KOPPELEN = 'functie/otp-koppelen.dtl'
TEMPLATE_OTP_GEKOPPELD = 'functie/otp-koppelen-gelukt.dtl'

my_logger = logging.getLogger('NHBApps.Functie')


def mag_wijzigen_of_404(request, functie):
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


def account_is_lid_bij_cwz_of_404(account, functie_nu):
    """ Stel zeker dat Account lid is bij de vereniging van functie_nu """
    if len(account.nhblid_set.all()) != 1:
        raise Resolver404()

    nhblid = account.nhblid_set.all()[0]
    if nhblid.bij_vereniging != functie_nu.nhb_ver:
        raise Resolver404()


class OntvangWijzigingenView(View):

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

        mag_wijzigen_of_404(request, functie)

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

        if add:
            rol_nu, functie_nu = rol_get_huidige_functie(request)
            if rol_nu == Rollen.ROL_CWZ:
                account_is_lid_bij_cwz_of_404(account, functie_nu)

            functie.accounts.add(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "%s beheerder gemaakt voor functie %s" % (account.volledige_naam(),
                                                                         functie.beschrijving))
        else:
            functie.accounts.remove(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "Beheerder %s losgekoppeld van functie %s" % (account.volledige_naam(),
                                                                             functie.beschrijving))

        return HttpResponseRedirect(reverse('Functie:wijzig', kwargs={'functie_pk': functie.pk}))


class WijzigView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders voor een functie gekozen worden """

    template_name = TEMPLATE_WIJZIG

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = None
        self.functie = None
        self.zoekterm = None

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
            self.functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Resolver404()

        mag_wijzigen_of_404(self.request, self.functie)

        self.form = ZoekBeheerdersForm(self.request.GET)
        self.form.full_clean()  # vult cleaned_data

        zoekterm = self.form.cleaned_data['zoekterm']
        if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
            self.zoekterm = zoekterm
            qset = Account.objects.\
                       exclude(nhblid__is_actief_lid=False).\
                       annotate(hele_naam=Concat('nhblid__voornaam', Value(' '), 'nhblid__achternaam')).\
                       filter(
                            Q(username__icontains=zoekterm) |  # dekt ook nhb_nr
                            Q(nhblid__voornaam__icontains=zoekterm) |
                            Q(nhblid__achternaam__icontains=zoekterm) |
                            Q(hele_naam__icontains=zoekterm)).order_by('nhblid__nhb_nr')

            rol_nu, functie_nu = rol_get_huidige_functie(self.request)
            if rol_nu == Rollen.ROL_CWZ:
                # CWZ en WL alleen uit de eigen gelederen laten kiezen
                return qset.filter(nhblid__bij_vereniging=functie_nu.nhb_ver)

            return qset[:50]

        self.zoekterm = ""
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['functie'] = self.functie
        context['huidige_beheerders'] = self.functie.accounts.all()
        context['rol_str'] = rol_get_beschrijving(self.request)
        context['wijzig_url'] = reverse('Functie:ontvang-wijzigingen', kwargs={'functie_pk': self.functie.pk})
        context['zoek_url'] = reverse('Functie:wijzig', kwargs={'functie_pk': self.functie.pk})
        context['zoekterm'] = self.zoekterm
        context['form'] = self.form
        if self.functie.rol == "CWZ":
            context['is_rol_cwz'] = True
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')
        menu_dynamics(self.request, context, actief='competitie')
        return context


class OverzichtVerenigingView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders binnen een vereniging getoond en gewijzigd worden.
    """

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

        # zet wijzig_url
        for obj in objs:
            obj.wijzig_url = None

            # alleen CWZ mag wijzigingen doen; WL niet
            if rol_nu == Rollen.ROL_CWZ:
                obj.wijzig_url = reverse('Functie:wijzig', kwargs={'functie_pk': obj.pk})
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

        menu_dynamics(self.request, context, actief='competitie')   # TODO: overweeg 'vereniging' in menu
        return context


class OverzichtView(UserPassesTestMixin, ListView):

    """ Via deze view worden de huidige beheerders getoond
        met Wijzig knoppen waar de gebruiker dit mag, aan de hand van de huidige rol
    """

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
                if rol_nu == Rollen.ROL_BB or obj.comp_type == functie_nu.comp_type:
                    obj.wijzig_url = reverse('Functie:wijzig', kwargs={'functie_pk': obj.pk})

                    # begrens RKO tot wijzigen van 'zijn' RCLs
                    if obj.rol == "RCL" and obj.nhb_regio.rayon.rayon_nr != rko_rayon_nr:
                        obj.wijzig_url = None
        # for

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # maak een lijst van de functies
        if rol_nu == Rollen.ROL_CWZ:
            # tool alleen de hierarchy vanuit deze vereniging omhoog
            functie_cwz = functie_nu
            objs = Functie.objects.filter(Q(rol='RCL', nhb_regio=functie_cwz.nhb_ver.regio) |
                                          Q(rol='RKO', nhb_rayon=functie_cwz.nhb_ver.regio.rayon) |
                                          Q(rol='BKO'))
        else:
            objs = Functie.objects.exclude(rol='CWZ')       # TODO: verander in filter(rol__in [BKO, RKO, RCL]")

        objs = self._sorteer_functies(objs)

        # zet de wijzig urls, waar toegestaan
        self._zet_wijzig_urls(objs)
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

        rol_nu = rol_get_huidige_functie(self.request)
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

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """
        objs = list()
        objs2 = list()

        hierarchy2 = dict()      # [parent_tup] = list of child_tup
        for child_tup, parent_tup in rol_enum_pallet(self.request):
            rol, functie_pk = child_tup

            # rollen die je altijd aan moet kunnen nemen als je ze hebt
            if rol == Rollen.ROL_IT:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'IT beheerder', 'url': url})

            elif rol == Rollen.ROL_BB:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'Manager competitiezaken', 'url': url})

            elif rol == Rollen.ROL_SCHUTTER:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs2.append({'titel': 'Schutter', 'url': url})

            elif rol == Rollen.ROL_NONE:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs2.append({'titel': 'Gebruiker', 'url': url})

            elif parent_tup == (None, None):
                # top-level rol voor deze gebruiker - deze altijd tonen
                url = reverse('Functie:activeer-rol-functie', kwargs={'functie_pk': functie_pk})
                functie = Functie.objects.get(pk=functie_pk)
                title = functie.beschrijving
                if functie.nhb_ver:
                    ver_naam = functie.nhb_ver.naam
                else:
                    ver_naam = ''
                objs.append({'titel': title, 'ver_naam': ver_naam, 'url': url})

            else:
                try:
                    hierarchy2[parent_tup].append(child_tup)
                except KeyError:
                    hierarchy2[parent_tup] = [child_tup,]
        # for

        # afhankelijk van de huidige rol
        if rol_get_huidige(self.request) == Rollen.ROL_IT:
            url = reverse('Account:account-wissel')
            objs.append({'titel': 'Account wissel', 'url': url})

        # zet 'lage' functies onderaan
        objs.extend(objs2)
        del objs2

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
            objs.append({'separator': True})
            for rol, functie_pk in child_tups:
                url = reverse('Functie:activeer-rol-functie', kwargs={'functie_pk': functie_pk})
                functie = Functie.objects.get(pk=functie_pk)
                title = functie.beschrijving
                if functie.rol == "CWZ":
                    ver_naam = functie.nhb_ver.naam
                else:
                    ver_naam = ""
                objs.append({'titel': title, 'ver_naam': ver_naam, 'url': url})
            # for

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

    # TODO: verbouw naar een POST (want: wijzigt iets)
    def get(self, request, *args, **kwargs):
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

        return redirect('Functie:wissel-van-rol')


class VhpgAfsprakenView(UserPassesTestMixin, TemplateView):

    """ Django class-based view om van rol te wisselen """

    # class variables shared by all instances
    template_name = TEMPLATE_VHPG_AFSPRAKEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        if self.request.user.is_authenticated:
            needs_vhpg, _ = account_needs_vhpg(self.request.user)
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
