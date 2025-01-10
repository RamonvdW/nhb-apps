# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Account.operations.otp import otp_is_controle_gelukt
from Functie.definities import Rol, rol2url
from Functie.models import Functie
from Functie.operations import account_needs_vhpg
from Functie.rol import rol_mag_wisselen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving, RolBepaler
from Vereniging.models import Vereniging


TEMPLATE_WISSEL_VAN_ROL = 'functie/wissel-van-rol.dtl'
TEMPLATE_WISSEL_NAAR_SEC = 'functie/wissel-naar-sec.dtl'


def functie_volgorde(functie: Functie) -> int:
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
        volgorde = 20 + functie.rayon.rayon_nr        # 21-24
    elif functie.rol == "RCL":
        volgorde = functie.regio.regio_nr             # 101-116
    elif functie.rol == "SEC":
        volgorde = functie.vereniging.ver_nr          # 1000-9999
    elif functie.rol == "HWL":
        volgorde = functie.vereniging.ver_nr + 10000  # 11000-19999
    elif functie.rol == "WL":
        volgorde = functie.vereniging.ver_nr + 20000  # 21000-29999
    elif functie.rol == "SUP":
        volgorde = 50000                              # 50000
    else:  # pragma: no cover
        volgorde = 0  # bovenaan zetten zodat het meteen opvalt
    return volgorde


