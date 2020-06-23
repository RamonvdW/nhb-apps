# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Competitie.models import (DeelCompetitie, RegioCompetitieSchutterBoog,
                               LAAG_REGIO, regiocompetitie_schutterboog_aanmelden)
from Score.models import Score
from Plein.menu import menu_dynamics
from .models import SchutterVoorkeuren, SchutterBoog


TEMPLATE_INSCHRIJVEN = 'schutter/bevestig-inschrijven.dtl'


class RegiocompetitieInschrijvenBevestigView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een schutter zich inschrijven voor een competitie """

    template_name = TEMPLATE_INSCHRIJVEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])
            schutterboog_pk = int(kwargs['schutterboog_pk'][:10])

            schutterboog = SchutterBoog.objects.get(pk=schutterboog_pk)
            deelcomp = DeelCompetitie.objects.get(pk=deelcomp_pk)
        except (ValueError, KeyError):
            # vuilnis
            raise Resolver404()
        except (SchutterBoog.DoesNotExist, DeelCompetitie.DoesNotExist):
            # niet bestaand record
            raise Resolver404()

        # controleer dat schutterboog bij de ingelogde gebruiker hoort
        # controleer dat deelcompetitie bij de juist regio hoort
        account = self.request.user
        nhblid = account.nhblid_set.all()[0]      # ROL_SCHUTTER geeft bescherming tegen geen nhblid
        if schutterboog.nhblid != nhblid or deelcomp.laag != LAAG_REGIO or deelcomp.nhb_regio != nhblid.bij_vereniging.regio:
            raise Resolver404()

        # invoer geaccepteerd
        context['deelcomp'] = deelcomp
        context['schutterboog'] = schutterboog
        context['voorkeuren'], _ = SchutterVoorkeuren.objects.get_or_create(nhblid=nhblid)
        #context['voorkeuren_url'] = reverse('Schutter:voorkeuren')
        context['bevestig_url'] = reverse('Schutter:inschrijven',
                                          kwargs={'schutterboog_pk': schutterboog.pk,
                                                  'deelcomp_pk': deelcomp.pk})

        menu_dynamics(self.request, context, actief='schutter')
        return context


class RegiocompetitieInschrijvenView(View):

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de schutter op zijn profiel pagina
            de knop Inschrijven gebruikt voor een specifieke regiocompetitie en boogtype.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerd nhblid vereist
        nhblid = None
        account = request.user
        if account.is_authenticated:
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                if not (nhblid.is_actief_lid and nhblid.bij_vereniging):
                    nhblid = None
        if not nhblid:
            raise Resolver404()

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])
            schutterboog_pk = int(kwargs['schutterboog_pk'][:10])

            schutterboog = SchutterBoog.objects.get(pk=schutterboog_pk)
            deelcomp = DeelCompetitie.objects.get(pk=deelcomp_pk)
        except (ValueError, KeyError):
            # vuilnis
            raise Resolver404()
        except (SchutterBoog.DoesNotExist, DeelCompetitie.DoesNotExist):
            # niet bestaand record
            raise Resolver404()

        # controleer dat schutterboog bij de ingelogde gebruiker hoort
        # controleer dat deelcompetitie bij de juist regio hoort
        if schutterboog.nhblid != nhblid or deelcomp.laag != LAAG_REGIO or deelcomp.nhb_regio != nhblid.bij_vereniging.regio:
            raise Resolver404()

        # invoer geaccepteerd

        # zoek het aanvangsgemiddelde erbij
        afstand = deelcomp.competitie.afstand
        try:
            score = Score.objects.get(is_ag=True, schutterboog=schutterboog, afstand_meter=deelcomp.competitie.afstand)
        except Score.DoesNotExist:
            ag = None
        else:
            ag = score.waarde / 1000

        regiocompetitie_schutterboog_aanmelden(deelcomp.competitie, schutterboog, ag)

        return HttpResponseRedirect(reverse('Schutter:profiel'))


class RegiocompetitieUitschrijvenView(View):

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de schutter op zijn profiel pagina
            de knop Uitschrijven gebruikt voor een specifieke regiocompetitie.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerd nhblid vereist
        nhblid = None
        account = request.user
        if account.is_authenticated:
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                if not (nhblid.is_actief_lid and nhblid.bij_vereniging):
                    nhblid = None
        if not nhblid:
            raise Resolver404()

        # converteer en doe eerste controle op de parameters
        try:
            regiocomp_pk = int(kwargs['regiocomp_pk'][:10])
            inschrijving = RegioCompetitieSchutterBoog.objects.get(pk=regiocomp_pk)
        except (ValueError, KeyError):
            # vuilnis
            raise Resolver404()
        except RegioCompetitieSchutterBoog.DoesNotExist:
            # niet bestaand record
            raise Resolver404()

        # controleer dat deze inschrijving bij het nhblid hoort
        if inschrijving.schutterboog.nhblid != nhblid:
            raise Resolver404()

        # schrijf de schutter uit
        inschrijving.delete()

        return HttpResponseRedirect(reverse('Schutter:profiel'))


# end of file
