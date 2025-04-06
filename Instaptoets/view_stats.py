# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.db.models import Sum
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_beschrijving
from Instaptoets.models import Vraag, ToetsAntwoord, Instaptoets
from Instaptoets.operations import instaptoets_is_beschikbaar
from types import SimpleNamespace

TEMPLATE_STATS_ANTWOORDEN = 'instaptoets/stats-antwoorden.dtl'
TEMPLATE_GEZAKT = 'instaptoets/gezakt.dtl'


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

    def _get_stats_vragen(self):
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

        vragen = (Vraag
                  .objects
                  .exclude(is_actief=False)
                  .exclude(gebruik_voor_toets=False, gebruik_voor_quiz=False)   # niet voor de toets, noch voor de quiz
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
                count_sum /= 100.0
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

            if vraag.gebruik_voor_toets:
                vraag.gebruik = "toets"
                if vraag.gebruik_voor_quiz:
                    vraag.gebruik += " & quiz"
            else:
                vraag.gebruik = "quiz"

            tup = (fouten, aantal_antwoorden, vraag.pk, vraag)
            lst.append(tup)
        # for

        lst.sort(reverse=True)      # hoogste eerst
        vragen = [tup[-1] for tup in lst]

        return antwoord_count, vragen

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['antwoord_count'], context['vragen'] = self._get_stats_vragen()

        context['toets_gestart'] = gestart = Instaptoets.objects.count()

        context['toets_unieke_sporters'] = Instaptoets.objects.distinct('sporter').count()

        qset = Instaptoets.objects.exclude(aantal_goed=0).filter(is_afgerond=True)

        context['toets_afgerond'] = afgerond = qset.count()
        if gestart > 0:
            context['toets_afgerond_perc'] = "%.0f%%" % round((afgerond * 100.0) / gestart, 0)
        else:
            context['toets_afgerond_perc'] = "0%"

        context['toets_geslaagd'] = geslaagd = qset.filter(geslaagd=True).count()
        if afgerond > 0:
            context['toets_geslaagd_perc'] = "%.0f%%" % round((geslaagd * 100.0) / afgerond, 0)
        else:
            context['toets_geslaagd_perc'] = "0%"

        aantal_goed = qset.aggregate(Sum('aantal_goed'))['aantal_goed__sum']
        if afgerond > 0:
            context['gemiddeld_goed'] = round(aantal_goed / afgerond, 0)
        else:
            context['gemiddeld_goed'] = '?'

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (None, 'Statistiek antwoorden instaptoets')
        )

        return context


class GezaktView(UserPassesTestMixin, TemplateView):
    """
        Deze view geeft informatie over wie de instaptoets gemaakt hebben maar hiervoor gezakt zijn
    """

    # class variables shared by all instances
    template_name = TEMPLATE_GEZAKT
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

        geslaagd = Instaptoets.objects.filter(geslaagd=True).distinct('sporter').values_list('sporter__lid_nr', flat=True)

        sporters = dict()   # [lid_nr] = SimpleNamespace

        for toets in (Instaptoets
                      .objects
                      .filter(is_afgerond=True,
                              geslaagd=False)
                      .select_related('sporter')):
            lid_nr = toets.sporter.lid_nr

            if lid_nr in geslaagd:
                # zowel geslaagd als gezakt
                continue

            try:
                data = sporters[lid_nr]
            except KeyError:
                data = SimpleNamespace(
                            lid_nr_en_naam=toets.sporter.lid_nr_en_volledige_naam(),
                            aantal_goed=0,
                            aantal_fout=0,
                            aantal_keer_gezakt=0,
                            laatste_poging=None)
                sporters[lid_nr] = data

            poging = toets.opgestart.date()
            if not data.laatste_poging or poging > data.laatste_poging:
                data.laatste_poging = poging

            data.aantal_goed += toets.aantal_goed
            data.aantal_fout += (toets.aantal_vragen - toets.aantal_goed)
            data.aantal_keer_gezakt += 1
        # for

        lijst = list()
        for lid_nr, data in sporters.items():
            tup = (data.laatste_poging, data.lid_nr_en_naam, data)
            lijst.append(tup)
        # for
        lijst.sort(reverse=True)        # nieuwste bovenaan

        context['gezakt'] = [tup[-1] for tup in lijst]

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (None, 'Gezakt voor de instaptoets')
        )

        return context


# end of file
