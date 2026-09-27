# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import MAXIMALE_LEEFTIJD_JEUGD
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Sporter.models import Sporter, SporterBoog

TEMPLATE_LEDEN_VOORKEUREN = 'vereniging/leden-voorkeuren.dtl'


class LedenVoorkeurenView(UserPassesTestMixin, ListView):

    """ Deze view laat de HWL de voorkeuren van de zijn leden aanpassen
        en geeft de SEC en WL inzicht in de voorkeuren
    """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_VOORKEUREN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.mag_wijzigen = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        self.mag_wijzigen = self.rol_nu in (Rol.ROL_SEC, Rol.ROL_LA, Rol.ROL_HWL)
        return self.functie_nu and self.functie_nu.rol in ('SEC', 'HWL', 'WL', 'LA')

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # pak het huidige jaar na conversie naar lokale tijdzone
        # zodat dit ook goed gaat in de laatste paar uren van het jaar
        now = timezone.now()  # is in UTC
        now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
        huidige_jaar = now.year
        jeugdgrens = huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD
        self.huidige_jaar = huidige_jaar

        objs = list()

        # deel 1: jeugd

        # sorteer op geboorte jaar en daarna naam
        for obj in (Sporter
                    .objects
                    .filter(bij_vereniging=self.functie_nu.vereniging)
                    .filter(geboorte_datum__year__gte=jeugdgrens)
                    .select_related('account')
                    .order_by('-geboorte_datum__year',
                              'achternaam',
                              'voornaam')):

            # de wedstrijdleeftijd voor dit hele jaar, gebruik WA methode
            wedstrijdleeftijd = obj.bereken_wedstrijdleeftijd_wa(huidige_jaar)
            obj.leeftijd = wedstrijdleeftijd
            obj.is_jeugd = True

            obj.url_bondspas = reverse('Bondspas:vereniging-bondspas-van', kwargs={'lid_nr': obj.lid_nr})
            objs.append(obj)
        # for

        # deel 2: volwassenen

        # volwassenen: sorteer op naam
        for obj in (Sporter
                    .objects
                    .filter(bij_vereniging=self.functie_nu.vereniging)
                    .filter(geboorte_datum__year__lt=jeugdgrens)
                    .select_related('account')
                    .order_by('achternaam',
                              'voornaam')):

            # de wedstrijdleeftijd voor dit hele jaar, gebruik WA methode
            obj.is_jeugd = False

            if not obj.is_actief_lid:
                obj.leeftijd = huidige_jaar - obj.geboorte_datum.year

            obj.url_bondspas = reverse('Bondspas:vereniging-bondspas-van', kwargs={'lid_nr': obj.lid_nr})
            objs.append(obj)
        # for

        # zoek de laatste-inlog bij elk lid
        for sporter in objs:
            # voorkeuren van de sporters aanpassen
            if self.mag_wijzigen:
                sporter.wijzig_url = reverse('Sporter:voorkeuren-sporter',
                                             kwargs={'sporter_pk': sporter.pk})
        # for

        sporter_dict = dict()
        for sporter in objs:
            sporter.wedstrijdbogen = list()
            sporter_dict[sporter.lid_nr] = sporter
        # for

        # zoek de bogen informatie bij elk lid
        for sporterboog in (SporterBoog
                            .objects
                            .filter(voor_wedstrijd=True)
                            .select_related('sporter',
                                            'boogtype')
                            .only('sporter__lid_nr',
                                  'boogtype__beschrijving')):
            try:
                sporter = sporter_dict[sporterboog.sporter.lid_nr]
            except KeyError:
                # sporter is niet van deze vereniging
                pass
            else:
                sporter.wedstrijdbogen.append(sporterboog.boogtype.beschrijving)
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = self.functie_nu.vereniging

        # splits the ledenlijst op in jeugd, senior en inactief
        jeugd = list()
        senior = list()
        for obj in context['object_list']:
            if obj.is_actief_lid:
                if obj.is_jeugd:
                    jeugd.append(obj)
                else:
                    senior.append(obj)
        # for

        context['leden_jeugd'] = jeugd
        context['leden_senior'] = senior
        context['toon_wijzig_kolom'] = self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (None, 'Voorkeuren leden')
        )

        return context


# end of file
