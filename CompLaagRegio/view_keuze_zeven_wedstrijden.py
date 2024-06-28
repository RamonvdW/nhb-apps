# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Competitie.definities import INSCHRIJF_METHODE_1
from Competitie.models import CompetitieMatch, RegiocompetitieRonde, RegiocompetitieSporterBoog


TEMPLATE_SPORTER_KEUZE7WEDSTRIJDEN = 'complaagregio/keuze-zeven-wedstrijden-methode1.dtl'


class KeuzeZevenWedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen sporters hun gekozen zeven wedstrijden kiezen (inschrijfmethode 1)"""

    template_name = TEMPLATE_SPORTER_KEUZE7WEDSTRIJDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) in (Rollen.ROL_SPORTER, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelnemer_pk = int(self.kwargs['deelnemer_pk'][:6])       # afkappen voor de veiligheid
            deelnemer = (RegiocompetitieSporterBoog
                         .objects
                         .select_related('regiocompetitie',
                                         'regiocompetitie__competitie')
                         .get(pk=deelnemer_pk,
                              regiocompetitie__inschrijf_methode=INSCHRIJF_METHODE_1))
        except (ValueError, TypeError, RegiocompetitieSporterBoog.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        context['deelnemer'] = deelnemer
        comp = deelnemer.regiocompetitie.competitie

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if rol_nu == Rollen.ROL_SPORTER:
            account = get_account(self.request)
            if account != deelnemer.sporterboog.sporter.account:
                raise PermissionDenied()
        else:
            # HWL: sporter moet lid zijn van zijn vereniging
            if deelnemer.bij_vereniging != functie_nu.vereniging:
                raise PermissionDenied('Sporter is niet van jouw vereniging')

            context['is_hwl'] = True

        # zoek alle dagdelen erbij
        pks = list()
        for ronde in (RegiocompetitieRonde
                      .objects
                      .select_related('regiocompetitie')
                      .prefetch_related('matches')
                      .filter(regiocompetitie=deelnemer.regiocompetitie)):
            pks.extend(ronde.matches.values_list('pk', flat=True))
        # for

        wedstrijden = (CompetitieMatch
                       .objects
                       .filter(pk__in=pks)
                       .exclude(vereniging__isnull=True)  # voorkom wedstrijd niet toegekend aan vereniging
                       .select_related('vereniging')
                       .order_by('datum_wanneer',
                                 'tijd_begin_wedstrijd'))

        keuze = list(deelnemer.inschrijf_gekozen_matches.values_list('pk', flat=True))

        # splits de wedstrijden op naar in-cluster en out-of-cluster
        ver = deelnemer.sporterboog.sporter.bij_vereniging
        ver_in_hwl_cluster = dict()  # [ver_nr] = True/False
        for cluster in (ver
                        .clusters
                        .prefetch_related('vereniging_set')
                        .filter(gebruik=deelnemer.regiocompetitie.competitie.afstand)
                        .all()):
            ver_nrs = list(cluster.vereniging_set.values_list('ver_nr', flat=True))
            for ver_nr in ver_nrs:
                ver_in_hwl_cluster[ver_nr] = True
            # for
        # for

        wedstrijden1 = list()
        wedstrijden2 = list()
        for wedstrijd in wedstrijden:
            wedstrijd.is_gekozen = (wedstrijd.pk in keuze)

            if wedstrijd.is_gekozen:
                wedstrijden1.append(wedstrijd)
            else:
                try:
                    in_cluster = ver_in_hwl_cluster[wedstrijd.vereniging.ver_nr]
                except KeyError:
                    in_cluster = False

                if in_cluster:
                    wedstrijden1.append(wedstrijd)
                else:
                    wedstrijden2.append(wedstrijd)
        # for

        if len(wedstrijden1):
            context['wedstrijden_1'] = wedstrijden1
            context['wedstrijden_2'] = wedstrijden2
        else:
            context['wedstrijden_1'] = wedstrijden2

        context['url_opslaan'] = reverse('CompLaagRegio:keuze-zeven-wedstrijden',
                                         kwargs={'deelnemer_pk': deelnemer.pk})

        if rol_nu == Rollen.ROL_SPORTER:
            context['kruimels'] = (
                (reverse('Sporter:profiel'), 'Mijn pagina'),
                (None, 'Aanpassen ' + comp.beschrijving.replace(' competitie', ''))
            )
        else:
            url_overzicht = reverse('Vereniging:overzicht')
            anker = '#competitie_%s' % comp.pk
            context['kruimels'] = (
                (url_overzicht, 'Beheer Vereniging'),
                (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRegio:wie-schiet-waar', kwargs={'deelcomp_pk': deelnemer.regiocompetitie.pk}),
                    'Wie schiet waar?'),
                (None, 'Aanpassen')
            )

        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de sporter de knop 'Opslaan' gebruikt
            op de pagina waar zijn 7 wedstrijden te kiezen zijn,
        """

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])       # afkappen voor de veiligheid
            deelnemer = (RegiocompetitieSporterBoog
                         .objects
                         .select_related('regiocompetitie',
                                         'regiocompetitie__competitie')
                         .get(pk=deelnemer_pk,
                              regiocompetitie__inschrijf_methode=INSCHRIJF_METHODE_1))
        except (ValueError, TypeError, RegiocompetitieSporterBoog.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        # controleer dat ingelogde gebruiker deze wijziging mag maken
        if rol_nu == Rollen.ROL_SPORTER:
            account = get_account(request)
            if account != deelnemer.sporterboog.sporter.account:
                raise PermissionDenied()
        else:
            # HWL: sporter moet lid zijn van zijn vereniging
            if deelnemer.bij_vereniging != functie_nu.vereniging:
                raise PermissionDenied('Sporter is niet van jouw vereniging')

        # zoek alle wedstrijden erbij
        pks = list()
        for ronde in (RegiocompetitieRonde
                      .objects
                      .select_related('regiocompetitie')
                      .prefetch_related('matches')
                      .filter(regiocompetitie=deelnemer.regiocompetitie)):
            pks.extend(ronde.matches.values_list('pk', flat=True))
        # for

        # zoek alle wedstrijden erbij
        wedstrijden = (CompetitieMatch
                       .objects
                       .filter(pk__in=pks)
                       .select_related('vereniging')
                       .order_by('datum_wanneer',
                                 'tijd_begin_wedstrijd'))

        keuze = list(deelnemer.inschrijf_gekozen_matches.values_list('pk', flat=True))
        keuze_add = list()
        aanwezig = len(keuze)

        for wedstrijd in wedstrijden:
            param = 'wedstrijd_%s' % wedstrijd.pk
            if request.POST.get(param, '') != '':
                # deze wedstrijd is gekozen
                if wedstrijd.pk in keuze:
                    # al gekozen, dus behouden
                    keuze.remove(wedstrijd.pk)
                else:
                    # toevoegen
                    keuze_add.append(wedstrijd.pk)
        # for

        # alle overgebleven wedstrijden zijn ongewenst
        aanwezig -= len(keuze)
        deelnemer.inschrijf_gekozen_matches.remove(*keuze)

        # controleer dat er maximaal 7 momenten gekozen worden
        if aanwezig + len(keuze_add) > 7:
            # begrens het aantal toe te voegen wedstrijden
            keuze_add = keuze_add[:7 - aanwezig]

        deelnemer.inschrijf_gekozen_matches.add(*keuze_add)

        if rol_nu == Rollen.ROL_SPORTER:
            url = reverse('Sporter:profiel')
        else:
            url = reverse('CompLaagRegio:wie-schiet-waar',
                          kwargs={'deelcomp_pk': deelnemer.regiocompetitie.pk})

        return HttpResponseRedirect(url)

# end of file
