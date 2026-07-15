# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from Sporter.models import Sporter
from Functie.definities import Rol
from Functie.models import Functie
from Functie.rol import rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving

TEMPLATE_OVERZICHT_VERENIGING = 'functie/lijst-beheerders-vereniging.dtl'
TEMPLATE_BEHEERDERS_ALLE_VERENIGINGEN = 'functie/lijst-beheerders-alle-verenigingen.dtl'


class BeheerdersVerenigingView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders binnen een vereniging getoond en gewijzigd worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_SEC, Rol.ROL_LA, Rol.ROL_HWL, Rol.ROL_WL)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # de huidige rol bepaalt welke functies gewijzigd mogen worden
        # en de huidige functie selecteert de vereniging
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        rol2volg_nr = {'SEC': 1, 'LA': 2, 'HWL': 3, 'WL': 4}

        # zoek alle rollen binnen deze vereniging
        unsorted = list()
        for obj in (Functie
                    .objects
                    .exclude(rol='MWW')     # is ook gekoppeld aan een vereniging, maar hebben we hier niet nodig
                    .filter(vereniging=functie_nu.vereniging)):

            # zet beheerders en urls voor de knoppen
            obj.beheerders = [account.volledige_naam()
                              for account in obj.accounts.only('username', 'first_name', 'last_name').all()]

            obj.wijzig_url = None
            obj.email_url = None

            mag_koppelen = False
            mag_email_wijzigen = False
            if rol_nu == Rol.ROL_SEC and obj.rol == 'HWL':
                # SEC mag HWL koppelen
                mag_koppelen = True
                mag_email_wijzigen = True

            elif rol_nu == Rol.ROL_HWL and obj.rol in ('HWL', 'WL'):
                # HWL mag andere HWL en WL koppelen
                mag_koppelen = True
                mag_email_wijzigen = True

            elif rol_nu == Rol.ROL_WL and obj.rol == 'WL':
                mag_email_wijzigen = True

            if mag_koppelen:
                obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})

            if mag_email_wijzigen:
                obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})

            volg_nr = rol2volg_nr[obj.rol]
            tup = (volg_nr, obj.pk, obj)
            unsorted.append(tup)
        # for

        unsorted.sort()
        return [obj for _, _, obj in unsorted]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # als er geen knop in beeld hoeft te komen, dan kan de tabel wat smaller
        context['show_wijzig_kolom'] = False
        for obj in context['object_list']:
            if obj.wijzig_url:
                context['show_wijzig_kolom'] = True
                break   # from the for
        # for

        context['terug_url'] = reverse('Vereniging:overzicht')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (None, 'Beheerders'),
        )

        return context


class BeheerdersAlleVerenigingenView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders de beheerders van alle verenigingen zien.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BEHEERDERS_ALLE_VERENIGINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_BB, Rol.ROL_SUP, Rol.ROL_MLA)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol2volg_nr = {'SEC': 1, 'LA': 2, 'HWL': 3, 'WL': 4}

        pks = list()
        objs = list()
        for obj in (Functie
                    .objects
                    .filter(rol__in=('SEC', 'HWL', 'WL', 'LA'))
                    .select_related('vereniging')
                    .prefetch_related('accounts')):

            account_pks = list(obj.accounts.values_list('pk', flat=True))
            pks.extend(account_pks)

            objs.append(obj)
        # for

        pk2sporter = dict()
        for sporter in (Sporter
                        .objects
                        .filter(account__pk__in=pks)
                        .select_related('bij_vereniging',
                                        'account')):
            pk2sporter[sporter.account.pk] = sporter
        # for

        unsorted = list()
        for obj in objs:

            obj.beheerders = list()
            obj.notities = list()
            heeft_notitie = 99

            for pk in obj.accounts.values_list('pk', flat=True):
                sporter = pk2sporter[pk]

                obj.beheerders.append(sporter)

                notitie = ''
                if sporter.bij_vereniging is None:
                    notitie = 'Let op: Geen lid meer!'
                    heeft_notitie = 1

                elif obj.vereniging.ver_nr not in settings.IGNORE_CONTROLE_BEHEERDERS_VER_NRS:
                    if sporter.bij_vereniging.ver_nr != obj.vereniging.ver_nr:
                        notitie = 'Niet lid bij deze vereniging'
                        heeft_notitie = 2

                obj.notities.append(notitie)
            # for

            volg_nr = rol2volg_nr[obj.rol]
            tup = (heeft_notitie, obj.vereniging.ver_nr, volg_nr, obj.pk, obj)
            unsorted.append(tup)
        # for

        del objs

        unsorted.sort()
        return [tup[-1] for tup in unsorted]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['kruimels'] = (
            (reverse('Functie:lijst-beheerders'), 'Beheerders'),
            (None, 'Alle verenigingen'),
        )

        return context


# end of file
