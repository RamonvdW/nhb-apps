# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import Resolver404, reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Wedstrijden.models import Wedstrijd, WedstrijdUitslag
from Schutter.models import SchutterBoog
from Score.models import Score, ScoreHist, SCORE_WAARDE_VERWIJDERD
from .models import (LAAG_REGIO, DeelCompetitie,
                     DeelcompetitieRonde, RegioCompetitieSchutterBoog)
import json
import sys


TEMPLATE_COMPETITIE_UITSLAG_INVOEREN_WEDSTRIJD = 'competitie/uitslag-invoeren-wedstrijd.dtl'


class UitslagInvoerenWedstrijdView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RCL de uitslag van een wedstrijd invoeren """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPETITIE_UITSLAG_INVOEREN_WEDSTRIJD

    # TODO: ondersteuning voor HWL en WL toevoegen

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RCL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def bepaal_wedstrijd_en_deelcomp_of_404(wedstrijd_pk):
        try:
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Resolver404()

        plan = wedstrijd.wedstrijdenplan_set.all()[0]

        # zoek de ronde erbij
        # deze hoort al bij een competitie type (indoor / 25m1pijl)
        ronde = (DeelcompetitieRonde
                 .objects
                 .select_related('deelcompetitie',
                                 'deelcompetitie__nhb_regio',
                                 'deelcompetitie__competitie')
                 .get(plan=plan))

        deelcomp = ronde.deelcompetitie

        # maak de WedstrijdUitslag aan indien nog niet gedaan
        if not wedstrijd.uitslag:
            uitslag = WedstrijdUitslag()
            if deelcomp.competitie.afstand == '18':
                uitslag.max_score = 300
                uitslag.afstand_meter = 18
            else:
                uitslag.max_score = 250
                uitslag.afstand_meter = 25
            uitslag.save()
            wedstrijd.uitslag = uitslag
            wedstrijd.save()

        return wedstrijd, deelcomp

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        wedstrijd_pk = kwargs['wedstrijd_pk'][:6]     # afkappen geeft beveiliging
        wedstrijd, deelcomp = self.bepaal_wedstrijd_en_deelcomp_of_404(wedstrijd_pk)

        context['wedstrijd'] = wedstrijd
        context['deelcomp'] = deelcomp

        # TODO: controleer toestemming om scoreverwerking te doen voor deze wedstrijd

        #rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        #if rol_nu == 'RCL':
        #    # regio = functie_nu.nhb_regio

        context['scores'] = (wedstrijd
                             .uitslag
                             .scores
                             .exclude(is_ag=True)
                             .exclude(waarde=SCORE_WAARDE_VERWIJDERD)
                             .select_related('schutterboog',
                                             'schutterboog__boogtype',
                                             'schutterboog__nhblid',
                                             'schutterboog__nhblid__bij_vereniging')
                             .order_by('schutterboog__nhblid__nhb_nr'))

        context['url_check_nhbnr'] = reverse('Competitie:dynamic-check-nhbnr')
        context['url_opslaan'] = reverse('Competitie:dynamic-scores-opslaan')
        context['url_deelnemers_ophalen'] = reverse('Competitie:dynamic-deelnemers-ophalen')

        plan = wedstrijd.wedstrijdenplan_set.all()[0]
        ronde = DeelcompetitieRonde.objects.get(plan=plan)
        context['url_terug'] = reverse('Competitie:regio-ronde-planning', kwargs={'ronde_pk': ronde.pk})

        menu_dynamics(self.request, context, actief='competitie')
        return context


class DynamicDeelnemersOphalenView(UserPassesTestMixin, View):

    # TODO: UserPassesTestMixing is niet echt nodig - kan direct in post()
    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        #TODO: HWL/WL toevoegen
        return rol_nu == Rollen.ROL_RCL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang """
        raise Resolver404()

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'deelnemers ophalen' gebruikt wordt
        """

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            raise Resolver404()         # garbage in

        # print('data: %s' % repr(data))

        try:
            deelcomp_pk = str(data['deelcomp_pk'])[:6]   # afkappen voor extra veiligheid
            deelcomp = DeelCompetitie.objects.get(laag=LAAG_REGIO,
                                                  pk=deelcomp_pk)
        except KeyError:
            raise Resolver404()         # garbage in
        except DeelCompetitie.DoesNotExist:
            raise Resolver404()         # garbage in

        # TODO: filter deelnemers op cluster (wedstrijd.vereniging.clusters)

        out = dict()
        out['deelnemers'] = deelnemers = list()

        for obj in (RegioCompetitieSchutterBoog
                    .objects
                    .select_related('schutterboog',
                                    'schutterboog__nhblid',
                                    'schutterboog__boogtype',
                                    'bij_vereniging')
                    .filter(deelcompetitie=deelcomp)):

            deelnemer = {
                'pk': obj.schutterboog.pk,
                'nhb_nr': obj.schutterboog.nhblid.nhb_nr,
                'naam': obj.schutterboog.nhblid.volledige_naam(),
                'ver_nr': obj.bij_vereniging.nhb_nr,
                'ver_naam': obj.bij_vereniging.naam,
                'boog': obj.schutterboog.boogtype.beschrijving,
            }

            deelnemers.append(deelnemer)
        # for

        return JsonResponse(out)


class DynamicZoekOpNhbnrView(UserPassesTestMixin, View):

    # TODO: UserPassesTestMixing is niet echt nodig - kan direct in post()
    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        #TODO: HWL/WL toevoegen
        return rol_nu == Rollen.ROL_RCL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang """
        raise Resolver404()

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Zoek' gebruikt wordt
        """

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            raise Resolver404()         # garbage in

        # zoek een
        # print('data: %s' % repr(data))

        try:
            nhb_nr = str(data['nhb_nr'])[:6]               # afkappen voor extra veiligheid
            wedstrijd_pk = str(data['wedstrijd_pk'])[:6]   # afkappen voor extra veiligheid
            wedstrijd = Wedstrijd.objects.get(pk=wedstrijd_pk)
        except KeyError:
            raise Resolver404()         # garbage in
        except Wedstrijd.DoesNotExist:
            raise Resolver404()         # garbage in

        plan = wedstrijd.wedstrijdenplan_set.all()[0]

        # zoek de ronde erbij
        # deze hoort al bij een competitie type (indoor / 25m1pijl)
        ronde = (DeelcompetitieRonde
                 .objects
                 .select_related('deelcompetitie',
                                 'deelcompetitie__nhb_regio',
                                 'deelcompetitie__competitie')
                 .get(plan=plan))

        # zoek schuttersboog die ingeschreven zijn voor deze competitie
        competitie = ronde.deelcompetitie.competitie

        out = dict()

        try:
            deelnemers = (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('schutterboog',
                                          'schutterboog__boogtype',
                                          'schutterboog__nhblid',
                                          'schutterboog__nhblid__bij_vereniging')
                          .filter(deelcompetitie__competitie=competitie,
                                  schutterboog__nhblid__nhb_nr=nhb_nr))
        except RegioCompetitieSchutterBoog.DoesNotExist:
            out['fail'] = 1
        else:
            if len(deelnemers) == 0:
                out['fail'] = 1         # is niet ingeschreven voor deze competitie
            else:
                # bouw het antwoord op
                nhblid = deelnemers[0].schutterboog.nhblid
                out['nhb_nr'] = nhblid.nhb_nr
                out['naam'] = nhblid.volledige_naam()
                out['vereniging'] = str(nhblid.bij_vereniging)
                out['regio'] = str(nhblid.bij_vereniging.regio)
                out['bogen'] = bogen = list()
                for deelnemer in deelnemers:

                    #MISSCHIEN BETER OM DEELNEMER.PK terug te geven

                    bogen.append({'pk': deelnemer.schutterboog.pk,
                                  'boog': deelnemer.schutterboog.boogtype.beschrijving})
                # for

        return JsonResponse(out)


class DynamicScoresOpslaanView(UserPassesTestMixin, View):

    # TODO: UserPassesTestMixing is niet echt nodig - kan direct in post()
    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        #TODO: HWL/WL toevoegen
        return rol_nu == Rollen.ROL_RCL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang """
        raise Resolver404()

    @staticmethod
    def laad_wedstrijd_of_404(data):
        try:
            # invoer kan string of numeriek zijn
            wedstrijd_pk = str(data['wedstrijd_pk'])[:6]     # afkappen geeft beveiliging
        except KeyError:
            # verplicht veld afwezig is suspicious
            raise Resolver404()

        try:
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('uitslag')
                         .prefetch_related('uitslag__scores')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Resolver404()

        return wedstrijd

    @staticmethod
    def nieuwe_score(uitslag, schutterboog_pk, waarde, datum, door_account):
        print('nieuwe score: %s = %s' % (schutterboog_pk, waarde))

        schutterboog = SchutterBoog.objects.get(pk=schutterboog_pk)

        score_obj = Score(schutterboog=schutterboog,
                          is_ag=False,
                          waarde=waarde,
                          afstand_meter=uitslag.afstand_meter)
        score_obj.save()
        uitslag.scores.add(score_obj)

        ScoreHist(score=score_obj,
                  oude_waarde=0,
                  nieuwe_waarde=waarde,
                  datum=datum,
                  door_account=door_account,
                  notitie="Invoer uitslag wedstrijd").save()

    @staticmethod
    def bijgewerkte_score(score_obj, waarde, datum, door_account):
        if score_obj.waarde != waarde:
            print('bijgewerkte score: %s --> %s' % (score_obj, waarde))

            ScoreHist(score=score_obj,
                      oude_waarde=score_obj.waarde,
                      nieuwe_waarde=waarde,
                      datum=datum,
                      door_account=door_account,
                      notitie="Invoer uitslag wedstrijd").save()

            score_obj.waarde = waarde
            score_obj.save()
        # else: zelfde score

    def scores_opslaan(self, uitslag, data, datum, door_account):
        """ sla de scores op
            data bevat schutterboog_pk + score
            als score leeg is moet pk uit de uitslag gehaald worden
        """

        # doorloop alle scores in de uitslag en haal de schutterboog erbij
        # hiermee kunnen we snel controleren of iemand al in de uitslag
        # voorkomt
        pk2score_obj = dict()
        for score_obj in uitslag.scores.all():
            pk2score_obj[score_obj.schutterboog.pk] = score_obj
        # for
        print('pk2score_obj: %s' % repr(pk2score_obj))

        for key, value in data.items():
            if key == 'wedstrijd_pk':
                # geen schutterboog
                continue

            try:
                pk = int(str(key)[:6])     # afkappen geeft beveiliging
            except ValueError:
                # fout pk: ignore
                continue        # met de for-loop

            try:
                score_obj = pk2score_obj[pk]
            except KeyError:
                # schutterboog zit nog niet in de uitslag
                score_obj = None

            if isinstance(value, str) and value == '':
                # lege invoer betekent: schutter deed niet mee
                #print('schutter deed niet mee: %s' % pk)

                if score_obj:
                    # verwijder deze score uit de uit, maar behoud de geschiedenis
                    waarde = SCORE_WAARDE_VERWIJDERD
                    self.bijgewerkte_score(score_obj, waarde, datum, door_account)
                else:
                    # geen score en al afwezig in de uitslag --> doe niets
                    continue

            # sla de score op
            try:
                waarde = int(str(value)[:4])   # afkappen geeft beveiliging
            except ValueError:
                # foute score: ignore
                continue

            if 0 <= waarde <= uitslag.max_score:
                print('score geaccepteerd: %s %s' % (pk, waarde))
                # score opslaan
                if not score_obj:
                    # het is een nieuwe score
                    self.nieuwe_score(uitslag, pk, waarde, datum, door_account)
                else:
                    self.bijgewerkte_score(score_obj, waarde, datum, door_account)
            # else: illegale score --> ignore
        # for

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Opslaan' gebruikt wordt
        """

        if not request.user.is_authenticated:
            raise Resolver404()

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            raise Resolver404()         # garbage in

        # print('data:', repr(data))

        wedstrijd = self.laad_wedstrijd_of_404(data)
        uitslag = wedstrijd.uitslag

        # TODO: controleer toestemming om scores op te slaan voor deze wedstrijd
        # plan = wedstrijd.wedstrijdenplan_set.all()[0]

        door_account = request.user
        datum = timezone.now()

        try:
            self.scores_opslaan(uitslag, data, datum, door_account)
        except:
            exc = sys.exc_info()[1]
            print('OHOH: %s' % exc)

        out = {'done': 1}
        return JsonResponse(out)


# end of file
