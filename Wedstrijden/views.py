# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek
from Plein.menu import menu_dynamics
from .models import WedstrijdLocatie, BAANTYPE2STR
from .forms import WedstrijdLocatieForm


TEMPLATE_LOCATIES = 'wedstrijden/locaties.dtl'
TEMPLATE_LOCATIE_DETAILS = 'wedstrijden/locatie-details.dtl'


class WedstrijdLocatiesView(UserPassesTestMixin, TemplateView):

    """ Deze view toon relevante wedstrijdlocaties aan beheerders """

    # class variables shared by all instances
    template_name = TEMPLATE_LOCATIES

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # BB/BKO krijgt alle locaties (geen filter)

        # RKO krijgt locaties in eigen rayon
        if rol_nu == Rollen.ROL_RKO:
            rayon_nr = functie_nu.nhb_rayon.rayon_nr
            context['filter'] = str(functie_nu.nhb_rayon)
        else:
            rayon_nr = None

        # RCL en CWZ krijgen locaties in eigen regio
        if rol_nu == Rollen.ROL_RCL:
            regio_nr = functie_nu.nhb_regio.regio_nr
            context['filter'] = str(functie_nu.nhb_regio)
        elif rol_nu == Rollen.ROL_CWZ:
            regio_nr = functie_nu.nhb_ver.regio.regio_nr
            context['filter'] = str(functie_nu.nhb_ver.regio)
        else:
            regio_nr = None

        objs = WedstrijdLocatie.objects.\
                    exclude(zichtbaar=False).\
                    order_by('pk').\
                    prefetch_related('verenigingen')        # database access booster

        context['locaties'] = lijst = list()
        for obj in objs:
            keep = False
            obj.nhb_ver = list()
            for ver in obj.verenigingen.all():
                obj.nhb_ver.append(str(ver))
                if rayon_nr:
                    # rayon filter voor RKO
                    if ver.regio.rayon.rayon_nr == rayon_nr:
                        keep = True
                elif regio_nr:
                    # regio filter voor RCL/CWZ
                    if ver.regio.regio_nr == regio_nr:
                        keep = True
                else:
                    # geen filter
                    keep = True
            # for
            if keep:
                obj.nhb_ver.sort()      # obj.verenigingen.order_by('nhb_nr') is much more expensive
                obj.details_url = reverse('Wedstrijden:locatie-details', kwargs={'locatie_pk': obj.pk})
                lijst.append(obj)
        # for

        menu_dynamics(self.request, context, actief='hetplein')
        return context


class WedstrijdLocatieDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een wedstrijdlocatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_LOCATIE_DETAILS

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        locatie_pk = kwargs['locatie_pk']
        try:
            context['locatie'] = locatie = WedstrijdLocatie.objects.get(pk=locatie_pk)
        except WedstrijdLocatie.DoesNotExist:
            raise Resolver404()

        locatie.baan_type_str = BAANTYPE2STR[locatie.baan_type]

        locatie.nhb_ver = list()
        regio = None
        for ver in locatie.verenigingen.order_by('nhb_nr'):
            regio = ver.regio
            locatie.nhb_ver.append(str(ver))
        # for
        if regio:
            # regio van de locatie afhankelijk van 1e vereniging
            context['regio'] = str(regio)

        if 'is_ver' in kwargs:
            context['terug_url'] = reverse('Vereniging:overzicht')
            context['opslaan_url'] = reverse('Wedstrijden:locatie-details-vereniging', kwargs={'locatie_pk': locatie.pk})
        else:
            context['terug_url'] = reverse('Wedstrijden:locaties')
            context['opslaan_url'] = reverse('Wedstrijden:locatie-details', kwargs={'locatie_pk': locatie.pk})

        # aantal banen waar uit gekozen kan worden
        context['banen'] = [nr for nr in range(2, 25)]

        context['readonly'] = True
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu:
            if rol_nu == Rollen.ROL_CWZ:
                if locatie.verenigingen.filter(nhb_nr=functie_nu.nhb_ver.nhb_nr).count() > 0:
                    # CWZ mag deze vereniging wijzigen
                    context['readonly'] = False
            elif rol_nu == Rollen.ROL_RCL:
                for ver in locatie.verenigingen.all():
                    if ver.regio == functie_nu.nhb_regio:
                        # dit is een vereniging in de regio van de RCL
                        context['readonly'] = False

        menu_dynamics(self.request, context, actief='hetplein')
        return context

    def post(self, request, *args, **kwargs):
        locatie_pk = kwargs['locatie_pk']
        try:
            locatie = WedstrijdLocatie.objects.get(pk=locatie_pk)
        except WedstrijdLocatie.DoesNotExist:
            raise Resolver404()

        form = WedstrijdLocatieForm(request.POST)
        if not form.is_valid():
            raise Resolver404()

        # TODO: controleer dat de gebruiker deze locatie mag wijzigen

        msgs = list()
        data = form.cleaned_data.get('baan_type')
        if locatie.baan_type != data:
            old_str = BAANTYPE2STR[locatie.baan_type]
            new_str = BAANTYPE2STR[data]
            msgs.append("baan type aangepast van '%s' naar '%s'" % (old_str, new_str))
            locatie.baan_type = data

        data = form.cleaned_data.get('banen_18m')
        if locatie.banen_18m != data:
            msgs.append("Aantal 18m banen aangepast van %s naar %s" % (locatie.banen_18m, data))
            locatie.banen_18m = data

        data = form.cleaned_data.get('banen_25m')
        if locatie.banen_25m != data:
            msgs.append("Aantal 25m banen aangepast van %s naar %s" % (locatie.banen_25m, data))
            locatie.banen_25m = data

        data = form.cleaned_data.get('max_dt')
        if locatie.max_dt_per_baan != data:
            msgs.append("Max DT per baan aangepast van %s naar %s" % (locatie.max_dt_per_baan, data))
            locatie.max_dt_per_baan = data

        if len(msgs) > 0:
            activiteit = "Aanpassingen aan locatie %s: %s" % (str(locatie), "; ".join(msgs))
            schrijf_in_logboek(request.user, 'Accommodaties', activiteit)

        data = form.cleaned_data.get('notities')
        if locatie.notities != data:
            activiteit = "Aanpassing notitie van locatie %s: %s (was %s)" % (str(locatie), repr(data), repr(locatie.notities))
            schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
            locatie.notities = data

        locatie.save()

        if 'is_ver' in kwargs:
            url = reverse('Vereniging:overzicht')
        else:
            url = reverse('Wedstrijden:locaties')

        return HttpResponseRedirect(url)


class WedstrijdLocatieDetailsVerenigingView(WedstrijdLocatieDetailsView):

    def get_context_data(self, **kwargs):
        kwargs['is_ver'] = True
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        kwargs['is_ver'] = True
        return super().post(request, *args, **kwargs)

# end of file
