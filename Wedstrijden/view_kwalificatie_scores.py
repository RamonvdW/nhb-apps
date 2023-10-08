# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.models import RegiocompetitieSporterBoog
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Kalender.view_maand import MAAND2URL
from Wedstrijden.definities import KWALIFICATIE_CHECK_NOG_DOEN
from Wedstrijden.models import Wedstrijd, WedstrijdInschrijving, Kwalificatiescore
import datetime


TEMPLATE_WEDSTRIJDEN_KWALIFICATIE_SCORES = 'wedstrijden/inschrijven-kwalificatie-scores.dtl'
TEMPLATE_WEDSTRIJDEN_TOEGEVOEGD_AAN_MANDJE = 'wedstrijden/inschrijven-toegevoegd-aan-mandje.dtl'
TEMPLATE_WEDSTRIJDEN_CHECK_KWALIFICATIE_SCORES = 'wedstrijden/check-kwalificatie-scores.dtl'


class KwalificatieScoresOpgevenView(UserPassesTestMixin, TemplateView):

    """ Met deze view wordt het opgeven van de kwalificatie-scores voor de sporter afgehandeld  """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_KWALIFICATIE_SCORES
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving = (WedstrijdInschrijving
                            .objects
                            .select_related('sporterboog__sporter',
                                            'koper')
                            .get(pk=inschrijving_pk,
                                 wedstrijd__eis_kwalificatie_scores=True))
        except WedstrijdInschrijving.DoesNotExist:
            raise Http404('Inschrijving niet gevonden')

        # controleer dat de wijziging door de koper of de sporter zelf gedaan wordt
        account = get_account(self.request)
        if account != inschrijving.koper and inschrijving.sporterboog.sporter.account != account:
            raise Http404('Mag niet wijzigen')

        context['sporter'] = inschrijving.sporterboog.sporter

        # zoek de bondscompetitie Indoor scores erbij
        try:
            deelnemer = (RegiocompetitieSporterBoog
                         .objects
                         .get(sporterboog=inschrijving.sporterboog,
                              regiocompetitie__competitie__afstand='18'))
        except RegiocompetitieSporterBoog.DoesNotExist:
            pass
        else:
            scores = [deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4,
                      deelnemer.score5, deelnemer.score6, deelnemer.score7]
            scores = [score for score in scores if score > 0]
            scores.sort(reverse=True)       # hoogste eerst
            scores = scores[:4]             # top 4
            scores = [str(score) for score in scores]
            context['indoor_scores'] = ", ".join(scores)

        context['wedstrijd'] = wedstrijd = inschrijving.wedstrijd
        wedstrijd.plaats_str = wedstrijd.locatie.plaats

        jaar = wedstrijd.datum_begin.year - 1

        # einddatum is de zondag van het weekend voor de wedstrijd
        # weekday 0 = maandag
        context['eind_datum'] = wedstrijd.datum_begin - datetime.timedelta(days=1+wedstrijd.datum_begin.weekday())
        context['begin_datum'] = datetime.date(jaar, 9, 1)      # 1 september

        context['eind_jaar'] = context['eind_datum'].year
        context['begin_jaar'] = context['begin_datum'].year

        # zoek de eerder opgegeven kwalificatie scores erbij
        kwalificatie_scores = list(Kwalificatiescore
                                   .objects
                                   .filter(inschrijving=inschrijving)
                                   .order_by('datum'))

        context['eerste_keer'] = len(kwalificatie_scores) == 0

        while len(kwalificatie_scores) < 3:
            score = Kwalificatiescore(inschrijving=inschrijving, datum=datetime.date(jaar, 12, 31))     # 31 december
            kwalificatie_scores.append(score)
        # while
        for nr, score in enumerate(kwalificatie_scores):
            score.name_str = 'score%s' % (nr + 1)
            score.datum_id = 'datum%s' % (nr + 1)
        # for
        context['kwalificatie_scores'] = kwalificatie_scores

        context['url_opslaan'] = reverse('Wedstrijden:inschrijven-kwalificatie-scores',
                                         kwargs={'inschrijving_pk': inschrijving.pk})

        url_kalender = reverse('Kalender:maand',
                               kwargs={'jaar': wedstrijd.datum_begin.year,
                                       'maand': MAAND2URL[wedstrijd.datum_begin.month],
                                       'soort': 'alle',
                                       'bogen': 'auto'})

        context['kruimels'] = (
            (url_kalender, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Kwalificatie scores'),
        )

        return context

    @staticmethod
    def render_toegevoegd_aan_mandje(request, inschrijving):
        # render de pagina "toegevoegd aan mandje"

        context = dict()

        wedstrijd = inschrijving.wedstrijd

        url_maand = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month],
                                    'soort': 'alle',
                                    'bogen': 'auto'})

        url = reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk})

        context['url_verder'] = url
        context['url_mandje'] = reverse('Bestel:toon-inhoud-mandje')

        context['kruimels'] = (
            (url_maand, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (url, 'Inschrijven'),
            (None, 'Toegevoegd aan mandje')
        )

        return render(request, TEMPLATE_WEDSTRIJDEN_TOEGEVOEGD_AAN_MANDJE, context)

    def post(self, request, *args, **kwargs):

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving = (WedstrijdInschrijving
                            .objects
                            .select_related('sporterboog__sporter',
                                            'koper')
                            .get(pk=inschrijving_pk,
                                 wedstrijd__eis_kwalificatie_scores=True))
        except WedstrijdInschrijving.DoesNotExist:
            raise Http404('Inschrijving niet gevonden')

        # controleer dat de wijziging door de koper of de sporter zelf gedaan wordt
        account = get_account(self.request)
        if account != inschrijving.koper and inschrijving.sporterboog.sporter.account != account:
            raise Http404('Mag niet wijzigen')

        wedstrijd = inschrijving.wedstrijd
        jaar = wedstrijd.datum_begin.year - 1
        begin_datum = datetime.date(jaar, 9, 1)      # 1 september
        eind_datum = wedstrijd.datum_begin - datetime.timedelta(days=1 + wedstrijd.datum_begin.weekday())

        eerste_keer = False
        qset = (Kwalificatiescore
                .objects
                .filter(inschrijving=inschrijving)
                .order_by('datum'))         # zelfde als voor de GET

        if qset.count() > 3:
            # uitzondering: te veel scores.
            # verwijder ze allemaal
            qset.delete()
            kwalificatie_scores = list()
        else:
            kwalificatie_scores = list(qset)
            eerste_keer = len(kwalificatie_scores) == 0

        while len(kwalificatie_scores) < 3:
            score = Kwalificatiescore(inschrijving=inschrijving, datum=datetime.date(jaar, 12, 31))     # 31 december
            kwalificatie_scores.append(score)
        # while

        # print('post:%s' % repr(request.POST))

        for nr, score in enumerate(kwalificatie_scores):
            name_str = 'score%s' % (nr + 1)

            datum_str = request.POST.get(name_str + '_datum', '')[:10]      # afkappen voor de veiligheid
            naam_str = request.POST.get(name_str + '_naam', '')[:50]        # afkappen voor de veiligheid
            waar_str = request.POST.get(name_str + '_waar', '')[:50]        # afkappen voor de veiligheid
            result_str = request.POST.get(name_str + '_result', '')[:5]     # afkappen voor de veiligheid

            try:
                datum = datetime.datetime.strptime(datum_str, '%Y-%m-%d').date()
            except ValueError:
                datum = begin_datum
            else:
                if datum < begin_datum or datum > eind_datum:
                    datum = begin_datum

            naam_str = naam_str.strip()
            waar_str = waar_str.strip()

            try:
                result = int(result_str)
            except ValueError:
                result = 0
            else:
                if result < 0 or result > 600:
                    result = 0

            # opslaan
            if datum != score.datum or score.naam != naam_str or score.waar != waar_str or score.resultaat != result:
                # gewijzigd, dus check moet opnieuw gedaan worden
                score.check_status = KWALIFICATIE_CHECK_NOG_DOEN

            score.datum = datum
            score.naam = naam_str
            score.waar = waar_str
            score.resultaat = result

            score.save()
        # for

        if eerste_keer:
            return self.render_toegevoegd_aan_mandje(request, inschrijving)

        # TODO: hoe zijn we hier gekomen? Via de bestelling? Via Mijn pagina?
        url = reverse('Plein:plein')

        return HttpResponseRedirect(url)


class CheckKwalificatieScoresView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de Manager Wedstrijdzaken de opgegeven kwalificatie-scores controleren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_CHECK_KWALIFICATIE_SCORES
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_MWZ, Rollen.ROL_BB)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])      # afkappen voor de veiligheid
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        jaar = wedstrijd.datum_begin.year - 1

        # einddatum is de zondag van het weekend voor de wedstrijd
        # weekday 0 = maandag
        context['eind_datum'] = wedstrijd.datum_begin - datetime.timedelta(days=1+wedstrijd.datum_begin.weekday())
        context['begin_datum'] = datetime.date(jaar, 9, 1)      # 1 september

        scores = Kwalificatiescore.objects.filter(inschrijving__wedstrijd=wedstrijd)



        return context


# end of file
