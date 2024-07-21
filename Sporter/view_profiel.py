# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from Account.models import get_account
from BasisTypen.models import BoogType
from Bestel.models import Bestelling
from Competitie.definities import DEEL_RK, INSCHRIJF_METHODE_1, DEELNAME_NEE
from Competitie.models import Regiocompetitie, RegiocompetitieSporterBoog, KampioenschapSporterBoog
from Competitie.plugin_sporter import get_sporter_competities
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

    def _find_contactgegevens(self, context):
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

        boog_afk2sporterboog, wedstrijdbogen = get_sporter_gekozen_bogen(self.sporter, self.alle_bogen)
        context['moet_bogen_kiezen'] = len(wedstrijdbogen) == 0

        context['toon_bondscompetities'] = False
        if self.ver and not self.ver.geen_wedstrijden and not (is_extern or is_administratief):

            context['toon_bondscompetities'] = True

            context['histcomp'] = self._find_histcomp_scores()

            lijst_comps, lijst_kan_inschrijven, lijst_inschrijvingen = get_sporter_competities(self.sporter,
                                                                                               wedstrijdbogen,
                                                                                               boog_afk2sporterboog)

            context['competities'] = lijst_comps
            context['comp_kan_inschrijven'] = len(lijst_kan_inschrijven) > 0
            context['deelcomps_lijst_kan_inschrijven'] = lijst_kan_inschrijven

            context['comp_is_ingeschreven'] = len(lijst_inschrijvingen) > 0
            context['comp_inschrijvingen_sb'] = lijst_inschrijvingen

            context['regiocomp_scores'] = self._find_scores()

            context['gemiddelden'], context['heeft_ags'] = self._find_gemiddelden()

            if not self.voorkeuren.voorkeur_meedoen_competitie:
                if len(lijst_inschrijvingen) == 0:
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

        self._find_contactgegevens(context)

        context['kruimels'] = (
            (None, 'Mijn pagina'),
        )

        return context


# end of file
