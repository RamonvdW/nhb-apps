# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige_functie
from Competitie.models import INSCHRIJF_METHODE_1, DeelCompetitie, RegioCompetitieSchutterBoog
from Wedstrijden.models import CompetitieWedstrijd


TEMPLATE_VERENIGING_WIESCHIETWAAR = 'vereniging/competitie-wieschietwaar-methode1.dtl'


class WieSchietWaarView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de HWL/WL zien wanneer de leden willen schieten
        en geeft ze de mogelijkheid dit aan te passen voor het lid.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_VERENIGING_WIESCHIETWAAR
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.functie_nu.rol in ('HWL', 'WL')

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

        context['nhb_ver'] = self.functie_nu.nhb_ver

        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('sporterboog',
                                'sporterboog__sporter',
                                'sporterboog__boogtype')
                .prefetch_related('inschrijf_gekozen_wedstrijden')
                .filter(deelcompetitie=deelcomp,
                        bij_vereniging=self.functie_nu.nhb_ver)
                .order_by('sporterboog__sporter__voornaam',
                          'sporterboog__sporter__achternaam'))

        context['object_list'] = objs

        # toon alleen de wedstrijden die in gebruik zijn (anders wordt het zo veel)
        wedstrijd_pks = list()
        for obj in objs:
            obj.pks = obj.inschrijf_gekozen_wedstrijden.values_list('pk', flat=True)

            for pk in obj.pks:
                if pk not in wedstrijd_pks:
                    wedstrijd_pks.append(pk)
        # for

        wedstrijden = (CompetitieWedstrijd
                       .objects
                       .filter(pk__in=wedstrijd_pks)
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

            wedstrijd.waar_str = "%s in %s" % (wedstrijd.vereniging.naam, wedstrijd.vereniging.plaats)      # TODO: moet locatie.plaats zijn?!
        # for

        herhaal = 0
        for obj in objs:
            herhaal += 1
            if herhaal == (10+1):
                herhaal -= 10
                obj.herhaal_header = True
            sporter = obj.sporterboog.sporter
            obj.lid_nr = sporter.lid_nr
            obj.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

            obj.boogtype_str = obj.sporterboog.boogtype.beschrijving

            if self.rol_nu == Rollen.ROL_HWL:
                obj.url_wijzig = reverse('Sporter:keuze-zeven-wedstrijden',
                                         kwargs={'deelnemer_pk': obj.pk})

            obj.kruisjes = list()
            for index in range(aantal):
                if index2pk[index] in obj.pks:
                    obj.kruisjes.append('X')
                else:
                    obj.kruisjes.append('')
            # for
        # for

        if self.rol_nu == Rollen.ROL_HWL:
            context['afmelden_url'] = reverse('Vereniging:leden-ingeschreven', kwargs={'deelcomp_pk': deelcomp.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context

# end of file
