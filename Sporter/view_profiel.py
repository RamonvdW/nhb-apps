# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect, reverse
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from Account.models import get_account
from BasisTypen.models import BoogType
from Bestel.models import Bestelling
from Competitie.definities import DEEL_RK, INSCHRIJF_METHODE_1, DEELNAME_NEE
from Competitie.models_competitie import Competitie
from Competitie.models_laag_regio import Regiocompetitie, RegiocompetitieSporterBoog
from Competitie.models_laag_kamp import KampioenschapSporterBoog
from Functie.definities import Rollen
from Functie.models import Functie
from Functie.rol import rol_get_huidige
from HistComp.definities import HISTCOMP_TYPE2STR
from HistComp.models import HistCompRegioIndiv
from Kalender.view_maand import maak_compacte_wanneer_str
from Records.definities import MATERIAALKLASSE
from Records.models import IndivRecord
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Score.definities import AG_DOEL_TEAM, AG_DOEL_INDIV
from Score.models import Aanvangsgemiddelde, AanvangsgemiddeldeHist
from Sporter.models import SporterBoog, Speelsterkte
from Sporter.operations import get_sporter_gekozen_bogen, get_sporter_voorkeuren
from Wedstrijden.definities import (INSCHRIJVING_STATUS_RESERVERING_MANDJE, INSCHRIJVING_STATUS_RESERVERING_BESTELD,
                                    INSCHRIJVING_STATUS_DEFINITIEF, INSCHRIJVING_STATUS_AFGEMELD,
                                    INSCHRIJVING_STATUS_VERWIJDERD)
from Wedstrijden.models import WedstrijdInschrijving
import datetime
import logging
import copy


TEMPLATE_PROFIEL = 'sporter/profiel.dtl'

my_logger = logging.getLogger('MH.Sporter')


