# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import Resolver404, reverse
from django.shortcuts import redirect
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.views.generic import ListView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Account.models import Account, account_needs_vhpg, account_is_otp_gekoppeld, user_is_otp_verified
from Overig.helpers import get_safe_from_ip
from .rol import Rollen, rol_mag_wisselen, rol_enum_pallet, rol2url,\
                 rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving, rol_is_beheerder, rol_is_CWZ,\
                 rol_activeer_rol, rol_activeer_functie, rol_evalueer_opnieuw
from .models import Functie
from .forms import ZoekBeheerdersForm, WijzigBeheerdersForm
import logging


TEMPLATE_FUNCTIE_OVERZICHT = 'functie/overzicht.dtl'
TEMPLATE_FUNCTIE_OVERZICHT_VERENIGING = 'functie/overzicht-vereniging.dtl'
TEMPLATE_FUNCTIE_WIJZIG = 'functie/wijzig.dtl'
TEMPLATE_FUNCTIE_WISSELVANROL = 'functie/wissel-van-rol.dtl'

my_logger = logging.getLogger('NHBApps.Account')


def mag_wijzigen_of_404(request, functie):
    # stuur gebruiker weg als illegaal van deze view gebruik gemaakt wordt
    rol_nu, functie_nu = rol_get_huidige_functie(request)

    # alle BB, BKO of RKO kunnen hier komen (zie test_func)

    if rol_nu == Rollen.ROL_BB:
        # BB mag BKO koppelen
        if functie.rol != 'BKO':
            raise Resolver404()
    else:
        # functie zoals BKO, RKO, RCL, CWZ

        if rol_nu == Rollen.ROL_CWZ:
            if functie.nhb_ver != functie_nu.nhb_ver:
                # verkeerde vereniging
                raise Resolver404()

            # CWZ or WL
            return

        # controleer dat deze wijziging voor de juiste competitie is
        # (voorkomt BKO 25m 1pijl probeert RKO Indoor te koppelen)
        if not functie_nu or functie_nu.comp_type != functie.comp_type:
            # CWZ verdwijnt hier ook
            raise Resolver404()

        if rol_nu == Rollen.ROL_BKO:
            if functie.rol != 'RKO':
                raise Resolver404()

        elif rol_nu == Rollen.ROL_RKO:
            if functie.rol != 'RCL':
                raise Resolver404()

            # controleer of deze regio gewijzigd mag worden
            if functie.nhb_regio.rayon != functie_nu.nhb_rayon:
                raise Resolver404()

        else:
            # niets hier te zoeken (RCL)
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
            functie.account_set.add(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "%s beheerder gemaakt voor functie %s" % (account.volledige_naam(),
                                                                         functie.beschrijving))
        else:
            functie.account_set.remove(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "Beheerder %s losgekoppeld van functie %s" % (account.volledige_naam(),
                                                                             functie.beschrijving))

        return HttpResponseRedirect(reverse('Functie:wijzig', kwargs={'functie_pk': functie.pk}))


class WijzigView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders voor een functie gekozen worden """

    template_name = TEMPLATE_FUNCTIE_WIJZIG

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
            return Account.objects.\
                       exclude(nhblid__is_actief_lid=False). \
                       annotate(hele_naam=Concat('nhblid__voornaam', Value(' '), 'nhblid__achternaam')). \
                       filter(
                            Q(username__icontains=zoekterm) |  # dekt ook nhb_nr
                            Q(nhblid__voornaam__icontains=zoekterm) |
                            Q(nhblid__achternaam__icontains=zoekterm) |
                            Q(hele_naam__icontains=zoekterm)).order_by('nhblid__nhb_nr')[:50]

        self.zoekterm = ""
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['functie'] = self.functie
        context['huidige_beheerders'] = self.functie.account_set.all()
        context['rol_str'] = rol_get_beschrijving(self.request)
        context['wijzig_url'] = reverse('Functie:ontvang-wijzigingen', kwargs={'functie_pk': self.functie.pk})
        context['zoek_url'] = reverse('Functie:wijzig', kwargs={'functie_pk': self.functie.pk})
        context['zoekterm'] = self.zoekterm
        context['form'] = self.form
        if self.functie.rol == "CWZ":
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')
        menu_dynamics(self.request, context, actief='competitie')
        return context


class OverzichtVerenigingView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders binnen een vereniging getoond en gewijzigd worden.
    """

    template_name = TEMPLATE_FUNCTIE_OVERZICHT_VERENIGING

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

    template_name = TEMPLATE_FUNCTIE_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_is_beheerder(self.request) or rol_is_CWZ(self.request)

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

        # maak een lijst van de functies
        if rol_is_CWZ(self.request):
            # tool alleen de hierarchy vanuit deze vereniging omhoog
            _, functie_cwz = rol_get_huidige_functie(self.request)
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

        if rol_is_CWZ(self.request):
            context['rol_is_cwz'] = True

        menu_dynamics(self.request, context, actief='competitie')
        return context


class WisselVanRolView(UserPassesTestMixin, ListView):

    """ Django class-based view om van rol te wisselen """

    # TODO: zou next parameter kunnen ondersteunen, net als login view

    # class variables shared by all instances
    template_name = TEMPLATE_FUNCTIE_WISSELVANROL

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
                objs.append({'titel': title, 'ver_naam': '', 'url': url})

            else:
                try:
                    hierarchy2[parent_tup].append(child_tup)
                except KeyError:
                    hierarchy2[parent_tup] = [child_tup,]
        # for

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
        context['show_otp_controle'] = False
        context['show_otp_koppelen'] = False
        context['is_verified'] = False

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if user_is_otp_verified(self.request):
            context['is_verified'] = True
        elif not account_is_otp_gekoppeld(self.request.user):
            context['show_otp_koppelen'] = True
        else:
            context['show_otp_controle'] = True

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

    # TODO: zou dit een POST moeten zijn?
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
        #return redirect('Plein:plein')


# end of file
