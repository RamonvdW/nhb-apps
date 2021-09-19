# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.otp import account_otp_is_gekoppeld
from Account.rechten import account_rechten_is_otp_verified
from Competitie.menu import get_url_voor_competitie
from Handleiding.views import reverse_handleiding
from NhbStructuur.models import NhbVereniging
from Plein.menu import menu_dynamics
from Overig.helpers import get_safe_from_ip
from Taken.taken import eval_open_taken
from .rol import (Rollen, rol_mag_wisselen, rol_enum_pallet, rol2url,
                  rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving,
                  rol_activeer_rol, rol_activeer_functie, rol_evalueer_opnieuw)
from .models import Functie, account_needs_vhpg
import logging


TEMPLATE_WISSEL_VAN_ROL = 'functie/wissel-van-rol.dtl'
TEMPLATE_WISSEL_NAAR_SEC = 'functie/wissel-naar-sec.dtl'

my_logger = logging.getLogger('NHBApps.Functie')


class WisselVanRolView(UserPassesTestMixin, ListView):

    """ Django class-based view om van rol te wisselen """

    # FUTURE: zou next parameter kunnen ondersteunen, net als login view

    # class variables shared by all instances
    template_name = TEMPLATE_WISSEL_VAN_ROL
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        # evalueer opnieuw welke rechten de gebruiker heeft
        rol_evalueer_opnieuw(self.request)

        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)

        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen naar tweede factor koppelen uitleg """

        if request.user.is_authenticated:
            if not account_otp_is_gekoppeld(request.user):
                return redirect('Functie:otp-koppelen-stap1')

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _functie_volgorde(functie):
        if functie.rol == "BKO":
            volgorde = 10  # 10
        elif functie.rol == "RKO":
            volgorde = 20 + functie.nhb_rayon.rayon_nr  # 21-24
        elif functie.rol == "RCL":
            volgorde = functie.nhb_regio.regio_nr       # 101-116
        elif functie.rol == "SEC":
            volgorde = functie.nhb_ver.ver_nr           # 1000-9999
        elif functie.rol == "HWL":
            volgorde = functie.nhb_ver.ver_nr + 10000   # 11000-19999
        elif functie.rol == "WL":
            volgorde = functie.nhb_ver.ver_nr + 20000   # 21000-29999
        else:             # pragma: no cover
            volgorde = 0  # valt meteen op dat 'ie bovenaan komt
        return volgorde

    def _get_functies_eigen(self):
        objs = list()

        pks = list()

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

            elif rol == Rollen.ROL_SPORTER:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'Sporter', 'url': url, 'volgorde': 90000})

            elif rol == Rollen.ROL_NONE:
                url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                objs.append({'titel': 'Gebruiker', 'url': url, 'volgorde': 90001})

            elif parent_tup == (None, None):
                # top-level rol voor deze gebruiker - deze altijd tonen
                pks.append(functie_pk)
            else:
                try:
                    hierarchy2[parent_tup].append(child_tup)
                except KeyError:
                    hierarchy2[parent_tup] = [child_tup]
        # for

        # haal alle functies met 1 database query op
        pk2func = dict()
        for obj in (Functie
                    .objects
                    .filter(pk__in=pks)
                    .select_related('nhb_ver', 'nhb_regio', 'nhb_rayon')
                    .only('beschrijving', 'rol',
                          'nhb_ver__ver_nr', 'nhb_ver__naam',
                          'nhb_rayon__rayon_nr', 'nhb_regio__regio_nr')):
            pk2func[obj.pk] = obj
        # for

        for functie_pk in pks:
            url = reverse('Functie:activeer-functie', kwargs={'functie_pk': functie_pk})
            functie = pk2func[functie_pk]
            title = functie.beschrijving
            ver_naam = ''
            if functie.nhb_ver:
                ver_naam = functie.nhb_ver.naam
            volgorde = self._functie_volgorde(functie)
            objs.append({'titel': title, 'ver_naam': ver_naam, 'url': url, 'volgorde': volgorde})
        # for

        objs.sort(key=lambda x: x['volgorde'])
        return objs, hierarchy2

    def _get_functies_help_anderen(self, hierarchy2):
        # uitzoeken welke ge-erfde functies we willen tonen
        # deze staan in hierarchy
        objs = list()

        if self.functie_nu:
            nu_tup = (self.rol_nu, self.functie_nu.pk)
        else:
            nu_tup = (self.rol_nu, None)

        try:
            child_tups = hierarchy2[nu_tup]
        except KeyError:
            # geen ge-erfde functies
            pass
        else:
            # haal alle benodigde functies met 1 query op
            pks = [pk for _, pk in child_tups]
            pk2func = dict()
            for obj in (Functie
                        .objects
                        .filter(pk__in=pks)
                        .select_related('nhb_ver', 'nhb_regio', 'nhb_rayon')
                        .only('beschrijving', 'rol',
                              'nhb_ver__ver_nr', 'nhb_ver__naam',
                              'nhb_rayon__rayon_nr', 'nhb_regio__regio_nr')):
                pk2func[obj.pk] = obj
            # for

            for rol, functie_pk in child_tups:
                url = reverse('Functie:activeer-functie', kwargs={'functie_pk': functie_pk})
                if rol in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL):
                    functie = pk2func[functie_pk]
                    volgorde = self._functie_volgorde(functie)
                    objs.append({'titel': functie.beschrijving, 'ver_naam': functie.nhb_ver.naam, 'url': url, 'volgorde': volgorde})
                else:
                    functie = pk2func[functie_pk]
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

    def _maak_alle_rollen(self):
        # maak linkjes voor alle rollen
        objs = (Functie
                .objects
                .filter(rol__in=('BKO', 'RKO', 'RCL'))
                .select_related('nhb_rayon', 'nhb_regio')
                .all())

        # alle indoor rollen
        for obj in objs:
            volgorde = self._functie_volgorde(obj)  # 0..29999
            if obj.comp_type == '25' and volgorde > 0:
                volgorde = 50000 + volgorde
                if obj.rol == 'BKO':
                    obj.comp_type_break = True
            obj.volgorde = volgorde
            obj.url = reverse('Functie:activeer-functie', kwargs={'functie_pk': obj.pk})

            if obj.rol == 'BKO':
                obj.knop_tekst = 'BKO'
            elif obj.rol == 'RKO':
                obj.knop_tekst = str(obj.nhb_rayon.rayon_nr)
            else:
                obj.knop_tekst = str(obj.nhb_regio.regio_nr)
                if obj.nhb_regio.regio_nr in (101, 109):
                    obj.insert_break = True
        # for

        output = sorted(objs, key=lambda x: x.volgorde)
        return output

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['show_vhpg'], context['vhpg'] = account_needs_vhpg(self.request.user)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # als we hier komen weten is de tweede factor gekoppeld is
        # de controle van de tweede factor moet misschien nog uitgevoerd worden
        context['show_otp_controle'] = not account_rechten_is_otp_verified(self.request)

        if context['show_vhpg']:
            context['show_beheerder_intro'] = True

        context['wiki_2fa_url'] = reverse_handleiding(self.request, settings.HANDLEIDING_2FA)
        context['wiki_rollen'] = reverse_handleiding(self.request, settings.HANDLEIDING_ROLLEN)
        context['wiki_intro_nieuwe_beheerders'] = reverse_handleiding(self.request, settings.HANDLEIDING_INTRO_NIEUWE_BEHEERDERS)

        # login-as functie voor IT beheerder
        if self.rol_nu == Rollen.ROL_IT:
            context['url_login_as'] = reverse('Account:account-wissel')

        # snel wissel kaartje voor IT en BB
        if self.rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB):
            context['heeft_alle_rollen'] = self._maak_alle_rollen()
            context['url_wissel_naar_sec'] = reverse('Functie:wissel-naar-sec')

        # bedoeld voor de testsuite, maar kan geen kwaad
        context['insert_meta'] = True
        context['meta_rol'] = rol2url[self.rol_nu]
        if self.functie_nu:
            context['meta_functie'] = self.functie_nu.beschrijving       # template doet html escaping
        else:
            context['meta_functie'] = ""

        eval_open_taken(self.request)

        menu_dynamics(self.request, context, actief='wissel-van-rol')
        return context


class WisselNaarSecretarisView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_WISSEL_NAAR_SEC
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) in (Rollen.ROL_IT, Rollen.ROL_BB)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # maak knoppen voor alle verenigingen
        vers = (NhbVereniging
                .objects
                .select_related('regio', 'regio__rayon')
                .exclude(regio__regio_nr=100)
                .prefetch_related('functie_set')
                .order_by('regio__regio_nr', 'ver_nr'))
        for ver in vers:
            try:
                functie_sec = ver.functie_set.filter(rol='SEC')[0]
            except IndexError:      # pragma: no cover
                # alleen tijdens test zonder SEC functie
                ver.url_wordt_sec = "#"
            else:
                ver.url_wordt_sec = reverse('Functie:activeer-functie',
                                            kwargs={'functie_pk': functie_sec.pk})
        # for
        context['verenigingen'] = vers

        menu_dynamics(self.request, context, actief='wissel-van-rol')
        return context


class ActiveerRolView(UserPassesTestMixin, View):
    """ Django class-based view om een andere rol aan te nemen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

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
        rol_nu, functie_nu = rol_get_huidige_functie(request)

        # if rol == Rollen.ROL_BB:
        #     return redirect('Competitie:kies')

        if rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL):
            return redirect('Vereniging:overzicht')

        if rol_nu in (Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            url = get_url_voor_competitie(functie_nu)
            # print('rol=%s, comp_type=%s, url=%s' % (functie_nu.rol, functie_nu.comp_type, url))
            if url:
                return redirect(url)

        return redirect('Functie:wissel-van-rol')


# end of file