class ProfielView(UserPassesTestMixin, TemplateView):

    """ Dit is de profielpagina van een sporter """

    template_name = TEMPLATE_PROFIEL
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.account = None
        self.sporter = None
        self.ver = None
        self.voorkeuren = None
        self.alle_bogen = BoogType.objects.all()

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu == Rollen.ROL_SPORTER

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als het we geen vragen meer hebben + bij oneigenlijk gebruik """
        if request.user.is_authenticated:
            self.account = get_account(request)

            if self.account.is_gast:
                gast = self.account.gastregistratie_set.first()
                if gast and gast.fase != REGISTRATIE_FASE_COMPLEET:
                    # registratie is nog niet voltooid
                    # dwing terug naar de lijst met vragen
                    return redirect('Registreer:gast-meer-vragen')

            self.sporter = (self.account
                            .sporter_set
                            .select_related('bij_vereniging',
                                            'bij_vereniging__regio',
                                            'bij_vereniging__regio__rayon')
                            .prefetch_related('bij_vereniging__secretaris_set',
                                              'opleidingdiploma_set')
                            .first())

            if self.sporter:                                    # pragma: no branch
                self.ver = self.sporter.bij_vereniging

        return super().dispatch(request, *args, **kwargs)

    def _find_histcomp_scores(self):
        """ Zoek alle scores van deze sporter """
        boogtype2str = dict()
        for boog in self.alle_bogen:
            boogtype2str[boog.afkorting] = boog.beschrijving
        # for

        objs = list()
        for obj in (HistCompRegioIndiv
                    .objects
                    .filter(sporter_lid_nr=self.sporter.lid_nr)
                    .exclude(totaal=0)
                    .select_related('seizoen')
                    .order_by('seizoen__comp_type',      # 18/25
                              '-seizoen__seizoen')):     # jaartal, aflopend
            obj.competitie_str = HISTCOMP_TYPE2STR[obj.seizoen.comp_type]
            obj.seizoen_str = obj.seizoen.seizoen
            try:
                obj.beschrijving = boogtype2str[obj.boogtype]
            except KeyError:
                obj.beschrijving = "?"

            scores = list()
            for score in (obj.score1, obj.score2, obj.score3, obj.score4, obj.score5, obj.score6, obj.score7):
                if score:
                    scores.append(str(score))
            # for
            obj.scores_str = ", ".join(scores)
            objs.append(obj)
        # for

        return objs

    def _find_records(self):
        """ Zoek de records van deze sporter """
        mat2str = dict()
        for tup in MATERIAALKLASSE:
            afk, beschrijving = tup
            mat2str[afk] = beschrijving
        # for

        show_loc = False
        objs = list()
        for rec in IndivRecord.objects.filter(sporter=self.sporter).order_by('-datum'):
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
    def _find_competities():
        comps = list()
        for comp in (Competitie
                     .objects.filter(is_afgesloten=False)
                     .order_by('afstand', 'begin_jaar')):
            comp.bepaal_fase()
            comp.bepaal_openbaar(Rollen.ROL_SPORTER)
            if comp.is_openbaar:
                # fase B of later
                comp.inschrijven = 'De inschrijving is gesloten'

                if comp.rk_indiv_afgesloten and comp.rk_teams_afgesloten:
                    comp.fase_str = 'Bondskampioenschappen'
                elif comp.regiocompetitie_is_afgesloten:
                    comp.fase_str = 'Rayonkampioenschappen'
                else:
                    comp.fase_str = 'Regiocompetitie'

                    if comp.fase_indiv == 'C':
                        comp.inschrijven = 'De inschrijving is open tot %s' % localize(comp.begin_fase_D_indiv)
                    elif comp.fase_indiv <= 'F':
                        # tijdens de hele wedstrijden fase kan er aangemeld worden
                        comp.inschrijven = 'Aanmelden kan nog tot %s' % localize(comp.einde_fase_F)

                comps.append(comp)
        # for
        return comps

    def _find_regiocompetities(self, comps, boogafk2sporterboog, boog_afkorting_wedstrijd):
        """ Zoek regiocompetities waar de sporter zich op aan kan melden """

        # stel vast welke boogtypen de sporter mee wil schieten (opt-in)
        boog_dict = dict()      # [afkorting] = BoogType()
        for boogtype in self.alle_bogen:
            boog_dict[boogtype.afkorting] = boogtype
        # for

        gebruik_knoppen = False

        # zoek alle inschrijvingen van deze sporter erbij
        inschrijvingen = list(RegiocompetitieSporterBoog
                              .objects
                              .select_related('regiocompetitie',
                                              'sporterboog')
                              .filter(sporterboog__sporter=self.sporter,
                                      regiocompetitie__competitie__in=comps))

        if not self.voorkeuren.voorkeur_meedoen_competitie:
            if len(inschrijvingen) == 0:        # niet nodig om "afmelden" knoppen te tonen
                return None, gebruik_knoppen

        kampioenen = list(KampioenschapSporterBoog
                          .objects
                          .select_related('kampioenschap',
                                          'kampioenschap__competitie',
                                          'kampioenschap__rayon',
                                          'sporterboog')
                          .filter(sporterboog__sporter=self.sporter,
                                  kampioenschap__competitie__in=comps))

        objs = list()
        comp_pks = [comp.pk for comp in comps]

        # zoek regiocompetities in deze regio (typisch zijn er 2 in de regio: 18m en 25m)
        regio = self.sporter.bij_vereniging.regio
        for deelcomp in (Regiocompetitie
                         .objects
                         .select_related('competitie')
                         .exclude(competitie__is_afgesloten=True)
                         .filter(competitie__in=comps,
                                 regio=regio)
                         .order_by('competitie__afstand')):
            comp = deelcomp.competitie
            comp.bepaal_fase()

            comp_boog_afk = [boogtype.afkorting for boogtype in comp.boogtypen.all()]

            # doorloop elk boogtype waar de sporter informatie/wedstrijden voorkeur voor heeft
            for afk in boog_afkorting_wedstrijd:
                if afk in comp_boog_afk:
                    obj = copy.copy(deelcomp)
                    objs.append(obj)

                    obj.boog_afkorting = afk
                    obj.boog_beschrijving = boog_dict[afk].beschrijving
                    obj.boog_niet_meer = False
                    obj.is_ingeschreven = False

                    # zoek uit of de sporter al ingeschreven is
                    sporterboog = boogafk2sporterboog[afk]
                    for inschrijving in inschrijvingen:
                        if inschrijving.sporterboog == sporterboog and inschrijving.regiocompetitie == obj:
                            obj.is_ingeschreven = True
                            obj.afgemeld_voorkeur_rk = not inschrijving.inschrijf_voorkeur_rk_bk
                            inschrijvingen.remove(inschrijving)
                            if comp.fase_indiv <= 'C':
                                obj.url_afmelden = reverse('CompInschrijven:afmelden',
                                                           kwargs={'deelnemer_pk': inschrijving.pk})
                                gebruik_knoppen = True

                            if obj.inschrijf_methode == INSCHRIJF_METHODE_1 and comp.fase_indiv <= 'F':
                                obj.url_schietmomenten = reverse('CompLaagRegio:keuze-zeven-wedstrijden',
                                                                 kwargs={'deelnemer_pk': inschrijving.pk})
                                gebruik_knoppen = True
                            break
                    # for

                    if 'C' <= comp.fase_indiv <= 'F':
                        # niet ingeschreven?
                        if not obj.is_ingeschreven:
                            obj.url_aanmelden = reverse('CompInschrijven:bevestig-aanmelden',
                                                        kwargs={'sporterboog_pk': sporterboog.pk,
                                                                'deelcomp_pk': obj.pk})
                            gebruik_knoppen = True

                    elif 'J' <= comp.fase_indiv <= 'N':
                        # zoek de inschrijving voor het RK erbij
                        for kampioen in kampioenen:
                            if (kampioen.kampioenschap.competitie == deelcomp.competitie and
                                    kampioen.kampioenschap.deel == DEEL_RK and
                                    kampioen.sporterboog == sporterboog):

                                # RK inschrijving van deze sporterboog gevonden
                                obj.rk_inschrijving = kampioen

                                if kampioen.deelname != DEELNAME_NEE:
                                    kampioenschap = kampioen.kampioenschap
                                    obj.url_rk_deelnemers = reverse('CompUitslagen:uitslagen-rk-indiv-n',
                                                                    kwargs={'comp_pk_of_seizoen': kampioenschap.competitie.maak_seizoen_url(),
                                                                            'comp_boog': afk.lower(),
                                                                            'rayon_nr': kampioenschap.rayon.rayon_nr})
                        # for

                    elif 'O' <= comp.fase_indiv < 'P':
                        # FUTURE: zelfde logica voor het BK
                        pass
            # for
        # for

        # voeg alle inschrijvingen toe waar geen boog meer voor gekozen is,
        # zodat er afgemeld kan worden
        for inschrijving in inschrijvingen:
            afk = inschrijving.sporterboog.boogtype.afkorting
            obj = inschrijving.regiocompetitie
            objs.append(obj)

            obj.is_ingeschreven = True
            obj.boog_niet_meer = True
            obj.boog_beschrijving = boog_dict[afk].beschrijving

            comp = obj.competitie
            comp.bepaal_fase()
            if comp.fase_indiv <= 'C':
                obj.url_afmelden = reverse('CompInschrijven:afmelden',
                                           kwargs={'deelnemer_pk': inschrijving.pk})
                gebruik_knoppen = True
        # for

        return objs, gebruik_knoppen

    def _find_gemiddelden(self):
        # haal de SporterBoog records op van deze gebruiker
        objs = (SporterBoog
                .objects
                .filter(sporter=self.sporter)
                .select_related('boogtype')
                .order_by('boogtype__volgorde'))

        # zoek de AG informatie erbij
        ags = (Aanvangsgemiddelde
               .objects
               .filter(sporterboog__sporter=self.sporter,
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

    def _get_contact_gegevens(self, context):

        context['sec_namen'] = list()
        context['hwl_namen'] = list()
        context['rcl18_namen'] = list()
        context['rcl25_namen'] = list()

        if self.ver:
            regio = self.ver.regio

            context['geen_wedstrijden'] = self.ver.geen_wedstrijden

            functies = (Functie
                        .objects
                        .prefetch_related('accounts')
                        .filter(Q(rol='RCL',
                                  regio=regio) |
                                Q(rol__in=('SEC', 'HWL'),
                                  vereniging=self.ver))
                        .all())

            for functie in functies:
                namen = [account.volledige_naam() for account in functie.accounts.all()]
                namen.sort()

                if functie.rol == 'SEC':
                    # nog geen account aangemaakt, dus haal de naam op van de secretaris volgens CRM
                    if len(namen) == 0 and self.ver.secretaris_set.count() > 0:
                        sec = self.ver.secretaris_set.first()
                        namen = [sec_sporter.volledige_naam() for sec_sporter in sec.sporters.all()]
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

    def _find_speelsterktes(self):
        sterktes = Speelsterkte.objects.filter(sporter=self.sporter).order_by('volgorde')
        if sterktes.count() == 0:           # pragma: no branch
            sterktes = None
        return sterktes

    def _find_diplomas(self):
        diplomas = list(self.sporter.opleidingdiploma_set.order_by('-datum_begin'))
        if len(diplomas) == 0:           # pragma: no branch
            diplomas = None
        return diplomas

    def _find_scores(self):
        scores = list()

        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('regiocompetitie',
                                          'regiocompetitie__competitie',
                                          'sporterboog',
                                          'sporterboog__boogtype')
                          .filter(sporterboog__sporter=self.sporter,
                                  regiocompetitie__competitie__is_afgesloten=False)
                          .order_by('regiocompetitie__competitie__afstand')):

            comp = deelnemer.regiocompetitie.competitie

            if comp.is_indoor():
                deelnemer.competitie_str = "18m Indoor"
            else:
                deelnemer.competitie_str = "25m 1pijl"

            deelnemer.seizoen_str = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)

            deelnemer.scores_str = "%s, %s, %s, %s, %s, %s, %s" % (deelnemer.score1,
                                                                   deelnemer.score2,
                                                                   deelnemer.score3,
                                                                   deelnemer.score4,
                                                                   deelnemer.score5,
                                                                   deelnemer.score6,
                                                                   deelnemer.score7)

            deelnemer.boog_str = deelnemer.sporterboog.boogtype.beschrijving

            scores.append(deelnemer)
        # for
        return scores

    def _find_wedstrijden(self):
        heeft_wedstrijden = False

        vandaag = timezone.now().date()
        wedstrijden = (WedstrijdInschrijving
                       .objects
                       .filter(sporterboog__sporter=self.sporter,
                               wedstrijd__datum_begin__gte=vandaag)
                       .select_related('wedstrijd',
                                       'wedstrijd__locatie')
                       .order_by('wedstrijd__datum_begin'))

        for inschrijving in wedstrijden:
            wedstrijd = inschrijving.wedstrijd

            inschrijving.datum_str = maak_compacte_wanneer_str(wedstrijd.datum_begin, wedstrijd.datum_einde)

            inschrijving.plaats_str = wedstrijd.locatie.plaats

            if inschrijving.status in (INSCHRIJVING_STATUS_RESERVERING_MANDJE, INSCHRIJVING_STATUS_RESERVERING_BESTELD):
                inschrijving.status_str = "Reservering; bestelling is nog niet voltooid"

            elif inschrijving.status == INSCHRIJVING_STATUS_VERWIJDERD:
                inschrijving.status_str = "Deze reservering is verwijderd"

            elif inschrijving.status == INSCHRIJVING_STATUS_AFGEMELD:
                inschrijving.status_str = "Je bent afgemeld"

            if inschrijving.status == INSCHRIJVING_STATUS_DEFINITIEF and wedstrijd.eis_kwalificatie_scores:
                inschrijven_voor = wedstrijd.datum_begin - datetime.timedelta(days=wedstrijd.inschrijven_tot + 1)
                inschrijving.mag_kwalificatiescores_aanpassen = timezone.now().date() < inschrijven_voor

                inschrijving.url_kwalificatie_scores = reverse('WedstrijdInschrijven:inschrijven-kwalificatie-scores',
                                                               kwargs={'inschrijving_pk': inschrijving.pk})

            inschrijving.url_details = reverse('Wedstrijden:wedstrijd-details',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})

            heeft_wedstrijden = True
        # for

        return heeft_wedstrijden, wedstrijden

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        self.voorkeuren = get_sporter_voorkeuren(self.sporter)

        if self.ver:
            is_administratief = self.ver.regio.is_administratief      # dus helemaal geen wedstrijden
            is_extern = self.ver.is_extern                            # dus geen bondscompetities
        else:
            is_administratief = False
            is_extern = False

        context['sporter'] = self.sporter
        context['records'], context['show_loc'] = self._find_records()

        if not self.sporter.is_gast:
            context['url_bondspas'] = reverse('Bondspas:toon-bondspas')

        boog_afk2sporterboog, boog_afkorting_wedstrijd = get_sporter_gekozen_bogen(self.sporter, self.alle_bogen)
        context['moet_bogen_kiezen'] = len(boog_afkorting_wedstrijd) == 0

        context['toon_bondscompetities'] = False
        if self.ver and not self.ver.geen_wedstrijden and not (is_extern or is_administratief):

            context['toon_bondscompetities'] = True

            context['histcomp'] = self._find_histcomp_scores()

            context['competities'] = comps = self._find_competities()

            regiocomps, gebruik_knoppen = self._find_regiocompetities(comps,
                                                                      boog_afk2sporterboog,
                                                                      boog_afkorting_wedstrijd)
            context['regiocompetities'] = regiocomps
            context['hint_voorkeuren'] = regiocomps is not None and len(regiocomps) == 0
            context['gebruik_knoppen'] = gebruik_knoppen

            context['regiocomp_scores'] = self._find_scores()

            context['gemiddelden'], context['heeft_ags'] = self._find_gemiddelden()

            if not self.voorkeuren.voorkeur_meedoen_competitie:
                if regiocomps is None:
                    # niet ingeschreven en geen interesse
                    context['toon_bondscompetities'] = False

            context['speelsterktes'] = self._find_speelsterktes()
            context['url_spelden_procedures'] = settings.URL_SPELDEN_PROCEDURES

            context['diplomas'] = self._find_diplomas()

            context['toon_wedstrijden'], context['wedstrijden'] = self._find_wedstrijden()

        if self.sporter.is_gast:
            context['gast'] = self.sporter.gastregistratie_set.first()

        if Bestelling.objects.filter(account=self.account).count() > 0:
            context['toon_bestellingen'] = True

        self._get_contact_gegevens(context)

        context['kruimels'] = (
            (None, 'Mijn pagina'),
        )

        return context


# end of file
