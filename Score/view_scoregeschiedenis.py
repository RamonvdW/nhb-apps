# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.models import SporterBoog
from Score.definities import SCORE_WAARDE_VERWIJDERD
from Score.forms import ScoreGeschiedenisForm
from Score.models import AanvangsgemiddeldeHist, ScoreHist

TEMPLATE_SCORE_GESCHIEDENIS = 'score/score-geschiedenis.dtl'


class ScoreGeschiedenisView(UserPassesTestMixin, View):

    """ Django class-based view voor het de sporter """

    # class variables shared by all instances
    template = TEMPLATE_SCORE_GESCHIEDENIS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rol.ROL_BB

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
            sportersboog = (SporterBoog
                            .objects
                            .select_related('sporter',
                                            'sporter__bij_vereniging',
                                            'sporter__bij_vereniging__regio')
                            .filter(sporter__lid_nr=zoekterm))
            context['sportersboog'] = sportersboog
            pks = [obj.pk for obj in sportersboog]

            if len(pks) == 0:
                context['niet_gevonden'] = True
            else:
                context['sporter'] = sportersboog[0].sporter
                context['afstanden'] = afstanden = list()

                hists = (ScoreHist
                         .objects
                         .select_related('score',
                                         'score__sporterboog',
                                         'score__sporterboog__boogtype',
                                         'door_account')
                         .prefetch_related('score__uitslag_set')
                         .filter(score__sporterboog__in=pks)
                         .order_by('-when'))

                # splitst de hists op per score
                score2hists = dict()    # [score.pk] = [hist, ...]
                for hist in hists:
                    if hist.door_account:
                        hist.door_account_str = str(hist.door_account)

                    if hist.oude_waarde == SCORE_WAARDE_VERWIJDERD:
                        hist.oude_waarde = "verwijderd"
                    if hist.nieuwe_waarde == SCORE_WAARDE_VERWIJDERD:
                        hist.nieuwe_waarde = "verwijderd"

                    try:
                        score2hists[hist.score.pk].append(hist)
                    except KeyError:
                        score2hists[hist.score.pk] = [hist]
                # for

                for obj in sportersboog:
                    obj.scores = list()
                    for hist in hists:      # deze volgorde aanhouden
                        if hist.score.sporterboog == obj:
                            score = hist.score
                            try:
                                score.hists = score2hists[score.pk]
                            except KeyError:
                                # al gedaan
                                pass
                            else:
                                del score2hists[score.pk]

                                if score.afstand_meter not in afstanden:
                                    afstanden.append(score.afstand_meter)

                                try:
                                    uitslag = score.uitslag_set.prefetch_related('competitiematch_set').all()[0]
                                    wedstrijd = uitslag.competitiematch_set.all()[0]
                                    score.wedstrijd_str = str(wedstrijd.datum_wanneer)
                                    tijd = str(wedstrijd.tijd_begin_wedstrijd)[:5]
                                    if tijd != "00:00":
                                        score.wedstrijd_str += " " + tijd
                                    if wedstrijd.vereniging:
                                        score.wedstrijd_waar = 'bij %s' % wedstrijd.vereniging
                                    else:
                                        score.wedstrijd_waar = 'bij ?'
                                    if score.waarde == SCORE_WAARDE_VERWIJDERD:
                                        score.waarde = 'verwijderd'

                                except IndexError:
                                    # skip
                                    pass

                                else:
                                    obj.scores.append(score)
                    # for
                # for

                hists = (AanvangsgemiddeldeHist
                         .objects
                         .select_related('ag',
                                         'ag__sporterboog',
                                         'ag__sporterboog__boogtype')
                         .filter(ag__sporterboog__in=pks)
                         .order_by('-when'))

                # splits de hists op per score
                ag2hists = dict()    # [ag.pk] = [hist, ...]
                for hist in hists:
                    if hist.door_account:
                        hist.door_account_str = str(hist.door_account)

                    try:
                        ag2hists[hist.ag.pk].append(hist)
                    except KeyError:
                        ag2hists[hist.ag.pk] = [hist]
                # for

                for obj in sportersboog:
                    obj.ags = list()
                    for hist in hists:      # deze volgorde aanhouden
                        if hist.ag.sporterboog == obj:
                            ag = hist.ag
                            try:
                                ag.hists = ag2hists[ag.pk]
                            except KeyError:
                                # al gedaan
                                pass
                            else:
                                del ag2hists[ag.pk]

                                if ag.afstand_meter not in afstanden:
                                    afstanden.append(ag.afstand_meter)

                                obj.ags.append(ag)
                    # for
                # for

                afstanden.sort()
        else:
            context['niet_gevonden'] = True

        context['kruimels'] = (
            (None, 'Score geschiedenis'),
        )

        return render(request, self.template, context)


# end of file
