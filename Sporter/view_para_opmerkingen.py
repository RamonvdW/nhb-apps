# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Sporter.models import SporterVoorkeuren


TEMPLATE_PARA_OPMERKINGEN = 'sporter/para-opmerkingen-lijst.dtl'
TEMPLATE_WIJZIG_PARA_OPMERKING = 'sporter/para-opmerkingen-wijzig.dtl'


class ParaOpmerkingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen de BB en MWZ de para notities van alle sporters inzien.
    """

    template_name = TEMPLATE_PARA_OPMERKINGEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en de rol Sporter gekozen hebben
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        voorkeuren = (SporterVoorkeuren
                      .objects
                      .exclude(opmerking_para_sporter='', para_voorwerpen=False)    # beide velden niet actief
                      .select_related('sporter')
                      .order_by('sporter__para_classificatie',
                                'para_voorwerpen',
                                'sporter__lid_nr'))

        for voorkeur in voorkeuren:
            voorkeur.url_edit = reverse('Sporter:wijzig-para-opmerking', kwargs={'sporter_pk': voorkeur.sporter.pk})
        # for

        context['voorkeuren'] = voorkeuren

        context['kruimels'] = (
            (None, 'Para opmerkingen'),
        )

        return context


class WijzigParaOpmerkingView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen de BB en MWZ de para notities van alle sporters inzien.
    """

    template_name = TEMPLATE_WIJZIG_PARA_OPMERKING
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.functie_nu = None
        self.voorkeuren = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en de rol Sporter gekozen hebben
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ)

    def _get_voorkeuren_or_404(self, sporter_pk: str):
        try:
            sporter_pk = int(sporter_pk[:6])    # afkappen voor de veiligheid
            self.voorkeuren = (SporterVoorkeuren
                               .objects
                               .select_related('sporter')
                               .get(sporter__lid_nr=sporter_pk))
        except (ValueError, ObjectDoesNotExist):
            raise Http404('Sporter niet gevonden')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self._get_voorkeuren_or_404(kwargs['sporter_pk'])
        context['voorkeuren'] = self.voorkeuren

        sporter = self.voorkeuren.sporter
        context['url_opslaan'] = reverse('Sporter:wijzig-para-opmerking',
                                         kwargs={'sporter_pk': sporter.pk})

        context['kruimels'] = (
            (reverse('Sporter:para-opmerkingen'), 'Para opmerkingen'),
            (None, 'Wijzig para opmerking'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als een POST request ontvangen is."""
        self._get_voorkeuren_or_404(kwargs['sporter_pk'])

        para_voorwerpen = request.POST.get('para_voorwerpen', '')
        self.voorkeuren.para_voorwerpen = (para_voorwerpen != '')

        para_notitie = request.POST.get('para_notitie', '')
        para_notitie = para_notitie.strip().replace('  ', ' ').capitalize()  # "  schiet met  .." --> "Schiet met .."
        self.voorkeuren.opmerking_para_sporter = para_notitie

        self.voorkeuren.save(update_fields=['para_voorwerpen', 'opmerking_para_sporter'])

        url = reverse('Sporter:para-opmerkingen')
        return HttpResponseRedirect(url)


# end of file
