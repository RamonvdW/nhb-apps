# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import JsonResponse, Http404, UnreadablePostError
from django.utils import timezone
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.operations.wedstrijdcapaciteit import bepaal_waarschijnlijke_deelnemers
from Competitie.models import CompetitieMatch
from CompLaagRegio.models import RegioComp, RegioDeelnemer
from CompScores.helpers import mag_deelcomp_wedstrijd_wijzigen, bepaal_match_en_deelcomp_of_404
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Score.definities import SCORE_WAARDE_VERWIJDERD
from Score.models import Score, ScoreHist
from Sporter.models import SporterBoog
import json


class DynamicDeelnemersOphalenView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_WL)

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'waarschijnlijke deelnemers ophalen' gebruikt wordt

            Dit is een POST by-design, om caching te voorkomen.
        """

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        try:
            deelcomp_pk = int(str(data['deelcomp_pk'])[:7])   # afkappen voor extra veiligheid
            deelcomp = (RegioComp
                        .objects
                        .select_related('competitie')
                        .get(pk=deelcomp_pk))
        except (KeyError, ValueError, RegioComp.DoesNotExist):
            raise Http404('Competitie niet gevonden')

        try:
            match_pk = int(str(data['wedstrijd_pk'])[:7])   # afkappen voor extra veiligheid
            match = (CompetitieMatch
                     .objects
                     .get(pk=match_pk))
        except (KeyError, ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        sporters, teams = bepaal_waarschijnlijke_deelnemers(deelcomp.competitie.afstand, deelcomp, match)

        out = dict()
        out['deelnemers'] = deelnemers = list()
        for sporter in sporters:
            deelnemers.append({
                'pk': sporter.sporterboog_pk,
                'lid_nr': sporter.lid_nr,
                'naam': sporter.volledige_naam,
                'ver_nr': sporter.ver_nr,
                'ver_naam': sporter.ver_naam,
                'boog': sporter.boog,
                'team_gem': sporter.team_gem,
                'team_pk': sporter.team_pk,
            })
        # for

        return JsonResponse(out)


class DynamicZoekOpBondsnummerView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_WL)

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Zoek' gebruikt wordt
        """

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        # zoek een
        # print('data: %s' % repr(data))

        out = dict()

        try:
            lid_nr = int(str(data['lid_nr'])[:7])               # afkappen voor extra veiligheid
            match_pk = int(str(data['wedstrijd_pk'])[:7])       # afkappen voor extra veiligheid
            match = CompetitieMatch.objects.get(pk=match_pk)
        except (KeyError, ValueError, CompetitieMatch.DoesNotExist):
            # garbage in
            out['fail'] = 1
            # raise Http404('Geen valide verzoek')
        else:
            rondes = match.regioronde_set.all()
            if len(rondes) == 0:
                raise Http404('Geen competitie wedstrijd')
            ronde = rondes[0]

            # zoek schuttersboog die ingeschreven zijn voor deze competitie
            competitie = ronde.regiocomp.competitie

            deelnemers = (RegioDeelnemer
                          .objects
                          .select_related('sporterboog',
                                          'sporterboog__boogtype',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__bij_vereniging')
                          .filter(regiocomp__competitie=competitie,
                                  sporterboog__sporter__lid_nr=lid_nr))

            if len(deelnemers) == 0:
                out['fail'] = 1         # is niet ingeschreven voor deze competitie
            else:
                out['deelnemers'] = list()

                geen_lid = True
                for deelnemer in deelnemers:
                    sporterboog = deelnemer.sporterboog
                    sporter = sporterboog.sporter
                    boog = sporterboog.boogtype

                    # volgende blok wordt een paar keer uitgevoerd, maar dat maak niet uit
                    ver = sporter.bij_vereniging
                    if not ver:
                        # niet lid bij een vereniging, dan niet toe te voegen
                        geen_lid = True
                        continue

                    out['vereniging'] = str(ver)
                    out['regio'] = str(ver.regio)
                    out['lid_nr'] = sporter.lid_nr
                    out['naam'] = sporter.volledige_naam()
                    out['ver_nr'] = sporter.bij_vereniging.ver_nr
                    out['ver_naam'] = sporter.bij_vereniging.naam

                    sub = {
                        'pk': sporterboog.pk,
                        'boog': boog.beschrijving,
                        'team_pk': 0,
                        'team_gem': ''
                    }

                    if deelnemer.inschrijf_voorkeur_team:
                        # TODO: gebruikt ronde team ag!
                        sub['team_gem'] = deelnemer.ag_voor_team
                        if not ronde.regiocomp.regio_heeft_vaste_teams:
                            if deelnemer.aantal_scores > 0:
                                sub['team_gem'] = deelnemer.gemiddelde

                        sub['vsg'] = sub['team_gem']        # TODO: obsolete vsg

                        # zoek het huidige team erbij
                        teams = deelnemer.regioteam_set.all()
                        if teams.count() > 0:
                            # sporter is gekoppeld aan een team
                            sub['team_pk'] = teams[0].pk

                    out['deelnemers'].append(sub)
                # for

                if geen_lid and len(out['deelnemers']) == 0:
                    out['fail'] = 1

        return JsonResponse(out)


class DynamicScoresOpslaanView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_RCL, Rol.ROL_HWL, Rol.ROL_WL)

    @staticmethod
    def nieuwe_score(bulk, uitslag, sporterboog_pk, waarde, when, door_account):
        # print('nieuwe score: %s = %s' % (sporterboog_pk, waarde))
        try:
            sporterboog = SporterBoog.objects.get(pk=sporterboog_pk)
        except (ValueError, SporterBoog.DoesNotExist):
            # garbage --> ignore
            return

        score_obj = Score(sporterboog=sporterboog,
                          waarde=waarde,
                          afstand_meter=uitslag.afstand)
        score_obj.save()
        uitslag.scores.add(score_obj)

        hist = ScoreHist(
                    score=score_obj,
                    oude_waarde=0,
                    nieuwe_waarde=waarde,
                    when=when,
                    door_account=door_account,
                    notitie="Invoer uitslag wedstrijd")
        bulk.append(hist)

    @staticmethod
    def bijgewerkte_score(bulk, score_obj, waarde, when, door_account):
        if score_obj.waarde != waarde:
            # print('bijgewerkte score: %s --> %s' % (score_obj, waarde))

            hist = ScoreHist(
                        score=score_obj,
                        oude_waarde=score_obj.waarde,
                        nieuwe_waarde=waarde,
                        when=when,
                        door_account=door_account,
                        notitie="Invoer uitslag wedstrijd")
            bulk.append(hist)

            score_obj.waarde = waarde
            score_obj.save()
        # else: zelfde score

    def scores_opslaan(self, uitslag, data, when, door_account):
        """ sla de scores op
            data bevat sporterboog_pk + score
            als score leeg is moet pk uit de uitslag gehaald worden
        """

        # doorloop alle scores in de uitslag en haal de sporterboog erbij
        # hiermee kunnen we snel controleren of iemand al in de uitslag
        # voorkomt
        pk2score_obj = dict()
        for score_obj in uitslag.scores.select_related('sporterboog').all():
            pk2score_obj[score_obj.sporterboog.pk] = score_obj
        # for
        # print('pk2score_obj: %s' % repr(pk2score_obj))

        bulk = list()
        for key, value in data.items():
            if key == 'wedstrijd_pk':
                # geen sporterboog
                continue

            try:
                pk = int(str(key)[:7])     # afkappen voor de veiligheid
            except ValueError:
                # fout pk: ignore
                continue        # met de for-loop

            try:
                score_obj = pk2score_obj[pk]
            except KeyError:
                # sporterboog zit nog niet in de uitslag
                score_obj = None

            if isinstance(value, str) and value == '':
                # lege invoer betekent: schutter deed niet mee
                if score_obj:
                    # verwijder deze score uit de uitslag, maar behoud de geschiedenis
                    self.bijgewerkte_score(bulk, score_obj, SCORE_WAARDE_VERWIJDERD, when, door_account)
                # laat tegen exceptie hieronder aanlopen

            # sla de score op
            try:
                waarde = int(str(value)[:4])   # afkappen voor de veiligheid
            except ValueError:
                # foute score: ignore
                continue

            if 0 <= waarde <= uitslag.max_score:
                # print('score geaccepteerd: %s %s' % (pk, waarde))
                # score opslaan
                if not score_obj:
                    # het is een nieuwe score
                    self.nieuwe_score(bulk, uitslag, pk, waarde, when, door_account)
                else:
                    self.bijgewerkte_score(bulk, score_obj, waarde, when, door_account)
            # else: illegale score --> ignore
        # for

        ScoreHist.objects.bulk_create(bulk)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        # print('data:', repr(data))
        try:
            match_pk = str(data['wedstrijd_pk'])[:7]  # afkappen voor de veiligheid
        except KeyError:
            raise Http404('Wedstrijd niet gevonden')

        match, deelcomp, ronde = bepaal_match_en_deelcomp_of_404(match_pk, mag_database_wijzigen=True)
        uitslag = match.uitslag

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if not mag_deelcomp_wedstrijd_wijzigen(match, functie_nu, ronde.regiocomp):
            raise PermissionDenied('Geen toegang')

        # voorkom wijzigingen bevroren wedstrijduitslag
        if rol_nu in (Rol.ROL_HWL, Rol.ROL_WL) and uitslag.is_bevroren:
            raise Http404('Uitslag mag niet meer gewijzigd worden')

        door_account = get_account(request)
        when = timezone.now()

        self.scores_opslaan(uitslag, data, when, door_account)

        out = {'done': 1}
        return JsonResponse(out)


# end of file
