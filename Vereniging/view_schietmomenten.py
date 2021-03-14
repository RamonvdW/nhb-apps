# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie
from Competitie.models import (INSCHRIJF_METHODE_1,
                               DeelCompetitie, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog)
from Wedstrijden.models import Wedstrijd


TEMPLATE_LEDEN_SCHIETMOMENT = 'vereniging/competitie-schietmomenten-methode1.dtl'


class LedenSchietmomentView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de HWL/WL zien wanneer de leden willen schieten
        en geeft ze de mogelijkheid dit aan te passen voor het lid.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_SCHIETMOMENT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol in ('HWL', 'WL')

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelcomp_pk = int(self.kwargs['deelcomp_pk'][:6])       # afkappen geeft veiligheid
            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk,
                             inschrijf_methode=INSCHRIJF_METHODE_1))
        except (ValueError, TypeError, DeelCompetitie.DoesNotExist):
            raise Http404('Geen valide competitie')

        context['deelcomp'] = deelcomp

        # zoek alle dagdelen erbij
        pks = list()
        for ronde in (DeelcompetitieRonde
                      .objects
                      .select_related('deelcompetitie',
                                      'plan')
                      .prefetch_related('plan__wedstrijden')
                      .filter(deelcompetitie=deelcomp)):
            if not ronde.is_voor_import_oude_programma():
                pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
        # for

        wedstrijden = (Wedstrijd
                       .objects
                       .filter(pk__in=pks)
                       .select_related('vereniging')
                       .order_by('datum_wanneer',
                                 'tijd_begin_wedstrijd'))

        index2pk = dict()
        for index, wedstrijd in enumerate(wedstrijden):
            index2pk[index] = wedstrijd.pk
        # for
        aantal = len(index2pk)

        context['kruisjes'] = kruisjes = list()
        context['wedstrijden'] = wedstrijden
        for nummer, wedstrijd in enumerate(wedstrijden, start=1):
            nummer_str = str(nummer )
            kruisjes.append(nummer_str)
            wedstrijd.nummer_str = nummer_str

            wedstrijd.beschrijving_str = "%s om %s bij %s in %s" % (wedstrijd.datum_wanneer,
                                                                    wedstrijd.tijd_begin_wedstrijd,
                                                                    wedstrijd.vereniging.naam,
                                                                    wedstrijd.vereniging.plaats)
        # for

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('schutterboog',
                                'schutterboog__nhblid')
                .prefetch_related('inschrijf_gekozen_wedstrijden')
                .filter(deelcompetitie=deelcomp,
                        bij_vereniging=functie_nu.nhb_ver)
                .order_by('schutterboog__nhblid__voornaam',
                          'schutterboog__nhblid__achternaam'))

        context['object_list'] = objs

        herhaal = 0
        for obj in objs:
            herhaal += 1
            if herhaal == (10+1):
                herhaal -= 10
                obj.herhaal_header = True
            lid = obj.schutterboog.nhblid
            obj.nhb_nr = lid.nhb_nr
            obj.naam_str = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())

            if rol_nu == Rollen.ROL_HWL:
                obj.url_wijzig = reverse('Schutter:schietmomenten',
                                         kwargs={'deelnemer_pk': obj.pk})

            pks = obj.inschrijf_gekozen_wedstrijden.values_list('pk', flat=True)
            obj.kruisjes = list()
            for index in range(aantal):
                if index2pk[index] in pks:
                    obj.kruisjes.append('X')
                else:
                    obj.kruisjes.append('')
            # for
        # for

        if rol_nu == Rollen.ROL_HWL:
            context['afmelden_url'] = reverse('Vereniging:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context

# end of file
