# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import Competitie
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
import datetime


TEMPLATE_COMPETITIE_WIJZIG_DATUMS = 'compbeheer/bb-wijzig-datums.dtl'


class WijzigDatumsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor het wijzigen van de competitie datums """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_WIJZIG_DATUMS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        context['comp'] = comp

        context['url_wijzig'] = reverse('CompBeheer:wijzig-datums',
                                        kwargs={'comp_pk': comp.pk})

        context['alle_datums'] = {
            1: comp.begin_fase_C,
            # note: begin_fase_D_indiv is nog niet in te stellen
            2: comp.begin_fase_F,
            3: comp.einde_fase_F,
            4: comp.datum_klassengrenzen_rk_bk_teams,
            5: comp.begin_fase_L_indiv,
            6: comp.einde_fase_L_indiv,
            7: comp.begin_fase_L_teams,
            8: comp.einde_fase_L_teams,
            9: comp.begin_fase_P_indiv,
            10: comp.einde_fase_P_indiv,
            11: comp.begin_fase_P_teams,
            12: comp.einde_fase_P_teams,
        }

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}),
                comp.beschrijving.replace(' competitie', '')),
            (None, 'Fase datums'),
        )

        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            --> de beheerder wil deze klassengrenzen vaststellen
        """
        try:
            comp_pk = int(kwargs['comp_pk'][:6])      # afkappen voor de veiligheid
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, Competitie.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        datums = list()
        for datum_nr in range(12):
            datum_s = request.POST.get('datum%s' % (datum_nr + 1), None)
            if not datum_s:
                # alle datums zijn verplicht
                raise Http404('Verplichte parameter ontbreekt')

            try:
                datum_p = datetime.datetime.strptime(datum_s, '%Y-%m-%d')
            except ValueError:
                raise Http404('Geen valide datum')

            datums.append(datum_p.date())
        # for

        datums.insert(0, None)      # dummy
        comp.begin_fase_C = datums[1]
        # note: begin_fase_D_indiv is nog niet in te stellen
        comp.begin_fase_F = datums[2]
        comp.einde_fase_F = datums[3]
        comp.datum_klassengrenzen_rk_bk_teams = datums[4]
        comp.begin_fase_L_indiv = datums[5]
        comp.einde_fase_L_indiv = datums[6]
        comp.begin_fase_L_teams = datums[7]
        comp.einde_fase_L_teams = datums[8]
        comp.begin_fase_P_indiv = datums[9]
        comp.einde_fase_P_indiv = datums[10]
        comp.begin_fase_P_teams = datums[11]
        comp.einde_fase_P_teams = datums[12]
        comp.save()

        return HttpResponseRedirect(reverse('CompBeheer:overzicht',
                                            kwargs={'comp_pk': comp.pk}))


# end of file
