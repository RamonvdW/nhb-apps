# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from BasisTypen.models import BoogType
from .models import SchutterBoog

TEMPLATE_SCHUTTER_VOORKEUREN = 'schutter/voorkeuren.dtl'
TEMPLATE_SCHUTTER_VOORKEUREN_OPGESLAGEN = 'schutter/voorkeuren-opgeslagen.dtl'


class VoorkeurenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen schutters hun voorkeuren inzien en aanpassen """

    template_name = TEMPLATE_SCHUTTER_VOORKEUREN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als een POST request ontvangen is."""

        # sla de nieuwe voorkeuren op
        for obj in SchutterBoog.objects.filter(account=self.request.user):
            check_info = 'info_' + obj.boogtype.afkorting

            old_voor_wedstrijd = obj.voor_wedstrijd
            old_heeft_interesse = obj.heeft_interesse
            old_voorkeur_dutchtarget_18m = obj.voorkeur_dutchtarget_18m

            if request.POST.get('schiet_' + obj.boogtype.afkorting, None):
                obj.voor_wedstrijd = True
            else:
                obj.voor_wedstrijd = False

            if request.POST.get('info_' + obj.boogtype.afkorting, None):
                obj.heeft_interesse = True
            else:
                obj.heeft_interesse = False

            if obj.boogtype.afkorting == "R":
                if request.POST.get('voorkeur_DT_18m', None):
                    obj.voorkeur_dutchtarget_18m = True
                else:
                    obj.voorkeur_dutchtarget_18m = False

            if (old_voor_wedstrijd != obj.voor_wedstrijd or
                    old_heeft_interesse != obj.heeft_interesse or
                    old_voorkeur_dutchtarget_18m != obj.voorkeur_dutchtarget_18m):
                # wijzigingen opslaan
                obj.save()
        # for

        context = dict()
        menu_dynamics(request, context, actief='schutter')
        return render(request, TEMPLATE_SCHUTTER_VOORKEUREN_OPGESLAGEN, context)

    def _get_bogen(self):
        # TODO: control order?

        # om het simpel te houden maken we voor elk account en boogtype
        # een SchutterBoog record aan waarin de instellingen opgeslagen worden

        # kijk welke schutter-boog er al bekend zijn voor deze gebruiker
        # we maken alleen een record aan als een voorkeur opgegeven wordt
        objs = SchutterBoog.objects.filter(account=self.request.user)

        boogtypen = BoogType.objects.all()
        if len(objs) < len(boogtypen):
            # kijk welke er ontbreken en maak deze aan
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            for boogtype in boogtypen.exclude(pk__in=aanwezig):
                schutterboog = SchutterBoog()
                schutterboog.account = self.request.user
                schutterboog.boogtype = boogtype
                schutterboog.save()
            # for
            objs = SchutterBoog.objects.filter(account=self.request.user)

        for obj in objs:
            obj.check_schiet = 'schiet_' + obj.boogtype.afkorting
            obj.check_info = 'info_' + obj.boogtype.afkorting
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['bogen'] = self._get_bogen()
        context['opslaan_url'] = reverse('Schutter:voorkeuren')
        menu_dynamics(self.request, context, actief='schutter')
        return context


# end of file
