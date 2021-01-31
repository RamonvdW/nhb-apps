# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Competitie.models import DeelcompetitieRonde
from Wedstrijden.models import Wedstrijd

TEMPLATE_WEDSTRIJDEN = 'vereniging/wedstrijden.dtl'


class WedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Toon de SEC, HWL, WL de wedstrijden die aan deze vereniging toegekend zijn
        of door deze vereniging georganiseerd worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        pks = (DeelcompetitieRonde
               .objects
               .filter(deelcompetitie__is_afgesloten=False,
                       plan__wedstrijden__vereniging=functie_nu.nhb_ver)
               .values_list('plan__wedstrijden', flat=True))

        wedstrijden = (Wedstrijd
                       .objects
                       .filter(pk__in=pks)
                       .order_by('datum_wanneer', 'tijd_begin_wedstrijd'))

        for obj in wedstrijden:
            # voor competitiewedstrijden wordt de beschrijving ingevuld
            # als de instellingen van de ronde opgeslagen worden
            # dit is slechts fall-back
            if obj.beschrijving == "":
                # als deze wedstrijd bij een competitieronde hoort,
                # maak er dan een passende beschrijving voor

                # Wedstrijd --> WedstrijdenPlan --> DeelcompetitieRonde
                plan = obj.wedstrijdenplan_set.all()[0]
                ronde = plan.deelcompetitieronde_set.all()[0]
                obj.beschrijving = "%s - %s" % (ronde.deelcompetitie.competitie.beschrijving,
                                                ronde.beschrijving)

            obj.toon_geen_uitslag = True
            heeft_uitslag = (obj.uitslag and obj.uitslag.scores.count() > 0)
            mag_wijzigen = not (obj.uitslag and obj.uitslag.is_bevroren)
            if rol_nu in (Rollen.ROL_HWL, Rollen.ROL_WL) and mag_wijzigen:
                # mag uitslag wijzigen
                url = reverse('Competitie:wedstrijd-uitslag-invoeren',
                              kwargs={'wedstrijd_pk': obj.pk})
                if heeft_uitslag:
                    obj.url_uitslag_aanpassen = url
                else:
                    obj.url_score_invoeren = url
                obj.toon_geen_uitslag = False
            else:
                if heeft_uitslag:
                    obj.url_uitslag_bekijken = reverse('Competitie:wedstrijd-bekijk-uitslag',
                                                       kwargs={'wedstrijd_pk': obj.pk})
                    obj.toon_geen_uitslag = False
        # for

        context['vereniging'] = functie_nu.nhb_ver
        context['huidige_rol'] = rol_get_beschrijving(self.request)
        context['wedstrijden'] = wedstrijden

        menu_dynamics(self.request, context, actief='vereniging')
        return context


# end of file
