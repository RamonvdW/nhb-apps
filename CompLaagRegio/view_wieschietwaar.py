# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import INSCHRIJF_METHODE_1
from Competitie.models import CompetitieMatch, Regiocompetitie, RegiocompetitieSporterBoog
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie


TEMPLATE_COMPREGIO_WIESCHIETWAAR = 'complaagregio/wieschietwaar-methode1.dtl'


class WieSchietWaarView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de HWL/WL zien wanneer de leden willen schieten
        en geeft ze de mogelijkheid dit aan te passen voor het lid.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_WIESCHIETWAAR
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

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
            deelcomp_pk = int(self.kwargs['deelcomp_pk'][:6])       # afkappen voor de veiligheid
            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk,
                             inschrijf_methode=INSCHRIJF_METHODE_1))
        except (ValueError, TypeError, Regiocompetitie.DoesNotExist):
            raise Http404('Geen valide competitie')

        context['deelcomp'] = deelcomp

        objs = (RegiocompetitieSporterBoog
                .objects
                .select_related('sporterboog',
                                'sporterboog__sporter',
                                'sporterboog__boogtype')
                .prefetch_related('inschrijf_gekozen_matches')
                .filter(regiocompetitie=deelcomp,
                        bij_vereniging=self.functie_nu.vereniging)
                .order_by('sporterboog__sporter__voornaam',
                          'sporterboog__sporter__achternaam'))

        context['object_list'] = objs

        # toon alleen de wedstrijden die in gebruik zijn (anders wordt het zo veel)
        wedstrijd_pks = list()
        for obj in objs:
            obj.pks = obj.inschrijf_gekozen_matches.values_list('pk', flat=True)

            for pk in obj.pks:
                if pk not in wedstrijd_pks:         # pragma: no branch
                    wedstrijd_pks.append(pk)
        # for

        matches = (CompetitieMatch
                   .objects
                   .filter(pk__in=wedstrijd_pks)
                   .select_related('vereniging')
                   .order_by('datum_wanneer',
                             'tijd_begin_wedstrijd'))

        index2pk = dict()
        for index, match in enumerate(matches):
            index2pk[index] = match.pk
        # for
        aantal = len(index2pk)

        context['kruisjes'] = kruisjes = list()
        context['wedstrijden'] = matches
        for nummer, match in enumerate(matches, start=1):
            nummer_str = str(nummer)
            kruisjes.append(nummer_str)
            match.nummer_str = nummer_str

            match.beschrijving_str = "%s om %s bij %s in %s" % (match.datum_wanneer,
                                                                match.tijd_begin_wedstrijd,
                                                                match.vereniging.naam,
                                                                match.vereniging.plaats)

            match.waar_str = "%s in %s" % (match.vereniging.naam, match.vereniging.plaats)      # TODO: moet locatie.plaats zijn?!
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

            if self.rol_nu == Rol.ROL_HWL:
                obj.url_wijzig = reverse('CompLaagRegio:keuze-zeven-wedstrijden',
                                         kwargs={'deelnemer_pk': obj.pk})

            obj.kruisjes = list()
            for index in range(aantal):
                if index2pk[index] in obj.pks:
                    obj.kruisjes.append('X')
                else:
                    obj.kruisjes.append('')
            # for
        # for

        if self.rol_nu == Rol.ROL_HWL:
            context['afmelden_url'] = reverse('CompInschrijven:leden-ingeschreven',
                                              kwargs={'deelcomp_pk': deelcomp.pk})

        comp = deelcomp.competitie
        url_overzicht = reverse('Vereniging:overzicht')
        anker = '#competitie_%s' % comp.pk
        context['kruimels'] = (
            (url_overzicht, 'Beheer Vereniging'),
            (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
            (None, 'Wie schiet waar?')
        )

        return context

# end of file
