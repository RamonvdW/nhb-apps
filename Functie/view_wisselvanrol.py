# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Account.operations.otp import otp_is_controle_gelukt
from Functie.definities import Rollen, rol2url
from Functie.models import Functie
from Functie.operations import account_needs_vhpg
from Functie.rol import (rol_mag_wisselen, rol_enum_pallet, rol_get_huidige, rol_get_huidige_functie,
                         rol_get_beschrijving, rol_bepaal_beschikbare_rollen_opnieuw)
from Taken.operations import eval_open_taken
from Vereniging.models import Vereniging


TEMPLATE_WISSEL_VAN_ROL = 'functie/wissel-van-rol.dtl'
TEMPLATE_WISSEL_NAAR_SEC = 'functie/wissel-naar-sec.dtl'


class WisselVanRolView(UserPassesTestMixin, TemplateView):

    """ Django class-based view om van rol te wisselen """

    # FUTURE: zou next parameter kunnen ondersteunen, net als login view

    # class variables shared by all instances
    template_name = TEMPLATE_WISSEL_VAN_ROL
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.account = None
        self.show_vhpg = False
        self.vhpg = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """

        if not self.request.user.is_authenticated:
            return False

        # evalueer opnieuw welke rechten de gebruiker heeft
        rol_bepaal_beschikbare_rollen_opnieuw(self.request)

        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)

        return rol_mag_wisselen(self.request)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.account = account = get_account(self.request)
            self.show_vhpg, self.vhpg = account_needs_vhpg(account)
            if self.show_vhpg and self.vhpg is not None:
                # herhaling van VHPG acceptatie: meteen daarheen sturen
                url = reverse('Functie:vhpg-acceptatie')
                return HttpResponseRedirect(url)

            if account.otp_is_actief:
                # gebruiker heeft 2FA actief en is na inlog en 2FA check hierheen gestuurd
                # als er geen rollen meer gekoppeld zijn, dan geeft test_func een foutcode 403
                if not account.is_BB and not account.is_staff and account.functie_set.count() == 0:
                    # voorkom de foutcode 403 (na inlog en 2FA controle): stuur ze door naar het plein
                    url = reverse('Plein:plein')
                    return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _functie_volgorde(functie):
        # BB heeft volgorde 2
        if functie.rol == "MWZ":
            volgorde = 4
        elif functie.rol == "MO":
            volgorde = 5
        elif functie.rol == "MWW":
            volgorde = 6
        elif functie.rol == "CS":
            volgorde = 7
        elif functie.rol == "BKO":
            volgorde = 10  # 10
        elif functie.rol == "RKO":
            volgorde = 20 + functie.rayon.rayon_nr  # 21-24
        elif functie.rol == "RCL":
            volgorde = functie.regio.regio_nr       # 101-116
        elif functie.rol == "SEC":
            volgorde = functie.vereniging.ver_nr           # 1000-9999
        elif functie.rol == "HWL":
            volgorde = functie.vereniging.ver_nr + 10000   # 11000-19999
        elif functie.rol == "WL":
            volgorde = functie.vereniging.ver_nr + 20000   # 21000-29999
        elif functie.rol == "SUP":
            volgorde = 50000
        else:             # pragma: no cover
            volgorde = 0  # bovenaan zetten zodat het meteen opvalt
        return volgorde

    def _get_functies_eigen(self):
        objs = list()

        pks = list()

        hierarchy2 = dict()      # [parent_tup] = list of child_tup
        for child_tup, parent_tup in rol_enum_pallet(self.account, self.request):
            rol, functie_pk = child_tup

            # rollen die je altijd aan moet kunnen nemen als je ze hebt
            if rol == Rollen.ROL_BB:
                obj = Functie(beschrijving='Manager MH')
                obj.url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                obj.selected = (self.rol_nu == rol)
                obj.pk = 90002
                volgorde = 2
                tup = (volgorde, obj.pk, obj)
                objs.append(tup)

            elif rol == Rollen.ROL_SPORTER:
                obj = Functie(beschrijving='Sporter')
                obj.url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                obj.selected = (self.rol_nu == rol)
                obj.pk = volgorde = 90000
                tup = (volgorde, obj.pk, obj)
                objs.append(tup)

            elif rol == Rollen.ROL_NONE:        # pragma: no cover
                # wisselen naar "geen rol" kan alleen door uit te loggen
                pass

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
        for obj in (Functie
                    .objects
                    .filter(pk__in=pks)
                    .select_related('vereniging',
                                    'regio',
                                    'rayon')
                    .only('beschrijving',
                          'rol',
                          'vereniging__ver_nr',
                          'vereniging__naam',
                          'vereniging__plaats',
                          'rayon__rayon_nr',
                          'regio__regio_nr')):

            obj.ver_naam = ''
            if obj.vereniging and obj.rol != 'MWW':
                obj.ver_naam = obj.vereniging.naam
                if obj.vereniging.plaats:
                    obj.ver_naam += ' (' + obj.vereniging.plaats + ')'

            if self.functie_nu:
                obj.selected = (obj.pk == self.functie_nu.pk)

            obj.url = reverse('Functie:activeer-functie',
                              kwargs={'functie_pk': obj.pk})

            volgorde = self._functie_volgorde(obj)
            tup = (volgorde, obj.pk, obj)
            objs.append(tup)
        # for

        objs.sort()
        objs = [obj for _, _, obj in objs]
        return objs, hierarchy2

    def _get_functies_help_anderen(self, hierarchy2):
        # uitzoeken welke ge-erfde functies we willen tonen
        # deze staan in hierarchy
        objs = list()
        hwls = list()

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
                        .select_related('vereniging',
                                        'regio',
                                        'rayon')
                        .only('beschrijving',
                              'rol',
                              'vereniging__ver_nr',
                              'vereniging__naam',
                              'vereniging__plaats',
                              'rayon__rayon_nr',
                              'regio__regio_nr')):
                pk2func[obj.pk] = obj
            # for

            if self.functie_nu and self.functie_nu.vereniging:
                selected_hwl = self.functie_nu.vereniging.ver_nr
            else:
                selected_hwl = -1

            for rol, functie_pk in child_tups:
                url = reverse('Functie:activeer-functie', kwargs={'functie_pk': functie_pk})

                if rol in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL):
                    # voeg de beschrijving van de vereniging toe
                    functie = pk2func[functie_pk]
                    volgorde = self._functie_volgorde(functie)

                    if rol == Rollen.ROL_SEC:               # pragma: no cover
                        # nergens in de hiërarchie kan je vandaag wisselen naar de HWL rol
                        kort = 'SEC'
                    elif rol == Rollen.ROL_HWL:
                        kort = 'HWL'
                    else:
                        kort = 'WL'

                    ver = functie.vereniging
                    kort += ' %s' % ver.ver_nr

                    if ver.plaats == '':
                        ver.plaats = 'onbekend'

                    objs.append({'titel': functie.beschrijving,
                                 'kort': kort,
                                 'ver_naam': '%s (%s)' % (ver.naam, ver.plaats),
                                 'url': url,
                                 'volgorde': volgorde,
                                 'pk': functie.pk})
                else:
                    functie = pk2func[functie_pk]
                    volgorde = self._functie_volgorde(functie)
                    objs.append({'titel': functie.beschrijving,
                                 'ver_naam': '',
                                 'url': url,
                                 'volgorde': volgorde,
                                 'pk': functie.pk})

                if rol == Rollen.ROL_HWL:
                    func = pk2func[functie_pk]

                    ver = functie.vereniging
                    # if ver.plaats == '':
                    #     ver.plaats = 'onbekend'       # is hierboven al gedaan

                    func.beschrijving = 'HWL %s %s (%s)' % (ver.ver_nr, ver.naam, ver.plaats)
                    func.selected = (functie.vereniging.ver_nr == selected_hwl)
                    func.url = url

                    tup = (functie.vereniging.ver_nr, func)
                    hwls.append(tup)
            # for

        objs.sort(key=lambda x: x['volgorde'])

        hwls.sort()
        hwls = [func for _, func in hwls]

        return objs, hwls

    def _maak_alle_rollen(self):
        # maak linkjes voor alle rollen

        alle_18 = list()
        alle_25 = list()

        for obj in (Functie
                    .objects
                    .filter(rol__in=('BKO', 'RKO', 'RCL'))
                    .select_related('rayon',
                                    'regio')
                    .all()):

            if obj.comp_type == '25':
                alle_25.append(obj)
            else:
                alle_18.append(obj)

            obj.volgorde = self._functie_volgorde(obj)  # 0..29999

            obj.url = reverse('Functie:activeer-functie', kwargs={'functie_pk': obj.pk})

            if obj.rol == 'BKO':
                obj.tekst_kort = obj.tekst_lang = 'BKO'
                obj.do_break_selective = True
                obj.ruimte = True
            elif obj.rol == 'RKO':
                obj.tekst_kort = "RKO%s" % obj.rayon.rayon_nr
                obj.tekst_lang = "RKO rayon %s" % obj.rayon.rayon_nr
                if obj.rayon.rayon_nr == 4:
                    obj.do_break = True
            else:
                obj.tekst_kort = "RCL%s" % obj.regio.regio_nr
                obj.tekst_lang = "RCL regio %s" % obj.regio.regio_nr
        # for

        alle_18.sort(key=lambda x: x.volgorde)
        alle_25.sort(key=lambda x: x.volgorde)

        return alle_18, alle_25

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # als je hier komt dan is OTP nodig

        context['show_vhpg'] = self.show_vhpg
        context['vhpg'] = self.vhpg
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if self.account.is_staff:
            context['url_admin_site'] = reverse('admin:index')
            context['url_login_as'] = reverse('Account:account-wissel')

        if not self.account.otp_is_actief:
            context['show_otp_koppelen'] = True
            context['url_handleiding_beheerders'] = settings.URL_PDF_HANDLEIDING_BEHEERDERS
        else:
            # tweede factor is al gekoppeld, maar misschien nog niet gecontroleerd
            context['show_otp_controle'] = not otp_is_controle_gelukt(self.request)

        # zoek de rollen (eigen + helpen)
        context['eigen_rollen'], hierarchy = self._get_functies_eigen()
        context['help_rollen'], context['hwl_rollen'] = self._get_functies_help_anderen(hierarchy)
        context['show_eigen_rollen'] = True
        context['show_hwl_rollen'] = len(context['hwl_rollen']) > 0
        context['show_help_rollen'] = len(context['help_rollen']) > 0
        context['url_hwl_naar_keuze'] = reverse('Functie:activeer-functie-hwl')

        # snel wissel kaartje voor BB
        if self.account.is_BB or self.account.is_staff:
            context['heeft_alle_rollen'] = True
            context['alle_18'], context['alle_25'] = self._maak_alle_rollen()

        if self.rol_nu == Rollen.ROL_BB:
            context['url_wissel_naar_sec'] = reverse('Functie:wissel-naar-sec')

        # bedoeld voor de testsuite, maar kan geen kwaad
        context['insert_meta'] = True
        context['meta_rol'] = rol2url[self.rol_nu]
        if self.functie_nu:
            context['meta_functie'] = self.functie_nu.beschrijving       # template doet html escaping
        else:
            context['meta_functie'] = ""

        eval_open_taken(self.request)

        context['kruimels'] = (
            (None, 'Wissel van rol'),
        )

        return context


class WisselNaarSecretarisView(UserPassesTestMixin, TemplateView):

    # class variables shared by all instances
    template_name = TEMPLATE_WISSEL_NAAR_SEC
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rollen.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # maak knoppen voor alle verenigingen
        vers = (Vereniging
                .objects
                .select_related('regio',
                                'regio__rayon')
                # .exclude(regio__regio_nr=100)
                .prefetch_related('functie_set')
                .order_by('regio__regio_nr',
                          'ver_nr'))
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

        context['kruimels'] = (
            (reverse('Functie:wissel-van-rol'), 'Wissel van rol'),
            (None, 'Secretaris')
        )

        return context


# end of file
