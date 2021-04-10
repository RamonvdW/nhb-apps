# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige
from Schutter.models import SchutterBoog
from Score.models import ScoreHist, SCORE_WAARDE_VERWIJDERD, SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG
from .forms import ScoreGeschiedenisForm
from Plein.menu import menu_dynamics


TEMPLATE_SCORE_GESCHIEDENIS = 'score/score-geschiedenis.dtl'


class ScoreGeschiedenisView(UserPassesTestMixin, View):

    """ Django class-based view voor het de schutter """

    # class variables shared by all instances
    template = TEMPLATE_SCORE_GESCHIEDENIS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) in (Rollen.ROL_IT, Rollen.ROL_BB)

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """

        context = dict()
        context['url_ophalen'] = reverse('Score:geschiedenis')

        context['form'] = form = ScoreGeschiedenisForm(self.request.GET)
        form.full_clean()  # vult cleaned_data

        zoekterm = form.cleaned_data['zoekterm']
        if zoekterm:
            try:
                zoekterm = int(zoekterm[:6])     # afkappen geeft veiligheid
            except ValueError:
                zoekterm = ''

        if zoekterm:
            schuttersboog = (SchutterBoog
                             .objects
                             .select_related('nhblid',
                                             'nhblid__bij_vereniging',
                                             'nhblid__bij_vereniging__regio')
                             .filter(nhblid__nhb_nr=zoekterm))
            context['schuttersboog'] = schuttersboog
            pks = [obj.pk for obj in schuttersboog]

            if len(pks) == 0:
                context['niet_gevonden'] = True
            else:
                context['nhblid'] = schuttersboog[0].nhblid

                hists = (ScoreHist
                         .objects
                         .select_related('score',
                                         'score__schutterboog',
                                         'score__schutterboog__boogtype')
                         .prefetch_related('score__competitiewedstrijduitslag_set')
                         .filter(score__schutterboog__in=pks)
                         .order_by('-when'))

                # splitst de hists op per score
                score2hists = dict()    # [score.pk] = [hist, ...]
                for hist in hists:
                    if hist.door_account:
                        hist.door_account_str = str(hist.door_account)

                    hist.is_edit = hist.oude_waarde > 0 or hist.score.type == 'T'

                    if hist.score.type in (SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG):
                        hist.oude_waarde = "%.3f" % (hist.oude_waarde / 1000)
                        hist.nieuwe_waarde = "%.3f" % (hist.nieuwe_waarde / 1000)
                    else:
                        if hist.oude_waarde == SCORE_WAARDE_VERWIJDERD:
                            hist.oude_waarde = "verwijderd"
                        if hist.nieuwe_waarde == SCORE_WAARDE_VERWIJDERD:
                            hist.nieuwe_waarde = "verwijderd"

                    try:
                        score2hists[hist.score.pk].append(hist)
                    except KeyError:
                        score2hists[hist.score.pk] = [hist]
                # for

                context['afstanden'] = afstanden = list()

                for obj in schuttersboog:
                    obj.scores = list()
                    for hist in hists:      # deze volgorde aanhouden
                        if hist.score.schutterboog == obj:
                            score = hist.score
                            try:
                                score.hists = score2hists[score.pk]
                            except KeyError:
                                # al gedaan
                                pass
                            else:
                                del score2hists[score.pk]
                                if score.type in (SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG):
                                    score.waarde = "%.3f" % (hist.score.waarde / 1000)

                                if score.afstand_meter not in afstanden:
                                    afstanden.append(score.afstand_meter)

                                try:
                                    uitslag = score.competitiewedstrijduitslag_set.prefetch_related('competitiewedstrijd_set').all()[0]
                                    wedstrijd = uitslag.competitiewedstrijd_set.all()[0]
                                    score.wedstrijd_str = str(wedstrijd.datum_wanneer)
                                    tijd = str(wedstrijd.tijd_begin_wedstrijd)[:5]
                                    if tijd != "00:00":
                                        score.wedstrijd_str += " " + tijd
                                    if wedstrijd.vereniging:
                                        score.wedstrijd_waar = 'bij %s' % wedstrijd.vereniging
                                except IndexError:
                                    pass

                                obj.scores.append(score)
                    # for

                    afstanden.sort()
                # for
        else:
            context['niet_gevonden'] = True

        menu_dynamics(self.request, context, actief='hetplein')
        return render(request, self.template, context)


# end of file