class WisselVanRolView(UserPassesTestMixin, TemplateView):

    """ Django class-based view om van rol te wisselen """

    # FUTURE: zou next parameter kunnen ondersteunen, net als login view

    # class variables shared by all instances
    template_name = TEMPLATE_WISSEL_VAN_ROL
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # wordt gezet in dispatch:
        self.account = None
        self.show_vhpg = False
        self.vhpg = None

        # wordt gezet in test_func:
        self.rol_bepaler = None
        self.rol_nu = None
        self.functie_nu = None

    def dispatch(self, request, *args, **kwargs):
        """ controleer of deze view gebruikt mag worden
            zo niet, stuur dan naar een andere view
        """
        if not request.user.is_authenticated:
            url = reverse('Plein:plein')
            return HttpResponseRedirect(url)

        self.account = account = get_account(self.request)

        # herhaling van VHPG acceptatie? meteen daarheen sturen
        self.show_vhpg, self.vhpg = account_needs_vhpg(account)
        if self.show_vhpg and self.vhpg is not None:
            url = reverse('Functie:vhpg-acceptatie')
            return HttpResponseRedirect(url)

        # TODO: ongewenste duplicatie van functionaliteit in "rol.*". Kan dit weg?
        if account.otp_is_actief:
            # gebruiker heeft 2FA actief en is na inlog en 2FA check hierheen gestuurd
            # als er geen rollen meer gekoppeld zijn, dan geeft test_func een foutcode 403
            if not account.is_BB and not account.is_staff and account.functie_set.count() == 0:
                # voorkom de foutcode 403 (na inlog en 2FA controle): stuur ze door naar het plein
                url = reverse('Plein:plein')
                return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view
            wordt aangeroepen NA dispatch
        """
        # al gecheckt in dispatch()
        # - self.request.user.is_authenticated:

        return rol_mag_wisselen(self.request)

    def _get_functies_eigen(self):
        """
            Geeft een lijst van eigen functies terug die altijd getoond moeten worden.
        """
        objs = list()

        for rol, functie in self.rol_bepaler.iter_directe_rollen():

            # rollen die je altijd aan moet kunnen nemen als je ze hebt
            if rol == Rol.ROL_BB:
                obj = Functie(beschrijving='Manager MH')
                obj.url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                obj.selected = (self.rol_nu == rol)
                obj.pk = 90002
                volgorde = 2
                tup = (volgorde, obj.pk, obj)
                objs.append(tup)

            elif rol == Rol.ROL_SPORTER:
                obj = Functie(beschrijving='Sporter')
                obj.url = reverse('Functie:activeer-rol', kwargs={'rol': rol2url[rol]})
                obj.selected = (self.rol_nu == rol)
                obj.pk = volgorde = 90000
                tup = (volgorde, obj.pk, obj)
                objs.append(tup)

            elif rol == Rol.ROL_NONE:  # pragma: no cover
                # wisselen naar "geen rol" kan alleen door uit te loggen
                pass

            else:
                obj = functie
                obj.ver_naam = ''
                if obj.vereniging and obj.rol != 'MWW':
                    obj.ver_naam = obj.vereniging.naam
                    if obj.vereniging.plaats:
                        obj.ver_naam += ' (' + obj.vereniging.plaats + ')'

                if self.functie_nu:
                    obj.selected = (obj.pk == self.functie_nu.pk)

                obj.url = reverse('Functie:activeer-functie',
                                  kwargs={'functie_pk': obj.pk})

                volgorde = functie_volgorde(obj)
                tup = (volgorde, obj.pk, obj)
                objs.append(tup)
        # for

        objs.sort()
        objs = [obj for _, _, obj in objs]
        return objs

    def _get_functies_help_anderen(self):
        objs = list()

        if not self.functie_nu:
            functie_nu_pk = None
        else:
            functie_nu_pk = self.functie_nu.pk

        for rol, functie in self.rol_bepaler.iter_indirecte_rollen(self.rol_nu, functie_nu_pk):

            url = reverse('Functie:activeer-functie', kwargs={'functie_pk': functie.pk})

            if rol in (Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_WL):
                # voeg de beschrijving van de vereniging toe
                volgorde = functie_volgorde(functie)

                if rol == Rol.ROL_SEC:               # pragma: no cover
                    # nergens in de hiërarchie kan je vandaag wisselen naar de HWL rol
                    kort = 'SEC'
                elif rol == Rol.ROL_HWL:
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
                volgorde = functie_volgorde(functie)
                objs.append({'titel': functie.beschrijving,
                             'ver_naam': '',
                             'url': url,
                             'volgorde': volgorde,
                             'pk': functie.pk})
        # for

        objs.sort(key=lambda x: x['volgorde'])
        return objs

    def _get_hwl_functies(self):
        # uitzoeken welke ge-erfde functies we willen tonen
        # deze staan in hierarchy

        objs = list()
        if not self.functie_nu:
            return objs

        if self.functie_nu.vereniging:
            selected_ver_nr = self.functie_nu.vereniging.ver_nr
        else:
            selected_ver_nr = -1

        for rol, functie in self.rol_bepaler.iter_indirecte_rollen(self.rol_nu, self.functie_nu.pk):
            if rol == Rol.ROL_HWL:

                if rol == Rol.ROL_SEC:               # pragma: no cover
                    # nergens in de hiërarchie kan je vandaag wisselen naar de HWL rol
                    kort = 'SEC'
                elif rol == Rol.ROL_HWL:
                    kort = 'HWL'
                else:
                    kort = 'WL'

                ver = functie.vereniging
                kort += ' %s' % ver.ver_nr

                if ver.plaats == '':
                    ver.plaats = 'onbekend'

                functie.beschrijving = 'HWL %s %s (%s)' % (ver.ver_nr, ver.naam, ver.plaats)
                functie.selected = (functie.vereniging.ver_nr == selected_ver_nr)
                functie.url = reverse('Functie:activeer-functie', kwargs={'functie_pk': functie.pk})

                tup = (functie.vereniging.ver_nr, functie)
                objs.append(tup)
        # for

        objs.sort()
        return [obj for _, obj in objs]

    @staticmethod
    def _alle_rollen_bondscompetities():
        """ Geeft twee gesorteerde lijsten van Functie terug met de rollen BKO, RKO, RCL voor de Indoor en 25m1pijl
        """
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

            obj.volgorde = functie_volgorde(obj)      # 0..29999

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

        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['show_vhpg'] = self.show_vhpg
        context['vhpg'] = self.vhpg

        if self.account.is_staff:
            # login-as voor de IT rol
            context['url_login_as'] = reverse('Account:account-wissel')

        if not self.account.otp_is_actief:
            context['show_otp_koppelen'] = True
            context['url_handleiding_beheerders'] = settings.URL_PDF_HANDLEIDING_BEHEERDERS
        else:
            # tweede factor is al gekoppeld, maar misschien nog niet gecontroleerd
            context['show_otp_controle'] = not otp_is_controle_gelukt(self.request)

        # zoek de rollen (eigen + anderen helpen)
        self.rol_bepaler = RolBepaler(self.account)

        context['eigen_rollen'] = self._get_functies_eigen()
        context['show_eigen_rollen'] = True

        context['help_rollen'] = self._get_functies_help_anderen()
        context['show_help_rollen'] = len(context['help_rollen']) > 0

        context['hwl_rollen'] = self._get_hwl_functies()
        context['show_hwl_rollen'] = len(context['hwl_rollen']) > 0

        context['url_hwl_naar_keuze'] = reverse('Functie:activeer-functie-hwl')

        if self.account.is_BB or self.account.is_staff:
            # toon snel-wissel voor bondscompetitie rollen
            # toon wissel naar HWL
            context['heeft_alle_rollen'] = True
            context['alle_18'], context['alle_25'] = self._alle_rollen_bondscompetities()

        if self.rol_nu == Rol.ROL_BB:
            # BB mag wisselen naar alle SEC
            context['url_wissel_naar_sec'] = reverse('Functie:wissel-naar-sec')

        # bedoeld voor de testsuite, maar kan geen kwaad
        context['insert_meta'] = True
        context['meta_rol'] = rol2url[self.rol_nu]
        if self.functie_nu:
            context['meta_functie'] = self.functie_nu.beschrijving       # template doet html escaping
        else:
            context['meta_functie'] = ""

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
        return rol_get_huidige(self.request) == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        ver_nr2sec = dict()
        for functie in Functie.objects.filter(rol='SEC').exclude(vereniging=None).select_related('vereniging'):
            ver_nr = functie.vereniging.ver_nr
            ver_nr2sec[ver_nr] = functie
        # for

        # maak knoppen voor alle verenigingen
        vers = (Vereniging
                .objects
                .select_related('regio',
                                'regio__rayon')
                .order_by('regio__regio_nr',
                          'ver_nr'))
        for ver in vers:
            functie_sec = ver_nr2sec.get(ver.ver_nr, None)
            if functie_sec:
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
