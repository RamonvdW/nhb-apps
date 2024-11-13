# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.rol import rol_mag_wisselen, rol_get_beschrijving
from Taken.models import Taak
from Taken.operations import eval_open_taken, get_taak_functie_pks


TEMPLATE_OVERZICHT = 'taken/overzicht.dtl'
TEMPLATE_DETAILS = 'taken/details.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders met taken """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # haal de taken op (maximaal 50)
        functie_pks, huidige_functie_pk = get_taak_functie_pks(self.request)

        # zorg dat alle open taken in beeld komen door te sorteren op is_afgerond
        context['taken'] = (Taak
                            .objects
                            .filter(toegekend_aan_functie__pk__in=functie_pks)
                            .select_related('toegekend_aan_functie',
                                            'aangemaakt_door')
                            .order_by('is_afgerond',
                                      '-deadline')[:50])        # nieuwste bovenaan

        count_open = count_afgerond = 0
        for taak in context['taken']:
            if taak.is_afgerond:
                count_afgerond += 1
            else:
                count_open += 1

            taak.url = reverse('Taken:details', kwargs={'taak_pk': taak.pk})

            # pos = taak.beschrijving.find('\n')
            # if pos < 1 or pos > 200:
            #     pos = 200
            # taak.titel = taak.beschrijving[:pos]

            taak.is_huidige_rol = huidige_functie_pk == taak.toegekend_aan_functie.pk
        # for

        context['heeft_open_taken'] = (count_open > 0)
        context['heeft_afgeronde_taken'] = (count_afgerond > 0)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # zorg dat de badge in het menu altijd overeen komt met werkelijk getoonde aantal
        eval_open_taken(self.request, forceer=True)

        context['kruimels'] = (
            (None, 'Taken'),
        )

        return context


class DetailsView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders met taken """

    # class variables shared by all instances
    template_name = TEMPLATE_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated and rol_mag_wisselen(self.request)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            taak_pk = int(kwargs['taak_pk'][:6])        # afkappen voor de veiligheid
            taak = (Taak
                    .objects
                    .select_related('toegekend_aan_functie',
                                    'aangemaakt_door')
                    .get(pk=taak_pk))
        except (ValueError, Taak.DoesNotExist):
            raise Http404('Geen valide taak')

        # controleer dat deze taak bij de beheerder hoort
        functie_pks, _ = get_taak_functie_pks(self.request)
        if taak.toegekend_aan_functie.pk not in functie_pks:
            raise PermissionDenied('Geen taak voor jou')

        if not taak.is_afgerond:
            taak.url_sluiten = reverse('Taken:details', kwargs={'taak_pk': taak.pk})

        context['taak'] = taak

        context['kruimels'] = (
            (reverse('Taken:overzicht'), 'Taken'),
            (None, 'Details')
        )

        return context

    def post(self, request, *args, **kwargs):

        try:
            taak_pk = int(kwargs['taak_pk'][:6])    # afkappen voor de veiligheid
            taak = Taak.objects.get(pk=taak_pk)
        except (ValueError, Taak.DoesNotExist):
            raise Http404('Geen valide taak')

        # controleer dat deze taak bij de beheerder hoort
        account = get_account(request)
        functie_pks, _ = get_taak_functie_pks(self.request)
        if taak.toegekend_aan_functie.pk not in functie_pks:
            raise PermissionDenied('Geen taak voor jou')

        if not taak.is_afgerond:
            if taak.log != "":
                taak.log += "\n"
            taak.log += "[%s] %s heeft deze taak gesloten" % (timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M'), account)
            taak.is_afgerond = True
            taak.save(update_fields=['log', 'is_afgerond'])

            eval_open_taken(request, forceer=True)

        return HttpResponseRedirect(reverse('Taken:overzicht'))

# end of file
