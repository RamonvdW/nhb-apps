# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.db.models import Q
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from Plein.menu import menu_dynamics
from .rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving
from .models import Functie


TEMPLATE_OVERZICHT = 'functie/overzicht.dtl'
TEMPLATE_OVERZICHT_VERENIGING = 'functie/overzicht-vereniging.dtl'
TEMPLATE_OVERZICHT_EMAILS_SEC_HWL = 'functie/overzicht-emails-sec-hwl.dtl'


class OverzichtVerenigingView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders binnen een vereniging getoond en gewijzigd worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    @staticmethod
    def _sorteer(objs):
        lst = list()
        for obj in objs:
            if obj.rol == "SEC":
                nr = 1
            elif obj.rol == "HWL":
                nr = 2
            else:
                # obj.rol == "WL":
                nr = 3
            tup = (nr, obj)
            lst.append(tup)
        # for
        lst.sort()
        return [obj for _, obj in lst]

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

            mag_koppelen = False
            mag_email_wijzigen = False
            if rol_nu == Rollen.ROL_SEC and obj.rol in ('SEC', 'HWL'):
                # SEC mag andere SEC and HWL koppelen
                mag_koppelen = True
                if obj.rol != 'SEC':
                    # email voor secretaris komt uit Onze Relaties
                    mag_email_wijzigen = True
            elif rol_nu == Rollen.ROL_HWL and obj.rol in ('HWL', 'WL'):
                # HWL mag andere HWL en WL koppelen
                mag_koppelen = True
                mag_email_wijzigen = True
            elif rol_nu == Rollen.ROL_WL and obj.rol == 'WL':
                mag_email_wijzigen = True

            if mag_koppelen:
                obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})

            if mag_email_wijzigen:
                obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})
        # for

        return self._sorteer(objs)

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

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, 'Beheerders'),
        )

        menu_dynamics(self.request, context)
        return context


class OverzichtView(UserPassesTestMixin, ListView):

    """ Via deze view worden de huidige beheerders getoond
        met Wijzig knoppen waar de gebruiker dit mag, aan de hand van de huidige rol

        Wordt ook gebruikt om de HWL relevante bestuurders te tonen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle competitie beheerders + HWL
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL)

    @staticmethod
    def _sorteer_functies(objs):
        """ Sorteer de functies zodat:
            18 < 25
            BKO < RKO < RCL
            op volgorde van rayon- of regionummer (oplopend)
        """
        sort_level = {'BKO': 1,  'RKO': 2, 'RCL': 3}
        tup2obj = dict()
        sort_me = list()
        for obj in objs:
            if obj.rol == 'RKO':
                deel = obj.nhb_rayon.rayon_nr
            elif obj.rol == 'RCL':
                deel = obj.nhb_regio.regio_nr
            else:
                deel = 0

            tup = (obj.comp_type, sort_level[obj.rol], deel)
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

        rko_rayon_nr = None
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

    @staticmethod
    def _zet_accounts(objs):
        """ als we de template door functie.accounts.all() laten lopen dan resulteert
            elke lookup in een database query voor het volledige account record.
            Hier doen we het iets efficienter.
        """
        for obj in objs:
            obj.beheerders = [account.volledige_naam() for account in obj.accounts.all()]
        # for

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # maak een lijst van de functies
        if rol_nu == Rollen.ROL_HWL:
            # toon alleen de hierarchy vanuit deze vereniging omhoog
            functie_hwl = functie_nu
            objs = (Functie.objects
                    .filter(Q(rol='RCL', nhb_regio=functie_hwl.nhb_ver.regio) |
                            Q(rol='RKO', nhb_rayon=functie_hwl.nhb_ver.regio.rayon) |
                            Q(rol='BKO'))
                    .select_related('nhb_rayon', 'nhb_regio', 'nhb_regio__rayon')
                    .prefetch_related('accounts'))
        else:
            objs = (Functie.objects
                    .filter(Q(rol='BKO') | Q(rol='RKO') | Q(rol='RCL'))
                    .select_related('nhb_rayon', 'nhb_regio', 'nhb_regio__rayon')
                    .prefetch_related('accounts'))

        objs = self._sorteer_functies(objs)

        # zet de wijzig urls, waar toegestaan
        self._zet_wijzig_urls(objs)
        self._zet_accounts(objs)
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if self.rol_nu == Rollen.ROL_HWL:
            context['rol_is_hwl'] = True

        if self.rol_nu == Rollen.ROL_BB:
            context['accounts_it'] = (Account
                                      .objects
                                      .filter(is_staff=True)
                                      .order_by('username'))

            context['accounts_bb'] = (Account
                                      .objects
                                      .filter(is_BB=True)
                                      .order_by('username'))

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL):
            context['url_sec_hwl'] = reverse('Functie:sec-hwl-lid_nrs')

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Beheerders'),
        )

        menu_dynamics(self.request, context)
        return context


class OverzichtEmailsSecHwlView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de BB en geeft een knip-en-plakbaar overzicht van
        de lidnummers van alle SEC en HWL, zodat hier makkelijk een mailing voor te maken is.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_EMAILS_SEC_HWL
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle competitie beheerders + HWL
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        emails = list()
        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            context['geo_str'] = ''
            print('hoi!')
            emails = (Functie
                      .objects
                      .filter(rol__in=('HWL', 'SEC'))
                      .exclude(bevestigde_email='')
                      .values_list('bevestigde_email', flat=True))

        elif self.rol_nu == Rollen.ROL_RKO:
            rayon_nr = self.functie_nu.nhb_rayon.rayon_nr
            context['geo_str'] = ' in Rayon %s' % rayon_nr
            emails = (Functie
                      .objects
                      .filter(rol__in=('HWL', 'SEC'),
                              nhb_ver__regio__rayon__rayon_nr=rayon_nr)
                      .exclude(bevestigde_email='')
                      .values_list('bevestigde_email', flat=True))

        elif self.rol_nu == Rollen.ROL_RCL:
            regio_nr = self.functie_nu.nhb_regio.regio_nr
            context['geo_str'] = ' in regio %s' % regio_nr
            emails = (Functie
                      .objects
                      .filter(rol__in=('HWL', 'SEC'),
                              nhb_ver__regio__regio_nr=regio_nr)
                      .exclude(bevestigde_email='')
                      .values_list('bevestigde_email', flat=True))

        context['aantal'] = len(emails)
        context['emails'] = "; ".join(emails)

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (reverse('Functie:overzicht'), 'Beheerders'),
            (None, 'Beheerder e-mailadressen')
        )

        menu_dynamics(self.request, context)
        return context


# end of file
