# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.db.models import Q
from django.views.generic import ListView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from Functie.definities import Rol
from Functie.models import Functie
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving

TEMPLATE_OVERZICHT = 'functie/beheerders.dtl'


class LijstBeheerdersView(UserPassesTestMixin, ListView):

    """ Via deze view worden de huidige beheerders getoond
        met Wijzig knoppen waar de gebruiker dit mag, aan de hand van de huidige rol

        Wordt ook gebruikt om de HWL relevante bestuurders te tonen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle competitie beheerders + HWL
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MO, Rol.ROL_MWZ, Rol.ROL_MWW, Rol.ROL_MLA, Rol.ROL_SUP,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_SEC, Rol.ROL_HWL, Rol.ROL_WL,
                               Rol.ROL_CS)

    @staticmethod
    def _sorteer_functies(objs):
        """ Sorteer de functies zodat:
            MWZ < MLA < MO < MWW  < CS < SUP < rest
            18 < 25
            BKO < RKO < RCL
            op volgorde van rayon- of regionummer (oplopend)
        """
        sort_level = {'MWZ': 1, 'MLA': 2, 'MO': 3, 'MWW': 4, 'CS': 5, 'SUP': 6, 'BKO': 7, 'RKO': 8, 'RCL': 9}
        tup2obj = dict()
        sort_me = list()
        for obj in objs:
            if obj.rol == 'RKO':
                deel = obj.rayon.rayon_nr
            elif obj.rol == 'RCL':
                deel = obj.regio.regio_nr
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
        rko_rayon_nr = None
        wijzigbare_functie = self.functie_nu
        wijzigbare_functie_rollen = ()
        wijzigbare_email_rollen = ()

        if self.rol_nu == Rol.ROL_BB:
            wijzigbare_functie_rollen = ('BKO', 'CS', 'MWW', 'MO', 'MWZ', 'MLA', 'SUP')
            wijzigbare_email_rollen = ('BKO', 'CS', 'MWW', 'MO', 'MWZ', 'MLA', 'SUP')

        elif self.rol_nu == Rol.ROL_BKO:
            wijzigbare_functie_rollen = ('RKO',)
            wijzigbare_email_rollen = ('RKO',)

        elif self.rol_nu == Rol.ROL_RKO:
            wijzigbare_functie_rollen = ('RCL',)
            wijzigbare_email_rollen = ('RCL',)
            rko_rayon_nr = self.functie_nu.rayon.rayon_nr

        for obj in objs:
            obj.wijzig_url = None
            obj.email_url = None

            if obj.rol in wijzigbare_functie_rollen:
                obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})

                # competitie beheerders: alleen van hun eigen competitie type (Indoor / 25m1pijl)
                if self.rol_nu in (Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
                    if obj.comp_type != self.functie_nu.comp_type:
                        obj.wijzig_url = None

                # verdere begrenzing RKO: alleen 'zijn' Regio's
                if self.rol_nu == Rol.ROL_RKO and obj.rol == "RCL" and obj.regio.rayon.rayon_nr != rko_rayon_nr:
                    obj.wijzig_url = None

            if obj == wijzigbare_functie or obj.rol in wijzigbare_email_rollen:
                obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})

                # competitie beheerders: alleen van hun eigen competitie type (Indoor / 25m1pijl)
                if self.rol_nu in (Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL):
                    if obj.comp_type != self.functie_nu.comp_type:
                        obj.email_url = None

                # verdere begrenzing RKO: alleen 'zijn' Regio's
                if self.rol_nu == Rol.ROL_RKO and obj.rol == "RCL" and obj.regio.rayon.rayon_nr != rko_rayon_nr:
                    obj.email_url = None
        # for

    @staticmethod
    def _zet_accounts(objs):
        """ als we de template door functie.accounts.all() laten lopen dan resulteert
            elke lookup in een database query voor het volledige account record.
            Hier doen we het iets efficiënter.
        """
        for obj in objs:
            obj.beheerders = [account.volledige_naam() for account in obj.accounts.all()]
        # for

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # maak een lijst van de functies
        if self.rol_nu == Rol.ROL_HWL:
            # toon alleen de hierarchy vanuit deze vereniging omhoog
            functie_hwl = self.functie_nu
            objs = (Functie.objects
                    .filter(Q(rol='RCL', regio=functie_hwl.vereniging.regio) |
                            Q(rol='RKO', rayon=functie_hwl.vereniging.regio.rayon) |
                            Q(rol='BKO'))
                    .select_related('rayon',
                                    'regio',
                                    'regio__rayon')
                    .prefetch_related('accounts'))
        else:
            objs = (Functie.objects
                    .filter(rol__in=('BKO', 'RKO', 'RCL', 'MWZ', 'MWW', 'MLA', 'SUP', 'MO', 'CS'))
                    .select_related('rayon',
                                    'regio',
                                    'regio__rayon')
                    .prefetch_related('accounts'))

        objs = self._sorteer_functies(objs)

        # zet de wijzig-urls, waar toegestaan
        self._zet_wijzig_urls(objs)
        self._zet_accounts(objs)
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if self.rol_nu == Rol.ROL_HWL:
            context['rol_is_hwl'] = True

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_SUP):
            context['accounts_it'] = (Account
                                      .objects
                                      .filter(is_staff=True)
                                      .order_by('username'))

            context['accounts_bb'] = (Account
                                      .objects
                                      .filter(is_BB=True)
                                      .order_by('username'))

        if self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_BKO, Rol.ROL_RKO):
            context['url_rcl'] = reverse('Functie:emails-beheerders')

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (None, 'Beheerders'),
        )

        return context

# end of file
