# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.formats import localize
from django.db.models import Q
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige
from Functie.models import Functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, DeelCompetitie,
                               RegioCompetitieSchutterBoog,
                               LAAG_REGIO, INSCHRIJF_METHODE_1)
from Records.models import IndivRecord, MATERIAALKLASSE
from Score.models import Score, ScoreHist, SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG
from .leeftijdsklassen import bereken_leeftijdsklassen
from .models import SchutterVoorkeuren, SchutterBoog
import logging
import copy


TEMPLATE_PROFIEL = 'schutter/profiel.dtl'

my_logger = logging.getLogger('NHBApps.Schutter')


class ProfielView(UserPassesTestMixin, TemplateView):

    """ Dit is de profiel pagina van een schutter """

    template_name = TEMPLATE_PROFIEL
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SCHUTTER

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
                    .order_by('histcompetitie__comp_type',      # 18/25
                              '-histcompetitie__seizoen')):     # jaartal, aflopend
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
        mat2str = dict()
        for tup in MATERIAALKLASSE:
            afk, beschrijving = tup
            mat2str[afk] = beschrijving
        # for

        show_loc = False
        objs = list()
        for rec in IndivRecord.objects.filter(nhb_lid=nhblid).order_by('-datum'):
            rec.url = reverse('Records:specifiek', kwargs={'discipline': rec.discipline, 'nummer': rec.volg_nr})
            objs.append(rec)

            loc = [rec.plaats]
            if rec.land:
                loc.append(rec.land)
            rec.loc_str = ", ".join(loc)
            if rec.loc_str:
                show_loc = True

            rec.boog_str = mat2str[rec.materiaalklasse]
        # for
        return objs, show_loc

    @staticmethod
    def _find_competities(voorkeuren):
        comps = list()
        if voorkeuren.voorkeur_meedoen_competitie:
            for comp in (Competitie
                         .objects.filter(is_afgesloten=False)
                         .order_by('afstand', 'begin_jaar')):
                comp.bepaal_fase()
                comp.bepaal_openbaar(Rollen.ROL_SCHUTTER)
                if comp.is_openbaar:
                    # fase B of later
                    comp.inschrijven = 'De inschrijving is gesloten'

                    if comp.alle_rks_afgesloten:
                        comp.fase_str = 'Bondskampioenschappen'
                    elif comp.alle_regiocompetities_afgesloten:
                        comp.fase_str = 'Rayonkampioenschappen'
                    else:
                        comp.fase_str = 'Regiocompetitie'
                        if comp.fase < 'C':
                            comp.inschrijven = 'Volwaardig inschrijven kan tot %s' % localize(comp.einde_aanmeldingen)
                        elif comp.fase < 'F':
                            comp.inschrijven = 'Meedoen kan tot %s' % localize(comp.laatst_mogelijke_wedstrijd)

                    comps.append(comp)
            # for
        return comps

    @staticmethod
    def _find_regiocompetities(comps, nhblid, voorkeuren, alle_bogen):
        """ Zoek regiocompetities waar de schutter zich op aan kan melden """

        # stel vast welke boogtypen de schutter mee wil schieten (opt-in)
        boog_dict = dict()      # [afkorting] = BoogType()
        for boogtype in alle_bogen:
            boog_dict[boogtype.afkorting] = boogtype
        # for

        boog_afkorting_wedstrijd = list()
        boogafk2schutterboog = dict()       # [boog_afkorting] = SchutterBoog()
        # typische 0 tot 5 records
        for schutterboog in (nhblid.schutterboog_set
                             .select_related('boogtype')
                             .order_by('boogtype__volgorde')):
            if schutterboog.voor_wedstrijd:
                afkorting = schutterboog.boogtype.afkorting
                boog_afkorting_wedstrijd.append(afkorting)
                boogafk2schutterboog[afkorting] = schutterboog
        # for

        # zoek alle inschrijvingen van deze schutter erbij
        inschrijvingen = list(RegioCompetitieSchutterBoog
                              .objects
                              .select_related('deelcompetitie', 'schutterboog')
                              .filter(schutterboog__nhblid=nhblid))

        if not voorkeuren.voorkeur_meedoen_competitie:
            if len(inschrijvingen) == 0:        # niet nodig om "afmelden" knoppen te tonen
                return None

        objs = list()

        comp_pks = [comp.pk for comp in comps]

        # zoek deelcompetities in deze regio (typisch zijn er 2 in de regio: 18m en 25m)
        regio = nhblid.bij_vereniging.regio
        for deelcompetitie in (DeelCompetitie
                               .objects
                               .select_related('competitie')
                               .prefetch_related('competitie__competitieklasse_set')
                               .exclude(competitie__is_afgesloten=True)
                               .filter(competitie__pk__in=comp_pks,
                                       laag=LAAG_REGIO,
                                       nhb_regio=regio)
                               .order_by('competitie__afstand')):
            comp = deelcompetitie.competitie
            comp.bepaal_fase()

            # doorloop elk boogtype waar de schutter informatie/wedstrijden voorkeur voor heeft
            for afk in boog_afkorting_wedstrijd:
                obj = copy.copy(deelcompetitie)
                objs.append(obj)

                obj.boog_afkorting = afk
                obj.boog_beschrijving = boog_dict[afk].beschrijving
                obj.boog_niet_meer = False
                obj.is_ingeschreven = False

                # zoek uit of de schutter al ingeschreven is
                schutterboog = boogafk2schutterboog[afk]
                for inschrijving in inschrijvingen:
                    if inschrijving.schutterboog == schutterboog and inschrijving.deelcompetitie == obj:
                        obj.is_ingeschreven = True
                        inschrijvingen.remove(inschrijving)
                        if comp.fase <= 'B':
                            obj.url_afmelden = reverse('Schutter:afmelden',
                                                       kwargs={'deelnemer_pk': inschrijving.pk})

                        if obj.inschrijf_methode == INSCHRIJF_METHODE_1 and comp.fase <= 'E':
                            obj.url_schietmomenten = reverse('Schutter:schietmomenten',
                                                             kwargs={'deelnemer_pk': inschrijving.pk})
                        break
                # for

                if not obj.is_ingeschreven:
                    # niet ingeschreven
                    if 'B' <= comp.fase < 'F':
                        obj.url_aanmelden = reverse('Schutter:bevestig-aanmelden',
                                                    kwargs={'schutterboog_pk': schutterboog.pk,
                                                            'deelcomp_pk': obj.pk})
            # for
        # for

        # voeg alle inschrijvingen toe waar geen boog meer voor gekozen is,
        # zodat er afgemeld kan worden
        for inschrijving in inschrijvingen:
            afk = inschrijving.schutterboog.boogtype.afkorting
            obj = inschrijving.deelcompetitie
            objs.append(obj)

            obj.is_ingeschreven = True
            obj.boog_niet_meer = True
            obj.boog_beschrijving = boog_dict[afk].beschrijving

            comp = obj.competitie
            comp.bepaal_fase()
            if comp.fase <= 'B':
                obj.url_afmelden = reverse('Schutter:afmelden',
                                           kwargs={'deelnemer_pk': inschrijving.pk})
        # for

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
                          type__in=(SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG))
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
                  .select_related('bij_vereniging',
                                  'bij_vereniging__regio',
                                  'bij_vereniging__regio__rayon')
                  .all())[0]
        voorkeuren, _ = SchutterVoorkeuren.objects.get_or_create(nhblid=nhblid)

        alle_bogen = BoogType.objects.all()

        context['nhblid'] = nhblid
        context['records'], context['show_loc'] = self._find_records(nhblid)
        context['histcomp'] = self._find_histcomp_scores(nhblid, alle_bogen)

        if nhblid.bij_vereniging and not nhblid.bij_vereniging.geen_wedstrijden:
            context['competities'] = comps = self._find_competities(voorkeuren)
            context['regiocompetities'] = self._find_regiocompetities(comps, nhblid, voorkeuren, alle_bogen)
            context['gemiddelden'], context['heeft_ags'] = self._find_gemiddelden(nhblid, alle_bogen)

        self._get_contact_gegevens(nhblid, context)

        menu_dynamics(self.request, context, actief='schutter-profiel')
        return context


# end of file
