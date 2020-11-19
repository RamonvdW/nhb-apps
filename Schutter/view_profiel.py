# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from Functie.models import Functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from BasisTypen.models import BoogType
from Competitie.models import (CompetitieKlasse, DeelCompetitie, RegioCompetitieSchutterBoog,
                               LAAG_REGIO)
from Records.models import IndivRecord
from Score.models import Score, ScoreHist
from .leeftijdsklassen import get_sessionvars_leeftijdsklassen
from .models import SchutterVoorkeuren, SchutterBoog
import logging
import copy


TEMPLATE_PROFIEL = 'schutter/profiel.dtl'

my_logger = logging.getLogger('NHBApps.Schutter')


class ProfielView(UserPassesTestMixin, TemplateView):

    """ Dit is de profiel pagina van een schutter """

    template_name = TEMPLATE_PROFIEL

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _find_histcomp_scores(nhblid, alle_bogen):
        """ Zoek alle scores van deze schutter """
        boogtype2str = dict()
        for boog in alle_bogen:
            boogtype2str[boog.afkorting] = boog.beschrijving
        # for

        objs = list()
        for obj in (HistCompetitieIndividueel
                    .objects
                    .filter(schutter_nr=nhblid.nhb_nr)
                    .exclude(totaal=0)
                    .select_related('histcompetitie')
                    .order_by('-histcompetitie__seizoen')):
            obj.competitie_str = HistCompetitie.comptype2str[obj.histcompetitie.comp_type]
            obj.seizoen_str = 'Seizoen ' + obj.histcompetitie.seizoen
            try:
                obj.boog_str = boogtype2str[obj.boogtype]
            except KeyError:
                obj.boog_str = "?"

            scores = list()
            for score in (obj.score1, obj.score2, obj.score3, obj.score4, obj.score5, obj.score6, obj.score7):
                if score:
                    scores.append(str(score))
            # for
            obj.scores_str = ", ".join(scores)
            objs.append(obj)
        # for

        return objs

    @staticmethod
    def _find_records(nhblid):
        """ Zoek de records van deze schutter """
        objs = list()
        for rec in IndivRecord.objects.filter(nhb_lid=nhblid).order_by('-datum'):
            rec.url = reverse('Records:specifiek', kwargs={'discipline': rec.discipline, 'nummer': rec.volg_nr})
            objs.append(rec)
        # for
        return objs

    @staticmethod
    def _find_regiocompetities(nhblid, voorkeuren, alle_bogen):
        """ Zoek regiocompetities waar de schutter zich op aan kan melden """

        # toon alle deelcompetities waarop ingeschreven kan worden met de bogen van de schutter
        # oftewel (deelcompetitie, schutterboog, is_ingeschreven)

        # stel vast welke boogtypen de schutter mee wil schieten (opt-in)
        # en welke hij informatie over wil hebben (opt-out)
        boog_afkorting_wedstrijd = list()
        boog_afkorting_info = list()

        boog_dict = dict()      # [afkorting] = BoogType()
        for boogtype in alle_bogen:
            boog_dict[boogtype.afkorting] = boogtype
            boog_afkorting_info.append(boogtype.afkorting)
        # for

        schutterboog_dict = dict()  # [boog_afkorting] = SchutterBoog()
        # typische 0 tot 5 records
        for schutterboog in (nhblid.schutterboog_set
                             .select_related('boogtype')
                             .all()):
            afkorting = schutterboog.boogtype.afkorting
            schutterboog_dict[afkorting] = schutterboog
            if schutterboog.voor_wedstrijd:
                boog_afkorting_wedstrijd.append(afkorting)
                boog_afkorting_info.remove(afkorting)
            elif not schutterboog.heeft_interesse:
                boog_afkorting_info.remove(afkorting)
        # for

        boog_afkorting_all = set(boog_afkorting_info + boog_afkorting_wedstrijd)

        # zoek alle inschrijvingen van deze schutter erbij
        schutterbogen = [schutterboog for _, schutterboog in schutterboog_dict.items()]
        inschrijvingen = list(RegioCompetitieSchutterBoog
                              .objects
                              .select_related('deelcompetitie', 'schutterboog')
                              .filter(schutterboog__in=schutterbogen))

        if not voorkeuren.voorkeur_meedoen_competitie:
            if len(inschrijvingen) == 0:
                return None

        objs_info = list()
        objs_wedstrijd = list()

        # zoek deelcompetities in deze regio (typisch zijn er 2 in de regio: 18m en 25m)
        regio = nhblid.bij_vereniging.regio
        for deelcompetitie in (DeelCompetitie
                               .objects
                               .select_related('competitie')
                               .prefetch_related('competitie__competitieklasse_set')
                               .filter(laag=LAAG_REGIO,
                                       nhb_regio=regio,
                                       is_afgesloten=False)):
            deelcompetitie.competitie.zet_fase()

            # zoek de klassen erbij die de schutter interessant vindt
            afkortingen = list(boog_afkorting_all)
            for klasse in (CompetitieKlasse
                           .objects
                           .select_related('indiv__boogtype')
                           .filter(indiv__boogtype__afkorting__in=boog_afkorting_all,
                                   competitie=deelcompetitie.competitie)):
                afk = klasse.indiv.boogtype.afkorting
                if afk in afkortingen:
                    # dit boogtype nog niet gehad
                    afkortingen.remove(afk)
                    obj = copy.copy(deelcompetitie)
                    obj.boog_afkorting = afk
                    obj.boog_beschrijving = boog_dict[afk].beschrijving
                    obj.is_ingeschreven = False
                    if afk in boog_afkorting_wedstrijd:
                        obj.is_voor_wedstrijd = True
                        objs_wedstrijd.append(obj)
                    else:
                        obj.is_voor_wedstrijd = False
                        objs_info.append(obj)
            # for
        # for

        # zoek uit of de schutter al ingeschreven is
        for obj in objs_wedstrijd:
            schutterboog = schutterboog_dict[obj.boog_afkorting]

            obj.is_ingeschreven = False
            for inschrijving in inschrijvingen:
                if inschrijving.schutterboog == schutterboog and inschrijving.deelcompetitie == obj:
                    obj.is_ingeschreven = True
                    obj.url_afmelden = reverse('Schutter:afmelden', kwargs={'regiocomp_pk': inschrijving.pk})
                    inschrijvingen.remove(inschrijving)
                    break

            if not obj.is_ingeschreven:
                # niet ingeschreven
                obj.url_aanmelden = reverse('Schutter:bevestig-aanmelden', kwargs={'schutterboog_pk': schutterboog.pk, 'deelcomp_pk': obj.pk})
        # for

        # voeg alle inschrijvingen toe waar geen boog meer voor gekozen is,
        # zodat er afgemeld kan worden
        for obj in inschrijvingen:
            afk = obj.schutterboog.boogtype.afkorting
            deelcomp = obj.deelcompetitie
            deelcomp.is_ingeschreven = True
            deelcomp.is_voor_wedstrijd = True
            deelcomp.boog_niet_meer = True
            deelcomp.boog_beschrijving = boog_dict[afk].beschrijving
            deelcomp.url_afmelden = reverse('Schutter:afmelden', kwargs={'regiocomp_pk': obj.pk})
            objs_wedstrijd.append(deelcomp)
        # for

        objs = objs_wedstrijd
        if len(objs_info):
            objs_info[0].separator_before = True
            objs.extend(objs_info)
        return objs

    @staticmethod
    def _find_gemiddelden(nhblid, alle_bogen):
        # haal de SchutterBoog records op van deze gebruiker
        objs = (SchutterBoog
                .objects
                .filter(nhblid=nhblid)
                .select_related('boogtype')
                .order_by('boogtype__volgorde'))

        # maak ontbrekende SchutterBoog records aan, indien nodig
        aantal_boogtypen = alle_bogen.count()
        if len(objs) < aantal_boogtypen:
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            for boogtype in alle_bogen.exclude(pk__in=aanwezig):
                schutterboog = SchutterBoog()
                schutterboog.nhblid = nhblid
                schutterboog.boogtype = boogtype
                schutterboog.save()
            # for
            objs = (SchutterBoog
                    .objects
                    .filter(nhblid=nhblid)
                    .select_related('boogtype')
                    .order_by('boogtype__volgorde'))

        # zoek de AG informatie erbij
        pks = [obj.pk for obj in objs]
        # haal AG's voor dit boogtype op, van 18m en 25m op, indien aanwezig
        scores = (Score
                  .objects
                  .filter(schutterboog__in=pks,
                          is_ag=True)
                  .select_related('schutterboog')
                  .order_by('afstand_meter'))

        # haal alle benodigde ScoreHist objects met 1 query op
        score_pks = scores.values_list('pk', flat=True)
        hists = (ScoreHist
                 .objects
                 .select_related('score')
                 .filter(score__in=score_pks)
                 .order_by('-when'))
        for score in scores:
            score.ag = score.waarde / 1000
            for hist in hists:
                if hist.score.pk == score.pk:
                    score.scorehist = hist       # nieuwste
                    break   # from the for
            # for
        # for

        # koppel de boog typen aan de schutterboog
        heeft_ags = False
        for obj in objs:
            obj.ags = list()
            for score in scores:
                if score.schutterboog == obj:
                    obj.ags.append(score)
            # for
            if len(obj.ags) > 0:
                heeft_ags = True
        # for

        return objs, heeft_ags

    @staticmethod
    def _get_contact_gegevens(nhblid, context):

        context['sec_namen'] = list()
        context['hwl_namen'] = list()
        context['rcl18_namen'] = list()
        context['rcl25_namen'] = list()

        if not nhblid.bij_vereniging:
            return

        if nhblid.bij_vereniging.geen_wedstrijden:
            context['geen_wedstrijden'] = True

        regio = nhblid.bij_vereniging.regio

        functies = (Functie
                    .objects
                    .prefetch_related('accounts')
                    .filter(Q(rol='RCL',
                              nhb_regio=regio) |
                            Q(rol__in=('SEC', 'HWL'),
                              nhb_ver=nhblid.bij_vereniging))
                    .all())

        for functie in functies:
            namen = [account.volledige_naam() for account in functie.accounts.all()]
            namen.sort()

            if functie.rol == 'SEC':
                if len(namen) == 0 and nhblid.bij_vereniging.secretaris_lid:
                    namen = [nhblid.bij_vereniging.secretaris_lid.volledige_naam()]
                context['sec_namen'] = namen
                context['sec_email'] = functie.bevestigde_email
            elif functie.rol == 'HWL':
                context['hwl_namen'] = namen
                context['hwl_email'] = functie.bevestigde_email
            else:
                if functie.comp_type == '18':
                    # RCL 18m
                    context['rcl18_namen'] = namen
                    context['rcl18_email'] = functie.bevestigde_email
                else:
                    # RCL 25m
                    context['rcl25_namen'] = namen
                    context['rcl25_email'] = functie.bevestigde_email
        # for

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        account = self.request.user
        nhblid = (account
                  .nhblid_set
                  .select_related('bij_vereniging')
                  .all())[0]
        voorkeuren, _ = SchutterVoorkeuren.objects.get_or_create(nhblid=nhblid)

        alle_bogen = BoogType.objects.all()

        context['nhblid'] = nhblid
        context['records'] = self._find_records(nhblid)
        context['histcomp'] = self._find_histcomp_scores(nhblid, alle_bogen)

        if nhblid.bij_vereniging and not nhblid.bij_vereniging.geen_wedstrijden:
            _, _, is_jong, _, _ = get_sessionvars_leeftijdsklassen(self.request)
            context['toon_leeftijdsklassen'] = is_jong

            context['show_voorkeuren'] = True
            context['regiocompetities'] = self._find_regiocompetities(nhblid, voorkeuren, alle_bogen)
            context['gemiddelden'], context['heeft_ags'] = self._find_gemiddelden(nhblid, alle_bogen)

        self._get_contact_gegevens(nhblid, context)

        menu_dynamics(self.request, context, actief='schutter')
        return context


# end of file
