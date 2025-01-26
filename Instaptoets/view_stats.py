# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_beschrijving
from Instaptoets.models import Vraag, ToetsAntwoord
from Instaptoets.operations import instaptoets_is_beschikbaar

TEMPLATE_STATS_ANTWOORDEN = 'instaptoets/stats-antwoorden.dtl'


class StatsInstaptoetsView(UserPassesTestMixin, TemplateView):
    """
        Deze view geeft statistiek over de antwoorden op de vragen van de instaptoets
    """

    # class variables shared by all instances
    template_name = TEMPLATE_STATS_ANTWOORDEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def dispatch(self, request, *args, **kwargs):
        if not instaptoets_is_beschikbaar():
            # geen toets --> terug naar landing page opleidingen
            return redirect('Opleiding:overzicht')

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn, geen gast zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rol.ROL_MO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        count_vraag_antwoord = dict()       # [vraag.pk][antwoord] = int
        antwoord_count = 0

        for antwoord in ToetsAntwoord.objects.filter(antwoord__in=('A', 'B', 'C', 'D')).select_related('vraag').all():
            antwoord_count += 1
            try:
                count_antwoorden = count_vraag_antwoord[antwoord.vraag.pk]
            except KeyError:
                count_vraag_antwoord[antwoord.vraag.pk] = count_antwoorden = dict()

            try:
                count_antwoorden[antwoord.antwoord] += 1
            except KeyError:
                count_antwoorden[antwoord.antwoord] = 1
        # for

        context['antwoord_count'] = antwoord_count

        vragen = (Vraag
                  .objects
                  .exclude(is_actief=False)
                  .select_related('categorie')
                  .order_by('categorie',
                            'pk'))

        lst = list()
        for vraag in vragen:
            vraag.rows = 4

            vraag.toon_d = vraag.antwoord_d != ''
            if not vraag.toon_d:
                vraag.rows -= 1

            vraag.toon_c = vraag.antwoord_c != ''
            if not vraag.toon_c:
                vraag.rows -= 1

            try:
                count_antwoorden = count_vraag_antwoord[vraag.pk]
            except KeyError:
                vraag.count_a = 0
                vraag.count_b = 0
                vraag.count_c = 0
                vraag.count_d = 0
            else:
                vraag.count_a = count_a = count_antwoorden.get('A', 0)
                vraag.count_b = count_b = count_antwoorden.get('B', 0)
                vraag.count_c = count_c = count_antwoorden.get('C', 0)
                vraag.count_d = count_d = count_antwoorden.get('D', 0)
                count_sum = count_a + count_b + count_c + count_d
                if count_sum == 0:
                    count_sum = 1
                count_sum = count_sum / 100
                vraag.perc_a = "%.0f" % (count_a / count_sum)
                vraag.perc_b = "%.0f" % (count_b / count_sum)
                vraag.perc_c = "%.0f" % (count_c / count_sum)
                vraag.perc_d = "%.0f" % (count_d / count_sum)

            vraag.kleur_a = ''
            vraag.kleur_b = ''
            vraag.kleur_c = ''
            vraag.kleur_d = ''

            fouten = 0
            if vraag.juiste_antwoord == 'A':
                vraag.kleur_a = 'green-text'
            elif vraag.count_a > 0:
                vraag.kleur_a = 'sv-rood-text'
                fouten += vraag.count_a

            if vraag.juiste_antwoord == 'B':
                vraag.kleur_b = 'green-text'
            elif vraag.count_b > 0:
                vraag.kleur_b = 'sv-rood-text'
                fouten += vraag.count_b

            if vraag.juiste_antwoord == 'C':
                vraag.kleur_c = 'green-text'
            elif vraag.count_c > 0:
                vraag.kleur_c = 'sv-rood-text'
                fouten += vraag.count_c

            if vraag.juiste_antwoord == 'D':
                vraag.kleur_d = 'green-text'
            elif vraag.count_d > 0:
                vraag.kleur_d = 'sv-rood-text'
                fouten += vraag.count_d

            aantal_antwoorden = vraag.count_a + vraag.count_b + vraag.count_c + vraag.count_d

            tup = (fouten, aantal_antwoorden, vraag.pk, vraag)
            lst.append(tup)
        # for

        lst.sort(reverse=True)      # hoogste eerst
        context['vragen'] = [tup[-1] for tup in lst]

        context['kruimels'] = (
            (reverse('Opleiding:overzicht'), 'Opleidingen'),
            (None, 'Statistiek antwoorden instaptoets')
        )

        return context

# end of file
