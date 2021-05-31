# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving
from Functie.models import Functie
from NhbStructuur.models import NhbVereniging
from Plein.menu import menu_dynamics


TEMPLATE_LIJST_VERENIGINGEN = 'vereniging/lijst-verenigingen.dtl'
TEMPLATE_CONTACT_GEEN_BEHEERDERS = 'vereniging/contact-geen-beheerders.dtl'


class LijstVerenigingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view worden kan een BKO, RKO of RCL
          de lijst van verenigingen zien, in zijn werkgebied
    """

    template_name = TEMPLATE_LIJST_VERENIGINGEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_SEC)

    def _get_verenigingen(self):

        # vul een kleine cache om vele database verzoeken te voorkomen
        hwl_functies = dict()   # [nhb_ver] = Functie()
        functie2count = dict()  # [functie.pk] = aantal
        for functie in (Functie
                        .objects
                        .select_related('nhb_ver')
                        .annotate(accounts_count=Count('accounts'))
                        .all()):
            if functie.rol == 'HWL':
                hwl_functies[functie.nhb_ver.ver_nr] = functie

            functie2count[functie.pk] = functie.accounts_count
        # for

        if self.rol_nu == Rollen.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de deelcompetitie van de functie
            return (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .filter(regio__rayon=self.functie_nu.nhb_rayon)
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('regio__regio_nr', 'ver_nr'))

        if self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # toon de landelijke lijst
            return (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('regio__regio_nr', 'ver_nr'))

        if self.rol_nu == Rollen.ROL_IT:
            # landelijke lijst + telling aantal leden
            objs = (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .prefetch_related('wedstrijdlocatie_set',
                                      'functie_set',
                                      'clusters')
                    .annotate(nhblid_set_count=Count('nhblid'))
                    .order_by('regio__regio_nr', 'ver_nr'))

            for obj in objs:
                obj.aantal_leden = obj.nhblid_set_count
                obj.aantal_beheerders = 0
                for functie in obj.functie_set.all():
                    obj.aantal_beheerders += functie2count[functie.pk]
                # for
            # for
            return objs

        # toon de lijst van verenigingen in de regio
        if self.rol_nu == Rollen.ROL_RCL:
            # het regionummer is verkrijgbaar via de deelcompetitie van de functie
            objs = (NhbVereniging
                    .objects
                    .filter(regio=self.functie_nu.nhb_regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('ver_nr'))
        else:
            # rol_nu == Rollen.ROL_HWL / ROL_SEC
            # het regionummer is verkrijgbaar via de vereniging
            objs = (NhbVereniging
                    .objects
                    .filter(regio=self.functie_nu.nhb_ver.regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('ver_nr'))

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toon_rayon'] = True
        context['toon_regio'] = True
        context['toon_cluster'] = False
        context['toon_details'] = True
        context['toon_ledental'] = False

        menu_actief = 'hetplein'

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['landelijk'] = self.rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO)

        if self.rol_nu == Rollen.ROL_IT:
            context['toon_ledental'] = True

        if self.rol_nu == Rollen.ROL_BB:
            context['contact_geen_beheerders'] = reverse('Vereniging:contact-geen-beheerders')

        if self.rol_nu == Rollen.ROL_RKO:
            context['toon_rayon'] = False

        if self.rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_SEC):
            context['toon_rayon'] = False
            context['toon_regio'] = False
            if self.rol_nu == Rollen.ROL_HWL:
                menu_actief = 'vereniging'

        context['verenigingen'] = verenigingen = self._get_verenigingen()

        # voeg de url toe voor de "details" knoppen
        for nhbver in verenigingen:

            nhbver.details_url = reverse('Vereniging:accommodatie-details',
                                         kwargs={'vereniging_pk': nhbver.pk})

            for loc in (nhbver
                        .wedstrijdlocatie_set
                        .filter(zichtbaar=True)):
                if loc.baan_type == 'E':
                    nhbver.heeft_externe_locaties = True
                elif loc.baan_type == 'B':
                    nhbver.buiten_locatie = loc
                else:
                    nhbver.locatie = loc
            # for

            if nhbver.clusters.count() > 0:
                context['toon_cluster'] = True
                letters = [cluster.letter for cluster in nhbver.clusters.all()]
                letters.sort()
                nhbver.cluster_letters = ",".join(letters)

                if not context['toon_regio']:
                    # verander in 101a,b
                    nhbver.cluster_letters = str(nhbver.regio.regio_nr) + nhbver.cluster_letters
        # for

        menu_dynamics(self.request, context, actief=menu_actief)
        return context


class GeenBeheerdersView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de BB contactgegevens ophalen van verenigingen zonder gekoppelde beheerders """

    # class variables shared by all instances
    template_name = TEMPLATE_CONTACT_GEEN_BEHEERDERS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        sec_count = dict()
        hwl_count = dict()
        alle_ver = list()
        for func in (Functie
                     .objects
                     .select_related('nhb_ver')
                     .filter(rol__in=('SEC', 'HWL'))
                     .exclude(nhb_ver__geen_wedstrijden=True)
                     .annotate(aantal_accounts=Count('accounts'))
                     .order_by('nhb_ver__ver_nr')):

            ver = func.nhb_ver
            ver_nr = ver.ver_nr
            if func.rol == 'SEC':
                sec_count[ver_nr] = func.aantal_accounts
            else:
                hwl_count[ver_nr] = func.aantal_accounts

            if ver not in alle_ver:
                alle_ver.append(ver)
        # for

        context['geen_sec'] = geen_sec = list()
        context['geen_beheerders'] = geen_beheerders = list()

        for ver in alle_ver:
            ver_nr = ver.ver_nr

            count = sec_count[ver_nr]
            if count == 0:
                geen_sec.append(ver)
                ver.nr_geen_sec = len(geen_sec)

            count += hwl_count[ver_nr]
            if count == 0:
                geen_beheerders.append(ver)
                ver.nr_geen_beheerders = len(geen_beheerders)
        # for

        menu_dynamics(self.request, context, actief='vereniging')
        return context


# end of file
