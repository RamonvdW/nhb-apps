# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.formats import localize
from django.db.models import Q
from BasisTypen.models import BoogType
from Bestel.models import Bestelling
from Competitie.models import (Competitie, DeelCompetitie,
                               RegioCompetitieSchutterBoog,
                               LAAG_REGIO, INSCHRIJF_METHODE_1)
from Functie.rol import Rollen, rol_get_huidige
from Functie.models import Functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Plein.menu import menu_dynamics
from Records.models import IndivRecord, MATERIAALKLASSE
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist, AG_DOEL_TEAM, AG_DOEL_INDIV
from Sporter.models import Sporter, SporterBoog, Speelsterkte, get_sporter_voorkeuren
import logging
import copy


TEMPLATE_PROFIEL = 'sporter/profiel.dtl'

my_logger = logging.getLogger('NHBApps.Sporter')


class ProfielView(UserPassesTestMixin, TemplateView):

    """ Dit is de profielpagina van een sporter """

    template_name = TEMPLATE_PROFIEL
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    @staticmethod
    def _find_histcomp_scores(sporter, alle_bogen):
        """ Zoek alle scores van deze sporter """
        boogtype2str = dict()
        for boog in alle_bogen:
            boogtype2str[boog.afkorting] = boog.beschrijving
        # for

        objs = list()
        for obj in (HistCompetitieIndividueel
                    .objects
                    .filter(sporter_lid_nr=sporter.lid_nr)
                    .exclude(totaal=0)
                    .select_related('histcompetitie')
                    .order_by('histcompetitie__comp_type',      # 18/25
                              '-histcompetitie__seizoen')):     # jaartal, aflopend
            obj.competitie_str = HistCompetitie.comptype2str[obj.histcompetitie.comp_type]
            obj.seizoen_str = obj.histcompetitie.seizoen
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
    def _find_records(sporter):
        """ Zoek de records van deze sporter """
        mat2str = dict()
        for tup in MATERIAALKLASSE:
            afk, beschrijving = tup
            mat2str[afk] = beschrijving
        # for

        show_loc = False
        objs = list()
        for rec in IndivRecord.objects.filter(sporter=sporter).order_by('-datum'):
            rec.url = reverse('Records:specifiek',
                              kwargs={'discipline': rec.discipline,
                                      'nummer': rec.volg_nr})
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
        for comp in (Competitie
                     .objects.filter(is_afgesloten=False)
                     .order_by('afstand', 'begin_jaar')):
            comp.bepaal_fase()
            comp.bepaal_openbaar(Rollen.ROL_SPORTER)
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
                        comp.inschrijven = 'De inschrijving is open tot %s' % localize(comp.einde_aanmeldingen)
                    elif comp.fase < 'F':
                        comp.inschrijven = 'Aanmelden kan nog tot %s' % localize(comp.laatst_mogelijke_wedstrijd)

                comps.append(comp)
        # for
        return comps

    @staticmethod
    def _find_regiocompetities(comps, sporter, voorkeuren, alle_bogen):
        """ Zoek regiocompetities waar de sporter zich op aan kan melden """

        # stel vast welke boogtypen de sporter mee wil schieten (opt-in)
        boog_dict = dict()      # [afkorting] = BoogType()
        for boogtype in alle_bogen:
            boog_dict[boogtype.afkorting] = boogtype
        # for

        boog_afkorting_wedstrijd = list()
        boogafk2sporterboog = dict()       # [boog_afkorting] = SporterBoog()
        # typische 0 tot 5 records
        for sporterboog in (sporter
                            .sporterboog_set
                            .select_related('boogtype')
                            .order_by('boogtype__volgorde')):
            if sporterboog.voor_wedstrijd:
                afkorting = sporterboog.boogtype.afkorting
                boog_afkorting_wedstrijd.append(afkorting)
                boogafk2sporterboog[afkorting] = sporterboog
        # for

        moet_bogen_kiezen = (len(boogafk2sporterboog) == 0)
        gebruik_knoppen = False

        # zoek alle inschrijvingen van deze sporter erbij
        inschrijvingen = list(RegioCompetitieSchutterBoog
                              .objects
                              .select_related('deelcompetitie', 'sporterboog')
                              .filter(sporterboog__sporter=sporter))

        if not voorkeuren.voorkeur_meedoen_competitie:
            if len(inschrijvingen) == 0:        # niet nodig om "afmelden" knoppen te tonen
                return None, moet_bogen_kiezen, gebruik_knoppen

        objs = list()

        comp_pks = [comp.pk for comp in comps]

        # zoek deelcompetities in deze regio (typisch zijn er 2 in de regio: 18m en 25m)
        regio = sporter.bij_vereniging.regio
        for deelcompetitie in (DeelCompetitie
                               .objects
                               .select_related('competitie')
                               .exclude(competitie__is_afgesloten=True)
                               .filter(competitie__pk__in=comp_pks,
                                       laag=LAAG_REGIO,
                                       nhb_regio=regio)
                               .order_by('competitie__afstand')):
            comp = deelcompetitie.competitie
            comp.bepaal_fase()

            comp_boog_afk = [boogtype.afkorting for boogtype in comp.boogtypen.all()]

            # doorloop elk boogtype waar de sporter informatie/wedstrijden voorkeur voor heeft
            for afk in boog_afkorting_wedstrijd:
                if afk in comp_boog_afk:
                    obj = copy.copy(deelcompetitie)
                    objs.append(obj)

                    obj.boog_afkorting = afk
                    obj.boog_beschrijving = boog_dict[afk].beschrijving
                    obj.boog_niet_meer = False
                    obj.is_ingeschreven = False

                    # zoek uit of de sporter al ingeschreven is
                    sporterboog = boogafk2sporterboog[afk]
                    for inschrijving in inschrijvingen:
                        if inschrijving.sporterboog == sporterboog and inschrijving.deelcompetitie == obj:
                            obj.is_ingeschreven = True
                            inschrijvingen.remove(inschrijving)
                            if comp.fase <= 'B':
                                obj.url_afmelden = reverse('CompInschrijven:afmelden',
                                                           kwargs={'deelnemer_pk': inschrijving.pk})
                                gebruik_knoppen = True

                            if obj.inschrijf_methode == INSCHRIJF_METHODE_1 and comp.fase <= 'E':
                                obj.url_schietmomenten = reverse('CompLaagRegio:keuze-zeven-wedstrijden',
                                                                 kwargs={'deelnemer_pk': inschrijving.pk})
                                gebruik_knoppen = True
                            break
                    # for

                    if not obj.is_ingeschreven:
                        # niet ingeschreven
                        if 'B' <= comp.fase < 'F':
                            obj.url_aanmelden = reverse('CompInschrijven:bevestig-aanmelden',
                                                        kwargs={'sporterboog_pk': sporterboog.pk,
                                                                'deelcomp_pk': obj.pk})
                            gebruik_knoppen = True
            # for
        # for

        # voeg alle inschrijvingen toe waar geen boog meer voor gekozen is,
        # zodat er afgemeld kan worden
        for inschrijving in inschrijvingen:
            afk = inschrijving.sporterboog.boogtype.afkorting
            obj = inschrijving.deelcompetitie
            objs.append(obj)

            obj.is_ingeschreven = True
            obj.boog_niet_meer = True
            obj.boog_beschrijving = boog_dict[afk].beschrijving

            comp = obj.competitie
            comp.bepaal_fase()
            if comp.fase <= 'B':
                obj.url_afmelden = reverse('CompInschrijven:afmelden',
                                           kwargs={'deelnemer_pk': inschrijving.pk})
                gebruik_knoppen = True
        # for

        return objs, moet_bogen_kiezen, gebruik_knoppen

    @staticmethod
    def _find_gemiddelden(sporter, alle_bogen):
        # haal de SporterBoog records op van deze gebruiker
        objs = (SporterBoog
                .objects
                .filter(sporter=sporter)
                .select_related('boogtype')
                .order_by('boogtype__volgorde'))

        # maak ontbrekende SporterBoog records aan, indien nodig
        aantal_boogtypen = alle_bogen.count()
        if len(objs) < aantal_boogtypen:
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            for boogtype in alle_bogen.exclude(pk__in=aanwezig):
                sporterboog = SporterBoog(
                                    sporter=sporter,
                                    boogtype=boogtype)
                sporterboog.save()
            # for
            objs = (SporterBoog
                    .objects
                    .filter(sporter=sporter)
                    .select_related('boogtype')
                    .order_by('boogtype__volgorde'))

        # zoek de AG informatie erbij
        pks = [obj.pk for obj in objs]
        # haal AG's voor dit boogtype op, van 18m en 25m op, indien aanwezig
        ags = (Aanvangsgemiddelde
               .objects
               .filter(sporterboog__in=pks,
                       doel__in=(AG_DOEL_INDIV, AG_DOEL_TEAM))
               .select_related('sporterboog')
               .order_by('afstand_meter'))

        # haal alle benodigde hist objects met 1 query op
        ag_pks = ags.values_list('pk', flat=True)
        hists = (AanvangsgemiddeldeHist
                 .objects
                 .select_related('ag')
                 .filter(ag__in=ag_pks)
                 .order_by('-when'))
        for ag in ags:
            for hist in hists:              # pragma: no branch
                if hist.ag.pk == ag.pk:
                    ag.hist = hist          # nieuwste
                    break   # from the for
            # for
        # for

        # koppel de boog typen aan de sporterboog
        heeft_ags = False
        for obj in objs:
            obj.ags = list()
            for ag in ags:
                if ag.sporterboog == obj:
                    obj.ags.append(ag)
            # for
            if len(obj.ags) > 0:
                heeft_ags = True
        # for

        return objs, heeft_ags

    @staticmethod
    def _get_contact_gegevens(sporter, context):

        context['sec_namen'] = list()
        context['hwl_namen'] = list()
        context['rcl18_namen'] = list()
        context['rcl25_namen'] = list()

        if sporter.bij_vereniging:

            if sporter.bij_vereniging.geen_wedstrijden:
                context['geen_wedstrijden'] = True

            regio = sporter.bij_vereniging.regio

            functies = (Functie
                        .objects
                        .prefetch_related('accounts')
                        .filter(Q(rol='RCL',
                                  nhb_regio=regio) |
                                Q(rol__in=('SEC', 'HWL'),
                                  nhb_ver=sporter.bij_vereniging))
                        .all())

            for functie in functies:
                namen = [account.volledige_naam() for account in functie.accounts.all()]
                namen.sort()

                if functie.rol == 'SEC':
                    # nog geen account aangemaakt, dus haal de naam op van de secretaris volgens CRM
                    if len(namen) == 0 and sporter.bij_vereniging.secretaris_set.count() > 0:
                        sec = sporter.bij_vereniging.secretaris_set.all()[0]
                        namen = [sporter.volledige_naam() for sporter in sec.sporters.all()]
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

        context['bb_email'] = settings.EMAIL_BONDSBUREAU
        context['url_vcp_contact'] = settings.URL_VCP_CONTACTGEGEVENS

    @staticmethod
    def _find_speelsterktes(sporter):
        sterktes = Speelsterkte.objects.filter(sporter=sporter).order_by('volgorde')
        if sterktes.count() == 0:           # pragma: no branch
            sterktes = None
        return sterktes

    @staticmethod
    def _find_diplomas(sporter):
        diplomas = list(sporter.opleidingdiploma_set.order_by('-datum_begin'))
        if len(diplomas) == 0:           # pragma: no branch
            diplomas = None
        return diplomas

    @staticmethod
    def _find_scores(sporter):
        scores = list()

        for deelnemer in (RegioCompetitieSchutterBoog
                          .objects
                          .select_related('deelcompetitie',
                                          'deelcompetitie__competitie',
                                          'sporterboog',
                                          'sporterboog__boogtype')
                          .filter(sporterboog__sporter=sporter)
                          .order_by('deelcompetitie__competitie__afstand')):

            comp = deelnemer.deelcompetitie.competitie

            if comp.afstand == '18':
                deelnemer.competitie_str = "18m Indoor"
            else:
                deelnemer.competitie_str = "25m 1pijl"

            deelnemer.seizoen_str = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

            deelnemer.scores_str = "%s, %s, %s, %s, %s, %s, %s" % (deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4, deelnemer.score5, deelnemer.score6, deelnemer.score7)

            deelnemer.boog_str = deelnemer.sporterboog.boogtype.beschrijving

            scores.append(deelnemer)
        # for
        return scores

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        account = self.request.user
        sporter = (account
                   .sporter_set
                   .select_related('bij_vereniging',
                                   'bij_vereniging__regio',
                                   'bij_vereniging__regio__rayon')
                   .all())[0]
        voorkeuren = get_sporter_voorkeuren(sporter)

        alle_bogen = BoogType.objects.all()

        context['sporter'] = sporter
        context['records'], context['show_loc'] = self._find_records(sporter)
        context['histcomp'] = self._find_histcomp_scores(sporter, alle_bogen)
        context['url_bondspas'] = reverse('Bondspas:toon-bondspas')

        context['toon_bondscompetities'] = False
        if sporter.bij_vereniging and not sporter.bij_vereniging.geen_wedstrijden:
            context['toon_bondscompetities'] = True

            context['competities'] = comps = self._find_competities(voorkeuren)

            regiocomps, moet_bogen_kiezen, gebruik_knoppen = self._find_regiocompetities(comps, sporter, voorkeuren, alle_bogen)
            context['regiocompetities'] = regiocomps
            context['moet_bogen_kiezen'] = moet_bogen_kiezen
            context['gebruik_knoppen'] = gebruik_knoppen

            context['regiocomp_scores'] = self._find_scores(sporter)

            context['gemiddelden'], context['heeft_ags'] = self._find_gemiddelden(sporter, alle_bogen)

            if not voorkeuren.voorkeur_meedoen_competitie:
                if regiocomps is None:
                    # niet ingeschreven en geen interesse
                    context['toon_bondscompetities'] = False

            context['speelsterktes'] = self._find_speelsterktes(sporter)
            context['diplomas'] = self._find_diplomas(sporter)

        if Bestelling.objects.filter(account=account).count() > 0:
            context['toon_bestellingen'] = True

        self._get_contact_gegevens(sporter, context)

        context['kruimels'] = (
            (None, 'Mijn pagina'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
