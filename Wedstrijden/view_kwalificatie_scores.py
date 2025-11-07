# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, UnreadablePostError, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Wedstrijden.definities import (KWALIFICATIE_CHECK_GOED, KWALIFICATIE_CHECK_NOG_DOEN, KWALIFICATIE_CHECK_AFGEKEURD,
                                    WEDSTRIJD_STATUS_URL_WACHT_OP_GEACCEPTEERD)
from Wedstrijden.models import Wedstrijd, Kwalificatiescore
from collections import OrderedDict
from types import SimpleNamespace
import datetime
import json

TEMPLATE_WEDSTRIJDEN_CHECK_KWALIFICATIE_SCORES = 'wedstrijden/check-kwalificatie-scores.dtl'
TEMPLATE_WEDSTRIJDEN_CHECK_KWALIFICATIE_WEDSTRIJD = 'wedstrijden/check-kwalificatie-scores-wedstrijd.dtl'


class CheckKwalificatieScoresView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de Manager Wedstrijdzaken de opgegeven kwalificatie-scores controleren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_CHECK_KWALIFICATIE_SCORES
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_MWZ, Rol.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])      # afkappen voor de veiligheid
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            # controleer dat dit de HWL van de wedstrijd is
            if wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
                raise PermissionDenied('Niet de organisator')

        context['wed'] = wedstrijd

        jaar = wedstrijd.datum_begin.year - 1

        # einddatum is de zondag van het weekend voor de wedstrijd
        # weekday 0 = maandag
        context['eind_datum'] = wedstrijd.datum_begin - datetime.timedelta(days=1+wedstrijd.datum_begin.weekday())
        context['begin_datum'] = datetime.date(jaar, 9, 1)      # 1 september

        wedstrijden = OrderedDict()     # [(datum, plaats)] = [Kwalificatiescore(), ..]
        todo = dict()                   # [(datum, plaats)] = True/False
        for score in (Kwalificatiescore
                      .objects
                      .filter(inschrijving__wedstrijd=wedstrijd)
                      .exclude(resultaat=0)
                      .select_related('inschrijving__sporterboog__boogtype',
                                      'inschrijving__sporterboog__sporter')
                      .order_by('datum',            # oudste eerst
                                '-resultaat')):     # hoogste eerst

            sporterboog = score.inschrijving.sporterboog
            score.sporter_str = sporterboog.sporter.lid_nr_en_volledige_naam()
            score.boog_str = sporterboog.boogtype.beschrijving

            tup = (score.datum, score.waar)

            try:
                wedstrijden[tup].append(score)
            except KeyError:
                wedstrijden[tup] = [score]

            if score.check_status == KWALIFICATIE_CHECK_NOG_DOEN:
                todo[tup] = True
            else:
                if tup not in todo.keys():
                    todo[tup] = False
        # for

        context['wedstrijden'] = lijst = list()

        for tup, scores in wedstrijden.items():
            datum, waar = tup

            url_controle = reverse('Wedstrijden:check-kwalificatie-scores-wedstrijd',
                                   kwargs={'score_pk': scores[0].pk})

            obj = SimpleNamespace(
                            datum=datum,
                            waar=waar,
                            scores=scores,
                            is_todo=todo[tup],
                            url_controle=url_controle)
            lijst.append(obj)
        # for

        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (None, 'Check kwalificatiescores'),
            )
        else:
            context['kruimels'] = (
                (reverse('Wedstrijden:manager-status',
                         kwargs={'status': WEDSTRIJD_STATUS_URL_WACHT_OP_GEACCEPTEERD}), 'Beheer wedstrijdkalender'),
                (None, 'Check kwalificatiescores'),
            )

        return context


class CheckKwalificatieScoresWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de Manager Wedstrijdzaken de opgegeven kwalificatie-scores controleren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_CHECK_KWALIFICATIE_WEDSTRIJD
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_MWZ, Rol.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            score_pk = int(str(kwargs['score_pk'])[:6])      # afkappen voor de veiligheid
            ref_score = Kwalificatiescore.objects.select_related('inschrijving__wedstrijd').get(pk=score_pk)
        except (ValueError, Kwalificatiescore.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        context['ref_score'] = ref_score
        wedstrijd = ref_score.inschrijving.wedstrijd

        if self.rol_nu == Rol.ROL_HWL:
            # controleer dat dit de HWL van de wedstrijd is
            if wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
                raise PermissionDenied('Niet de organisator')

        scores = (Kwalificatiescore
                  .objects
                  .filter(inschrijving__wedstrijd=wedstrijd,
                          datum=ref_score.datum,
                          waar=ref_score.waar)
                  .exclude(resultaat=0)
                  .select_related('inschrijving__sporterboog__boogtype',
                                  'inschrijving__sporterboog__sporter')
                  .order_by('inschrijving__sporterboog__boogtype__volgorde',
                            '-resultaat'))  # hoogste eerst

        check_status2keuze = {
            KWALIFICATIE_CHECK_GOED: 1,
            KWALIFICATIE_CHECK_NOG_DOEN: 2,
            KWALIFICATIE_CHECK_AFGEKEURD: 3,
        }

        for score in scores:
            sporterboog = score.inschrijving.sporterboog
            score.sporter_str = sporterboog.sporter.lid_nr_en_volledige_naam()
            score.boog_str = sporterboog.boogtype.beschrijving
            score.keuze = check_status2keuze[score.check_status]
            score.url_status = reverse('Wedstrijden:check-kwalificatie-scores-wedstrijd',
                                       kwargs={'score_pk': score.pk})
            score.id = 'score%s' % score.pk
        # for

        context['scores'] = scores

        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (reverse('Wedstrijden:check-kwalificatie-scores',
                         kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Check kwalificatiescores'),
                (None, 'Controleer wedstrijd')
            )
        else:
            context['kruimels'] = (
                (reverse('Wedstrijden:manager-status',
                         kwargs={'status': WEDSTRIJD_STATUS_URL_WACHT_OP_GEACCEPTEERD}), 'Wedstrijdkalender'),
                (reverse('Wedstrijden:check-kwalificatie-scores',
                         kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Check kwalificatiescores'),
                (None, 'Controleer wedstrijd')
            )

        return context

    def post(self, request, *args, **kwargs):

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        try:
            keuze = int(str(data['keuze'])[:6])
        except (KeyError, ValueError):
            # garbage in
            raise Http404('Geen valide verzoek')

        if keuze == 1:
            check_status = KWALIFICATIE_CHECK_GOED
        elif keuze == 2:
            check_status = KWALIFICATIE_CHECK_NOG_DOEN
        elif keuze == 3:
            check_status = KWALIFICATIE_CHECK_AFGEKEURD
        else:
            raise Http404('Geen valide verzoek')

        try:
            score_pk = int(str(kwargs['score_pk'])[:6])      # afkappen voor de veiligheid
            score = (Kwalificatiescore
                     .objects
                     .select_related('inschrijving__sporterboog__sporter')
                     .get(pk=score_pk))
        except (ValueError, Kwalificatiescore.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if score.check_status != check_status:

            now = timezone.now()
            now = timezone.localtime(now)
            now_str = now.strftime("%Y-%m-%d %H:%M")

            account = get_account(self.request)
            door_str = "[%s] %s" % (account.username, account.volledige_naam())

            if check_status == KWALIFICATIE_CHECK_AFGEKEURD:
                score.log += "[%s] Afgekeurd door %s\n" % (now_str, door_str)

            if check_status == KWALIFICATIE_CHECK_GOED:
                score.log += "[%s] Goedgekeurd door %s\n" % (now_str, door_str)

            if check_status == KWALIFICATIE_CHECK_NOG_DOEN:
                score.log += "[%s] Terug gezet naar 'nog te doen' door %s\n" % (now_str, door_str)

            score.check_status = check_status
            score.save(update_fields=['check_status', 'log'])

        out = dict()
        return JsonResponse(out)


# end of file
