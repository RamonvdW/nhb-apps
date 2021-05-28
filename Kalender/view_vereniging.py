# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from .models import (KalenderWedstrijd,
                     WEDSTRIJD_DISCIPLINE_TO_STR, WEDSTRIJD_STATUS_TO_STR)
from datetime import date

TEMPLATE_KALENDER_OVERZICHT_VERENIGING = 'kalender/overzicht-vereniging.dtl'


class VerenigingKalenderWedstrijdenView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL de wedstrijden van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()
        ver = self.functie_nu.nhb_ver

        wedstrijden = (KalenderWedstrijd
                       .objects
                       .filter(organiserende_vereniging=ver)
                       .order_by('-datum_begin'))

        for wed in wedstrijden:
            wed.disc_str = WEDSTRIJD_DISCIPLINE_TO_STR[wed.discipline]
            wed.status_str = WEDSTRIJD_STATUS_TO_STR[wed.status]
            wed.url_wijzig = reverse('Kalender:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_sessies = reverse('Kalender:wijzig-sessies', kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        # vereniging kan alleen een wedstrijd beginnen als er een locatie is
        if ver.wedstrijdlocatie_set.exclude(zichtbaar=False).count() > 0:
            context['url_nieuwe_wedstrijd'] = reverse('Kalender:vereniging')
        else:
            context['geen_locatie'] = True

        menu_dynamics(self.request, context, actief='kalender')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        if request.POST.get('nieuwe_wedstrijd', ''):

            ver = self.functie_nu.nhb_ver
            locaties = ver.wedstrijdlocatie_set.exclude(zichtbaar=False)
            aantal = locaties.count()
            if aantal > 0:
                now = timezone.now()
                begin = date(now.year, now.month, now.day)

                wed = KalenderWedstrijd(
                            datum_begin=begin,
                            datum_einde=begin,
                            organiserende_vereniging=self.functie_nu.nhb_ver,
                            voorwaarden_a_status_when=now,
                            locatie=locaties[0])
                wed.save()

                # default alle bogen aan zetten
                bogen = BoogType.objects.all()
                wed.boogtypen.set(bogen)

                # default alle wedstrijdklassen kiezen die onder A-status vallen
                klassen = KalenderWedstrijdklasse.objects.exclude(leeftijdsklasse__volgens_wa=False).all()
                wed.wedstrijdklassen.set(klassen)

        url = reverse('Kalender:vereniging')
        return HttpResponseRedirect(url)


# end of file
